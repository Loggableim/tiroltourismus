#!/usr/bin/env bash
# Wrapper to run enrich_batch.py with OPENCODE_GO_API_KEY from the Hermes .env file
set -e
HERMES_ENV="/c/Users/logga/AppData/Local/hermes/.env"
if [ -f "$HERMES_ENV" ]; then
  # Source the .env file (it's bash-incompatible, so we source and then
  # only export the specific var we need by grepping for it)
  export OPENCODE_GO_API_KEY=$(grep -E "^OPENCODE_GO_API_KEY=" "$HERMES_ENV" | cut -d= -f2-)
fi

cd /f/tiroltourismus
python scripts/enrich_batch.py --file "scripts/batches/batch_$1.json"
