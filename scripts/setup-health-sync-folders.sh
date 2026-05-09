#!/usr/bin/env zsh
set -euo pipefail

mkdir -p "$HOME/health-sync/raw" \
         "$HOME/health-sync/normalized" \
         "$HOME/ActivityWatchImports/apple-health" \
         "$HOME/Library/Logs/aw-activitywatch-stack" \
         "$HOME/Library/Application Support/aw-activitywatch-stack"

echo "Created local Apple Health sync folders:"
echo "- $HOME/health-sync/raw"
echo "- $HOME/health-sync/normalized"
echo "- $HOME/ActivityWatchImports/apple-health"
echo "- $HOME/Library/Logs/aw-activitywatch-stack"
