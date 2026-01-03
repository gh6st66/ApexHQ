"""Data models for scraped content."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RawRecord(BaseModel):
    source: str
    source_url: str
    reputation: str = Field(description="reputable or nonreputable")
    verified: bool = False
    fetched_at: datetime
    endpoint: str | None = None
    payload: Any


class LegendPickRate(BaseModel):
    legend: str
    pick_rate: float = Field(ge=0.0, le=1.0)
    window: str
    region: str | None = None


class MapLegendPriority(BaseModel):
    map_name: str
    legend: str
    tier: str
    rationale: str | None = None
