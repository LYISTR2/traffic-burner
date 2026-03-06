#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="traffic-burner"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
ARGS="${*:---preset low --mode mixed}"

cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Traffic Burner
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=${SCRIPT_DIR}
ExecStart=/usr/bin/env bash ${SCRIPT_DIR}/run.sh ${ARGS}
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now "$SERVICE_NAME"
systemctl --no-pager --full --lines=20 status "$SERVICE_NAME"
