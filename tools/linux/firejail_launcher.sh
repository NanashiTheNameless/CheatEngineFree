#!/usr/bin/env bash
set -euo pipefail
CE_BIN="$1"
shift || true
if command -v firejail >/dev/null 2>&1; then
  echo "Running with firejail --net=none"
  exec firejail --net=none "$CE_BIN" "$@"
else
  echo "firejail not found. Install firejail to run Cheat Engine with network disabled." >&2
  echo "Exiting to avoid launching without network restrictions." >&2
  exit 1
fi
