from __future__ import annotations

import hashlib
import json
import socket
from typing import Any

import httpx
from dateutil import parser as date_parser

AW_BASE_URL = "http://127.0.0.1:5600/api/0"
BUCKET_PREFIX = "aw-importer-apple-health"


def stable_hash(record: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(record, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def record_id(record: dict[str, Any]) -> str:
    raw = "|".join(str(record.get(k, "")) for k in ("type", "start", "end", "value", "unit"))
    return hashlib.sha256(raw.encode()).hexdigest()[:24]


def record_times(record: dict[str, Any]) -> tuple[str, float]:
    start = record["start"]
    end = record.get("end") or start
    a = date_parser.parse(str(start))
    b = date_parser.parse(str(end))
    return str(start), max(0.0, (b - a).total_seconds())


class ActivityWatchClient:
    def __init__(self, base_url: str = AW_BASE_URL, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._hostname: str | None = None
        self._ensured_buckets: set[str] = set()

    def hostname(self) -> str:
        if self._hostname:
            return self._hostname
        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                r = client.get(f"{self.base_url}/info")
                if r.status_code == 200 and r.json().get("hostname"):
                    self._hostname = str(r.json()["hostname"])
                    return self._hostname
        except Exception:
            pass
        return socket.gethostname()

    def ensure_bucket(self, bucket_id: str, event_type: str) -> None:
        if bucket_id in self._ensured_buckets:
            return
        payload = {"client": "aw-importer-apple-health", "type": event_type, "hostname": self.hostname()}
        with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
            r = client.post(f"{self.base_url}/buckets/{bucket_id}", json=payload)
            if r.status_code not in (200, 201, 304):
                r.raise_for_status()
        self._ensured_buckets.add(bucket_id)

    def insert_record(self, category: str, record: dict[str, Any]) -> int:
        bucket_id = f"{BUCKET_PREFIX}-{category}"
        self.ensure_bucket(bucket_id, f"apple_health.{category}")
        timestamp, duration = record_times(record)
        event = {"timestamp": timestamp, "duration": duration, "data": {"apple_health_id": record_id(record), "record": record}}
        with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
            r = client.post(f"{self.base_url}/buckets/{bucket_id}/events", json=event)
            r.raise_for_status()
            return int(r.json()) if r.json() is not None else -1
