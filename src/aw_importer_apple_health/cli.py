from __future__ import annotations

from collections import Counter
import hashlib
from pathlib import Path

import click

from .activitywatch import ActivityWatchClient, stable_hash
from .json_import import parse_json_records
from .parser import DEFAULT_TYPES, parse_records
from .state import ImportState


@click.group()
def main() -> None:
    """Import selected Apple Health export data into local ActivityWatch."""


@main.command("import-export")
@click.argument("path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--type", "types", multiple=True, help="HealthKit type identifier to include. Repeatable.")
@click.option("--dry-run", is_flag=True, help="Parse without writing to ActivityWatch.")
def import_export(path: Path, types: tuple[str, ...], dry_run: bool) -> None:
    records, stats = parse_records(path, types or DEFAULT_TYPES)
    by_category = Counter(r["category"] for r in records)
    inserted = _write_records(records, dry_run=dry_run)
    click.echo(f"parsed={stats.parsed} skipped={stats.skipped} inserted={inserted} dry_run={dry_run} categories={dict(by_category)}")


@main.command("inspect")
@click.argument("path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
def inspect(path: Path) -> None:
    """Inspect an Apple Health export without importing."""
    records, stats = parse_records(path)
    by_category = Counter(r["category"] for r in records)
    click.echo(f"parsed={stats.parsed} skipped={stats.skipped} categories={dict(by_category)}")


def _write_records(records: list[dict], dry_run: bool = False) -> int:
    if dry_run:
        return 0
    aw = ActivityWatchClient()
    state = ImportState.load()
    inserted = 0
    for record in records:
        key = stable_hash(record)
        if key in state.record_hashes:
            continue
        aw.insert_record(record["category"], record)
        state.record_hashes.add(key)
        inserted += 1
    state.save()
    return inserted


@main.command("import-json")
@click.argument("path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--type", "fallback_type", help="Fallback metric type if JSON records do not include one, e.g. steps or sleep.")
@click.option("--dry-run", is_flag=True, help="Parse without writing to ActivityWatch.")
def import_json(path: Path, fallback_type: str | None, dry_run: bool) -> None:
    """Import HealthKit-sync style JSON records."""
    records = parse_json_records(path, fallback_type=fallback_type)
    by_category = Counter(r["category"] for r in records)
    inserted = _write_records(records, dry_run=dry_run)
    click.echo(f"parsed={len(records)} inserted={inserted} dry_run={dry_run} categories={dict(by_category)}")


@main.command("sync-folder")
@click.argument("folder", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--dry-run", is_flag=True, help="Parse files without writing to ActivityWatch/state.")
def sync_folder(folder: Path, dry_run: bool) -> None:
    """Import all JSON/XML/ZIP health files from a local sync dropzone idempotently."""
    state = ImportState.load()
    parsed = inserted = files = skipped_files = 0
    for path in sorted(folder.rglob("*")):
        if not path.is_file() or path.name.startswith("."):
            continue
        if path.suffix.lower() not in {".json", ".xml", ".zip", ".gz"}:
            continue
        file_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if state.imported_files.get(str(path)) == file_hash and not dry_run:
            skipped_files += 1
            continue
        if path.suffix.lower() == ".json":
            records = parse_json_records(path)
        else:
            records, _ = parse_records(path)
        parsed += len(records)
        inserted += _write_records(records, dry_run=dry_run)
        files += 1
        if not dry_run:
            state.imported_files[str(path)] = file_hash
            state.save()
    click.echo(f"files={files} skipped_files={skipped_files} parsed={parsed} inserted={inserted} dry_run={dry_run}")
