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
    search_restaurants,
)
from app.services.google_reviews_sync import sync_google_reviews_with_stats


def _contains_kirikkale(value: Any) -> bool:
    target = "kırıkkale".casefold()
    if isinstance(value, str):
        return target in value.casefold()
    if isinstance(value, list):
        return any(_contains_kirikkale(item) for item in value)
    if isinstance(value, dict):
        return any(_contains_kirikkale(item) for item in value.values())
    return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import Kırıkkale restaurants from SerpAPI and sync Google reviews after each import."
    )
    parser.add_argument(
        "--search-pages",
        type=int,
        default=3,
        help="Maximum number of SerpAPI search pages to fetch per district (default: 3).",
    )
    parser.add_argument(
        "--reviews-max-pages",
        type=int,
        default=20,
        help="Maximum number of Google reviews pages to fetch per restaurant (default: 20).",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING, format="%(message)s")

    started = time.perf_counter()
    districts = [
        "Kırıkkale Merkez Kırıkkale",
        "Yahşihan Kırıkkale",
    ]

    raw_results: list[dict[str, Any]] = []
    for district_query in districts:
        raw_results.extend(search_restaurants(district_query, max_pages=max(1, args.search_pages)))

    filtered_results = [item for item in raw_results if _contains_kirikkale(item)]
    total = len(filtered_results)

    restaurants_imported = 0
    restaurants_skipped = 0
    restaurants_errors = 0

    google_imported = 0
    google_updated = 0
    google_skipped = 0

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

            try:
                with db.begin():
                    stats = sync_google_reviews_with_stats(
                        db,
                        restaurant_id,
                        max_pages=max(1, args.reviews_max_pages),
                    )
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
    print("Restaurants imported:")
    print(restaurants_imported)
    print()
    print("Restaurants skipped:")
    print(restaurants_skipped)
    print()
    print("Restaurants errors:")
    print(restaurants_errors)
    print()
    print("Google reviews imported:")
    print(google_imported)
    print()
    print("Google reviews updated:")
    print(google_updated)
    print()
    print("Google reviews skipped:")
    print(google_skipped)
    print()
    print("Elapsed time:")
    print(f"{elapsed:.2f} sec")


if __name__ == "__main__":
    main()

