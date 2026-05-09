from __future__ import annotations

import gzip
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Iterable
from xml.etree import ElementTree as ET

TYPE_MAP = {
    # Activity / movement
    "HKQuantityTypeIdentifierStepCount": ("daily", "steps"),
    "HKQuantityTypeIdentifierDistanceWalkingRunning": ("daily", "walking_running_distance"),
    "HKQuantityTypeIdentifierDistanceCycling": ("daily", "cycling_distance"),
    "HKQuantityTypeIdentifierDistanceSwimming": ("daily", "swimming_distance"),
    "HKQuantityTypeIdentifierFlightsClimbed": ("daily", "flights_climbed"),
    "HKQuantityTypeIdentifierAppleExerciseTime": ("daily", "exercise_time"),
    "HKQuantityTypeIdentifierAppleStandTime": ("daily", "stand_time"),
    "HKQuantityTypeIdentifierActiveEnergyBurned": ("daily", "active_energy"),
    "HKQuantityTypeIdentifierBasalEnergyBurned": ("daily", "basal_energy"),
    "HKQuantityTypeIdentifierVO2Max": ("daily", "vo2max"),

    # Heart / vitals
    "HKQuantityTypeIdentifierHeartRate": ("vitals", "heart_rate"),
    "HKQuantityTypeIdentifierRestingHeartRate": ("daily", "resting_heart_rate"),
    "HKQuantityTypeIdentifierWalkingHeartRateAverage": ("daily", "walking_heart_rate_average"),
    "HKQuantityTypeIdentifierHeartRateVariabilitySDNN": ("daily", "hrv_sdnn"),
    "HKQuantityTypeIdentifierRespiratoryRate": ("vitals", "respiratory_rate"),
    "HKQuantityTypeIdentifierOxygenSaturation": ("vitals", "blood_oxygen"),
    "HKQuantityTypeIdentifierBodyTemperature": ("vitals", "body_temperature"),
    "HKQuantityTypeIdentifierBloodPressureSystolic": ("vitals", "blood_pressure_systolic"),
    "HKQuantityTypeIdentifierBloodPressureDiastolic": ("vitals", "blood_pressure_diastolic"),
    "HKQuantityTypeIdentifierBloodGlucose": ("vitals", "blood_glucose"),

    # Body metrics
    "HKQuantityTypeIdentifierBodyMass": ("daily", "body_mass"),
    "HKQuantityTypeIdentifierBodyMassIndex": ("daily", "bmi"),
    "HKQuantityTypeIdentifierBodyFatPercentage": ("daily", "body_fat_percentage"),
    "HKQuantityTypeIdentifierLeanBodyMass": ("daily", "lean_body_mass"),
    "HKQuantityTypeIdentifierHeight": ("daily", "height"),
    "HKQuantityTypeIdentifierWaistCircumference": ("daily", "waist_circumference"),

    # Nutrition / hydration, if present in HealthKit
    "HKQuantityTypeIdentifierDietaryEnergyConsumed": ("nutrition", "dietary_energy"),
    "HKQuantityTypeIdentifierDietaryProtein": ("nutrition", "protein"),
    "HKQuantityTypeIdentifierDietaryCarbohydrates": ("nutrition", "carbohydrates"),
    "HKQuantityTypeIdentifierDietaryFatTotal": ("nutrition", "fat_total"),
    "HKQuantityTypeIdentifierDietarySugar": ("nutrition", "sugar"),
    "HKQuantityTypeIdentifierDietaryFiber": ("nutrition", "fiber"),
    "HKQuantityTypeIdentifierDietaryWater": ("nutrition", "water"),
    "HKQuantityTypeIdentifierDietaryCaffeine": ("nutrition", "caffeine"),

    # Sessions / categories
    "HKCategoryTypeIdentifierMindfulSession": ("mindfulness", "mindful_session"),
    "HKCategoryTypeIdentifierSleepAnalysis": ("sleep", "sleep_analysis"),
    "HKCategoryTypeIdentifierToothbrushingEvent": ("habits", "toothbrushing"),
    "HKCategoryTypeIdentifierHandwashingEvent": ("habits", "handwashing"),
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
            out = outdir / "export.xml"
            with zf.open(candidates[0]) as src, out.open("wb") as dst:
                shutil.copyfileobj(src, dst)
            return out, tmp
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
    include = {"Workout" if t.lower() in {"workout", "workouts"} else t for t in include_types}
    records: list[dict[str, Any]] = []
    stats = ParseStats()
    try:
        for _, elem in ET.iterparse(xml_path, events=("end",)):
            if elem.tag not in {"Record", "Workout"}:
                elem.clear()
                continue
            attrs = dict(elem.attrib)
            health_type = attrs.get("type") if elem.tag == "Record" else "Workout"
            if elem.tag == "Workout" and "Workout" not in include:
                stats.skipped += 1
                elem.clear()
                continue
            if elem.tag != "Workout" and health_type not in TYPE_MAP:
                stats.skipped += 1
                elem.clear()
                continue
            if elem.tag != "Workout" and health_type not in include:
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
