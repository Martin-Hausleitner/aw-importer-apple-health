from __future__ import annotations

import gzip
import zipfile
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Iterable
from xml.etree import ElementTree as ET

TYPE_MAP = {
    "HKQuantityTypeIdentifierStepCount": ("daily", "steps"),
    "HKQuantityTypeIdentifierActiveEnergyBurned": ("daily", "active_energy"),
    "HKQuantityTypeIdentifierHeartRate": ("vitals", "heart_rate"),
    "HKQuantityTypeIdentifierRestingHeartRate": ("daily", "resting_heart_rate"),
    "HKQuantityTypeIdentifierHeartRateVariabilitySDNN": ("daily", "hrv_sdnn"),
    "HKQuantityTypeIdentifierBodyMass": ("daily", "body_mass"),
    "HKQuantityTypeIdentifierAppleExerciseTime": ("daily", "exercise_time"),
    "HKCategoryTypeIdentifierMindfulSession": ("mindfulness", "mindful_session"),
    "HKCategoryTypeIdentifierSleepAnalysis": ("sleep", "sleep_analysis"),
    "HKQuantityTypeIdentifierToothbrushingEvent": ("habits", "toothbrushing"),
}

DEFAULT_TYPES = tuple(TYPE_MAP)


@dataclass
class ParseStats:
    parsed: int = 0
    skipped: int = 0


def _export_xml_path(path: Path) -> tuple[Path, TemporaryDirectory | None]:
    if path.suffix.lower() == ".xml":
        return path, None
    tmp = TemporaryDirectory()
    outdir = Path(tmp.name)
    if path.suffix.lower() == ".gz":
        out = outdir / "export.xml"
        with gzip.open(path, "rb") as src, out.open("wb") as dst:
            dst.write(src.read())
        return out, tmp
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as zf:
            candidates = [n for n in zf.namelist() if n.endswith("export.xml")]
            if not candidates:
                raise ValueError("Apple Health ZIP does not contain export.xml")
            zf.extract(candidates[0], outdir)
            return outdir / candidates[0], tmp
    raise ValueError("Expected Apple Health export.xml, .xml.gz, or export ZIP")


def _value(attrs: dict[str, str]) -> float | str | None:
    raw = attrs.get("value")
    if raw is None:
        return None
    try:
        return float(raw)
    except ValueError:
        return raw


def parse_records(path: Path, include_types: Iterable[str] = DEFAULT_TYPES) -> tuple[list[dict[str, Any]], ParseStats]:
    xml_path, tmp = _export_xml_path(path)
    include = set(include_types)
    records: list[dict[str, Any]] = []
    stats = ParseStats()
    try:
        for _, elem in ET.iterparse(xml_path, events=("end",)):
            if elem.tag not in {"Record", "Workout"}:
                elem.clear()
                continue
            attrs = dict(elem.attrib)
            health_type = attrs.get("type") if elem.tag == "Record" else "Workout"
            if health_type not in include and elem.tag != "Workout":
                stats.skipped += 1
                elem.clear()
                continue
            if elem.tag == "Workout":
                category, short_type = "workout", attrs.get("workoutActivityType", "workout")
            else:
                category, short_type = TYPE_MAP[health_type]
            record = {
                "type": short_type,
                "category": category,
                "source": attrs.get("sourceName"),
                "unit": attrs.get("unit"),
                "value": _value(attrs),
                "start": attrs.get("startDate") or attrs.get("creationDate"),
                "end": attrs.get("endDate") or attrs.get("startDate") or attrs.get("creationDate"),
            }
            records.append({k: v for k, v in record.items() if v not in (None, "")})
            stats.parsed += 1
            elem.clear()
    finally:
        if tmp:
            tmp.cleanup()
    return records, stats
