from pathlib import Path

from aw_importer_apple_health.json_import import parse_json_records
from aw_importer_apple_health.parser import parse_records


def test_parse_selected_health_records(tmp_path: Path) -> None:
    xml = tmp_path / "export.xml"
    xml.write_text('''<?xml version="1.0" encoding="UTF-8"?>
<HealthData>
  <Record type="HKQuantityTypeIdentifierStepCount" sourceName="iPhone" unit="count" value="120" startDate="2026-05-09 08:00:00 +0200" endDate="2026-05-09 08:10:00 +0200"/>
  <Record type="HKQuantityTypeIdentifierHeartRate" sourceName="Watch" unit="count/min" value="72" startDate="2026-05-09 08:00:00 +0200" endDate="2026-05-09 08:00:05 +0200"/>
  <Record type="HKQuantityTypeIdentifierUnknownThing" value="1" startDate="2026-05-09 08:00:00 +0200"/>
  <Workout workoutActivityType="HKWorkoutActivityTypeRunning" sourceName="Watch" startDate="2026-05-09 09:00:00 +0200" endDate="2026-05-09 09:30:00 +0200"/>
</HealthData>''')
    records, stats = parse_records(xml)
    assert stats.parsed == 3
    assert stats.skipped == 1
    assert {r["category"] for r in records} == {"daily", "vitals", "workout"}
    assert records[0]["value"] == 120


def test_parse_health_sync_json(tmp_path: Path) -> None:
    path = tmp_path / "steps.json"
    path.write_text('[{"type":"steps","value":42,"unit":"count","start":"2026-05-09T08:00:00+02:00","end":"2026-05-09T08:05:00+02:00"}]')
    records = parse_json_records(path)
    assert records[0]["category"] == "daily"
    assert records[0]["type"] == "steps"
    assert records[0]["value"] == 42
