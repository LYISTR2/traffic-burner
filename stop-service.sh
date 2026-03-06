#!/usr/bin/env bash
set -euo pipefail
SERVICE_NAME="traffic-burner"
systemctl stop "$SERVICE_NAME"
systemctl --no-pager --full --lines=10 status "$SERVICE_NAME" || true
