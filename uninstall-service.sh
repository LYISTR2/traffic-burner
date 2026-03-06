#!/usr/bin/env bash
set -euo pipefail
SERVICE_NAME="traffic-burner"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
systemctl disable --now "$SERVICE_NAME" >/dev/null 2>&1 || true
rm -f "$SERVICE_FILE"
systemctl daemon-reload
printf 'removed %s\n' "$SERVICE_NAME"
