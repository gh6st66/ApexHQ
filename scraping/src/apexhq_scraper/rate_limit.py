"""Simple per-host rate limiter."""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class RateLimiter:
    rate_per_minute: int
    _next_allowed: dict[str, float] = field(default_factory=dict)

    def wait(self, host: str) -> None:
        if self.rate_per_minute <= 0:
            return
        min_interval = 60.0 / float(self.rate_per_minute)
        now = time.monotonic()
        next_time = self._next_allowed.get(host, now)
        if next_time > now:
            time.sleep(next_time - now)
            now = time.monotonic()
        self._next_allowed[host] = now + min_interval
