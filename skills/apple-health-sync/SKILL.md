---
name: apple-health-sync
description: Use for local-first Apple Health / HealthKit sync into ActivityWatch via a Mac JSON dropzone. Handles low-effort setup, folder sync, dry-runs, launchd scheduling, and privacy-safe HealthKit import checks.
---

# Apple Health Sync Skill

Use when the user wants Apple Health, HealthKit, iPhone health data, Oclean/toothbrushing, steps, sleep, heart-rate, HRV, workouts, or body metrics imported into the local ActivityWatch stack.

## Safety

- Never upload or commit real Apple Health exports, JSON payloads, or generated reports.
- Start with the 4 core types only: steps, sleep, heart-rate, workouts.
- First historical fetch should be 30 days, not multi-year.
- Prefer local JSON dropzone sync before OpenClaw automation.
- No medical diagnosis. Health outputs are awareness/coaching only.

## Local folders

- Raw local sync input: `~/health-sync/raw/`
- Optional normalized output: `~/health-sync/normalized/`
- Manual Apple Health export fallback: `~/ActivityWatchImports/apple-health/`
- Logs: `~/Library/Logs/aw-activitywatch-stack/`

## Recommended first workflow

1. Make iPhone/Mac helper write JSON for only:
   - `steps.json`
   - `sleep.json`
   - `heart-rate.json`
   - `workouts.json`
2. Run dry-run:

```bash
aw-importer-apple-health sync-folder ~/health-sync/raw --dry-run
```

3. If parsed counts look right, import:

```bash
aw-importer-apple-health sync-folder ~/health-sync/raw
```

4. Verify ActivityWatch buckets start with:

```text
aw-importer-apple-health-
```

## Commands in this repo

```bash
scripts/setup-health-sync-folders.sh
scripts/sync-health-folder.sh --dry-run
scripts/sync-health-folder.sh
```

## LaunchAgent

Use `contrib/launchd/ai.servas.aw-apple-health-sync.plist.template` after replacing:

- `__HOME__`
- `__REPO_DIR__`

Keep it disabled until the raw JSON producer is stable.
