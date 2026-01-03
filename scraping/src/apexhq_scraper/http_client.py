"""HTTP client with retries, caching, and rate limiting."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .rate_limit import RateLimiter
from .robots import RobotsCache


@dataclass
class FetchResult:
    url: str
    status_code: int
    headers: dict[str, str]
    text: str
    from_cache: bool = False


class ResponseCache:
    def __init__(self, cache_dir: Path, ttl_seconds: int) -> None:
        self.cache_dir = cache_dir
        self.ttl_seconds = ttl_seconds
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _key_path(self, url: str) -> Path:
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{digest}.json"

    def get(self, url: str) -> FetchResult | None:
        path = self._key_path(url)
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        timestamp = payload.get("timestamp", 0)
        if time.time() - timestamp > self.ttl_seconds:
            return None
        return FetchResult(
            url=payload["url"],
            status_code=payload["status_code"],
            headers=payload.get("headers", {}),
            text=payload.get("text", ""),
            from_cache=True,
        )

    def set(self, result: FetchResult) -> None:
        payload = {
            "url": result.url,
            "status_code": result.status_code,
            "headers": result.headers,
            "text": result.text,
            "timestamp": time.time(),
        }
        path = self._key_path(result.url)
        path.write_text(json.dumps(payload, ensure_ascii=True), encoding="utf-8")


class HttpClient:
    def __init__(
        self,
        rate_limiter: RateLimiter,
        timeout_seconds: float,
        retries: int,
        backoff_seconds: float,
        user_agent: str,
        cache: ResponseCache | None = None,
        max_requests: int | None = None,
        robots_cache: RobotsCache | None = None,
    ) -> None:
        self.rate_limiter = rate_limiter
        self.timeout_seconds = timeout_seconds
        self.user_agent = user_agent
        self.cache = cache
        self.max_requests = max_requests
        self.robots_cache = robots_cache
        self._request_count = 0

        retry_config = Retry(
            total=retries,
            backoff_factor=backoff_seconds,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "HEAD"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_config)
        session = requests.Session()
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        self.session = session

    def get(self, url: str, params: dict[str, Any] | None = None) -> FetchResult:
        if self.cache:
            cached = self.cache.get(url)
            if cached:
                return cached
        if self.max_requests is not None and self._request_count >= self.max_requests:
            raise RuntimeError("Max request limit reached")
        if self.robots_cache and not self.robots_cache.allowed(url):
            raise RuntimeError(f"Blocked by robots.txt: {url}")

        host = urlparse(url).netloc
        self.rate_limiter.wait(host)
        headers = {"User-Agent": self.user_agent}
        response = self.session.get(url, params=params, headers=headers, timeout=self.timeout_seconds)
        result = FetchResult(
            url=response.url,
            status_code=response.status_code,
            headers={k: v for k, v in response.headers.items()},
            text=response.text,
        )
        if self.cache:
            self.cache.set(result)
        self._request_count += 1
        return result
