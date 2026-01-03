"""Robots.txt policy handling."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests

logger = logging.getLogger("apexhq_scraper.robots")


@dataclass
class RobotsCache:
    user_agent: str
    timeout_seconds: float
    _cache: dict[str, RobotFileParser] = field(default_factory=dict)

    def allowed(self, url: str) -> bool:
        parsed = urlparse(url)
        host = parsed.netloc
        if not host:
            return True
        parser = self._cache.get(host)
        if not parser:
            parser = self._fetch_robots(parsed.scheme or "https", host)
            self._cache[host] = parser
        return parser.can_fetch(self.user_agent, url)

    def _fetch_robots(self, scheme: str, host: str) -> RobotFileParser:
        robots_url = urljoin(f"{scheme}://{host}", "/robots.txt")
        parser = RobotFileParser()
        try:
            response = requests.get(robots_url, timeout=self.timeout_seconds)
            if response.status_code >= 400:
                logger.warning("robots.txt fetch failed for %s", host)
                parser.parse([])
            else:
                parser.parse(response.text.splitlines())
        except requests.RequestException:
            logger.warning("robots.txt fetch error for %s", host)
            parser.parse([])
        return parser
