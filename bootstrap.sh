#!/usr/bin/env bash
set -euo pipefail
TARGET_DIR="/opt/traffic-burner"
REPO_URL="https://github.com/LYISTR2/traffic-burner.git"

if ! command -v git >/dev/null 2>&1; then
  if command -v apt-get >/dev/null 2>&1; then
    apt-get update && apt-get install -y git python3
  elif command -v apk >/dev/null 2>&1; then
    apk add --no-cache git python3
  fi
fi

rm -rf "$TARGET_DIR"
git clone --depth=1 "$REPO_URL" "$TARGET_DIR"
chmod +x "$TARGET_DIR"/*.sh
cd "$TARGET_DIR"
echo "traffic-burner installed to $TARGET_DIR"
echo "Run: $TARGET_DIR/run.sh --preset low --target 5GB"
