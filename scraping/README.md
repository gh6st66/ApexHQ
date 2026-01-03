# ApexHQ Scraping

Data collection and ingestion service for ApexHQ. This service is designed to
be resilient, observable, and config-driven so sources can be added without
rewriting the pipeline.

This setup targets ARC Raiders data collection with strict rules:
- Do not infer or fabricate data; only record what is explicitly present.
- Every record must include the source URL.
- Non-reputable sources are treated as leads; data is UNVERIFIED until
  confirmed by reputable sources.
- If data cannot be confirmed, leave it empty.

## Architecture

- Config-driven sources (`config/sources.json`)
- Per-host rate limiting and retry/backoff
- Optional response caching
- JSONL raw output for replayable processing
- Structured logging and run metrics
- Verified vs UNVERIFIED records are separated in output.

## Quickstart

```bash
cd scraping
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env

# List sources (disabled by default)
python -m apexhq_scraper --list-sources --include-disabled
```

Enable specific sources by setting `enabled: true` in `config/sources.json` or
use `--include-disabled` for local testing.

## Configuration

Environment variables:

- `APEXHQ_SOURCES_FILE`: path to sources config (default `config/sources.json`)
- `APEXHQ_OUTPUT_DIR`: output directory for JSONL files
- `APEXHQ_CACHE_DIR`: enable on-disk cache for responses
- `APEXHQ_CACHE_TTL`: cache TTL in seconds (default 3600)
- `APEXHQ_HTTP_TIMEOUT`: request timeout in seconds (default 20)
- `APEXHQ_HTTP_RETRIES`: retry count (default 3)
- `APEXHQ_HTTP_BACKOFF`: retry backoff factor (default 1)
- `APEXHQ_RATE_LIMIT`: requests per minute per host (default 60)
- `APEXHQ_USER_AGENT`: override default user agent
- `APEXHQ_LOG_JSON`: set to true for JSON logs
- `APEXHQ_MAX_REQUESTS`: hard cap for requests per run
- `APEXHQ_RESPECT_ROBOTS`: enforce robots.txt (default true)

## Output

Raw data is written to `output/raw/*.jsonl` and run metrics to
`output/metrics/runs.jsonl` (unless `--dry-run` is used).

Files:
- `raw_verified.jsonl`: records from reputable sources
- `raw_unverified.jsonl`: records from nonreputable/lead sources

## Next steps

- Replace placeholder endpoints in `config/sources.json` with concrete ARC
  Raiders URLs.
- Implement parsers per source that emit structured payloads with `source_url`
  and `verified` flags.
- Add a Postgres sink for direct ingestion into the main database.
- Add cross-source validation to promote UNVERIFIED records when corroborated
  by reputable sources.
