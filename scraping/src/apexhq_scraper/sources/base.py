"""Source base classes."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin

from ..config import SourceConfig, SourceEndpoint
from ..http_client import FetchResult, HttpClient
from ..models import RawRecord


@dataclass
class SourceResult:
    source: str
    records: list[RawRecord]
    errors: list[str]


class Source:
    def __init__(self, config: SourceConfig) -> None:
        self.config = config

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def is_reputable(self) -> bool:
        return self.config.is_reputable

    def run(self, client: HttpClient) -> SourceResult:
        records: list[RawRecord] = []
        errors: list[str] = []
        for endpoint in self.config.endpoints:
            try:
                result = self.fetch_endpoint(client, endpoint)
                records.extend(self.parse(result, endpoint))
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{self.name}:{endpoint.path}:{exc}")
        return SourceResult(source=self.name, records=records, errors=errors)

    def fetch_endpoint(self, client: HttpClient, endpoint: SourceEndpoint) -> FetchResult:
        url = urljoin(self.config.base_url.rstrip("/") + "/", endpoint.path.lstrip("/"))
        return client.get(url, params=endpoint.params)

    def parse(self, result: FetchResult, endpoint: SourceEndpoint) -> list[RawRecord]:
        raise NotImplementedError


class HttpJsonSource(Source):
    def parse(self, result: FetchResult, endpoint: SourceEndpoint) -> list[RawRecord]:
        payload = json.loads(result.text)
        return [
            RawRecord(
                source=self.name,
                source_url=result.url,
                reputation="reputable" if self.is_reputable else "nonreputable",
                verified=self.is_reputable,
                fetched_at=datetime.now(timezone.utc),
                endpoint=endpoint.path,
                payload=payload,
            )
        ]


class HttpHtmlSource(Source):
    def parse(self, result: FetchResult, endpoint: SourceEndpoint) -> list[RawRecord]:
        payload: dict[str, Any] = {"html": result.text}
        return [
            RawRecord(
                source=self.name,
                source_url=result.url,
                reputation="reputable" if self.is_reputable else "nonreputable",
                verified=self.is_reputable,
                fetched_at=datetime.now(timezone.utc),
                endpoint=endpoint.path,
                payload=payload,
            )
        ]
