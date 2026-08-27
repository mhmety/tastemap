"""Generic menu enrichment flow: extract menus from Restaurant.website -> save MenuItem rows.

Restaurant-agnostic: NO per-restaurant branches, NO hard-coded names/URLs.

Usage (safe default = DRY RUN = NO DB WRITES):
    python -X utf8 app/scripts/restaurant_import/menu_enrichment.py --dry-run

Actual write run (CAREFUL — this deletes + rewrites menu_items for matched restaurants,
excluding Cielo/Pufuwa by default):
    python -X utf8 app/scripts/restaurant_import/menu_enrichment.py --apply

Include Cielo/Pufuwa (replace their existing menu_items if extraction succeeds):
    python -X utf8 app/scripts/restaurant_import/menu_enrichment.py --apply --include-known

Runtime-only stats are printed; no new DB columns / migrations are added (per spec).
"""

from __future__ import annotations

import argparse
import os
import sys
import time
import traceback
from dataclasses import dataclass, field
from typing import Any

# Ensure the project root is on sys.path when the script is run directly.
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# Local developer fallback for host-machine runs where .env uses hostname "db"
# but the script is invoked from outside Docker. Must be set BEFORE
# from app.db.session import SessionLocal because app.core.config reads env.
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://tastemap:tastemap@localhost:5432/tastemap",
)

from sqlalchemy import delete, func, select  # noqa: E402
from sqlalchemy.exc import SQLAlchemyError  # noqa: E402

from app.db.session import SessionLocal  # noqa: E402
from app.models.menu_item import MenuItem  # noqa: E402
from app.models.restaurant import Restaurant  # noqa: E402
from app.services.menu_render import (  # noqa: E402
    NormalizedMenuItem,
    extract_menu_items_for_website,
    extract_menu_items_for_website_with_report,
)

# Restaurants we never touch by default (to preserve their hand-curated DB data).
# This is NOT a restaurant-specific extraction branch; it only prevents OVERWRITING
# their existing menu_items during enrichment. Extraction itself uses the exact same
# generic pipeline -- they are just never written back to DB by default.
_PRESERVE_NAME_SUBSTRINGS_LOWER: tuple[str, ...] = (
    "cie-lo",
    "pufuwa",
)


@dataclass
class _RunStats:
    total_restaurants: int = 0
    with_website: int = 0
    without_website: int = 0
    preserved_skipped: int = 0  # preserve-list restaurants (skipped write)
    success_extracted_and_would_write: int = 0  # with items, would/was written
    total_items_written_or_found: int = 0
    menu_unavailable: int = 0  # extraction OK but 0 items returned
    error_count: int = 0  # any exception raised while processing one restaurant
    per_restaurant_lines: list[str] = field(default_factory=list)


def _is_preserved_restaurant(name: str | None) -> bool:
    lowered = (name or "").strip().lower()
    if not lowered:
        return False
    return any(sub in lowered for sub in _PRESERVE_NAME_SUBSTRINGS_LOWER)


def _validate_extraction_output(items: Any) -> list[NormalizedMenuItem]:
    """Hardening: only accept list[NormalizedMenuItem-shaped dicts] with name + price."""
    if not isinstance(items, list):
        return []
    out: list[NormalizedMenuItem] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        name = it.get("name")
        price = it.get("price")
        if not isinstance(name, str) or not name.strip():
            continue
        # MenuItem.price is Numeric(10,2) -> reject nonsense.
        try:
            price_f = float(price)
        except (TypeError, ValueError):
            continue
        if price_f <= 0 or price_f > 100000:
            continue
        out.append(
            NormalizedMenuItem(
                name=name.strip()[:255],
                price=price_f,
                category=(str(it["category"]).strip()[:100])
                if isinstance(it.get("category"), str) and it.get("category").strip()
                else "Menü",
                description=(str(it["description"]).strip()[:1000])
                if isinstance(it.get("description"), str) and it.get("description").strip()
                else None,
            )
        )
    # Dedup again defensively at write time too (in case caller output changes).
    seen: set[tuple[str, int]] = set()
    deduped: list[NormalizedMenuItem] = []
    for it in out:
        key = (it["name"].lower(), int(round(it["price"] * 100)))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(it)
    return deduped


def _save_menu_items_for_restaurant(
    db,
    restaurant_id: object,
    validated_items: list[NormalizedMenuItem],
) -> int:
    """Wipe previous menu_items for this restaurant and insert new ones in one TX.

    Returns the number of rows inserted.
    """
    # Per-restaurant nested TX so that an error here rolls back only this row.
    with db.begin_nested():
        # 1. Delete existing menu_items for this restaurant.
        del_stmt = delete(MenuItem).where(MenuItem.restaurant_id == restaurant_id)
        db.execute(del_stmt)
        db.flush()
        # 2. Build new MenuItem ORM rows.
        new_rows: list[MenuItem] = []
        for it in validated_items:
            new_rows.append(
                MenuItem(
                    restaurant_id=restaurant_id,  # type: ignore[arg-type]
                    name=it["name"],
                    price=it["price"],
                    category=it.get("category") or "Menü",
                    description=it.get("description") or None,
                )
            )
        if new_rows:
            db.add_all(new_rows)
            db.flush()
        return len(new_rows)


def _enrich_all(dry_run: bool, include_preserved: bool) -> _RunStats:
    stats = _RunStats()
    t0 = time.time()

    with SessionLocal() as db:
        # Load every restaurant (we need .id, .name, .website -- lightweight).
        rows = list(db.execute(select(Restaurant)).scalars().all())
        stats.total_restaurants = len(rows)

        for idx, r in enumerate(rows, start=1):
            name = r.name or "<unknown>"
            website = (r.website or "").strip() or None
            line_prefix = f"[{idx:>3}/{stats.total_restaurants}] {name!r:<40.40}"

            if website is None:
                stats.without_website += 1
                stats.per_restaurant_lines.append(f"{line_prefix}  SKIP: no website URL")
                continue
            stats.with_website += 1

            # Preserve-list check (Cielo/Pufuwa by default).
            is_preserved = _is_preserved_restaurant(r.name)
            if is_preserved and not include_preserved:
                stats.preserved_skipped += 1
                stats.per_restaurant_lines.append(
                    f"{line_prefix}  PRESERVE: existing menu_items retained (did not overwrite)"
                )
                continue

            # ---- Generic extraction (the exact same pipeline for every restaurant).
            try:
                raw_items, extraction_report = extract_menu_items_for_website_with_report(website)
                validated = _validate_extraction_output(raw_items)
            except Exception:  # noqa: BLE001 -- never abort the whole loop
                stats.error_count += 1
                exc_summary = traceback.format_exc(limit=1).strip().splitlines()[-1]
                stats.per_restaurant_lines.append(
                    f"{line_prefix}  ERROR: {exc_summary[:180]}"
                )
                continue
            if not raw_items:
                print(
                    f"    extraction report: "
                    f"home={extraction_report['homepage_extract']['items']}, "
                    f"discover={extraction_report['discovered_menu']['items']}, "
                    f"sections={extraction_report['section_chunks']['items']}, "
                    f"images={extraction_report['image_detect']['items']}, "
                    f"ocr={extraction_report['ocr']['items']}, "
                    f"ocr_note={extraction_report['ocr']['note']}, "
                    f"filtered={extraction_report['trust_filtered']}, "
                    f"final={extraction_report['final_items']}, "
                    f"status={extraction_report['status']}"
                )    

            if not validated:
                stats.menu_unavailable += 1
                stats.per_restaurant_lines.append(
                    f"{line_prefix}  UNAVAILABLE: extraction returned 0 trusted items"
                )
                continue

            # ---- We have items. Handle dry-run / write.
            n_items = len(validated)
            stats.success_extracted_and_would_write += 1
            stats.total_items_written_or_found += n_items

            if dry_run:
                # Always safe -- no DB mutation.
                stats.per_restaurant_lines.append(
                    f"{line_prefix}  DRY-RUN: found {n_items} menu items (NO WRITE PERFORMED)"
                )
                # Show 2 example items for visibility (safe preview).
                for j, ex in enumerate(validated, start=1):
                    cat = ex.get("category") or ""
                    stats.per_restaurant_lines.append(
                        f"          #{j} {ex['name'][:40]!r:<42}  ₺{ex['price']:<7.2f}  cat={cat!r}"
                    )
                continue

            # Actual DB write. Wrapped in per-restaurant nested try; never kills loop.
            try:
                written = _save_menu_items_for_restaurant(db, r.id, validated)
                stats.per_restaurant_lines.append(
                    f"{line_prefix}  WROTE: {written} menu items committed (overwrote previous)"
                )
            except SQLAlchemyError:
                stats.error_count += 1
                exc_summary = traceback.format_exc(limit=1).strip().splitlines()[-1]
                stats.per_restaurant_lines.append(
                    f"{line_prefix}  DB-ERROR (rolled back this restaurant): {exc_summary[:160]}"
                )
                # Per-restaurant nested TX already rolled back; loop continues.

        # Finalize session-level transaction. If we got here there is no session-wide
        # error; per-restaurant failures were caught in nested TXs.
        try:
            db.commit()
        except SQLAlchemyError:
            db.rollback()
            raise

    stats.per_restaurant_lines.append("")
    stats.per_restaurant_lines.append(
        f"Total wall-clock time: {(time.time() - t0) * 1000:.0f}ms."
    )
    return stats


def _print_stats(stats: _RunStats, dry_run: bool) -> None:
    # Don't print the (potentially 100+ line) per-restaurant log to stdout by
    # default to keep the summary readable; write it to a log file next to the
    # script for auditing. This also makes the summary visible quickly.
    log_path = os.path.join(_THIS_DIR, f"menu_enrichment_{'dry' if dry_run else 'apply'}.log")
    try:
        with open(log_path, "w", encoding="utf-8") as f:
            for line in stats.per_restaurant_lines:
                f.write(line + "\n")
        print(f"(Per-restaurant detail log written to: {log_path})")
    except OSError:
        for line in stats.per_restaurant_lines:
            print(line)
    print()
    print("=" * 88)
    print(f"MODE                : {'DRY-RUN (no writes)' if dry_run else 'APPLY (writes committed)'}")
    print(f"toplam restoran     : {stats.total_restaurants}")
    print(f"website'i olan      : {stats.with_website}")
    print(f"website'i olmayan   : {stats.without_website}")
    print(
        f"menü başarıyla çıkarılan (yazılan/would-write): {stats.success_extracted_and_would_write}"
    )
    print(f"DB'ye kaydedilen (veya DRY-RUN'da bulunan) toplam menu item : {stats.total_items_written_or_found}")
    print(f"menüsü bulunamayan   : {stats.menu_unavailable}")
    print(f"hata alan restoran   : {stats.error_count}")
    if stats.preserved_skipped:
        print(f"korunan (Cielo/Pufuwa) overwrite edilmeyen: {stats.preserved_skipped}")
    print("=" * 88)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Enrich existing restaurants with menu_items from their website URL.",
    )
    parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help="Default behaviour: NO DB writes. Print what would be written.",
    )
    parser.add_argument(
        "--apply",
        dest="dry_run",
        action="store_false",
        help="Actually DELETE + INSERT menu_items. Default is safe dry-run.",
    )
    parser.add_argument(
        "--include-known",
        dest="include_preserved",
        action="store_true",
        help="Also process Cielo/Pufuwa (overwrites their existing menu_items if extraction returns items). Default: False -> preserve.",
    )
    parser.set_defaults(dry_run=True, include_preserved=False)
    args = parser.parse_args()

    stats = _enrich_all(dry_run=args.dry_run, include_preserved=args.include_preserved)
    _print_stats(stats, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
