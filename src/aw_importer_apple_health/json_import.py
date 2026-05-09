from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from dateutil import parser as date_parser

TYPE_ALIASES = {
    "steps": ("daily", "steps"),
    "step_count": ("daily", "steps"),
    "heart-rate": ("vitals", "heart_rate"),
    "heart_rate": ("vitals", "heart_rate"),
    "resting-heart-rate": ("daily", "resting_heart_rate"),
    "resting_heart_rate": ("daily", "resting_heart_rate"),
    "hrv": ("daily", "hrv_sdnn"),
    "hrv_sdnn": ("daily", "hrv_sdnn"),
    "sleep": ("sleep", "sleep_analysis"),
    "workout": ("workout", "workout"),
    "workouts": ("workout", "workout"),
    "active_energy": ("daily", "active_energy"),
    "body_mass": ("daily", "body_mass"),
    "weight": ("daily", "body_mass"),
    "toothbrushing": ("habits", "toothbrushing"),
    "blood_glucose": ("vitals", "blood_glucose"),
    "glucose": ("vitals", "blood_glucose"),
    "blood_oxygen": ("vitals", "blood_oxygen"),
    "oxygen_saturation": ("vitals", "blood_oxygen"),
    "respiratory_rate": ("vitals", "respiratory_rate"),
    "vo2max": ("daily", "vo2max"),
    "caffeine": ("nutrition", "caffeine"),
    "water": ("nutrition", "water"),
    "protein": ("nutrition", "protein"),
    "carbohydrates": ("nutrition", "carbohydrates"),
    "fat_total": ("nutrition", "fat_total"),
}


def _parse_time(value: Any) -> str | None:
    if not value:
        return None
    try:
        return date_parser.parse(str(value)).isoformat()
    except Exception:
        return None


def _first_present(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _load_payload(path: Path) -> Any:
    data = json.loads(path.read_text())
    if isinstance(data, dict):
        for key in ("records", "data", "samples", "items"):
            if isinstance(data.get(key), list):
                return data[key]
        return [data]
    return data


def _normalize_one(item: dict[str, Any], fallback_type: str | None = None) -> dict[str, Any] | None:
    raw_type = str(item.get("type") or item.get("metric") or item.get("name") or fallback_type or "").strip()
    key = raw_type.replace("HKQuantityTypeIdentifier", "").replace("HKCategoryTypeIdentifier", "")
    key = key.replace("StepCount", "steps").replace("HeartRateVariabilitySDNN", "hrv_sdnn").replace("HeartRate", "heart_rate")
    key = key.replace("SleepAnalysis", "sleep").replace("BodyMass", "body_mass")
    norm_key = key.lower().replace(" ", "_").replace("-", "_")
    category, short = TYPE_ALIASES.get(norm_key, TYPE_ALIASES.get(raw_type.lower().replace(" ", "_"), ("daily", norm_key or "unknown")))
    start = _parse_time(item.get("start") or item.get("startDate") or item.get("start_time") or item.get("date"))
    end = _parse_time(item.get("end") or item.get("endDate") or item.get("end_time") or start)
    if not start:
        return None
    record = {
        "type": short,
        "category": category,
        "source": item.get("source") or item.get("sourceName") or item.get("device"),
        "unit": item.get("unit"),
        "value": _first_present(item.get("value"), item.get("quantity"), item.get("duration")),
        "start": start,
        "end": end,
    }
    return {k: v for k, v in record.items() if v not in (None, "")}


def parse_json_records(path: Path, fallback_type: str | None = None) -> list[dict[str, Any]]:
    payload = _load_payload(path)
    if not isinstance(payload, list):
        raise ValueError("Expected JSON object/list with health records")
    records: list[dict[str, Any]] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        normalized = _normalize_one(item, fallback_type=fallback_type)
        if normalized:
            records.append(normalized)
    return records
