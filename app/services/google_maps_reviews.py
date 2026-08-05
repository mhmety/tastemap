import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

SERPAPI_ENDPOINT = "https://serpapi.com/search.json"

PROJECT_ROOT = Path(__file__).resolve().parents[2]

logger = logging.getLogger(__name__)


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
        raise RuntimeError("SERPAPI_KEY not found. Set SERPAPI_KEY in your environment or in .env.")
    return key


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


def _extract_reviews(response: dict[str, Any]) -> list[dict[str, Any]]:
    raw = response.get("reviews")
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    return []


def _http_get_json(url: str, params: dict[str, Any], *, timeout: int) -> dict[str, Any]:
    query = urlencode(params)
    request = Request(
        f"{url}?{query}",
        headers={"Accept": "application/json"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = response.read().decode("utf-8")
            return json.loads(payload)
    except HTTPError as exc:
        body = None
        try:
            body = exc.read().decode("utf-8")
        except Exception:
            body = None
        raise RuntimeError(
            f"SerpAPI request failed: HTTP {exc.code} {exc.reason}{f' - {body}' if body else ''}"
        ) from exc
    except (URLError, TimeoutError) as exc:
        raise RuntimeError(f"SerpAPI request failed: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError("SerpAPI response is not valid JSON") from exc


def _extract_params_from_reviews_link(reviews_link: str) -> dict[str, str]:
    parsed = urlparse(reviews_link)
    query_params = parse_qs(parsed.query)

    picked: dict[str, str] = {}
    for key in ("data_id", "place_id", "hl", "sort_by", "topic_id", "query"):
        values = query_params.get(key)
        if not values:
            continue
        value = values[0]
        if isinstance(value, str) and value.strip():
            picked[key] = value.strip()
    return picked


class GoogleMapsReviewsService:
    def __init__(
        self,
        *,
        api_key: str,
        timeout: int = 30,
        max_retries: int = 3,
        retry_backoff_seconds: float = 1.0,
    ) -> None:
        self._api_key = api_key
        self._timeout = timeout
        self._max_retries = max(1, max_retries)
        self._retry_backoff_seconds = max(0.0, retry_backoff_seconds)

    def iter_review_pages(
        self,
        *,
        data_id: str | None = None,
        place_id: str | None = None,
        reviews_link: str | None = None,
        max_pages: int = 10,
        hl: str | None = None,
    ) -> list[list[dict[str, Any]]]:
        base_params: dict[str, Any] = {
            "engine": "google_maps_reviews",
            "api_key": self._api_key,
        }

        if reviews_link:
            extracted = _extract_params_from_reviews_link(reviews_link)
            if not data_id:
                data_id = extracted.get("data_id")
            if not place_id:
                place_id = extracted.get("place_id")
            if not hl:
                hl = extracted.get("hl")
            for key in ("sort_by", "topic_id", "query"):
                if key in extracted:
                    base_params[key] = extracted[key]

        if hl:
            base_params["hl"] = hl

        if data_id:
            base_params["data_id"] = data_id
        elif place_id:
            base_params["place_id"] = place_id
        else:
            raise ValueError("Either data_id, place_id, or reviews_link with those parameters must be provided.")

        pages: list[list[dict[str, Any]]] = []
        next_token: Optional[str] = None

        for page_index in range(max(1, max_pages)):
            params = dict(base_params)
            if next_token:
                params["next_page_token"] = next_token

            response = self._request_with_retries(params)
            page_reviews = _extract_reviews(response)
            pages.append(page_reviews)

            next_token = _next_page_token(response)
            if not next_token:
                break

        return pages

    def fetch_all_reviews(
        self,
        *,
        data_id: str | None = None,
        place_id: str | None = None,
        reviews_link: str | None = None,
        max_pages: int = 10,
        hl: str | None = None,
    ) -> list[dict[str, Any]]:
        pages = self.iter_review_pages(
            data_id=data_id,
            place_id=place_id,
            reviews_link=reviews_link,
            max_pages=max_pages,
            hl=hl,
        )
        flattened: list[dict[str, Any]] = []
        for page in pages:
            flattened.extend(page)
        return flattened

    def _request_with_retries(self, params: dict[str, Any]) -> dict[str, Any]:
        last_exc: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                return _http_get_json(SERPAPI_ENDPOINT, params, timeout=self._timeout)
            except Exception as exc:
                last_exc = exc
                wait_seconds = self._retry_backoff_seconds * (2**attempt)
                if attempt + 1 < self._max_retries and wait_seconds > 0:
                    time.sleep(wait_seconds)

        assert last_exc is not None
        raise last_exc
