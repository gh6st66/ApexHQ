"""Source adapters."""

from .base import HttpHtmlSource, HttpJsonSource, Source
from .factory import build_source

__all__ = ["Source", "HttpJsonSource", "HttpHtmlSource", "build_source"]
