from __future__ import annotations

from collections import Counter
from pathlib import Path

import click

from .activitywatch import ActivityWatchClient, stable_hash
from .parser import DEFAULT_TYPES, parse_records


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
    inserted = 0
    if not dry_run:
        aw = ActivityWatchClient()
        seen: set[str] = set()
        for record in records:
            key = stable_hash(record)
            if key in seen:
                continue
            seen.add(key)
            aw.insert_record(record["category"], record)
            inserted += 1
    click.echo(f"parsed={stats.parsed} skipped={stats.skipped} inserted={inserted} dry_run={dry_run} categories={dict(by_category)}")


@main.command("inspect")
@click.argument("path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
def inspect(path: Path) -> None:
    """Inspect an Apple Health export without importing."""
    records, stats = parse_records(path)
    by_category = Counter(r["category"] for r in records)
    click.echo(f"parsed={stats.parsed} skipped={stats.skipped} categories={dict(by_category)}")
