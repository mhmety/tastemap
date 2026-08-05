import argparse
import logging
import sys
from pathlib import Path

import uuid

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db.session import SessionLocal
from app.services.google_reviews_sync import sync_google_reviews


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    parser = argparse.ArgumentParser(description="Sync Google reviews for a restaurant from SerpAPI.")
    parser.add_argument("--restaurant-id", required=True, help="Restaurant UUID")
    parser.add_argument(
        "--max-pages",
        type=int,
        default=10,
        help="Maximum number of review pages to fetch (default: 10).",
    )
    args = parser.parse_args()

    restaurant_id = uuid.UUID(args.restaurant_id)
    max_pages = max(1, args.max_pages)

    with SessionLocal() as db:
        with db.begin():
            sync_google_reviews(db, restaurant_id, max_pages=max_pages)


if __name__ == "__main__":
    main()

