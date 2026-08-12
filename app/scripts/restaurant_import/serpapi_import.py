import argparse
import json
import os
import sys
import traceback
from pathlib import Path
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db.session import SessionLocal
from app.models.restaurant import Restaurant

SERPAPI_ENDPOINT = "https://serpapi.com/search.json"


def _read_env_value_from_dotenv(key: str) -> Optional[str]:
    dotenv_path = PROJECT_ROOT / ".env"
    if not dotenv_path.exists():
        return None

    try:
        for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            if k.strip() != key:
                continue
            value = v.strip().strip('"').strip("'")
            return value or None
    except OSError:
        return None

    return None


def get_serpapi_key() -> str:
    key = os.getenv("SERPAPI_KEY") or _read_env_value_from_dotenv("SERPAPI_KEY")
    if not key:
        raise SystemExit(
            "SERPAPI_KEY not found. Set SERPAPI_KEY in your environment or in .env."
        )
    return key


def _http_get_json(url: str, params: dict[str, Any]) -> dict[str, Any]:
    query = urlencode(params)
    request = Request(
        f"{url}?{query}",
        headers={"Accept": "application/json"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=30) as response:
            payload = response.read().decode("utf-8")
            return json.loads(payload)
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(f"SerpAPI request failed: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError("SerpAPI response is not valid JSON") from exc


def _extract_search_results(response: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("local_results", "place_results", "places"):
        value = response.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def _next_page_token(response: dict[str, Any]) -> Optional[str]:
    pagination = response.get("serpapi_pagination")
    if isinstance(pagination, dict):
        token = pagination.get("next_page_token")
        if isinstance(token, str) and token.strip():
            return token.strip()
    token = response.get("next_page_token")
    if isinstance(token, str) and token.strip():
        return token.strip()
    return None


def search_restaurants(city: str, *, max_pages: int = 3) -> list[dict[str, Any]]:
    """Backward compatible: search for restaurants in a city."""
    return search_places(query=f"restaurants in {city}", max_pages=max_pages)


def search_places(query: str, *, max_pages: int = 3) -> list[dict[str, Any]]:
    """Generic SerpAPI Google Maps search using a free‑form query."""
    api_key = get_serpapi_key()

    results: list[dict[str, Any]] = []
    next_token: Optional[str] = None

    for _ in range(max_pages):
        params: dict[str, Any] = {
            "engine": "google_maps",
            "q": query,
            "api_key": api_key,
        }
        if next_token:
            params["next_page_token"] = next_token

        response = _http_get_json(SERPAPI_ENDPOINT, params)
        results.extend(_extract_search_results(response))

        next_token = _next_page_token(response)
        if not next_token:
            break

    return results


def _extract_float(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _extract_int(value: Any) -> Optional[int]:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _repair_text(value: str) -> str:
    text = value
    for encoding in ("latin1", "cp1252"):
        try:
            repaired = text.encode(encoding).decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue
        if repaired != text:
            text = repaired
    return text


def _repair_value(value: Any) -> Any:
    if isinstance(value, str):
        return _repair_text(value)
    if isinstance(value, list):
        return [_repair_value(item) for item in value]
    if isinstance(value, dict):
        return {k: _repair_value(v) for k, v in value.items()}
    return value


def _extract_restaurant_payload(item: dict[str, Any]) -> dict[str, Any]:
    gps = item.get("gps_coordinates")
    if not isinstance(gps, dict):
        gps = {}

    return {
        "name": _repair_value(item.get("title") or item.get("name")),
        "address": _repair_value(item.get("address")),
        "latitude": _extract_float(gps.get("latitude") or item.get("latitude")),
        "longitude": _extract_float(gps.get("longitude") or item.get("longitude")),
        "rating": _extract_float(item.get("rating")),
        "review_count": _extract_int(item.get("reviews") or item.get("review_count")),
        "phone": _repair_value(item.get("phone")),
        "website": _repair_value(item.get("website")),
        "description": _repair_value(item.get("description")),
        "opening_hours": _repair_value(item.get("hours")),
        "operating_hours": _repair_value(item.get("operating_hours")),
        "category": _repair_value(item.get("type") or item.get("category")),
        "price_level": _repair_value(item.get("price")),
        "google_maps_place_id": _repair_value(item.get("place_id") or item.get("google_maps_place_id")),
        "serpapi_data_id": _repair_value(item.get("data_id") or item.get("serpapi_data_id")),
        "thumbnail": _repair_value(item.get("thumbnail")),
        "reviews_link": _repair_value(item.get("reviews_link")),
        "photos_link": _repair_value(item.get("photos_link")),
        "user_review": _repair_value(item.get("user_review")),
    }


def _normalize_text(value: Optional[str], max_length: int) -> Optional[str]:
    if value is None:
        return None
    text = _repair_text(str(value)).strip()
    if not text:
        return None
    return text[:max_length]


def _extract_district(address: Optional[str], city: str) -> str:
    if not address:
        return "Unknown"

    normalized_city = _repair_text(city).strip().lower()
    raw = _repair_text(address).strip()

    if "/" in raw:
        parts = [p.strip() for p in raw.split("/") if p.strip()]
        if len(parts) >= 2 and parts[-1].lower() == normalized_city:
            return parts[-2][:100]

    segments = [s.strip() for s in raw.split(",") if s.strip()]
    for idx, segment in enumerate(segments):
        if normalized_city in segment.lower():
            if idx > 0:
                return segments[idx - 1][:100]
            break

    return "Unknown"


def _restaurant_exists(
    db: Session,
    *,
    name: str,
    latitude: float,
    longitude: float,
) -> bool:
    query = select(Restaurant.id).where(
        Restaurant.name == name,
        Restaurant.latitude == latitude,
        Restaurant.longitude == longitude,
    )
    return db.execute(query).scalar_one_or_none() is not None


def import_restaurants(city: str, raw_results: list[dict[str, Any]]) -> tuple[int, int, int]:
    imported = 0
    skipped = 0
    errors = 0

    with SessionLocal() as db:
        try:
            with db.begin():
                for item in raw_results:
                    payload = _extract_restaurant_payload(item)
                    name = _normalize_text(payload.get("name"), 255)
                    latitude = payload.get("latitude")
                    longitude = payload.get("longitude")

                    if not name or latitude is None or longitude is None:
                        print(f"Restaurant: {name or '<unknown>'}")
                        print("Error: Missing required fields (name/latitude/longitude).")
                        errors += 1
                        continue

                    try:
                        with db.begin_nested():
                            if _restaurant_exists(db, name=name, latitude=latitude, longitude=longitude):
                                skipped += 1
                                continue

                            print(f"Restaurant: {name}")
                            restaurant = Restaurant(
                                name=name,
                                city=_normalize_text(city, 100) or city[:100],
                                district=_extract_district(payload.get("address"), city),
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
                            imported += 1
                    except SQLAlchemyError:
                        print(f"Restaurant: {name}")
                        print("Error:")
                        print(traceback.format_exc())
                        errors += 1
        except SQLAlchemyError:
            db.rollback()
            raise

    return imported, skipped, errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Import restaurants from SerpAPI into PostgreSQL.")
    parser.add_argument("--city", required=True, help="City to search restaurants in (e.g., Ankara)")
    parser.add_argument(
        "--max-pages",
        type=int,
        default=3,
        help="Maximum number of SerpAPI pages to fetch (default: 3)",
    )
    args = parser.parse_args()

    city = args.city.strip()
    if not city:
        raise SystemExit("--city cannot be empty")

    results = search_restaurants(city, max_pages=max(1, args.max_pages))
    imported, skipped, errors = import_restaurants(city, results)

    print(f"Imported: {imported}")
    print(f"Skipped: {skipped}")
    print(f"Errors: {errors}")


if __name__ == "__main__":
    main()

