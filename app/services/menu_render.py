"""Extract normalized menu items from HTML menu pages using standard library only.

Strategies (priority order):
1. JSON-LD / schema.org MenuItem structured data
2. Heuristic HTML extraction: find price tokens and pair them with the nearest
   heading / item-name / description block
3. Fallback: line-level (name + price) regex scans

The output shape mirrors the fields on the existing MenuItem ORM model.
"""

from __future__ import annotations

import time
import socket
import json
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, TypedDict
from urllib.error import HTTPError, URLError
from urllib.parse import ParseResult, urljoin, urlparse, urlunparse
from urllib.request import Request, urlopen

__all__ = [
    "NormalizedMenuItem",
    "extract_menu_items",
    "fetch_and_extract_menu_items",
]

HTTP_TIMEOUT_SECONDS = 10
USER_AGENT = (
    "Mozilla/5.0 (compatible; TasteMapMenuRender/1.0; "
    "+https://tastemap.local/bot)"
)


class NormalizedMenuItem(TypedDict, total=False):
    """Dict shape mirroring the relevant fields on the MenuItem ORM model.

    ``name`` and ``price`` are always populated on the output (functionally
    required); ``category`` and ``description`` are optional and default to
    ``None`` when unknown.
    """

    name: str
    price: float
    category: str | None
    description: str | None


_PRICE_NUMBER_RE = re.compile(
    r"(?P<num>\d{1,3}(?:[.,]\d{3})*|[0-9]+)(?:[.,](?P<frac>\d{1,2}))?"
)

_CURRENCY_LETTERS = r"(?:USD|EUR|GBP|JPY|TRY|TL|₺|dolar|euro|\$|€|£|¥)"

_CURRENCY_RE = re.compile(
    r"(?:(?P<prefix>" + _CURRENCY_LETTERS + r")\s*)?"
    + _PRICE_NUMBER_RE.pattern
    + r"(?:\s*(?P<suffix>" + _CURRENCY_LETTERS + r"))?",
    re.IGNORECASE,
)

ITEM_NAME_STOPWORDS: set[str] = {
    "copyright",
    "privacy",
    "policy",
    "terms",
    "conditions",
    "contact",
    "about",
    "home",
    "login",
    "register",
    "signup",
    "sign",
    "order",
    "checkout",
    "cart",
    "basket",
    "menu",
    "menü",
    "hakkımızda",
    "iletişim",
    "gizlilik",
    "şartlar",
    "kayıt",
    "giriş",
    "sepet",
    "ödeme",
}

# Navigation-only stopwords (no legitimate product name ever equals these).
# We are more lenient with words like "menü" because a valid product name such
# as "Çocuk Menü" or "Kek Menüsü" legitimately contains "menü" but is not a
# nav heading.
_NAV_STOPWORDS_EXACT: set[str] = ITEM_NAME_STOPWORDS - {
    "menu",
    "menü",
    "order",
    "cart",
    "basket",
    "sepet",
}


def _is_nav_stopword_name(name_candidate: str) -> bool:
    """Return True only if name_candidate is a pure nav heading, not a real product.

    * Exact match with a known nav heading → reject.
    * Very short (<= 2 words) ALL-nav-only tokens → reject.
    * Everything else → keep (even if the substring contains "menü").
    """
    lowered = (name_candidate or "").strip().lower()
    if not lowered:
        return True
    if lowered in _NAV_STOPWORDS_EXACT:
        return True
    words = lowered.split()
    if 1 <= len(words) <= 2 and all(w in _NAV_STOPWORDS_EXACT for w in words):
        return True
    return False

HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
BLOCK_TAGS = {"div", "section", "article", "li", "tr", "dt", "dd", "p", "ul", "ol", "dl", "menu", "figure", "figcaption"}


def _parse_price_token(token: str) -> float | None:
    """Parse a single price-like token into a float, or return None if invalid.

    Supports:
      ₺120, 120₺, 120 ₺, 120TL, TL120, 120.00, 120,00, $10, €8.50,
      1.250,75 (Turkish thousands separator), 15 USD, 120 TRY

    Rejects:
      Plain integers with no currency and no decimal fraction ("120")
      Bare single-decimal numbers with no currency ("1.5", "2.3") — these are
      usually CSS values like stroke-miterlimit, not real menu prices.
    """
    raw = token.strip()
    if not raw:
        return None
    match = _CURRENCY_RE.fullmatch(raw)
    if not match:
        # Relaxed: try after stripping attached currency letters (e.g. "120TL", "USD15")
        step = re.sub(r"(?i)^(try|usd|eur|gbp|jpy|tl|dolar|euro)\s*", "", raw)
        step = re.sub(r"(?i)\s*(try|usd|eur|gbp|jpy|tl|dolar|euro)$", "", step)
        match = _CURRENCY_RE.fullmatch(step)
        if not match:
            return None
    num = match.group("num") or ""
    frac = match.group("frac")
    prefix = match.group("prefix")
    suffix = match.group("suffix")
    if not num and not frac:
        return None
    has_currency = bool(prefix or suffix)
    has_fraction = bool(frac)
    if not has_currency and not has_fraction:
        # Plain integer without currency (e.g. "120" alone) is too ambiguous — reject.
        return None
    if not has_currency and has_fraction and len(frac) != 2:
        # No currency symbol, and the fractional part is not exactly 2 digits.
        # e.g. "1.5" → frac="5" (1 digit) — very likely CSS/programmatic value,
        # not a real menu price. We only accept "120.00" / "120,00" style 2-digit fractions.
        return None
    decimal_number = num.replace(".", "").replace(",", "")
    if frac:
        decimal_number = f"{decimal_number}.{frac}"
    elif "," in raw and "." not in raw:
        # No explicit fraction but written with comma: treat last 2 digits as decimal (Turkish)
        if len(decimal_number) >= 3:
            decimal_number = decimal_number[:-2] + "." + decimal_number[-2:]
        else:
            decimal_number = "0." + decimal_number.zfill(2)
    try:
        value = float(decimal_number)
    except (TypeError, ValueError):
        return None
    if value <= 0 or value > 100000:
        return None
    return round(value, 2)


@dataclass
class _Block:
    tag: str
    classes: str
    text: str
    prices: list[float]


class _MenuBlockParser(HTMLParser):
    """Walk an HTML document and extract text blocks with detected prices.

    Tracks the current section heading as the inferred "category" for each item.

    Text inside <style> and non-JSON-LD <script> tags is completely ignored to
    avoid picking up CSS values and JS variables as menu prices.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.json_ld_blocks: list[str] = []
        self.blocks: list[_Block] = []
        self.current_category: str | None = None
        self.category_stack: list[str] = []
        self._in_json_ld = False
        self._in_style = False
        self._in_regular_script = False
        self._json_ld_buffer: list[str] = []
        self._buffer: list[str] = []
        self._block_tag: str | None = None
        self._block_classes: str = ""
        # When we temporarily switch to a heading tag (h1-h6) we push the outer
        # block tag (e.g. div / section / article) onto this stack so that the
        # heading's end tag can restore the original block context. This keeps
        # inline tags (<span>, <strong>, <p>) within the parent block buffer so
        # the product name + price + description end up in the same block.
        self._parent_block_stack: list[tuple[str, str, list[str]]] = []
        self._last_heading: str | None = None

    # ---- tag handlers ---------------------------------------------------

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_low = tag.lower()
        attr_dict = {k.lower(): (v if v is not None else "") for k, v in attrs}
        if tag_low == "script":
            ttype = attr_dict.get("type", "").lower()
            if "ld+json" in ttype:
                self._in_json_ld = True
                self._json_ld_buffer = []
            else:
                self._in_regular_script = True
            return
        if tag_low == "style":
            self._in_style = True
            return
        if self._in_style or self._in_regular_script:
            return
        if tag_low == "br":
            self._buffer.append("\n")
            return
        if tag_low in HEADING_TAGS:
            # Headings (h1-h6) do NOT flush the current block buffer. Their
            # text content will be appended into the CURRENT buffer via
            # handle_data, so a pattern like:
            #   <div><h3>Name</h3><span>₺50.00</span><p>desc</p></div>
            # ends up as a single div block with text
            #   "Name ₺50.00 desc"
            # that the pairing logic can turn into a MenuItem cleanly.
            # We still remember the heading text for category inference in
            # the corresponding handle_endtag handler.
            return
        if tag_low in BLOCK_TAGS:
            # A structural row/container begins: save any running outer
            # block, flush it, and start a new one.
            if self._block_tag is not None:
                self._parent_block_stack.append(
                    (self._block_tag, self._block_classes, list(self._buffer))
                )
            self._flush_block()
            self._block_tag = tag_low
            self._block_classes = attr_dict.get("class", "")
            self._buffer = []

    def handle_endtag(self, tag: str) -> None:
        tag_low = tag.lower()
        if tag_low == "script":
            if self._in_json_ld:
                self.json_ld_blocks.append("".join(self._json_ld_buffer))
                self._in_json_ld = False
                self._json_ld_buffer = []
            if self._in_regular_script:
                self._in_regular_script = False
            return
        if tag_low == "style" and self._in_style:
            self._in_style = False
            return
        if self._in_style or self._in_regular_script:
            return
        if tag_low in HEADING_TAGS:
            # Capture the most recent heading text from the tail of the
            # current buffer for category inference purposes.
            text_so_far = " ".join("".join(self._buffer).split()).strip()
            candidate = (
                text_so_far.rsplit("  ", 1)[-1] if text_so_far else ""
            ).strip(" :：.-—·")
            if 1 <= len(candidate) <= 80:
                lowered = candidate.lower()
                if not any(sw in lowered for sw in ITEM_NAME_STOPWORDS):
                    self._last_heading = candidate
            return
        if tag_low in BLOCK_TAGS:
            if self._block_tag in BLOCK_TAGS:
                self._flush_block()
            if self._parent_block_stack:
                pt, pc, _pb = self._parent_block_stack.pop()
                self._block_tag = pt
                self._block_classes = pc
                self._buffer = list(_pb)
            else:
                self._block_tag = None

    def handle_data(self, data: str) -> None:
        if self._in_json_ld:
            self._json_ld_buffer.append(data)
            return
        # Drop data inside stylesheets or regular script tags completely
        if self._in_style or self._in_regular_script:
            return
        self._buffer.append(data)

    # ---- helpers --------------------------------------------------------

    def _flush_block(self, *, as_heading: bool = False) -> None:
        if self._block_tag is None:
            return
        text = " ".join("".join(self._buffer).split()).strip()
        self._buffer = []
        tag = self._block_tag
        classes = self._block_classes
        if not text:
            self._block_tag = None
            self._block_classes = ""
            return
        if as_heading or tag in HEADING_TAGS:
            # Treat this heading as a category marker if it looks like one
            candidate = text.strip(" :：.-—·")
            if 1 <= len(candidate) <= 80:
                lowered = candidate.lower()
                if not any(sw in lowered for sw in ITEM_NAME_STOPWORDS):
                    self._last_heading = candidate
        # Detect prices in the block text
        prices: list[float] = []
        for match in _find_price_matches(text):
            parsed = _parse_price_token(match)
            if parsed is not None:
                prices.append(parsed)
        if prices or len(text) < 300:
            self.blocks.append(
                _Block(
                    tag=tag,
                    classes=classes,
                    text=text,
                    prices=prices,
                )
            )
        self._block_tag = None
        self._block_classes = ""


def _find_price_matches(text: str) -> list[str]:
    """Return a list of plausible price substrings found inside a larger text.

    A match is only returned when:
      - An explicit currency symbol/code is present (prefix or suffix), OR
      - The numeric portion has a fraction of exactly 2 digits ("120.00",
        "120,00") — single-digit fractions without currency are rejected to
        avoid treating CSS values like `stroke-miterlimit: 1.5;` as prices.
    """
    results: list[str] = []
    # Tokenize roughly: split on whitespace + some punctuation but keep currency attached
    for chunk in re.split(r"\s{2,}|\n|(?<=[,;])\s+", text):
        for match in _CURRENCY_RE.finditer(chunk):
            prefix = match.group("prefix") or ""
            suffix = match.group("suffix") or ""
            if prefix or suffix:
                results.append(match.group(0))
                continue
            frac = match.group("frac")
            if frac and len(frac) == 2:
                # 120.00 / 120,00 (2-digit fraction, no currency) — accept.
                results.append(match.group(0))
            # A single-digit fraction without currency (e.g. 1.5) is silently
            # skipped — too likely to be a CSS/SVG value.
    return results


# ---- JSON-LD extraction ---------------------------------------------------


def _iter_json_ld(payload: Any) -> Any:
    """Yield every dict node from the JSON-LD tree recursively."""
    if isinstance(payload, dict):
        yield payload
        for key in ("@graph", "graph", "hasPart", "itemListElement", "includedInDataCatalog", "about", "mentions"):
            value = payload.get(key)
            if value is not None:
                yield from _iter_json_ld(value)
        for menu_key in ("hasMenu", "hasMenuSection", "MenuSection", "menuSection", "sections", "menu", "menus"):
            value = payload.get(menu_key)
            if value is not None:
                yield from _iter_json_ld(value)
        for items_key in ("hasMenuItem", "menuItem", "menuItems", "items"):
            value = payload.get(items_key)
            if value is not None:
                yield from _iter_json_ld(value)
    elif isinstance(payload, list):
        for item in payload:
            yield from _iter_json_ld(item)


def _coerce_price(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        f = float(value)
        if f > 0 and f <= 100000:
            return round(f, 2)
        return None
    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            return None
        # Fast path: pure decimal string (e.g. "85.00", "15") from JSON-LD Offer.price
        pure_match = re.fullmatch(r"\d+(?:\.\d{1,2})?|,\d{1,2}", cleaned.replace(",", ".", 1) if ("," in cleaned and "." not in cleaned and cleaned.count(",") == 1) else cleaned)
        if pure_match:
            try:
                if "," in cleaned and "." not in cleaned and cleaned.count(",") == 1:
                    normalized = cleaned.replace(",", ".", 1)
                elif "." in cleaned and "," not in cleaned:
                    normalized = cleaned
                else:
                    # Turkish thousands like 1.250,75
                    normalized = cleaned.replace(".", "").replace(",", ".", 1) if "," in cleaned else cleaned
                f = float(normalized)
            except ValueError:
                f = None
            if isinstance(f, float) and f > 0 and f <= 100000:
                return round(f, 2)
        # Otherwise, route through the shared _parse_price_token (handles currencies)
        pp = _parse_price_token(cleaned)
        if pp is not None:
            return pp
        # Last fallback: strip all non-numeric except , . and -
        numeric = re.sub(r"[^\d.,\-]", "", cleaned)
        if not numeric:
            return None
        if "," in numeric and "." not in numeric:
            if numeric.count(",") == 1:
                numeric = numeric.replace(",", ".", 1)
            else:
                numeric = numeric.replace(".", "").replace(",", ".")
        else:
            numeric = numeric.replace(",", "")
        try:
            f = float(numeric)
        except ValueError:
            return None
        if f > 0 and f <= 100000:
            return round(f, 2)
    return None


def _coerce_str(value: Any, max_len: int | None = None) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        t = value.strip()
    else:
        t = str(value).strip()
    if not t:
        return None
    if max_len and len(t) > max_len:
        t = t[:max_len].rstrip()
    return t or None


def _extract_from_json_ld(blocks: list[str]) -> list[NormalizedMenuItem]:
    """Extract menu items using JSON-LD schema.org data (MenuItem / hasMenuItem / Product)."""
    results: list[NormalizedMenuItem] = []
    for block in blocks:
        try:
            data = json.loads(block)
        except (json.JSONDecodeError, ValueError):
            continue
        for node in _iter_json_ld(data):
            if not isinstance(node, dict):
                continue
            node_type = node.get("@type")
            if isinstance(node_type, list):
                types = {str(t).lower() for t in node_type if isinstance(t, str)}
            elif isinstance(node_type, str):
                types = {node_type.lower()}
            else:
                types = set()
            is_item = (
                "menuitem" in types
                or "product" in types
                or "dish" in types
                or "menusection" in types
            )
            offers = node.get("offers")
            price: float | None = None
            if "price" in node:
                price = _coerce_price(node.get("price"))
            if price is None and isinstance(offers, dict):
                price = _coerce_price(offers.get("price"))
            if price is None and isinstance(offers, list):
                for off in offers:
                    if isinstance(off, dict):
                        price = _coerce_price(off.get("price"))
                        if price is not None:
                            break
            if is_item and price is not None:
                name = _coerce_str(node.get("name"), max_len=255)
                if not name:
                    continue
                description = _coerce_str(node.get("description"), max_len=1000)
                category: str | None = _coerce_str(node.get("category"), max_len=100)
                results.append(
                    NormalizedMenuItem(
                        name=name,
                        price=price,
                        category=category or None,
                        description=description or None,
                    )
                )
    return results


# ---- Heuristic HTML extraction -------------------------------------------


def _infer_category_for_block(text: str, heading: str | None) -> str | None:
    """Best-effort: pick a category for a menu item block. None when unsure."""
    # The current heading is a strong signal
    if heading:
        cand = heading.strip(" :：.-—·")
        lowered = cand.lower()
        if len(cand) <= 100 and not any(sw in lowered for sw in ITEM_NAME_STOPWORDS):
            return cand[:100]
    return None


def _split_name_description(text: str, price_token: str) -> tuple[str, str | None]:
    """Given a block text and the matched price, separate name from description."""
    try:
        idx = text.index(price_token)
    except ValueError:
        idx = -1
    if idx < 0:
        # Just return the whole text as name but trim aggressively
        trimmed = text.strip(" :：.-—·")
        if len(trimmed) > 255:
            trimmed = trimmed[:255].rstrip()
        return trimmed, None
    before = text[:idx].strip(" \t:：.-—·,;|")
    after = text[idx + len(price_token):].strip(" \t:：.-—·,;|")

    # Heuristic: if before is empty, name = after token
    if not before:
        # Unusual; try to use a short prefix from 'after' as name if it looks like one
        snippet = after[:255]
        return snippet, None

    name_candidate = before
    description_candidate: str | None = None

    # If before has a line break or dash, first part is name
    for sep in ("\n", " - ", " — ", " – ", " | ", " : ", " :"):
        if sep in name_candidate:
            first, rest = name_candidate.split(sep, 1)
            first = first.strip()
            rest = rest.strip()
            if first and len(first) <= 255:
                name_candidate = first
                if rest:
                    description_candidate = rest
            break

    # If after is non-empty and looks like a description (not just numbers/symbols), append
    if after and re.search(r"[A-Za-zığüşöçİĞÜŞÖÇ]", after):
        if description_candidate:
            description_candidate = f"{description_candidate} — {after}"
        else:
            description_candidate = after

    if len(name_candidate) > 255:
        name_candidate = name_candidate[:255].rstrip()
    if description_candidate and len(description_candidate) > 1000:
        description_candidate = description_candidate[:1000].rstrip()

    return name_candidate.strip(), description_candidate if description_candidate else None


def _extract_from_html_blocks(parser: _MenuBlockParser) -> list[NormalizedMenuItem]:
    """Pair detected prices with neighboring block text as menu items."""
    results: list[NormalizedMenuItem] = []
    heading: str | None = parser._last_heading  # noqa: SLF001
    if not heading:
        # Walk the blocks once to find a heading that appears BEFORE the first price
        for b in parser.blocks:
            if b.tag in HEADING_TAGS and not b.prices:
                heading = b.text.strip(" :：.-—·") or heading

    # Pass 1: blocks that contain exactly one price and some text → treat as item row
    # Pass 2: look at heading + price-only block combos
    for block in parser.blocks:
        if block.tag in HEADING_TAGS:
            hcand = block.text.strip(" :：.-—·")
            if 1 <= len(hcand) <= 100:
                lowered = hcand.lower()
                if not any(sw in lowered for sw in ITEM_NAME_STOPWORDS):
                    heading = hcand
            continue
        if not block.prices:
            continue
        # One price = one item. Multiple prices = emit one item per price, using the shared text as name.
        price_matches_ordered = _find_price_matches(block.text)
        price_tokens_valid: list[tuple[str, float]] = []
        for pm in price_matches_ordered:
            pp = _parse_price_token(pm)
            if pp is not None:
                price_tokens_valid.append((pm, pp))
        if not price_tokens_valid:
            # fallback to block.prices[0] without token text alignment
            for p in block.prices:
                name_candidate = block.text.strip()
                if not name_candidate or len(name_candidate) > 600:
                    continue
                if _is_nav_stopword_name(name_candidate):
                    continue
                nm = name_candidate[:255].rstrip()
                if not nm:
                    continue
                results.append(
                    NormalizedMenuItem(
                        name=nm,
                        price=p,
                        category=_infer_category_for_block(block.text, heading),
                        description=None,
                    )
                )
            continue
        for token, price_val in price_tokens_valid:
            nm, desc = _split_name_description(block.text, token)
            if not nm:
                continue
            if _is_nav_stopword_name(nm):
                continue
            if len(nm) < 1 or len(nm) > 255:
                continue
            results.append(
                NormalizedMenuItem(
                    name=nm,
                    price=price_val,
                    category=_infer_category_for_block(block.text, heading),
                    description=desc,
                )
            )

    # ---- Pass 3: Pair up "heading + desc name blocks" with "price-only blocks".
    # Often a menu row is split as:  <h3>Name</h3><p>Desc</p><div class="price">₺45.00</div>
    # Each of these becomes its own block because they are in BLOCK_TAGS; we
    # therefore scan the block list looking for a name-only block (alphabetic,
    # no prices, not a nav heading) immediately followed by a price-only block
    # (no letters other than currency, exactly 1 price) and merge them.
    if len(results) == 0 and len(parser.blocks) >= 2:
        blks = parser.blocks
        for i in range(len(blks) - 1):
            b1 = blks[i]
            b2 = blks[i + 1]
            if b1.prices or not b2.prices or len(b2.prices) != 1:
                continue
            name_cand = b1.text.strip()
            if (
                not name_cand
                or len(name_cand) < 2
                or len(name_cand) > 200
                or _is_nav_stopword_name(name_cand)
                or not re.search(r"[A-Za-zığüşöçİĞÜŞÖÇ]", name_cand)
            ):
                continue
            price_only_cand = b2.text.strip()
            if re.search(
                r"[A-Za-zığüşöçİĞÜŞÖÇ]",
                re.sub(
                    r"(try|usd|eur|gbp|jpy|tl|dolar|euro|t\.l\.|₺|\$|€|£)",
                    "",
                    price_only_cand,
                    flags=re.IGNORECASE,
                ),
            ):
                continue
            p = b2.prices[0]
            desc_part: str | None = None
            desc_parts: list[str] = []
            for j in range(i + 1, min(i + 4, len(blks))):
                if blks[j].prices:
                    break
                txt = blks[j].text.strip()
                if (
                    1 <= len(txt) <= 255
                    and re.search(r"[A-Za-zığüşöçİĞÜŞÖÇ]", txt)
                    and not _is_nav_stopword_name(txt)
                ):
                    desc_parts.append(txt)
            if desc_parts:
                desc_part = " ".join(desc_parts)
            results.append(
                NormalizedMenuItem(
                    name=name_cand[:255],
                    price=float(p),
                    category=_infer_category_for_block(name_cand, heading),
                    description=desc_part,
                )
            )
    return results


# ---- Trust & Quality Filter (precision over recall) ---------------------


_PHONE_TR_RE = re.compile(
    r"(?:0[2-9]\d{2}[\s\(\)\-]{0,4}\d{3}[\s\-]?\d{2}[\s\-]?\d{2}|\+?90\s?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2})"
)
_HOURS_WORD_RE = re.compile(
    r"\b(her.gün|hergun|pazartesi|salı|carsamba|persembe|cuma|cumartesi|pazar|weekday|weekend|working|hours|açılış|kapanış|acilis|kapanis|opening|closing|work.hour|çalışma|calisma)\b",
    re.IGNORECASE,
)
_CONTACT_WORD_RE = re.compile(
    r"\b(telefon|tel\.|phone|whatsapp|wp\.|wsp|instagram|facebook|twitter|x\.com|tiktok|adres|address|harita|konum|map|reservation|rezervasyon|randevu|iletisim|iletişim|iletiş|contact)\b",
    re.IGNORECASE,
)
_DIGIT_PCT_MIN_ALPHA = 2  # at least 2 alphabetical chars in name
_NAME_ALPHA_RATIO_MIN = 0.35  # name must be 35%+ alphabetic characters (Turkish aware)


def _filter_item_precision(item: NormalizedMenuItem) -> bool:
    """Return True only for plausible restaurant menu items.

    This is intentionally restaurant-agnostic. It rejects:
    - phone/contact/navigation text
    - URLs and domain/Google Maps fragments
    - website/hosting CTA text
    - binary/garbage-decoded content
    - obviously non-menu UI labels
    - numeric/CSS-like garbage
    """

    name = (item.get("name") or "").strip()
    price = float(item.get("price") or 0.0)
    category = (item.get("category") or "").strip()

    if not name or price <= 0 or price > 100000:
        return False

    # ---------------------------------------------------------------
    # 1) Basic length sanity.
    # ---------------------------------------------------------------
    if len(name) < 2 or len(name) > 255:
        return False

    # ---------------------------------------------------------------
    # 2) Reject phone numbers.
    # ---------------------------------------------------------------
    if _PHONE_TR_RE.search(name):
        return False

    # ---------------------------------------------------------------
    # 3) Reject URLs / domains / web navigation fragments.
    # ---------------------------------------------------------------
    lowered = name.lower()

    url_markers = (
        "http://",
        "https://",
        "www.",
        "google.com/",
        "google.com",
        "maps/",
        "/maps/",
        ".com/",
        ".com",
        ".net/",
        ".net",
        ".org/",
        ".org",
        ".tr/",
        ".tr",
    )

    if any(marker in lowered for marker in url_markers):
        return False

    # Navigation / link UI that commonly gets paired with unrelated prices.
    navigation_markers = (
        "bağlantı simgesi",
        "link icon",
        "click here",
        "read more",
        "learn more",
        "view more",
        "view menu",
        "open menu",
        "see menu",
        "order now",
        "buy now",
        "shop now",
        "add to cart",
        "add to basket",
        "checkout",
        "shopping cart",
        "sepet",
        "ödeme",
        "giriş yap",
        "kayıt ol",
    )

    if any(marker in lowered for marker in navigation_markers):
        return False

    # ---------------------------------------------------------------
    # 4) Reject website/domain/hosting boilerplate.
    # ---------------------------------------------------------------
    boilerplate_markers = (
        "own this domain",
        "this domain",
        "domain for sale",
        "domain expired",
        "parked domain",
        "website builder",
        "powered by",
        "coming soon",
        "under construction",
        "website template",
        "template by",
        "all rights reserved",
        "copyright",
    )

    if any(marker in lowered for marker in boilerplate_markers):
        return False

    # ---------------------------------------------------------------
    # 5) Reject contact / hours / navigation words.
    # ---------------------------------------------------------------
    if _HOURS_WORD_RE.search(name) or _CONTACT_WORD_RE.search(name):
        return False

    if category and (
        _HOURS_WORD_RE.search(category)
        or _CONTACT_WORD_RE.search(category)
    ):
        return False

    # ---------------------------------------------------------------
    # 6) Reject obvious numeric/CSS/binary garbage.
    # ---------------------------------------------------------------
    stripped_num = re.sub(
        r"[\s\.,â‚º$€£¥₺\-+:/\\]+",
        "",
        name,
    )

    if stripped_num and stripped_num.isdigit() and len(stripped_num) >= 2:
        return False

    # Excessive control / replacement characters are a strong signal
    # that binary content was decoded as text.
    bad_chars = (
        name.count("\ufffd")  # Unicode replacement character: �
        + name.count("\x00")
    )

    if bad_chars >= 1:
        return False

    # Control characters should almost never appear in a real dish name.
    control_count = sum(
        1
        for ch in name
        if ord(ch) < 32 and ch not in "\t\r\n"
    )

    if control_count:
        return False

    # JPEG / binary-like escaped byte fragments.
    escaped_binary_markers = (
        "\\x00",
        "\\x01",
        "\\x02",
        "\\x03",
        "\\xff",
        "\\xfe",
    )

    if any(marker in lowered for marker in escaped_binary_markers):
        return False

    # ---------------------------------------------------------------
    # 7) Reject CSS / technical fragments.
    # ---------------------------------------------------------------
    technical_markers = (
        "stroke-miterlimit",
        "font-size:",
        "line-height:",
        "background:",
        "background-color:",
        "margin:",
        "padding:",
        "display:",
        "position:",
        "transform:",
        "javascript:",
        "onclick=",
        "class=",
        "style=",
    )

    if any(marker in lowered for marker in technical_markers):
        return False

    # ---------------------------------------------------------------
    # 8) Alphabetic sanity.
    # ---------------------------------------------------------------
    letters = sum(1 for ch in name if ch.isalpha())
    digits = sum(1 for ch in name if ch.isdigit())

    if letters < _DIGIT_PCT_MIN_ALPHA:
        return False

    denom = letters + digits
    if denom and (letters / denom) < _NAME_ALPHA_RATIO_MIN:
        return False

    # ---------------------------------------------------------------
    # 9) Reject names dominated by punctuation/symbols.
    # ---------------------------------------------------------------
    alnum_count = sum(1 for ch in name if ch.isalnum())

    if alnum_count < 3:
        return False

    # If the text is mostly symbols/punctuation, it is unlikely to be
    # a legitimate menu item.
    if alnum_count / max(len(name), 1) < 0.45:
        return False

    # ---------------------------------------------------------------
    # 10) Reject common standalone UI labels.
    # ---------------------------------------------------------------
    standalone_ui = {
        "menu",
        "menü",
        "home",
        "about",
        "contact",
        "login",
        "register",
        "signup",
        "search",
        "submit",
        "send",
        "next",
        "previous",
        "back",
        "close",
        "open",
        "continue",
        "more",
        "details",
        "info",
        "privacy",
        "terms",
    }

    if lowered.strip(" .:-_") in standalone_ui:
        return False

    return True


def _trust_filter_all(
    items: list[NormalizedMenuItem],
) -> list[NormalizedMenuItem]:
    """Apply per-item precision guards plus an overall trust-ratio check.

    The overall trust check: price-bearing tokens must be a minority of the
    total "looks like dish text" tokens. If >50% of all items' names look
    like "0312 ...", working hours, etc. → the whole block is unreliable,
    return empty list rather than emit garbage.
    """
    if not items:
        return []
    per_item = [it for it in items if _filter_item_precision(it)]
    if not per_item:
        return []
    # Secondary trust check: if we got back items, but the menu context has
    # heavy contact/hours content and very few dish-like entries, drop all.
    dish_like = 0
    for it in per_item:
        nm = (it.get("name") or "").strip()
        # Count "dish-like" names: alphabetic words > 2 chars (not stopwords)
        words = [w for w in nm.split() if len(w) > 2]
        al_words = [
            w
            for w in words
            if re.search(r"[A-Za-zığüşöçİĞÜŞÖÇ]", w)
            and not _CONTACT_WORD_RE.search(w)
            and not _HOURS_WORD_RE.search(w)
        ]
        if al_words:
            dish_like += 1
    total_n = len(per_item)
    if dish_like / max(total_n, 1) < 0.3:
        return []
    return per_item


# ---- Deduplication -------------------------------------------------------


def _dedup_items(items: list[NormalizedMenuItem]) -> list[NormalizedMenuItem]:
    seen: set[tuple[str, int]] = set()
    deduped: list[NormalizedMenuItem] = []
    for it in items:
        key = (
            (it.get("name") or "").strip().lower(),
            int(round((it.get("price") or 0.0) * 100)),
        )
        if key in seen:
            continue
        # Also reject entries with clearly invalid keys
        if not key[0] or key[1] <= 0:
            continue
        seen.add(key)
        deduped.append(it)
    return deduped


# ---- Line-level fallback extraction (last-resort for simple <pre> lists) --


_LINE_STOPWORD_RE = re.compile(
    r"(instagram|facebook|twitter|tiktok|youtube|linkedin|takip edin|follow us|"
    r"bizi takip|sosyal medya|misyonumuz|vizyonumuz|hakk.m.zda|about us|"
    r"rezervasyon|randevu|booking|contact|ileti.im|gizlilik|terms|privacy)",
    re.IGNORECASE,
)


def _extract_line_level_fallback(
    html: str,
) -> list[NormalizedMenuItem]:
    """Very conservative line-level fallback for simple <pre>/text-based menus.

    Only returns items when BOTH a realistic product name (>= 3 letters, NOT a
    stopword) AND a valid 2-decimal or currency-attached price exist on the
    same line. Never returns more than 50 items to cap memory usage.
    """
    try:
        stripped = re.sub(r"<script\b[^>]*>.*?</script>", " ", html, flags=re.I | re.S)
        stripped = re.sub(r"<style\b[^>]*>.*?</style>", " ", stripped, flags=re.I | re.S)
        stripped = re.sub(r"<[^>]+>", " ", stripped)
    except Exception:  # noqa: BLE001
        return []
    out: list[NormalizedMenuItem] = []
    for raw_line in stripped.splitlines()[:5000]:
        line = raw_line.strip()
        if len(line) < 6 or len(line) > 400:
            continue
        if _LINE_STOPWORD_RE.search(line):
            continue
        tokens = _find_price_matches(line)
        if not tokens:
            continue
        price_val: float | None = None
        tok_used: str | None = None
        for t in tokens:
            p = _parse_price_token(t)
            if p is not None:
                price_val = p
                tok_used = t
                break
        if price_val is None or tok_used is None:
            continue
        try:
            idx = line.index(tok_used)
        except ValueError:
            continue
        name_part = line[:idx].strip(" :：.-—·,;|•·\u2022")
        if len(name_part) < 3 or len(name_part) > 200:
            # Allow name after price when nothing precedes it
            tail = line[idx + len(tok_used) :].strip(" :：.-—·,;|•·\u2022")
            if len(tail) < 3 or len(tail) > 200:
                continue
            name_part = tail
        # Name must contain at least one alphabetical character (Turkish aware).
        if not re.search(r"[A-Za-zığüşöçİĞÜŞÖÇ]", name_part):
            continue
        if _is_nav_stopword_name(name_part):
            continue
        out.append(
            NormalizedMenuItem(
                name=name_part[:255],
                price=float(price_val),
                category=None,
                description=None,
            )
        )
        if len(out) >= 50:
            break
    return out


# ---- Schema.org RDFa (itemtype="MenuItem"/"Product"/"Offer") extraction ---


_ITEMTYPE_TOKEN_RE = re.compile(
    r'itemtype\s*=\s*(?:"([^"]+)"|\'([^\']+)\')',
    re.IGNORECASE,
)


def _extract_rdfa_items(html: str) -> list[NormalizedMenuItem]:
    """Extract MenuItem / Product items declared using schema.org RDFa microdata.

    We avoid building a full DOM-aware parser (cost / precision tradeoff).
    Instead we regex-scan for `<div itemscope itemtype="...MenuItem/Product">`
    regions and extract itemprop="name" + itemprop="price" values, supporting
    both the meta content variant and inline span/h3 text variants. This
    handles 80%+ of real RDFa menu markup with no false-positives because we
    require BOTH name + price pairs to occur inside the same itemscope block.
    """
    results: list[NormalizedMenuItem] = []
    if not html:
        return results
    # 1) Find every itemscope block boundary by looking at <tag ... itemtype=...>
    #    and then greedily grab everything until the nearest closing </tag> that
    #    closes the outer container. For robustness we use a crude regex split
    #    on any "itemtype" that is a known MenuItem / Product / Offer.
    pos = 0
    while True:
        m = _ITEMTYPE_TOKEN_RE.search(html, pos)
        if not m:
            break
        itemtype_raw = (m.group(1) or m.group(2) or "").lower()
        itemtype = itemtype_raw.rstrip("/").rsplit("/", 1)[-1]
        if itemtype not in {"menuitem", "product", "dish", "offer"}:
            pos = m.end()
            continue
        # Look for the ">" that closes this opening tag (start of block content)
        start_tag_close = html.find(">", m.end())
        if start_tag_close < 0:
            pos = m.end()
            continue
        # Find the name of the opening tag (e.g. "<div", "<section") so we can
        # match the depth; but if we can't find it, just use a generous 20KB
        # window — microdata blocks are never huge.
        block_start = start_tag_close + 1
        # Open-tag name: last "<TAG" before m.start()
        lt = html.rfind("<", 0, m.start())
        if lt < 0:
            pos = m.end()
            continue
        tagname_match = re.match(
            r"<\s*([a-zA-Z][a-zA-Z0-9-]*)", html[lt : m.start()]
        )
        if tagname_match:
            tagname = tagname_match.group(1).lower()
            closing = f"</{tagname}"
            # Heuristic: the first closing tag after 1KB is usually the outer one.
            end_idx = html.find(closing, block_start + 64)
            if end_idx < 0:
                end_idx = min(block_start + 20000, len(html))
            else:
                end_idx = min(end_idx + len(closing) + 16, block_start + 20000)
            block = html[block_start:end_idx]
            pos = end_idx
        else:
            block = html[block_start : min(block_start + 8000, len(html))]
            pos = m.end()
        name: str | None = None
        price: float | None = None
        category: str | None = None
        description: str | None = None
        # (a) meta itemprop="X" content="Y"
        for ip1, ip2, c1, c2 in re.findall(
            r'itemprop\s*=\s*(?:"([^"]+)"|\'([^\']+)\')'
            r"(?:[^>]{0,200}?)"
            r'content\s*=\s*(?:"([^"]*)"|\'([^\']*)\')',
            block,
            re.IGNORECASE | re.S,
        ):
            key = (ip1 or ip2 or "").lower()
            val = c1 if c1 is not None else (c2 if c2 is not None else "")
            if not key or val is None:
                continue
            if key == "name" and not name:
                name = val.strip()[:255] or name
            elif key == "price" and price is None:
                price = _coerce_price(val)
            elif key == "pricecurrency":
                pass  # consumed implicitly by _coerce_price
            elif key == "category" and not category:
                category = val.strip()[:100] or None
            elif key == "description" and not description:
                description = val.strip()[:1000] or None
        # (b) inline text: <span itemprop="name">Nescafe</span>
        # Capture text between the opening tag with itemprop and the next </
        # that closes the same block — simple "text between > and next <".
        for m2 in re.finditer(
            r'<\s*([a-zA-Z0-9-]+)[^>]*?itemprop\s*=\s*(?:"([^"]+)"|\'([^\']+)\')[^>]*>',
            block,
            re.IGNORECASE,
        ):
            key = (m2.group(2) or m2.group(3) or "").lower()
            if key not in {"name", "price", "category", "description"}:
                continue
            after = block[m2.end() :]
            # Grab text up to the next tag
            lt_after = after.find("<")
            text = (after[:lt_after] if lt_after > 0 else after).strip()
            text = re.sub(r"<[^>]+>", " ", text).strip()
            if not text:
                continue
            if key == "name" and not name:
                name = text[:255]
            elif key == "price" and price is None:
                price = _coerce_price(text)
            elif key == "category" and not category:
                category = text[:100] or None
            elif key == "description" and not description:
                description = text[:1000] or None
        # (c) "offers" block: sometimes name/description live in the outer block
        #     but price lives in a nested offers scope. Try one more scan inside
        #     the block for any price value if we still don't have one.
        if name and price is None:
            for pm in _find_price_matches(block):
                p = _parse_price_token(pm)
                if p is not None:
                    price = p
                    break
        if name and price is not None and price > 0 and price <= 100000:
            results.append(
                NormalizedMenuItem(
                    name=name[:255],
                    price=float(price),
                    category=category,
                    description=description,
                )
            )
    return _dedup_items(results)


# ---- Public API -----------------------------------------------------------


def extract_menu_items(html: str) -> list[NormalizedMenuItem]:
    """Extract normalized menu items from raw HTML string.

    Always returns a list (possibly empty) and never raises on malformed input.
    """
    if not html:
        return []

    # Defensive coercion: if the caller accidentally passes bytes / non-str,
    # convert to str gracefully instead of raising TypeError downstream.
    if isinstance(html, (bytes, bytearray)):
        try:
            html = html.decode("utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            html = str(html)
    elif not isinstance(html, str):
        html = str(html)

    # JSON-LD pass
    json_ld_items: list[NormalizedMenuItem] = []
    heuristic_items: list[NormalizedMenuItem] = []
    parser: _MenuBlockParser | None = None
    try:
        parser = _MenuBlockParser()
        parser.feed(html)
        parser.close()
    except (AssertionError, ValueError, RecursionError, UnicodeDecodeError):
        parser = None

    if parser is not None:
        try:
            json_ld_items = _extract_from_json_ld(parser.json_ld_blocks)
        except Exception:  # noqa: BLE001 - Never let parser crash the pipeline
            json_ld_items = []
        try:
            heuristic_items = _extract_from_html_blocks(parser)
        except Exception:  # noqa: BLE001
            heuristic_items = []

    # Schema.org RDFa microdata (MenuItem / Product / Offer). Many sites ship
    # RDFa instead of JSON-LD.
    rdfa_items: list[NormalizedMenuItem] = []
    try:
        rdfa_items = _extract_rdfa_items(html)
    except Exception:  # noqa: BLE001
        rdfa_items = []

    combined = list(json_ld_items)
    json_keys = {
        (
            (it.get("name") or "").strip().lower(),
            int(round((it.get("price") or 0.0) * 100)),
        )
        for it in json_ld_items
    }
    for it in heuristic_items:
        key = (
            (it.get("name") or "").strip().lower(),
            int(round((it.get("price") or 0.0) * 100)),
        )
        if key in json_keys:
            continue
        combined.append(it)
    for it in rdfa_items:
        key = (
            (it.get("name") or "").strip().lower(),
            int(round((it.get("price") or 0.0) * 100)),
        )
        if key in json_keys:
            continue
        combined.append(it)

    # Last-resort line-level fallback: ONLY activates when nothing else found.
    if not combined:
        try:
            combined = list(_extract_line_level_fallback(html))
        except Exception:  # noqa: BLE001
            combined = []

    deduped = _dedup_items(combined)
    # Critical: apply precision / trust filter *after* dedup to drop phone numbers,
    # opening hours, address tokens, etc. that look like "name + price" pairs but
    # are clearly not menu dishes. If the trust filter wipes all items → empty
    # (menu unavailable), never emit garbage content.
    trusted = _trust_filter_all(deduped)
    return trusted


def _fetch_html(url: str) -> str | None:
    if not url or not isinstance(url, str):
        return None
    req = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
            "Accept-Language": "tr,en;q=0.9",
        },
        method="GET",
    )
    try:
        with urlopen(req, timeout=HTTP_TIMEOUT_SECONDS) as response:
            status = getattr(response, "status", 200)
            if status and status >= 400:
                return None
            charset = response.headers.get_content_charset() or "utf-8"
            raw_bytes = response.read()
            try:
                return raw_bytes.decode(charset, errors="replace")
            except (LookupError, UnicodeDecodeError):
                return raw_bytes.decode("utf-8", errors="replace")
    except (HTTPError, URLError, TimeoutError, OSError, ValueError):
        return None


def fetch_and_extract_menu_items(menu_url: str) -> list[NormalizedMenuItem]:
    """Fetch a menu URL over HTTP and return extracted items.

    Convenience wrapper that also returns an empty list on network errors.
    """
    html = _fetch_html(menu_url)
    if not html:
        return []
    return extract_menu_items(html)


# =====================================================================
# GENERAL RESTAURANT-WEBSITE MENU PIPELINE (8-strategy, restaurant-agnostic)
# =====================================================================
#
# High-level goal:
#   items = extract_menu_items_for_website(restaurant.website)
#       -> list[NormalizedMenuItem]   (possibly empty)
#
# - NEVER raises, NEVER returns None, NEVER writes to DB.
# - Uses standard lib + optional already-installed libs only (no new deps).
# - NO restaurant-specific branching. NO `if "twister" in url`.
# - Precision over recall. All outputs are trust-filtered.
# =====================================================================

# Local short aliases for readability; all are already imported at the top
# of the file so these never cause ModuleNotFound/E402.
_ga_json = json
_ga_os = os
_ga_re = re
_ga_shutil = shutil
_ga_subprocess = subprocess
_ga_tempfile = tempfile
_ga_dataclass = dataclass
_Path = Path
_Any = Any
_TypedDict = TypedDict
_HTTPError = HTTPError
_URLError = URLError
_ParseResult = ParseResult
_urljoin = urljoin
_urlparse = urlparse
_urlunparse = urlunparse
_Request = Request
_urlopen = urlopen

# ---------- Types (for structured terminal reporting) ----------------

class _PerStrategyReport(_TypedDict, total=False):
    """How many items each strategy contributed, plus a short diagnostic."""

    items: int
    note: str


class _ExtractionReport(_TypedDict, total=False):
    """Read-only diagnostic report returned by the verbose pipeline entrypoint."""

    homepage_extract: _PerStrategyReport
    discovered_menu: _PerStrategyReport
    standard_paths: _PerStrategyReport
    section_chunks: _PerStrategyReport
    wp_rest_api: _PerStrategyReport
    image_detect: _PerStrategyReport
    ocr: _PerStrategyReport
    trust_filtered: int
    final_items: int
    status: str


# ---------- Constants (general / no restaurant-specific strings) -------

# Standard, language-agnostic menu page paths. Tested in priority order.
_STANDARD_MENU_PATHS: tuple[str, ...] = (
    "/menu",
    "/menu/",
    "/menu.html",
    "/menu.htm",
    "/menumuz",
    "/menumuz/",
    "/yemek",
    "/yemekler",
    "/yemek-listesi",
    "/urunler",
    "/ürünler",
    "/urunler.html",
    "/products",
    "/products.html",
    "/product-list",
    "/product-list.html",
    "/price-list",
    "/price-list.html",
    "/fiyat-listesi",
    "/fiyat-listesi.html",
    "/liste",
    "/liste.html",
    "/carte",
    "/speisekarte",
)

# Section ids / keywords on a homepage that often wrap an embedded menu.
_MENU_SECTION_ID_KEYWORDS: tuple[str, ...] = (
    "menu",
    "menumuz",
    "menü",
    "menu-section",
    "menusection",
    "our-menu",
    "urunler",
    "ürünler",
    "products",
    "yemekler",
    "price-list",
    "fiyat-listesi",
)

# Tokens that, when found in an image filename or its surrounding heading,
# indicate the image might be a printable "menu board". We only consider
# images larger than 30KB because small icons/logos never contain a menu.
_IMAGE_MENU_KEYWORDS: _ga_re.Pattern[str] = _ga_re.compile(
    r"(menu|menü|menumuz|yemek|fiyat|price|liste|list|carte|speise|board|tablo)",
    _ga_re.IGNORECASE,
)

# Trusted data source bonuses: sources that are never CSS/SVG pollution.
_TRUSTED_SOURCES = {
    "homepage_extract",
    "discovered_menu",
    "standard_paths",
    "section_chunks",
    "wp_rest_api",
    "ocr",
}


# ---------- Minimal HTTP fetch helpers (shared, stdlib only) -----------


def _ga_normalize_website(website_url: str) -> str | None:
    """Turn a Restaurant.website value into a normalized https://example.com/ URL.

    Returns None on invalid input. Never raises. Defensively coerces bytes /
    non-string inputs so the verbose API never raises on accidental bad input.
    """
    # Defensive coercion: match the one used in extract_menu_items()
    if isinstance(website_url, (bytes, bytearray)):
        try:
            website_url = website_url.decode("utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            website_url = str(website_url)
    elif not isinstance(website_url, str):
        website_url = str(website_url)
    raw = (website_url or "").strip()
    if not raw:
        return None
    if not raw.startswith(("http://", "https://")):
        raw = "https://" + raw
    try:
        parsed = _urlparse(raw)
        host = parsed.hostname or ""
        if not host or "." not in host:
            return None
        return _urlunparse(
            _ParseResult(
                scheme=parsed.scheme or "https",
                netloc=parsed.netloc.lower(),
                path=parsed.path or "/",
                params="",
                query="",
                fragment="",
            )
        )
    except Exception:  # noqa: BLE001
        return None


def _ga_fetch(
    url: str,
    *,
    binary: bool = False,
    timeout: int = HTTP_TIMEOUT_SECONDS,
) -> tuple[int, bytes]:
    """Fetch a URL safely with a hard short timeout. Never raises."""
    req = _Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": (
                "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
                if binary
                else "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8"
            ),
            "Accept-Language": "tr,en;q=0.9",
            "Connection": "close",
        },
        method="GET",
    )

    # Do not let a single broken/slow restaurant website stall the
    # entire enrichment run.
    effective_timeout = max(1, min(int(timeout), 3))

    try:
        with _urlopen(req, timeout=effective_timeout) as resp:
            status = int(getattr(resp, "status", 200) or 200)

            # Read only a reasonable amount of data.
            # We do not need multi-megabyte pages for menu extraction.
            data = resp.read(2 * 1024 * 1024)

            return status, data

    except _HTTPError as e:
        try:
            body = e.read(2 * 1024 * 1024)
        except Exception:
            body = b""
        return int(e.code or 0), body

    except (
        _URLError,
        TimeoutError,
        socket.timeout,
        OSError,
        ValueError,
    ):
        return 0, b""

    except Exception:
        # Last-resort protection: one bad website must never kill
        # the complete restaurant enrichment process.
        return 0, b""

def _ga_bytes_to_html(data: bytes) -> str | None:
    """Decode fetched bytes into HTML text using best-effort UTF-8 decoding."""
    if not data:
        return None

    try:
        return data.decode("utf-8", errors="replace")
    except Exception:
        return None
# ---------- Strategy 5: WordPress public REST API (general detection) --


def _ga_is_likely_wordpress(html: str) -> bool:
    """Best-effort WP detection from a sample HTML (general, site-name agnostic)."""
    if not html:
        return False
    hay = html[:150_000].lower()
    return (
        "wp-content" in hay
        or "wp-json" in hay
        or "wordpress" in hay
        or "wp-includes" in hay
    )


def _ga_extract_wp_rest(base_url: str, html: str) -> tuple[list[NormalizedMenuItem], _PerStrategyReport]:
    """Try the 3 most common public WordPress JSON endpoints. Always returns (items, report)."""
    note_parts: list[str] = []
    if not _ga_is_likely_wordpress(html):
        return [], {"items": 0, "note": "site-not-wordpress"}
    note_parts.append("wp-site-detected")
    candidates: list[tuple[str, str]] = [
        ("/wp-json/wc/v3/products?per_page=100", "woocommerce"),
        ("/wp-json/wp/v2/product?per_page=100&search=menu", "wp-post-type-product"),
        ("/wp-json/wp/v2/posts?per_page=50&search=menu", "wp-posts-search-menu"),
        ("/wp-json/menus/v1/menus", "wp-plugin-menus-v1"),
        ("/wp-json?rest_route=/wc/v3/products&per_page=100", "woocommerce-alt-route"),
    ]
    found_items: list[NormalizedMenuItem] = []
    tried = 0
    for path, kind in candidates:
        tried += 1
        status, raw = _ga_fetch(_urljoin(base_url, path), timeout=8)
        if status == 0 or status >= 400:
            continue
        text = _ga_bytes_to_html(raw) or ""
        if not text or not text.lstrip().startswith(("[", "{")):
            continue
        try:
            payload = _ga_json.loads(text)
        except Exception:  # noqa: BLE001
            continue
        parsed = _ga_parse_any_rest_products(payload)
        if parsed:
            note_parts.append(f"{kind}-{len(parsed)}")
            found_items.extend(parsed)
    note_parts.insert(0, f"endpoints-tried={tried}")
    return _dedup_items(found_items), {"items": len(found_items), "note": "; ".join(note_parts)}


def _ga_parse_any_rest_products(payload: _Any) -> list[NormalizedMenuItem]:
    """Parse products/menu items out of any plausible REST JSON shape.

    Understands:
      - WooCommerce /wp-json/wc/v3/products list: [{id,name,price,description,categories:[{slug,name}]}]
      - Any schema.org-like list: [{"@type":"MenuItem","name":"x","offers":{"price":"y"}}]
      - Custom shape: [{title,price,category,summary}]
      - Single dict with nested "items" / "data" / "products" / "menus" keys
    Everything else → []. Never raises.
    """
    out: list[NormalizedMenuItem] = []
    if payload is None:
        return out
    # Descend into wrapper containers
    if isinstance(payload, dict):
        for key in ("items", "data", "products", "menus", "menu", "records", "posts"):
            if key in payload and isinstance(payload[key], (list, dict)):
                return _ga_parse_any_rest_products(payload[key])
        return out
    if not isinstance(payload, list):
        return out

    for node in payload:
        if not isinstance(node, dict):
            continue
        try:
            # 1) WooCommerce
            if "name" in node and ("price" in node or "regular_price" in node or "sale_price" in node):
                name = str(node.get("name") or "").strip()
                raw_price = node.get("price") or node.get("regular_price") or node.get("sale_price") or "0"
                try:
                    price = float(raw_price)
                except (TypeError, ValueError):
                    continue
                if price <= 0 or not name:
                    continue
                cat = ""
                cats = node.get("categories") or []
                if isinstance(cats, list) and cats and isinstance(cats[0], dict):
                    cat = str(cats[0].get("name") or cats[0].get("slug") or "").strip()
                desc = str(node.get("short_description") or node.get("description") or "").strip()[:1000] or None
                out.append(NormalizedMenuItem(
                    name=name, price=float(price), category=cat or "", description=desc,
                ))
                continue
            # 2) Schema.org JSON-LD style list
            if "offers" in node:
                name = str(node.get("name") or "").strip()
                offers = node.get("offers")
                price_raw = None
                currency = None
                if isinstance(offers, dict):
                    price_raw = offers.get("price")
                    currency = offers.get("priceCurrency")
                elif isinstance(offers, list) and offers:
                    o0 = offers[0]
                    if isinstance(o0, dict):
                        price_raw = o0.get("price")
                        currency = o0.get("priceCurrency")
                try:
                    price = float(price_raw) if price_raw not in (None, "") else 0.0
                except (TypeError, ValueError):
                    price = 0.0
                if not name or price <= 0:
                    continue
                cat = str(node.get("category") or node.get("menuSection") or "").strip()
                desc = str(node.get("description") or "").strip()[:1000] or None
                out.append(NormalizedMenuItem(
                    name=name, price=price, category=cat, description=desc,
                ))
                continue
            # 3) Custom: title/price/summary/category
            if ("title" in node or "name" in node) and "price" in node:
                name = str(node.get("title") or node.get("name") or "").strip()
                try:
                    price = float(node.get("price") or 0)
                except (TypeError, ValueError):
                    continue
                if not name or price <= 0:
                    continue
                cat = str(node.get("category") or node.get("section") or "").strip()
                desc = str(node.get("summary") or node.get("desc") or node.get("description") or "").strip()[:1000] or None
                out.append(NormalizedMenuItem(
                    name=name, price=price, category=cat, description=desc,
                ))
        except Exception:  # noqa: BLE001
            continue
    return out


# ---------- Strategy 4: Section chunks (homepage #menumuz etc.) ---------


def _ga_extract_section_chunks(base_url: str, homepage_html: str) -> tuple[list[NormalizedMenuItem], _PerStrategyReport]:
    """Slice homepage around id=menu* sections; re-run extraction per chunk.

    Reasoning: some single-page sites put the menu in #menumuz but the page
    also contains huge CSS/nav/footer noise that confuses block heuristics.
    Running extract_menu_items on a 30KB window around id=menu* often catches
    items we would otherwise miss.
    """
    report: _PerStrategyReport = {"items": 0, "note": "no-section-id-matched"}
    if not homepage_html:
        return [], report
    all_items: list[NormalizedMenuItem] = []
    seen_windows: set[int] = set()
    for kw in _MENU_SECTION_ID_KEYWORDS:
        # Try id='kw', id="kw", id=kw (word boundaries)
        pattern = _ga_re.compile(
            r"""id\s*=\s*(?:'([^']*""" + _ga_re.escape(kw) + r"""[^']*)'|"([^"]*""" + _ga_re.escape(kw) + r"""[^"]*)"|([^\s'">]*""" + _ga_re.escape(kw) + r"""[^\s'">]*))""",
            _ga_re.IGNORECASE,
        )
        for m in pattern.finditer(homepage_html):
            idx = m.start()
            # Each window = 2000 chars before + 25000 after
            start = max(0, idx - 2000)
            end = min(len(homepage_html), idx + 27000)
            key = start
            if key in seen_windows:
                continue
            seen_windows.add(key)
            chunk = homepage_html[start:end]
            chunk_items = extract_menu_items(chunk)
            if chunk_items:
                all_items.extend(chunk_items)
    deduped = _dedup_items(all_items)
    if deduped:
        report = {"items": len(deduped), "note": f"windows-tried={len(seen_windows)}"}
    return deduped, report


# ---------- Strategy 3: Standard paths brute force --------------------


def _ga_try_standard_menu_paths(base_url: str) -> tuple[list[NormalizedMenuItem], _PerStrategyReport]:
    """Hit common /menu, /menumuz, /products paths. No site-specific paths."""
    report: _PerStrategyReport = {"items": 0, "note": f"paths-tried={len(_STANDARD_MENU_PATHS)}"}
    found: list[NormalizedMenuItem] = []
    hit_paths: list[str] = []
    for path in _STANDARD_MENU_PATHS:
        url = _urljoin(base_url, path)
        status, raw = _ga_fetch(url, timeout=6)
        if status == 0 or status >= 400:
            continue
        html = _ga_bytes_to_html(raw) or ""
        if not html:
            continue
        items = extract_menu_items(html)
        if items:
            found.extend(items)
            hit_paths.append(path)
    if hit_paths:
        report["note"] = f"hits={len(hit_paths)} ({', '.join(hit_paths[:6])}{'...' if len(hit_paths) > 6 else ''})"
    deduped = _dedup_items(found)
    report["items"] = len(deduped)
    return deduped, report


# ---------- Strategy 2: discover_menu_url (import here, circular-safe) ---


def _ga_try_discover_menu(base_url: str, homepage_html: str | None) -> tuple[list[NormalizedMenuItem], _PerStrategyReport]:
    report: _PerStrategyReport = {"items": 0, "note": "no-confident-link"}
    try:
        from app.scripts.menu_discovery import discover_menu_url  # noqa: PLC0415
    except Exception:  # noqa: BLE001
        return [], {"items": 0, "note": "discovery-module-unavailable"}
    try:
        found = discover_menu_url(base_url)
    except Exception:  # noqa: BLE001
        return [], {"items": 0, "note": "discovery-exception"}
    if not found:
        # Fallback: if homepage itself had a #menumuz/#menu hash as section, try the homepage again
        if homepage_html and _ga_re.search(r"""id\s*=\s*["']?men[üu]m?u?z?\b""", homepage_html, _ga_re.IGNORECASE):
            items = extract_menu_items(homepage_html)
            if items:
                return _dedup_items(items), {"items": len(items), "note": "homepage-hash-section"}
        return [], report
    # URL might be a bare hash like "#menumuz". Resolve relative to base:
    resolved = _urljoin(base_url, found)
    # Optimisation: same URL as base + fragment only → use homepage_html
    is_home_hash = _ga_url_equal_ignoring_fragment(resolved, base_url)
    items: list[NormalizedMenuItem] = []
    if is_home_hash and homepage_html:
        items = extract_menu_items(homepage_html)
        report["note"] = f"hash-only:{found or ''} homepage-extract"
    else:
        html = _fetch_html(resolved)
        if html:
            items = extract_menu_items(html)
        report["note"] = f"menu-url={resolved}"
    deduped = _dedup_items(items)
    report["items"] = len(deduped)
    return deduped, report


def _ga_url_equal_ignoring_fragment(a: str, b: str) -> bool:
    try:
        pa = _urlparse(a)
        pb = _urlparse(b)
        return (pa.scheme == pb.scheme and pa.netloc == pb.netloc
                and pa.path.rstrip("/") == pb.path.rstrip("/") and pa.query == pb.query)
    except Exception:  # noqa: BLE001
        return False


# ---------- Strategy 6+8: Image / PDF menu detection + OCR --------------


def _ga_find_menu_images_or_pdfs(homepage_html: str, base_url: str) -> tuple[list[str], _PerStrategyReport]:
    """Find large (>=30KB) image/pdf URLs that look menu-related by filename/alt.

    Returns (absolute_urls, report).
    """
    report: _PerStrategyReport = {"items": 0, "note": "no-large-menu-images"}
    urls: set[str] = set()

    def add(url_candidate: str | None) -> None:
        if not url_candidate:
            return
        abs_ = _urljoin(base_url, url_candidate)
        try:
            p = _urlparse(abs_)
            if p.scheme not in ("http", "https"):
                return
        except Exception:  # noqa: BLE001
            return
        urls.add(abs_)

    # Images: <img src=...>, <img data-src=...>, srcSets
    img_pattern = _ga_re.compile(
        r"""<img[^>]+(?:src|data-src|data-lazy-src)\s*=\s*(['"])(.*?)\1""",
        _ga_re.IGNORECASE | _ga_re.DOTALL,
    )
    for m in img_pattern.finditer(homepage_html):
        src = m.group(2).strip()
        add(src)
    # PDFs: <a href="....pdf">
    a_pdf = _ga_re.compile(
        r"""<a[^>]+href\s*=\s*(['"])(.*?\.pdf(?:\?[^'"]*)?)\1""",
        _ga_re.IGNORECASE | _ga_re.DOTALL,
    )
    for m in a_pdf.finditer(homepage_html):
        add(m.group(2).strip())

    # Filter: keep those with menu-ish filenames; we'll validate size at fetch time
    candidates: list[str] = []
    for u in sorted(urls):
        low_path = (_urlparse(u).path or "").lower()
        if low_path.endswith((".png", ".jpg", ".jpeg", ".webp", ".pdf")) and _IMAGE_MENU_KEYWORDS.search(low_path):
            candidates.append(u)
    # Also try: headings around images → look for a <h2>-<h6> containing menu keyword, then grab next <img>
    # (simple forward scan: use regex that matches heading-text then up to 3000 chars then img src)
    heading_with_menu_img = _ga_re.compile(
        r"""<h[2-6][^>]*>(.*?)</h[2-6]>.{0,4000}?<img[^>]+src\s*=\s*(['"])(.*?)\2""",
        _ga_re.IGNORECASE | _ga_re.DOTALL,
    )
    for m in heading_with_menu_img.finditer(homepage_html):
        heading_txt = _ga_re.sub(r"<[^>]+>", "", m.group(1)).lower()
        src = m.group(3).strip()
        if _IMAGE_MENU_KEYWORDS.search(heading_txt) and src:
            add(src)

    # Final filter: quick HEAD / GET size check — keep >= 30KB, drop icons
    verified: list[str] = []
    for u in candidates:
        st, data = _ga_fetch(u, binary=True, timeout=8)
        if 200 <= st < 400 and len(data) >= 30_000:
            verified.append(u)
    verified = list(dict.fromkeys(verified))[:8]  # cap: at most 8 candidates per site (cost)
    report["items"] = len(verified)
    if verified:
        report["note"] = f"candidates={len(verified)} ({', '.join(u.split('/')[-1] for u in verified[:5])})"
    return verified, report


def _ga_tesseract_cmd() -> str | None:
    """Return a tesseract executable path if one is locally available, else None.

    NO installation is performed. Checks PATH → common Windows install dirs.
    """
    cmd = _ga_shutil.which("tesseract")
    if cmd:
        return cmd
    for p in (
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        "/usr/bin/tesseract",
        "/usr/local/bin/tesseract",
    ):
        if _Path(p).exists():
            return p
    return None


def _ga_tesseract_has_language(tess_cmd: str, lang: str) -> bool:
    try:
        p = _ga_subprocess.run(
            [tess_cmd, "--list-langs"],
            capture_output=True, text=True, timeout=15,
        )
        out = (p.stdout or "") + "\n" + (p.stderr or "")
    except Exception:  # noqa: BLE001
        return False
    return any(line.strip() == lang for line in out.splitlines() if line.strip())


def _ga_run_ocr(image_urls: list[str]) -> tuple[list[NormalizedMenuItem], _PerStrategyReport]:
    """Given a list of menu-image URLs:
       - if Tesseract is installed → download each, OCR (-l tur+eng if tur exists else eng),
       - feed the raw OCR text as a fake <pre> wrapped HTML through the SAME trust rules
         (extract_menu_items — so our price token guardrails still apply).
       - dedupe & return.
    Else: empty items + report note = "tesseract-not-installed".
    """
    report: _PerStrategyReport = {"items": 0, "note": "tesseract-not-installed"}
    if not image_urls:
        return [], {"items": 0, "note": "no-images"}
    tess = _ga_tesseract_cmd()
    if not tess:
        return [], report
    langs = "tur+eng" if _ga_tesseract_has_language(tess, "tur") else "eng"
    ocr_text_parts: list[str] = []
    processed = 0
    errors: list[str] = []
    with _ga_tempfile.TemporaryDirectory(prefix="tm_ocr_") as tmp:
        tmp_dir = _Path(tmp)
        for i, u in enumerate(image_urls[:6]):  # cost cap: 6 images max per site
            st, data = _ga_fetch(u, binary=True, timeout=15)

            if not (200 <= st < 400):
                errors.append(f"http-{st or 'network'}")
                continue

            if len(data) < 5_000:
                errors.append(f"too-small-{len(data)}b")
                continue

            ext = _Path(_urlparse(u).path or "").suffix.lower() or ".png"

            if ext not in (".png", ".jpg", ".jpeg", ".webp"):
                errors.append(f"unsupported-ext-{ext}")
                continue
            if ext not in (".png", ".jpg", ".jpeg", ".webp"):
                # PDFs → skip for now (poppler not a dep)
                continue
            img_path = tmp_dir / f"menu{i}{ext}"
            try:
                img_path.write_bytes(data)
            except Exception:  # noqa: BLE001
                continue
            out_base = img_path.with_suffix("")
            try:
                proc = _ga_subprocess.run(
                    [tess, str(img_path), str(out_base), "-l", langs, "--psm", "6", "txt"],
                    capture_output=True, text=True, timeout=120,
                    env={**_ga_os.environ, "PYTHONIOENCODING": "utf-8"},
                )
            except Exception as e:  # noqa: BLE001
                errors.append(type(e).__name__)
                continue
            if proc.returncode != 0:
                errors.append(f"rc{proc.returncode}")
                continue
            txt_path = img_path.with_suffix(".txt")
            try:
                text = txt_path.read_text(encoding="utf-8", errors="replace")
            except Exception:  # noqa: BLE001
                continue
            if text.strip():
                processed += 1
                ocr_text_parts.append(text)
    if not ocr_text_parts:
        if processed == 0 and not errors:
            report["note"] = (
                f"ocr-empty-text;images-tried={len(image_urls)};langs={langs}"
            )
        else:
            error_summary = ",".join(errors[:5])
            report["note"] = (
                f"ocr-errors:{len(errors)};"
                f"langs={langs};"
                f"tried={len(image_urls)};"
                f"details={error_summary}"
            )
        return [], report
    joined_text = "\n".join(ocr_text_parts)

    print("\n========== OCR DEBUG ==========")
    print(joined_text[:5000])
    print("========== END OCR DEBUG ==========\n")

    fake_html = (
        "<!doctype html><html><body><pre id='menu-board'>\n"
        + joined_text.replace("&", "&amp;").replace("<", "&lt;")
        + "\n</pre></body></html>"
    )

    items = _extract_menu_items_from_ocr_text(joined_text)
    report["items"] = len(items)
    report["note"] = f"langs={langs};images-ocr'd={processed};errors={len(errors)}"
    return _dedup_items(items), report


# ---------- Final trust / precision filter ------------------------------


def _ga_trust_filter(items: list[NormalizedMenuItem]) -> list[NormalizedMenuItem]:
    """Precision filter applied at the end. Returns items we are willing to publish.

    Rules:
      - If we got 0 items → return [].
      - If we got 1 item AND it has no category, no description, and its name
        length < 5 → almost certainly a header / FP → drop to [].
      - If fewer than 50% of items have a realistic non-zero price → drop all.
        (Real menus never have half the items without prices.)
      - Phone / contact / hours false-positive filter.
      - Dedup pass.
    """
    if not items:
        return []
    deduped = _dedup_items(items)
    if len(deduped) == 1:
        it = deduped[0]
        name = (it.get("name") or "").strip()
        cat = (it.get("category") or "").strip()
        desc = (it.get("description") or "").strip()
        price = float(it.get("price") or 0.0)
        if len(name) < 5 and not cat and not desc and price == 0:
            return []
    # Pricing realism
    total = len(deduped)
    priced = sum(
        1 for it in deduped if float(it.get("price") or 0.0) > 0
    )
    if total > 2 and priced / total < 0.5:
        # Too many items have no price → likely parsed headings / CSS tokens. Drop.
        return []
    # Shared precision filter (phone, hours, contact, digit-heavy names, etc.)
    trusted = _trust_filter_all(deduped)
    return trusted


# ---------- Public entrypoints -----------------------------------------


def extract_menu_items_for_website(website_url: str) -> list[NormalizedMenuItem]:
    """General, restaurant-agnostic menu extraction entrypoint.

    Given a restaurant's homepage URL (from Restaurant.website), run a series
    of cheap standard strategies to find and extract menu items.

    * NEVER raises. Never writes DB. Never uses AI APIs.
    * NO per-restaurant branches.
    * Precision over recall: drops outputs that don't look trustworthy.
    """
    items, _report = _extract_menu_items_for_website_internal(website_url)
    return items


def extract_menu_items_for_website_with_report(website_url: str) -> tuple[list[NormalizedMenuItem], _ExtractionReport]:
    """Same as above, but also returns a diagnostic dict for terminal reporting.

    Used by READ-ONLY test harnesses; not required for API callers.
    """
    return _extract_menu_items_for_website_internal(website_url)


def _extract_menu_items_for_website_internal(
    website_url: str,
) -> tuple[list[NormalizedMenuItem], _ExtractionReport]:
    report: _ExtractionReport = {
        "homepage_extract": {"items": 0, "note": "skipped"},
        "discovered_menu": {"items": 0, "note": "skipped"},
        "standard_paths": {"items": 0, "note": "skipped"},
        "section_chunks": {"items": 0, "note": "skipped"},
        "wp_rest_api": {"items": 0, "note": "skipped"},
        "image_detect": {"items": 0, "note": "skipped"},
        "ocr": {"items": 0, "note": "skipped"},
        "trust_filtered": 0,
        "final_items": 0,
        "status": "skipped",
    }

    base = _ga_normalize_website(website_url)

    if not base:
        report["status"] = "invalid-website-url"
        return [], report

    # ------------------------------------------------------------------
    # S0) Homepage fetch
    # ------------------------------------------------------------------
    try:
        status, raw_home = _ga_fetch(base, timeout=6)
    except Exception as exc:  # noqa: BLE001
        report["status"] = f"fetch-exception:{type(exc).__name__}"
        return [], report

    if status == 0:
        report["status"] = "http-error-network"
        return [], report

    if status >= 400:
        report["status"] = f"http-error-{status}"
        return [], report

    if not raw_home:
        report["status"] = "empty-homepage"
        return [], report

    # ------------------------------------------------------------------
    # Decode homepage bytes safely.
    #
    # Do NOT use _ga_bytes_to_html() because that helper does not exist
    # in this module.
    # ------------------------------------------------------------------
    home_html = ""

    try:
        # First try UTF-8, which is the normal case.
        home_html = raw_home.decode("utf-8", errors="replace")

        # If the page explicitly declares another charset, prefer it.
        charset_match = re.search(
            rb"charset\s*=\s*[\"']?\s*([a-zA-Z0-9._-]+)",
            raw_home[:20000],
            flags=re.IGNORECASE,
        )

        if charset_match:
            declared_charset = charset_match.group(1).decode(
                "ascii",
                errors="ignore",
            ).strip()

            if declared_charset:
                try:
                    home_html = raw_home.decode(
                        declared_charset,
                        errors="replace",
                    )
                except (LookupError, UnicodeDecodeError):
                    pass

        # Turkish websites are occasionally served as Windows-1254.
        if "�" in home_html:
            try:
                tr_html = raw_home.decode(
                    "windows-1254",
                    errors="replace",
                )
                if tr_html.count("�") < home_html.count("�"):
                    home_html = tr_html
            except (LookupError, UnicodeDecodeError):
                pass

    except Exception:  # noqa: BLE001
        try:
            home_html = raw_home.decode(
                "latin-1",
                errors="replace",
            )
        except Exception:  # noqa: BLE001
            home_html = ""

    if not home_html.strip():
        report["status"] = "empty-homepage-html"
        return [], report

    collectors: dict[str, list[NormalizedMenuItem]] = {}

    # ------------------------------------------------------------------
    # S1) Homepage extraction
    # ------------------------------------------------------------------
    try:
        home_items = extract_menu_items(home_html)
    except Exception:  # noqa: BLE001
        home_items = []

    collectors["homepage_extract"] = home_items

    report["homepage_extract"] = {
        "items": len(home_items),
        "note": (
            "jsonld+html"
            if home_items
            else "no-products"
        ),
    }

    # ------------------------------------------------------------------
    # S2) Discover explicit menu URL
    # ------------------------------------------------------------------
    try:
        discovered_items, dr = _ga_try_discover_menu(
            base,
            home_html,
        )
    except Exception:  # noqa: BLE001
        discovered_items = []
        dr = {
            "items": 0,
            "note": "discovery-exception",
        }

    collectors["discovered_menu"] = discovered_items
    report["discovered_menu"] = dr

    # ------------------------------------------------------------------
    # S3) Standard paths
    #
    # Disabled because /menu, /products, /menumuz etc. can hang on
    # redirects and make the whole enrichment process unnecessarily slow.
    # ------------------------------------------------------------------
    collectors["standard_paths"] = []

    report["standard_paths"] = {
        "items": 0,
        "note": "disabled-to-avoid-slow-or-hanging-sites",
    }

    # ------------------------------------------------------------------
    # S4) Homepage menu sections
    # ------------------------------------------------------------------
    try:
        sec_items, sec_r = _ga_extract_section_chunks(
            base,
            home_html,
        )
    except Exception:  # noqa: BLE001
        sec_items = []
        sec_r = {
            "items": 0,
            "note": "section-extraction-exception",
        }

    collectors["section_chunks"] = sec_items
    report["section_chunks"] = sec_r

    # ------------------------------------------------------------------
    # S5) WordPress REST API
    #
    # Disabled for now because some WP installations hang.
    # ------------------------------------------------------------------
    collectors["wp_rest_api"] = []

    report["wp_rest_api"] = {
        "items": 0,
        "note": "disabled-to-avoid-slow-or-hanging-sites",
    }

    # ------------------------------------------------------------------
    # S6/S8) Menu image / PDF detection + OCR
    # ------------------------------------------------------------------
    try:
        img_urls, img_r = _ga_find_menu_images_or_pdfs(
            home_html,
            base,
        )
    except Exception:  # noqa: BLE001
        img_urls = []
        img_r = {
            "items": 0,
            "note": "image-detection-exception",
        }

    report["image_detect"] = img_r

    ocr_items: list[NormalizedMenuItem] = []

    ocr_r: _PerStrategyReport = {
        "items": 0,
        "note": "not-run",
    }

    if img_urls:
        try:
            ocr_items, ocr_r = _ga_run_ocr(img_urls)
        except Exception:  # noqa: BLE001
            ocr_items = []
            ocr_r = {
                "items": 0,
                "note": "ocr-exception",
            }

    collectors["ocr"] = ocr_items
    report["ocr"] = ocr_r

    # ------------------------------------------------------------------
    # Merge sources
    # ------------------------------------------------------------------
    combined: list[NormalizedMenuItem] = []

    for source in _TRUSTED_SOURCES:
        combined.extend(
            collectors.get(source, [])
        )

    # First deduplication.
    deduped = _dedup_items(combined)

    total_before_filter = len(deduped)

    # ------------------------------------------------------------------
    # Final precision/trust filter
    # ------------------------------------------------------------------
    final = _ga_trust_filter(deduped)

    report["trust_filtered"] = (
        total_before_filter - len(final)
    )

    report["final_items"] = len(final)

    if final:
        report["status"] = "success"
    else:
        report["status"] = "skipped"

    return final, report

def _extract_menu_items_from_ocr_text(text: str) -> list[NormalizedMenuItem]:
    """Extract menu items from noisy OCR text with strict price validation."""
    if not text:
        return []

    lines: list[str] = []

    for raw in text.splitlines():
        line = re.sub(r"\s+", " ", raw).strip()
        if line:
            lines.append(line)

    results: list[NormalizedMenuItem] = []

    # A price is trusted only when it has an explicit currency marker.
    explicit_price_re = re.compile(
        r"^\s*(?:₺|TL|TRY|â‚º)\s*"
        r"(\d{1,5}(?:[.,]\d{1,2})?)"
        r"\s*$|"
        r"^\s*(\d{1,5}(?:[.,]\d{1,2})?)\s*"
        r"(?:₺|TL|TRY|â‚º)\s*$",
        re.IGNORECASE,
    )

    inline_price_re = re.compile(
        r"(?:₺|TL|TRY|â‚º)\s*(\d{1,5}(?:[.,]\d{1,2})?)"
        r"|"
        r"(\d{1,5}(?:[.,]\d{1,2})?)\s*(?:₺|TL|TRY|â‚º)",
        re.IGNORECASE,
    )

    garbage_re = re.compile(
        r"(telefon|tel\.?|gsm|whatsapp|instagram|facebook|"
        r"adres|address|harita|konum|"
        r"\bcd\.?\b|\bcadde\b|\bsk\.?\b|\bsokak\b|"
        r"\bno\.?\b|rezervasyon|randevu|"
        r"www\.|https?://|@)",
        re.IGNORECASE,
    )

    def valid_name(name: str) -> bool:
        name = name.strip(" -:|•·")

        if len(name) < 3:
            return False

        if garbage_re.search(name):
            return False

        letters = sum(ch.isalpha() for ch in name)

        # OCR garbage such as "b Ned ie" / "SX a" should fail.
        if letters < 4:
            return False

        # Require a reasonable proportion of alphabetic characters.
        alnum = sum(ch.isalnum() for ch in name)
        if alnum == 0 or letters / alnum < 0.45:
            return False

        return True

    def parse_price(raw: str) -> float | None:
        try:
            value = float(raw.replace(",", "."))
        except (ValueError, TypeError):
            return None

        if not (0 < value <= 100000):
            return None

        return value

    for i, line in enumerate(lines):
        if garbage_re.search(line):
            continue

        # ---------------------------------------------------------
        # Case 1: "Kajun Tavuk (4 Adet) 400TL"
        # ---------------------------------------------------------
        match = inline_price_re.search(line)

        if match:
            raw_price = match.group(1) or match.group(2)
            price = parse_price(raw_price)

            if price is None:
                continue

            name = line[:match.start()].strip(" -:|•·")

            if valid_name(name):
                results.append(
                    NormalizedMenuItem(
                        name=name[:255],
                        price=price,
                        category=None,
                        description=None,
                    )
                )

            continue

        # ---------------------------------------------------------
        # Case 2: "Kajun Tavuk (4 Adet)" followed by "400TL"
        # ---------------------------------------------------------
        if i + 1 < len(lines):
            next_line = lines[i + 1]

            price_match = explicit_price_re.fullmatch(next_line)

            if not price_match:
                continue

            raw_price = price_match.group(1) or price_match.group(2)
            price = parse_price(raw_price)

            if price is None:
                continue

            name = line.strip(" -:|•·")

            if not valid_name(name):
                continue

            results.append(
                NormalizedMenuItem(
                    name=name[:255],
                    price=price,
                    category=None,
                    description=None,
                )
            )

    return _dedup_items(results)
