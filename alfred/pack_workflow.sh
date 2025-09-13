#!/usr/bin/env bash
set -euo pipefail

WF_DIR=$(cd "$(dirname "$0")" && pwd)
OUT="$WF_DIR/GmailTrashMover.alfredworkflow"

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

cp "$WF_DIR/info.plist" "$TMP/info.plist"

# Optional icons can be added here in the future.

(cd "$TMP" && zip -q -r "$OUT" .)

echo "Created: $OUT"
