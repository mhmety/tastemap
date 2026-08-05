import hashlib
import logging
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.google_review import GoogleReview
from app.models.restaurant import Restaurant
from app.services.google_maps_reviews import GoogleMapsReviewsService, get_serpapi_key

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class GoogleReviewsSyncStats:
    imported: int
    updated: int
    skipped: int
    pages_fetched: int
    elapsed_seconds: float


def _parse_iso_datetime(value: str | None) -> Optional[datetime]:
    if not value:
        return None
    raw = value.strip()
    if not raw:
        return None
    try:
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        parsed = datetime.fromisoformat(raw)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        return None


def _normalize_hash_component(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def _compute_review_hash(review: dict[str, Any]) -> str:
    user = review.get("user") if isinstance(review.get("user"), dict) else {}
    author_name = user.get("name") if isinstance(user, dict) else None
    rating = review.get("rating")
    review_text = _extract_review_text(review)
    iso_date = review.get("iso_date") or review.get("date")

    payload = "|".join(
        [
            _normalize_hash_component(author_name),
            _normalize_hash_component(rating),
            _normalize_hash_component(review_text),
            _normalize_hash_component(iso_date),
        ]
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _extract_review_text(review: dict[str, Any]) -> Optional[str]:
    for key in ("review_text", "text", "snippet"):
        value = review.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    extracted = review.get("extracted_snippet")
    if isinstance(extracted, dict):
        original = extracted.get("original")
        if isinstance(original, str) and original.strip():
            return original.strip()

    return None



def _extract_review_fields(
    *,
    restaurant_id: uuid.UUID,
    review: dict[str, Any],
    default_language: str | None,
) -> dict[str, Any]:
    user = review.get("user") if isinstance(review.get("user"), dict) else {}
    author_name = user.get("name") if isinstance(user, dict) else None
    profile_photo = user.get("thumbnail") if isinstance(user, dict) else None


    provider_review_id = review.get("review_id")
    if not isinstance(provider_review_id, str) or not provider_review_id.strip():
        provider_review_id = None

    rating_value = review.get("rating")
    rating_int: int | None
    try:
        rating_int = int(round(float(rating_value)))
    except (TypeError, ValueError):
        rating_int = None

    review_text = _extract_review_text(review)

    iso_date = review.get("iso_date")
    if not isinstance(iso_date, str) or not iso_date.strip():
        iso_date = None

    likes_value = review.get("likes")
    likes_int: int | None
    try:
        likes_int = int(likes_value) if likes_value is not None else None
    except (TypeError, ValueError):
        likes_int = None

    language = review.get("language")
    if not isinstance(language, str) or not language.strip():
        language = default_language

    return {
        "restaurant_id": restaurant_id,
        "author_name": author_name.strip() if isinstance(author_name, str) and author_name.strip() else None,
        "rating": rating_int,
        "review_text": review_text,
        "review_date": iso_date.strip() if isinstance(iso_date, str) and iso_date.strip() else None,
        "profile_photo": profile_photo.strip()
        if isinstance(profile_photo, str) and profile_photo.strip()
        else None,
        "likes": likes_int,
        "provider_review_id": provider_review_id,
        "language": language.strip() if isinstance(language, str) and language.strip() else None,
        "review_hash": _compute_review_hash(review),
        "raw_json": review,
    }


def sync_google_reviews(
    db: Session,
    restaurant_id: uuid.UUID,
    *,
    max_pages: int = 10,
) -> int:
    stats = sync_google_reviews_with_stats(db, restaurant_id, max_pages=max_pages)
    if stats is None:
        return 0
    return stats.imported + stats.updated


def sync_google_reviews_with_stats(
    db: Session,
    restaurant_id: uuid.UUID,
    *,
    max_pages: int = 10,
) -> GoogleReviewsSyncStats | None:
    restaurant = db.execute(
        select(Restaurant).where(Restaurant.id == restaurant_id)
    ).scalar_one_or_none()
    if restaurant is None:
        raise ValueError("Restaurant not found.")

    data_id = restaurant.serpapi_data_id
    place_id = restaurant.google_place_id
    reviews_link = restaurant.reviews_link

    if not data_id and not place_id and not reviews_link:
        logger.info("Skipping Google reviews sync for restaurant=%s (no data_id/place_id/reviews_link).", restaurant.id)
        return None

    try:
        api_key = get_serpapi_key()
    except Exception as exc:
        logger.warning("Skipping Google reviews sync for restaurant=%s (SERPAPI_KEY missing: %s).", restaurant.id, exc)
        return None

    started = time.perf_counter()
    logger.info("Restaurant: %s", restaurant.name)

    service = GoogleMapsReviewsService(api_key=api_key)

    try:
        pages = service.iter_review_pages(
            data_id=data_id,
            place_id=place_id,
            reviews_link=reviews_link,
            max_pages=max_pages,
        )
    except Exception as exc:
        logger.warning("Failed to fetch Google reviews for restaurant=%s: %s", restaurant.id, exc)
        return None

    imported = 0
    updated = 0
    skipped = 0

    existing_reviews = db.execute(
        select(GoogleReview).where(GoogleReview.restaurant_id == restaurant.id)
    ).scalars().all()
    existing_by_provider_id: dict[str, GoogleReview] = {
        review.provider_review_id: review
        for review in existing_reviews
        if isinstance(review.provider_review_id, str) and review.provider_review_id.strip()
    }
    existing_by_hash: dict[str, GoogleReview] = {
        review.review_hash: review for review in existing_reviews
    }

    for page_index, page_reviews in enumerate(pages, start=1):
        logger.info("Fetched page %s", page_index)
        for review in page_reviews:
            payload = _extract_review_fields(
                restaurant_id=restaurant.id,
                review=review,
                default_language=None,
            )

            provider_review_id = payload.get("provider_review_id")
            review_hash = payload["review_hash"]

            existing = (
                existing_by_provider_id.get(provider_review_id)
                if provider_review_id
                else None
            )
            if existing is None:
                existing = existing_by_hash.get(review_hash)

            if existing is None:
                created = GoogleReview(**payload)
                db.add(created)
                existing_by_hash[review_hash] = created
                if provider_review_id:
                    existing_by_provider_id[provider_review_id] = created
                imported += 1
                continue

            changed = False
            for key in (
                "author_name",
                "rating",
                "review_text",
                "review_date",
                "profile_photo",
                "likes",
                "provider_review_id",
                "language",
                "review_hash",
                "raw_json",
            ):
                if getattr(existing, key) != payload.get(key):
                    changed = True
                    break

            if not changed:
                skipped += 1
                continue

            for key, value in payload.items():
                setattr(existing, key, value)
            existing_by_hash[review_hash] = existing
            if provider_review_id:
                existing_by_provider_id[provider_review_id] = existing
            updated += 1

    db.flush()

    elapsed = time.perf_counter() - started
    logger.info("Imported: %s reviews", imported)
    logger.info("Updated: %s reviews", updated)
    logger.info("Skipped: %s duplicates", skipped)
    logger.info("Elapsed: %.2f sec", elapsed)

    return GoogleReviewsSyncStats(
        imported=imported,
        updated=updated,
        skipped=skipped,
        pages_fetched=page_index if "page_index" in locals() else 0,
        elapsed_seconds=elapsed,
    )


def google_review_to_review_response_payload(
    *,
    google_review: GoogleReview,
    restaurant_id: uuid.UUID,
) -> dict[str, Any]:
    parsed = _parse_iso_datetime(google_review.review_date)
    created_at = parsed or google_review.created_at
    updated_at = created_at

    return {
        "id": google_review.id,
        "user_id": None,
        "rating": google_review.rating if google_review.rating is not None else 0,
        "comment": google_review.review_text,
        "created_at": created_at,
        "updated_at": updated_at,
        "author_name": google_review.author_name,
        "profile_photo": google_review.profile_photo,
        "likes": google_review.likes,
        "source": "google",
    }
