#!/usr/bin/env bash
set -euo pipefail

src="${1:?source config required}"
dst="config/agentgateway-active.yaml"

if [ ! -f "$src" ]; then
  echo "ERROR: source config not found: $src" >&2
  exit 1
fi

{
  echo "# GENERATED FILE - DO NOT EDIT DIRECTLY"
  echo "# Source: $src"
  echo "# Edit source config files, not this active mounted file."
  echo
  cat "$src"
} > "$dst"

echo "Wrote $dst from $src"
