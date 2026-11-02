"""Minimal SWAPI HTTP client built on the standard library (no third-party deps)."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Iterator

DEFAULT_BASE_URL = "https://swapi.dev/api"


@dataclass(frozen=True)
class Response:
    status: int
    body: Any  # parsed JSON (dict/list) or None


class SwapiClient:
    def __init__(self, base_url: str | None = None, timeout: float = 15.0, retries: int = 2):
        self.base_url = (base_url or os.environ.get("SWAPI_BASE_URL", DEFAULT_BASE_URL)).rstrip("/")
        self.timeout = timeout
        self.retries = retries
        self._cache: dict[str, Response] = {}

    # ---- low level -------------------------------------------------------
    def get(self, path_or_url: str, params: dict[str, Any] | None = None) -> Response:
        url = path_or_url if path_or_url.startswith("http") else f"{self.base_url}/{path_or_url.lstrip('/')}"
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"
        if url in self._cache:
            return self._cache[url]

        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                req = urllib.request.Request(url, headers={"Accept": "application/json"})
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    result = Response(resp.status, json.loads(resp.read().decode("utf-8")))
                    break
            except urllib.error.HTTPError as exc:
                # A real HTTP status (e.g. 404) is an answer, not a transient failure.
                raw = exc.read().decode("utf-8", errors="replace")
                try:
                    body = json.loads(raw) if raw else None
                except json.JSONDecodeError:
                    body = None
                result = Response(exc.code, body)
                break
            except (urllib.error.URLError, TimeoutError) as exc:
                last_error = exc
                time.sleep(0.5 * (attempt + 1))
        else:
            raise ConnectionError(f"GET {url} failed after {self.retries + 1} attempts: {last_error}")

        self._cache[url] = result
        return result

    # ---- starships -------------------------------------------------------
    def starship(self, ship_id: int) -> Response:
        return self.get(f"starships/{ship_id}/")

    def starships_page(self, page: int = 1) -> Response:
        return self.get("starships/", {"page": page})

    def search_starships(self, term: str) -> Response:
        return self.get("starships/", {"search": term})

    def iter_starships(self) -> Iterator[dict[str, Any]]:
        """Yield every starship, following the `next` pagination links."""
        url: str | None = f"{self.base_url}/starships/"
        while url:
            resp = self.get(url)
            if resp.status != 200:
                raise AssertionError(f"Pagination request {url} returned HTTP {resp.status}")
            yield from resp.body["results"]
            url = resp.body["next"]


def parse_number(value: str) -> float | None:
    """Turn SWAPI's string numbers into floats.

    "47,060" -> 47060, "30-165" -> 165 (upper bound), "n/a"/"unknown" -> None.
    """
    if value is None:
        return None
    cleaned = value.replace(",", "").strip().lower()
    if cleaned in {"", "n/a", "unknown", "none"}:
        return None
    if "-" in cleaned:
        cleaned = cleaned.split("-")[-1]
    try:
        return float(cleaned)
    except ValueError:
        return None


# One shared client per process so all test modules reuse the response cache.
client = SwapiClient()
