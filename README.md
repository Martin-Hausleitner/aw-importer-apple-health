# aw-importer-apple-health

Local-first Apple Health importer for ActivityWatch.

## Best source

Use an Apple Health `export.xml` or export ZIP. Keep real exports local and out of Git.

## Commands

```bash
aw-importer-apple-health inspect ~/ActivityWatchImports/apple-health/export.zip
aw-importer-apple-health import-export ~/ActivityWatchImports/apple-health/export.zip --dry-run
aw-importer-apple-health import-export ~/ActivityWatchImports/apple-health/export.zip
```

## Imported buckets

- `aw-importer-apple-health-daily`
- `aw-importer-apple-health-vitals`
- `aw-importer-apple-health-workout`
- `aw-importer-apple-health-sleep`
- `aw-importer-apple-health-mindfulness`
- `aw-importer-apple-health-habits`

## Privacy

- Do not commit Apple Health exports.
- Import selected HealthKit types only.
- Prefer aggregated/daily use in coaching outputs.
- No medical diagnosis; use this for personal awareness and trend review.

## Local iPhone → Mac sync workflow

This importer is designed to sit behind a local HealthKit sync tool such as Health.md or a future `healthsync` CLI. The sync tool writes JSON files locally; this importer normalizes them into ActivityWatch.

Suggested local folders:

```text
~/health-sync/raw/          # files received from iPhone/Mac companion
~/health-sync/normalized/   # optional normalized exports
~/ActivityWatchImports/apple-health/  # fallback ZIP/XML backfills
```

Conceptual sync flow:

```bash
# Exact commands depend on the chosen iPhone/Mac sync tool.
healthsync discover
healthsync pair
healthsync status
healthsync types
healthsync fetch --type steps --days 30 --out ~/health-sync/raw/steps.json
healthsync fetch --type sleep --days 30 --out ~/health-sync/raw/sleep.json
healthsync fetch --type heart-rate --days 30 --out ~/health-sync/raw/heart-rate.json
healthsync fetch --type workouts --days 30 --out ~/health-sync/raw/workouts.json

# OpenClaw/ActivityWatch import side
aw-importer-apple-health import-json ~/health-sync/raw/steps.json --dry-run
aw-importer-apple-health sync-folder ~/health-sync/raw --dry-run
aw-importer-apple-health sync-folder ~/health-sync/raw
```

Supported commands:

- `import-export` — Apple Health `export.xml` / ZIP backfill.
- `import-json` — HealthKit-sync style JSON file.
- `sync-folder` — idempotently import JSON/XML/ZIP files from a local dropzone.

The importer keeps a local state file to avoid duplicate imports.
