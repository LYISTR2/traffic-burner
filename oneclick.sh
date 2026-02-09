#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_DIR"

echo "=== Traffic Burner 一键启动 ==="

if ! command -v python3 >/dev/null 2>&1; then
  echo "[错误] 未检测到 python3，请先安装 Python 3.9+"
  exit 1
fi

if [ ! -d ".venv" ]; then
  echo "[1/4] 创建虚拟环境..."
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "[2/4] 安装依赖..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

read -rp "运行小时数（默认 1）: " HOURS
HOURS=${HOURS:-1}

read -rp "目标速率 MB/s（默认 0.5）: " RATE
RATE=${RATE:-0.5}

echo "[3/4] 启动流量消耗..."
echo "提示：按 Ctrl+C 可随时停止"

ARGS=(--hours "$HOURS" --rate "$RATE" --log-interval 5)
if [ -f "urls.example.txt" ]; then
  ARGS+=(--urls-file "urls.example.txt")
fi

echo "[4/4] 运行参数: ${ARGS[*]}"
python3 traffic_burner.py "${ARGS[@]}"
