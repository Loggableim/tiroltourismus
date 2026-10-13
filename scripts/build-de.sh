#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export BUILD_LANGS=de
npm run build
