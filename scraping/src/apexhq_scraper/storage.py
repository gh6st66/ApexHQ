"""Storage sinks for scraped data."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .models import RawRecord


class StorageSink:
    def write_raw(self, records: Iterable[RawRecord]) -> None:
        raise NotImplementedError

    def write_metrics(self, metrics: dict[str, int | float | str]) -> None:
        raise NotImplementedError


@dataclass
class JsonlSink(StorageSink):
    output_dir: Path

    def __post_init__(self) -> None:
        self.raw_dir = self.output_dir / "raw"
        self.metrics_dir = self.output_dir / "metrics"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)

    def write_raw(self, records: Iterable[RawRecord]) -> None:
        verified: list[RawRecord] = []
        unverified: list[RawRecord] = []
        for record in records:
            (verified if record.verified else unverified).append(record)

        if verified:
            path = self.raw_dir / "raw_verified.jsonl"
            with path.open("a", encoding="utf-8") as handle:
                for item in verified:
                    handle.write(json.dumps(item.model_dump(), ensure_ascii=True) + "\n")

        if unverified:
            path = self.raw_dir / "raw_unverified.jsonl"
            with path.open("a", encoding="utf-8") as handle:
                for item in unverified:
                    handle.write(json.dumps(item.model_dump(), ensure_ascii=True) + "\n")

    def write_metrics(self, metrics: dict[str, int | float | str]) -> None:
        path = self.metrics_dir / "runs.jsonl"
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(metrics, ensure_ascii=True) + "\n")


class NullSink(StorageSink):
    def write_raw(self, records: Iterable[RawRecord]) -> None:
        return None

    def write_metrics(self, metrics: dict[str, int | float | str]) -> None:
        return None
