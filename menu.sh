#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_SCRIPT="$SCRIPT_DIR/run.sh"
INSTALL_SERVICE_SCRIPT="$SCRIPT_DIR/install-service.sh"
STOP_SERVICE_SCRIPT="$SCRIPT_DIR/stop-service.sh"
UNINSTALL_SERVICE_SCRIPT="$SCRIPT_DIR/uninstall-service.sh"

pause_enter() {
  read -r -p "按回车继续..." _
}

prompt_default_cn() {
  local label="$1"
  local default_value="$2"
  local input
  if [[ -n "$default_value" ]]; then
    read -r -p "$label [$default_value]: " input
    echo "${input:-$default_value}"
  else
    read -r -p "$label: " input
    echo "$input"
  fi
}

build_args_cn() {
  local preset mode target target_per_day duration start_hour end_hour
  preset="$(prompt_default_cn "选择预设（tiny/low/medium/high）" "low")"
  mode="$(prompt_default_cn "选择模式（download/upload/mixed）" "mixed")"
  target="$(prompt_default_cn "单次目标流量（留空表示不限，如 5GB）" "")"
  target_per_day="$(prompt_default_cn "每日目标流量（留空表示不限，如 20GB）" "")"
  duration="$(prompt_default_cn "运行时长秒数（留空表示不限）" "")"
  start_hour="$(prompt_default_cn "开始小时 0-23（留空表示不限）" "")"
  end_hour="$(prompt_default_cn "结束小时 0-23（留空表示不限）" "")"

  local args=()
  args+=(--preset "$preset" --mode "$mode")
  [[ -n "$target" ]] && args+=(--target "$target")
  [[ -n "$target_per_day" ]] && args+=(--target-per-day "$target_per_day")
  [[ -n "$duration" ]] && args+=(--duration "$duration")
  [[ -n "$start_hour" ]] && args+=(--start-hour "$start_hour")
  [[ -n "$end_hour" ]] && args+=(--end-hour "$end_hour")
  printf '%q ' "${args[@]}"
}

run_foreground_cn() {
  local args
  args="$(build_args_cn)"
  echo
  echo "即将执行：$RUN_SCRIPT $args"
  # shellcheck disable=SC2086
  eval "$RUN_SCRIPT $args"
  pause_enter
}

install_background_cn() {
  local args
  args="$(build_args_cn)"
  echo
  echo "即将安装后台服务：$INSTALL_SERVICE_SCRIPT $args"
  # shellcheck disable=SC2086
  eval "$INSTALL_SERVICE_SCRIPT $args"
  pause_enter
}

quick_run_cn() {
  local preset="$1"
  local extra_args="$2"
  echo
  echo "正在运行：预设=$preset $extra_args"
  # shellcheck disable=SC2086
  eval "$RUN_SCRIPT --preset $preset $extra_args"
  pause_enter
}

main_menu_cn() {
  while true; do
    clear || true
    echo "================================"
    echo "     流量消耗脚本 traffic-burner"
    echo "================================"
    echo "1）轻度慢烧（tiny）"
    echo "2）长期挂机（low）"
    echo "3）今天烧 20GB 自动停"
    echo "4）自定义前台运行"
    echo "5）安装后台服务"
    echo "6）停止后台服务"
    echo "7）卸载后台服务"
    echo "0）退出"
    echo
    read -r -p "请输入选项：" choice

    case "$choice" in
      1) quick_run_cn tiny "" ;;
      2) quick_run_cn low "--mode mixed" ;;
      3) quick_run_cn low "--target-per-day 20GB --mode mixed" ;;
      4) run_foreground_cn ;;
      5) install_background_cn ;;
      6) "$STOP_SERVICE_SCRIPT"; pause_enter ;;
      7) "$UNINSTALL_SERVICE_SCRIPT"; pause_enter ;;
      0) exit 0 ;;
      *) echo "无效选项"; pause_enter ;;
    esac
  done
}

main_menu_cn
