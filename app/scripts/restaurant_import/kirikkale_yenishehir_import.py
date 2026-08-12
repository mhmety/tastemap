import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy.exc import SQLAlchemyError

from app.db.session import SessionLocal
from app.models.restaurant import Restaurant
from app.scripts.restaurant_import.serpapi_import import (
    _extract_district,
    _extract_restaurant_payload,
    _normalize_text,
    _restaurant_exists,
    search_places,
)
from app.services.google_reviews_sync import sync_google_reviews_with_stats


def _is_target_area(value: Any) -> bool:
    """Return True if address/location indicates Yenişehir or University area in Kırıkkale."""
    targets = [
        "yenişehir",
        "yenişehir",  # alternate unicode
        "üniversite",
        "universite",
        "kırıkkale üniversitesi",
        "kirikkale universitesi",
    ]
    text = ""
    if isinstance(value, str):
        text = value.casefold()
    elif isinstance(value, list):
        text = " ".join(str(v).casefold() for v in value)
    elif isinstance(value, dict):
        text = " ".join(str(v).casefold() for v in value.values())
    else:
        text = str(value).casefold()

    # Must mention Kırıkkale and one of the target neighbourhoods
    if "kırıkkale" not in text and "kirikkale" not in text:
        return False
    return any(t in text for t in targets)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import Yenişehir / University area restaurants in Kırıkkale from SerpAPI and sync Google reviews."
    )
    parser.add_argument(
        "--search-pages",
        type=int,
        default=2,
        help="Maximum SerpAPI pages per query (default: 2).",
    )
    parser.add_argument(
        "--reviews-max-pages",
        type=int,
        default=10,
        help="Maximum Google review pages per restaurant (default: 10).",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING, format="%(message)s")

    started = time.perf_counter()

    # Targeted queries for Yenişehir / University surroundings
    queries = [
        "restaurants in Kırıkkale Yenişehir",
        "cafes in Kırıkkale Yenişehir",
        "dessert shops in Kırıkkale Yenişehir",
        "burger restaurants in Kırıkkale Yenişehir",
        "pizza restaurants in Kırıkkale Yenişehir",
        "döner restaurants in Kırıkkale Yenişehir",
        "kebab restaurants in Kırıkkale Yenişehir",
        "coffee shops in Kırıkkale Yenişehir",
        "breakfast restaurants in Kırıkkale Yenişehir",
        "newly opened restaurants in Kırıkkale Yenişehir",
        "restaurants near Kırıkkale University",
        "cafes near Kırıkkale University",
        "student restaurants Kırıkkale University",
    ]

    raw_results: list[dict[str, Any]] = []
    searches_used = 0
    for q in queries:
        try:
            results = search_places(q, max_pages=max(1, args.search_pages))
            searches_used += 1
            raw_results.extend(results)
        except Exception as exc:
            print(f"Warning: Search failed for query '{q}': {exc}")

    # Filter to target area
    filtered_results = [item for item in raw_results if _is_target_area(item)]
    total = len(filtered_results)

    restaurants_imported = 0
    restaurants_skipped = 0
    restaurants_errors = 0
    invalid_skipped = len(raw_results) - total

    google_imported = 0
    google_updated = 0
    google_skipped = 0
    restaurants_with_review_sync = 0

    newly_imported_names = []

    with SessionLocal() as db:
        for index, item in enumerate(filtered_results, start=1):
            payload = _extract_restaurant_payload(item)
            name = _normalize_text(payload.get("name"), 255)
            latitude = payload.get("latitude")
            longitude = payload.get("longitude")

            print(f"[{index}/{total}]")
            print("Restaurant:")
            print(name or "<unknown>")

            if not name or latitude is None or longitude is None:
                restaurants_errors += 1
                print("Error: Missing required fields (name/latitude/longitude).")
                print()
                continue

            restaurant_id = None
            try:
                with db.begin():
                    if _restaurant_exists(db, name=name, latitude=latitude, longitude=longitude):
                        restaurants_skipped += 1
                        print("Skipped: Duplicate restaurant")
                        print()
                        continue

                    restaurant = Restaurant(
                        name=name,
                        city="Kırıkkale",
                        district=_extract_district(payload.get("address"), "Kırıkkale"),
                        latitude=latitude,
                        longitude=longitude,
                        rating=payload.get("rating"),
                        review_count=payload.get("review_count"),
                        category=_normalize_text(payload.get("category"), 100),
                        description=_normalize_text(payload.get("description"), 1000),
                        price_level=_normalize_text(payload.get("price_level"), 20),
                        opening_hours=_normalize_text(payload.get("opening_hours"), 4000),
                        operating_hours=payload.get("operating_hours")
                        if isinstance(payload.get("operating_hours"), dict)
                        else None,
                        google_place_id=_normalize_text(payload.get("google_maps_place_id"), 255),
                        serpapi_data_id=_normalize_text(payload.get("serpapi_data_id"), 255),
                        thumbnail=_normalize_text(payload.get("thumbnail"), 500),
                        reviews_link=_normalize_text(payload.get("reviews_link"), 500),
                        photos_link=_normalize_text(payload.get("photos_link"), 500),
                        user_review=_normalize_text(payload.get("user_review"), 4000),
                        website=_normalize_text(payload.get("website"), 255),
                        phone=_normalize_text(payload.get("phone"), 50),
                    )
                    db.add(restaurant)
                    db.flush()
                    restaurant_id = restaurant.id
                    restaurants_imported += 1
                    newly_imported_names.append(name)
            except SQLAlchemyError as exc:
                restaurants_errors += 1
                print(f"Error: Failed to insert restaurant ({exc}).")
                print()
                continue

            if restaurant_id is None:
                restaurants_errors += 1
                print("Error: Restaurant insert did not produce an id.")
                print()
                continue

            # Sync Google reviews if identifiers present
            try:
                with db.begin():
                    stats = sync_google_reviews_with_stats(
                        db,
                        restaurant_id,
                        max_pages=max(1, args.reviews_max_pages),
                    )
                restaurants_with_review_sync += 1
            except Exception as exc:
                print(f"Warning: Google reviews sync failed ({exc}).")
                print()
                continue

            if stats is None:
                print("Imported:")
                print("0 reviews")
                print()
                continue

            google_imported += stats.imported
            google_updated += stats.updated
            google_skipped += stats.skipped

            print()
            print("Imported:")
            print(f"{stats.imported} reviews")
            print()
            print("Updated:")
            print(stats.updated)
            print()
            print("Skipped:")
            print(stats.skipped)
            print()

    elapsed = time.perf_counter() - started
    print("=== Import Summary ===")
    print(f"Restaurants discovered: {len(raw_results)}")
    print(f"New restaurants imported: {restaurants_imported}")
    print(f"Existing restaurants skipped: {restaurants_skipped}")
    print(f"Invalid/out-of-area results skipped: {invalid_skipped}")
    print(f"Restaurants with review sync: {restaurants_with_review_sync}")
    print(f"Google reviews imported: {google_imported}")
    print(f"Google reviews updated: {google_updated}")
    print(f"Google reviews skipped (duplicates): {google_skipped}")
    print(f"Errors: {restaurants_errors}")
    print(f"SerpAPI searches used: {searches_used}")
    if newly_imported_names:
        print("Newly imported restaurants:")
        for n in newly_imported_names:
            print(f" - {n}")
    print(f"Elapsed time: {elapsed:.2f} sec")


if __name__ == "__main__":
    main()