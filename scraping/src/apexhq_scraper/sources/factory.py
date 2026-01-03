"""Source factory."""

from __future__ import annotations

from ..config import SourceConfig
from .base import HttpHtmlSource, HttpJsonSource, Source


def build_source(config: SourceConfig) -> Source:
    source_type = config.type.lower().strip()
    if source_type == "http_json":
        return HttpJsonSource(config)
    if source_type == "http_html":
        return HttpHtmlSource(config)
    raise ValueError(f"Unsupported source type: {config.type}")
