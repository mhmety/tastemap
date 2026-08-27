"""Discover menu URLs on restaurant websites using standard library only.

Supports two discovery strategies in priority order:
1. JSON-LD structured data (schema.org Menu / hasMenu / menu fields)
2. HTML anchor link inspection (text / href / title keyword matching)
"""

from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import ParseResult, urljoin, urlparse, urlunparse
from urllib.request import Request, urlopen

MENU_KEYWORDS: tuple[str, ...] = (
    "menu",
    "menus",
    "menü",
    "yemek",
    "food",
    "dining",
)

NEGATIVE_KEYWORDS: tuple[str, ...] = (
    "instagram.com",
    "facebook.com",
    "twitter.com",
    "x.com",
    "tiktok.com",
    "youtube.com",
    "wa.me",
    "whatsapp",
    "reservation",
    "rezervasyon",
    "booking",
    "randevu",
    "contact",
    "iletisim",
    "iletişim",
    "privacy",
    "gizlilik",
    "terms",
    "sartlar",
    "şartlar",
    "hakkimizda",
    "hakkımızda",
    "about",
    "career",
    "kariyer",
)

KEYWORD_RE = re.compile(
    r"(" + "|".join(re.escape(k) for k in MENU_KEYWORDS) + r")",
    re.IGNORECASE,
)

NEGATIVE_RE = re.compile(
    r"(" + "|".join(re.escape(k) for k in NEGATIVE_KEYWORDS) + r")",
    re.IGNORECASE,
)

JSON_LD_MENU_KEYS: tuple[str, ...] = ("menu", "hasMenu", "hasMenuPage")

USER_AGENT = (
    "Mozilla/5.0 (compatible; TasteMapMenuDiscovery/1.0; "
    "+https://tastemap.local/bot)"
)

HTTP_TIMEOUT_SECONDS = 10


def _normalize_website_url(url: str) -> str | None:
    """Return a cleaned, absolute website URL with scheme, or None if invalid."""
    raw = (url or "").strip()
    if not raw:
        return None
    if not raw.startswith(("http://", "https://")):
        raw = "https://" + raw
    try:
        parsed = urlparse(raw)
        if not parsed.hostname or "." not in parsed.hostname:
            return None
        cleaned = ParseResult(
            scheme=parsed.scheme or "https",
            netloc=parsed.netloc.lower(),
            path=parsed.path or "/",
            params="",
            query="",
            fragment="",
        )
        return urlunparse(cleaned)
    except ValueError:
        return None


def _fetch_html(url: str) -> str | None:
    """Fetch the page body as text, returning None on any network/HTTP error."""
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


class _MenuPageParser(HTMLParser):
    """HTML parser that collects JSON-LD blocks and candidate anchor links."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.json_ld_blocks: list[str] = []
        self.links: list[dict[str, str]] = []
        self._in_json_ld = False
        self._json_ld_buffer: list[str] = []
        self._anchor_buffer: list[str] = []
        self._current_href: str | None = None
        self._current_title: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_low = tag.lower()
        attr_dict = {k.lower(): (v if v is not None else "") for k, v in attrs}
        if tag_low == "script":
            ttype = attr_dict.get("type", "").lower()
            if "ld+json" in ttype:
                self._in_json_ld = True
                self._json_ld_buffer = []
            return
        if tag_low == "a":
            href = attr_dict.get("href", "")
            if href and not href.lower().startswith(("javascript:", "mailto:", "tel:")):
                self._current_href = href.strip()
                self._current_title = attr_dict.get("title", "").strip() or None
                self._anchor_buffer = []

    def handle_endtag(self, tag: str) -> None:
        tag_low = tag.lower()
        if tag_low == "script" and self._in_json_ld:
            self.json_ld_blocks.append("".join(self._json_ld_buffer))
            self._in_json_ld = False
            self._json_ld_buffer = []
            return
        if tag_low == "a" and self._current_href is not None:
            text = " ".join("".join(self._anchor_buffer).split())
            self.links.append(
                {
                    "href": self._current_href,
                    "text": text,
                    "title": self._current_title or "",
                }
            )
            self._current_href = None
            self._current_title = None
            self._anchor_buffer = []

    def handle_data(self, data: str) -> None:
        if self._in_json_ld:
            self._json_ld_buffer.append(data)
            return
        if self._current_href is not None:
            self._anchor_buffer.append(data)


def _iter_json_ld(payload: Any) -> Any:
    """Recursively yield every dict inside a JSON-LD structure (graph/list aware)."""
    if isinstance(payload, dict):
        yield payload
        for key in ("@graph", "graph", "hasPart", "itemListElement", "includedInDataCatalog"):
            value = payload.get(key)
            if value is not None:
                yield from _iter_json_ld(value)
    elif isinstance(payload, list):
        for item in payload:
            yield from _iter_json_ld(item)


def _extract_menu_url_from_json_ld(blocks: list[str], base_url: str) -> str | None:
    """Return the first usable menu URL discovered inside JSON-LD payloads."""
    for block in blocks:
        try:
            data = json.loads(block)
        except (json.JSONDecodeError, ValueError):
            continue
        for node in _iter_json_ld(data):
            if not isinstance(node, dict):
                continue
            node_type = node.get("@type")
            type_matches = False
            if isinstance(node_type, str):
                nt = node_type.lower()
                type_matches = "menu" in nt or nt in {"restaurant", "foodestablishment", "cafeorbar", "bakery"}
            elif isinstance(node_type, list):
                type_matches = any(
                    isinstance(t, str)
                    and ("menu" in t.lower() or t.lower() in {"restaurant", "foodestablishment", "cafeorbar", "bakery"})
                    for t in node_type
                )
            for key in JSON_LD_MENU_KEYS:
                value = node.get(key)
                candidate: str | None = None
                if isinstance(value, str) and value.strip():
                    candidate = value.strip()
                elif isinstance(value, dict):
                    for subkey in ("url", "@id", "sameAs", "href"):
                        sub = value.get(subkey)
                        if isinstance(sub, str) and sub.strip():
                            candidate = sub.strip()
                            break
                elif isinstance(value, list):
                    for entry in value:
                        if isinstance(entry, str) and entry.strip():
                            candidate = entry.strip()
                            break
                        if isinstance(entry, dict):
                            for subkey in ("url", "@id", "sameAs", "href"):
                                sub = entry.get(subkey)
                                if isinstance(sub, str) and sub.strip():
                                    candidate = sub.strip()
                                    break
                        if candidate:
                            break
                if candidate:
                    absolute = urljoin(base_url, candidate)
                    if _looks_like_menu_url(absolute) and not _looks_like_self(absolute, base_url):
                        return absolute
            # If node is itself a Menu / MenuPage and has a url
            if type_matches:
                url_val = node.get("url")
                if isinstance(url_val, str) and url_val.strip():
                    absolute = urljoin(base_url, url_val.strip())
                    if not _looks_like_self(absolute, base_url):
                        return absolute
    return None


def _looks_like_self(candidate: str, base: str) -> bool:
    """Return True if candidate is essentially the base website URL."""
    try:
        c = urlparse(candidate)
        b = urlparse(base)
    except ValueError:
        return False
    if c.hostname and b.hostname and c.hostname.lower() != b.hostname.lower():
        return False
    c_path = (c.path or "/").rstrip("/") or "/"
    b_path = (b.path or "/").rstrip("/") or "/"
    return c_path == b_path and not c.query and not c.fragment


def _looks_like_menu_url(url: str) -> bool:
    """Best-effort: reject obviously unrelated URLs, accept domain-local links."""
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    if not parsed.hostname or not parsed.scheme.startswith(("http", "https")):
        return False
    haystack = f"{parsed.path} {parsed.query}"
    if NEGATIVE_RE.search(haystack):
        return False
    return True


def _score_link_candidate(link: dict[str, str], base_url: str) -> tuple[int, str | None]:
    """Return (score, absolute_url) for an anchor link candidate. Score <= 0 → reject."""
    href_raw = link["href"]
    if not href_raw:
        return 0, None
    try:
        absolute = urljoin(base_url, href_raw)
    except ValueError:
        return 0, None
    parsed_abs = urlparse(absolute)
    parsed_base = urlparse(base_url)
    if (
        not parsed_abs.hostname
        or not parsed_abs.scheme.startswith(("http", "https"))
        or (parsed_abs.hostname.lower() != parsed_base.hostname.lower())
    ):
        # Cross-domain menu links are allowed but penalize negative patterns
        combined = f"{parsed_abs.hostname or ''} {parsed_abs.path or ''} {parsed_abs.query or ''}"
        if NEGATIVE_RE.search(combined):
            return 0, None
    if _looks_like_self(absolute, base_url):
        return 0, None
    if not _looks_like_menu_url(absolute):
        return 0, None

    text = link.get("text", "") or ""
    title = link.get("title", "") or ""
    href_display = f"{parsed_abs.path or ''} {parsed_abs.query or ''} {parsed_abs.fragment or ''}"

    haystack = f"{text}\n{title}\n{href_display}"
    score = 0
    if KEYWORD_RE.search(haystack):
        score += 5
    m = KEYWORD_RE.search(text)
    if m:
        score += 3
    m = KEYWORD_RE.search(title)
    if m:
        score += 1
    m = KEYWORD_RE.search(href_display)
    if m:
        score += 4
    # Strong bonus if menu keyword is in path (e.g. /menu.html)
    path = parsed_abs.path or ""
    if re.search(r"(?<=/)(menu|menü|yemek|food|dining)", path, re.IGNORECASE):
        score += 6
    # Penalize long text that contains the keyword only marginally
    if len(text) > 120:
        score -= 1
    return score, absolute


def _discover_menu_url_from_html(html: str, base_url: str) -> str | None:
    """Run JSON-LD first, then fall back to anchor link scanning."""
    try:
        parser = _MenuPageParser()
        parser.feed(html)
        parser.close()
    except (AssertionError, ValueError, RecursionError):
        return None

    json_ld_url = _extract_menu_url_from_json_ld(parser.json_ld_blocks, base_url)
    if json_ld_url:
        return json_ld_url

    seen: set[str] = set()
    best_score = 0
    best_url: str | None = None
    for link in parser.links:
        score, absolute = _score_link_candidate(link, base_url)
        if not absolute or score <= 0:
            continue
        if absolute in seen:
            continue
        seen.add(absolute)
        if score > best_score:
            best_score = score
            best_url = absolute
    return best_url


def discover_menu_url(website_url: str) -> str | None:
    """Return the most plausible menu page URL for the given restaurant website.

    Returns None on any error, when the website is invalid, or when no confident
    menu link can be found.
    """
    normalized = _normalize_website_url(website_url)
    if not normalized:
        return None
    html = _fetch_html(normalized)
    if not html:
        return None
    return _discover_menu_url_from_html(html, normalized)
