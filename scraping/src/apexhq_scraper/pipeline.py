"""Scraping pipeline orchestrator."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .config import Settings, SourceConfig
from .http_client import HttpClient, ResponseCache
from .logging_utils import configure_logging
from .rate_limit import RateLimiter
from .robots import RobotsCache
from .sources import build_source
from .storage import JsonlSink, NullSink, StorageSink

logger = logging.getLogger("apexhq_scraper.pipeline")


def build_sink(output_dir: Path, dry_run: bool) -> StorageSink:
    if dry_run:
        return NullSink()
    return JsonlSink(output_dir=output_dir)


def run_pipeline(
    settings: Settings,
    sources: Iterable[SourceConfig],
    dry_run: bool = False,
) -> int:
    configure_logging(json_output=settings.log_json)
    logger.info("starting scrape run")

    source_list = list(sources)
    cache = None
    if settings.cache_dir:
        cache = ResponseCache(settings.cache_dir, settings.cache_ttl_seconds)

    robots_cache = None
    if settings.respect_robots:
        robots_cache = RobotsCache(settings.user_agent, settings.http_timeout_seconds)

    client = HttpClient(
        rate_limiter=RateLimiter(settings.rate_limit_per_minute),
        timeout_seconds=settings.http_timeout_seconds,
        retries=settings.http_retries,
        backoff_seconds=settings.http_backoff_seconds,
        user_agent=settings.user_agent,
        cache=cache,
        max_requests=settings.max_requests,
        robots_cache=robots_cache,
    )
    sink = build_sink(settings.output_dir, dry_run)

    total_records = 0
    total_verified = 0
    total_errors = 0
    for config in source_list:
        source = build_source(config)
        logger.info("running source %s", source.name)
        result = source.run(client)
        if result.records:
            sink.write_raw(result.records)
        if result.errors:
            for error in result.errors:
                logger.error("source error: %s", error)
        total_records += len(result.records)
        total_verified += sum(1 for r in result.records if r.verified)
        total_errors += len(result.errors)

    metrics = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "sources": len(source_list),
        "records": total_records,
        "verified_records": total_verified,
        "errors": total_errors,
        "dry_run": dry_run,
    }
    sink.write_metrics(metrics)
    logger.info("completed scrape run", extra=metrics)

    return 1 if total_errors else 0
