import json
import os
import sys
from pathlib import Path
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[3]

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


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    api_key = get_serpapi_key()
    city = "Ankara"
    query = f"restaurants in {city}"

    response = _http_get_json(
        SERPAPI_ENDPOINT,
        {
            "engine": "google_maps",
            "q": query,
            "api_key": api_key,
        },
    )

    local_results = response.get("local_results")
    if not isinstance(local_results, list) or not local_results:
        raise SystemExit("SerpAPI response has no local_results.")

    first_restaurant = local_results[0]
    if not isinstance(first_restaurant, dict):
        raise SystemExit("First local_results item is not a JSON object.")

    print(json.dumps(first_restaurant, indent=2, ensure_ascii=False, sort_keys=False))
    print("\nAvailable keys:")
    for key in sorted(first_restaurant.keys()):
        print(key)


if __name__ == "__main__":
    main()

