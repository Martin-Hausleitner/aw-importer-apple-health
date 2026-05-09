#!/usr/bin/env zsh
set -euo pipefail

# Low-effort local HealthKit sync adapter.
# Assumption: an iPhone/Mac helper such as Health.md or a future healthsync CLI
# writes JSON files into RAW_DIR. This script imports them into ActivityWatch.

RAW_DIR="${HEALTH_SYNC_RAW_DIR:-$HOME/health-sync/raw}"
LOG_DIR="${HEALTH_SYNC_LOG_DIR:-$HOME/Library/Logs/aw-activitywatch-stack}"
IMPORTER="${APPLE_HEALTH_IMPORTER:-aw-importer-apple-health}"

mkdir -p "$RAW_DIR" "$LOG_DIR"

# Default 4 core files/types for first phase:
# - steps.json
# - sleep.json
# - heart-rate.json
# - workouts.json
# The producer is responsible for writing JSON. We only consume local files.

if ! command -v "$IMPORTER" >/dev/null 2>&1; then
  echo "ERROR: $IMPORTER not found on PATH" >&2
  exit 127
fi

"$IMPORTER" sync-folder "$RAW_DIR" "$@"
