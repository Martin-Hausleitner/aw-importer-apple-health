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
