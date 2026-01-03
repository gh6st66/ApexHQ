"""Command-line interface for the scraper."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Iterable

from .config import Settings, load_settings, load_sources
from .pipeline import run_pipeline

logger = logging.getLogger("apexhq_scraper.cli")


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _apply_overrides(settings: Settings, args: argparse.Namespace) -> Settings:
    if args.output_dir:
        return Settings(
            sources_file=settings.sources_file,
            output_dir=Path(args.output_dir),
            cache_dir=settings.cache_dir,
            cache_ttl_seconds=settings.cache_ttl_seconds,
            database_url=settings.database_url,
            http_timeout_seconds=settings.http_timeout_seconds,
            http_retries=settings.http_retries,
            http_backoff_seconds=settings.http_backoff_seconds,
            rate_limit_per_minute=settings.rate_limit_per_minute,
            user_agent=settings.user_agent,
            respect_robots=settings.respect_robots,
            log_json=settings.log_json,
            max_requests=settings.max_requests,
        )
    return settings


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run ApexHQ scraping pipeline")
    parser.add_argument("--sources", help="Comma-separated source names")
    parser.add_argument("--include-disabled", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output-dir", help="Override output directory")
    parser.add_argument("--list-sources", action="store_true")
    parser.add_argument(
        "--allow-unverified", action="store_true", help="Include nonreputable sources"
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    settings = _apply_overrides(load_settings(), args)
    sources = load_sources(
        settings.sources_file,
        only=_split_csv(args.sources),
        include_disabled=args.include_disabled,
    )

    if not args.allow_unverified:
        sources = [s for s in sources if s.is_reputable]

    if args.list_sources:
        for source in sources:
            print(source.name)
        return 0

    if not sources:
        print("No sources enabled. Update config/sources.json or use --include-disabled.")
        return 1

    return run_pipeline(settings, sources, dry_run=args.dry_run)
