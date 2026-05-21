#!/usr/bin/env bash
# One-shot local backup of src/data/ JSON content
# Usage: bash scripts/backup-now.sh
# Creates a timestamped zip in ../backups/ relative to this repo root

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKUP_DIR="$REPO_ROOT/backups"

mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +'%Y-%m-%d_%H-%M-%S')
ARCHIVE="$BACKUP_DIR/tirol-content-${TIMESTAMP}.zip"

echo "→ Creating backup: $ARCHIVE"

cd "$REPO_ROOT/src/data"
zip -r "$ARCHIVE" . -x ".*" -x "*/.*"

echo "✓ Backup created: $(ls -lh "$ARCHIVE" | awk '{print $5}')"
echo "→ Total backups in $BACKUP_DIR/: $(ls -1 "$BACKUP_DIR"/*.zip 2>/dev/null | wc -l)"
