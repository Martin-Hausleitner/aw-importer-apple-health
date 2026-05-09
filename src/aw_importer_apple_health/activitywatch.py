from __future__ import annotations

import hashlib
import json
import socket
from datetime import datetime
from typing import Any

import httpx

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
    a = datetime.fromisoformat(str(start).replace("Z", "+00:00"))
    b = datetime.fromisoformat(str(end).replace("Z", "+00:00"))
    return str(start), max(0.0, (b - a).total_seconds())


class ActivityWatchClient:
    def __init__(self, base_url: str = AW_BASE_URL, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def hostname(self) -> str:
        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                r = client.get(f"{self.base_url}/info")
                if r.status_code == 200 and r.json().get("hostname"):
                    return str(r.json()["hostname"])
        except Exception:
            pass
        return socket.gethostname()

    def ensure_bucket(self, bucket_id: str, event_type: str) -> None:
        payload = {"client": "aw-importer-apple-health", "type": event_type, "hostname": self.hostname()}
        with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
            r = client.post(f"{self.base_url}/buckets/{bucket_id}", json=payload)
            if r.status_code not in (200, 201, 304):
                r.raise_for_status()

    def insert_record(self, category: str, record: dict[str, Any]) -> int:
        bucket_id = f"{BUCKET_PREFIX}-{category}"
        self.ensure_bucket(bucket_id, f"apple_health.{category}")
        timestamp, duration = record_times(record)
        event = {"timestamp": timestamp, "duration": duration, "data": {"apple_health_id": record_id(record), "record": record}}
        with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
            r = client.post(f"{self.base_url}/buckets/{bucket_id}/events", json=event)
            r.raise_for_status()
            return int(r.json()) if r.json() is not None else -1
