# Low-effort Apple Health Mac/CLI Sync

## Goal

Get Apple Health into the local ActivityWatch/Leo stack with the least moving parts.

## Scope v1

Only sync 4 core types first:

- steps
- sleep
- heart-rate
- workouts

Use 30 days history for the first run. Do not sync everything.

## Folder layout

```text
~/health-sync/raw/                    # iPhone/Mac helper writes JSON here
~/health-sync/normalized/             # optional later
~/ActivityWatchImports/apple-health/  # manual ZIP/XML fallback
~/Library/Logs/aw-activitywatch-stack/
```

## First run

```bash
scripts/setup-health-sync-folders.sh
aw-importer-apple-health sync-folder ~/health-sync/raw --dry-run
aw-importer-apple-health sync-folder ~/health-sync/raw
```

## Automation

Use `contrib/launchd/ai.servas.aw-apple-health-sync.plist.template` only after the raw JSON producer is stable.

Default interval: 15 minutes.

## Producer options

- Health.md iOS + macOS companion
- future `healthsync` CLI
- iOS Shortcut writing JSON files
- custom HealthKit iPhone app later

## Privacy

Raw JSON stays local. Never commit `~/health-sync`, Apple Health exports, or generated personal reports.
