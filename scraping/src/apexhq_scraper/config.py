"""Configuration and source loading."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from pydantic import BaseModel, Field


class SourceEndpoint(BaseModel):
    path: str
    method: str = "GET"
    params: dict[str, Any] = Field(default_factory=dict)


class SourceConfig(BaseModel):
    name: str
    type: str
    base_url: str
    enabled: bool = False
    reputation: str = Field(
        default="reputable", description="reputable or nonreputable lead source"
    )
    endpoints: list[SourceEndpoint] = Field(default_factory=list)

    @property
    def is_reputable(self) -> bool:
        return self.reputation.lower().strip() == "reputable"


class SourcesFile(BaseModel):
    sources: list[SourceConfig]


@dataclass(frozen=True)
class Settings:
    sources_file: Path
    output_dir: Path
    cache_dir: Path | None
    cache_ttl_seconds: int
    database_url: str | None
    http_timeout_seconds: float
    http_retries: int
    http_backoff_seconds: float
    rate_limit_per_minute: int
    user_agent: str
    respect_robots: bool
    log_json: bool
    max_requests: int | None


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _env_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_settings() -> Settings:
    root = project_root()
    sources_file = Path(
        os.getenv("APEXHQ_SOURCES_FILE", root / "config" / "sources.json")
    )
    output_dir = Path(os.getenv("APEXHQ_OUTPUT_DIR", root / "output"))
    cache_dir_value = os.getenv("APEXHQ_CACHE_DIR")
    cache_dir = Path(cache_dir_value) if cache_dir_value else None
    return Settings(
        sources_file=sources_file,
        output_dir=output_dir,
        cache_dir=cache_dir,
        cache_ttl_seconds=int(os.getenv("APEXHQ_CACHE_TTL", "3600")),
        database_url=os.getenv("APEXHQ_DATABASE_URL"),
        http_timeout_seconds=float(os.getenv("APEXHQ_HTTP_TIMEOUT", "20")),
        http_retries=int(os.getenv("APEXHQ_HTTP_RETRIES", "3")),
        http_backoff_seconds=float(os.getenv("APEXHQ_HTTP_BACKOFF", "1")),
        rate_limit_per_minute=int(os.getenv("APEXHQ_RATE_LIMIT", "60")),
        user_agent=os.getenv(
            "APEXHQ_USER_AGENT", "ApexHQScraper/0.1 (+https://github.com/gh6st66/ApexHQ)"
        ),
        respect_robots=_env_bool(os.getenv("APEXHQ_RESPECT_ROBOTS"), True),
        log_json=_env_bool(os.getenv("APEXHQ_LOG_JSON"), False),
        max_requests=_env_int_optional(os.getenv("APEXHQ_MAX_REQUESTS")),
    )


def _env_int_optional(value: str | None) -> int | None:
    if value is None or not value.strip():
        return None
    return int(value)


def load_sources(
    sources_file: Path, only: Iterable[str] | None = None, include_disabled: bool = False
) -> list[SourceConfig]:
    data = json.loads(sources_file.read_text(encoding="utf-8"))
    sources = SourcesFile.model_validate(data).sources
    if only:
        names = {name.strip() for name in only if name.strip()}
        sources = [source for source in sources if source.name in names]
    if not include_disabled:
        sources = [source for source in sources if source.enabled]
    return sources
