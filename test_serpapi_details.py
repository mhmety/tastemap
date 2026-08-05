import json
import os
import socket
import sys
from pathlib import Path
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from urllib.request import Request, urlopen

from sqlalchemy import or_, select

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


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


def _ensure_database_url() -> None:
    if os.getenv("DATABASE_URL"):
        return

    dotenv_value = _read_env_value_from_dotenv("DATABASE_URL")
    if dotenv_value:
        os.environ["DATABASE_URL"] = dotenv_value

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        return

    if "@db:" not in database_url and "@db/" not in database_url:
        return

    try:
        socket.gethostbyname("db")
        return
    except OSError:
        pass

    database_url = database_url.replace("@db:", "@localhost:")
    database_url = database_url.replace("@db/", "@localhost/")
    os.environ["DATABASE_URL"] = database_url


def get_serpapi_key() -> str:
    key = os.getenv("SERPAPI_KEY") or _read_env_value_from_dotenv("SERPAPI_KEY")
    if not key:
        raise SystemExit(
            "SERPAPI_KEY not found. Set SERPAPI_KEY in your environment or in .env."
        )
    return key


def _http_get_json(url: str) -> dict[str, Any]:
    request = Request(
        url,
        headers={"Accept": "application/json"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=60) as response:
            payload = response.read().decode("utf-8")
            return json.loads(payload)
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(f"Request failed: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError("Response is not valid JSON") from exc


def _with_api_key(url: str, api_key: str) -> str:
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    if "api_key" not in query:
        query["api_key"] = api_key
    new_query = urlencode(query)
    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment,
        )
    )


def _build_data_param(data_id: str, latitude: float, longitude: float) -> str:
    return f"!4m5!3m4!1s{data_id}!8m2!3d{latitude}!4d{longitude}"


def _fetch_initial_details(*, api_key: str, place_id: Optional[str], data_id: Optional[str], latitude: Optional[float], longitude: Optional[float]) -> dict[str, Any]:
    base = "https://serpapi.com/search.json"
    params: dict[str, Any] = {"engine": "google_maps", "api_key": api_key}

    if place_id:
        params["place_id"] = place_id
    elif data_id and latitude is not None and longitude is not None:
        params["type"] = "place"
        params["data"] = _build_data_param(data_id, latitude, longitude)
    elif data_id:
        params["data_id"] = data_id
    else:
        raise RuntimeError("Missing place_id and data_id for details request.")

    url = f"{base}?{urlencode(params)}"
    return _http_get_json(url)


def main() -> None:
    _ensure_database_url()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    api_key = get_serpapi_key()

    from app.db.session import SessionLocal
    from app.models.restaurant import Restaurant

    with SessionLocal() as db:
        restaurant = (
            db.execute(
                select(Restaurant).where(
                    or_(
                        Restaurant.google_place_id.is_not(None),
                        Restaurant.serpapi_data_id.is_not(None),
                    )
                )
            )
            .scalars()
            .first()
        )
        if restaurant is None:
            restaurant = db.execute(select(Restaurant)).scalars().first()

        if restaurant is None:
            raise SystemExit("No restaurants found in database.")

        name = restaurant.name
        place_id = getattr(restaurant, "google_place_id", None)
        data_id = getattr(restaurant, "serpapi_data_id", None)

        print(f"name: {name}")
        print(f"place_id: {place_id}")
        print(f"data_id: {data_id}")

        details = _fetch_initial_details(
            api_key=api_key,
            place_id=place_id,
            data_id=data_id,
            latitude=restaurant.latitude,
            longitude=restaurant.longitude,
        )

        print("\n--- initial_details JSON ---")
        print(json.dumps(details, ensure_ascii=False, indent=2, sort_keys=True))

        place_results = details.get("place_results")
        if not isinstance(place_results, dict):
            raise SystemExit("SerpAPI details response does not contain place_results.")

        place_id_search = place_results.get("place_id_search")
        reviews_link = place_results.get("reviews_link")
        photos_link = place_results.get("photos_link")

        if not isinstance(place_id_search, str):
            raise SystemExit("place_id_search is missing from SerpAPI response.")
        if not isinstance(reviews_link, str):
            raise SystemExit("reviews_link is missing from SerpAPI response.")
        if not isinstance(photos_link, str):
            raise SystemExit("photos_link is missing from SerpAPI response.")

        for label, url in (
            ("place_id_search", place_id_search),
            ("reviews_link", reviews_link),
            ("photos_link", photos_link),
        ):
            print(f"\n--- {label} JSON ---")
            response = _http_get_json(_with_api_key(url, api_key))
            print(json.dumps(response, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
