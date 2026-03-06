#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_SCRIPT="$SCRIPT_DIR/run.sh"
INSTALL_SERVICE_SCRIPT="$SCRIPT_DIR/install-service.sh"
STOP_SERVICE_SCRIPT="$SCRIPT_DIR/stop-service.sh"
UNINSTALL_SERVICE_SCRIPT="$SCRIPT_DIR/uninstall-service.sh"

prompt_default() {
  local label="$1"
  local default_value="$2"
  local result
  read -r -p "$label [$default_value]: " result
  echo "${result:-$default_value}"
}

build_common_args() {
  local preset mode target target_per_day duration start_hour end_hour
  preset="$(prompt_default "Preset (tiny/low/medium/high)" "low")"
  mode="$(prompt_default "Mode (download/upload/mixed)" "mixed")"
  target="$(prompt_default "Single-run target traffic (blank for none)" "")"
  target_per_day="$(prompt_default "Daily target traffic (blank for none)" "")"
  duration="$(prompt_default "Duration seconds (blank for none)" "")"
  start_hour="$(prompt_default "Start hour 0-23 (blank for none)" "")"
  end_hour="$(prompt_default "End hour 0-23 (blank for none)" "")"

  local args=()
  args+=(--preset "$preset" --mode "$mode")
  [[ -n "$target" ]] && args+=(--target "$target")
  [[ -n "$target_per_day" ]] && args+=(--target-per-day "$target_per_day")
  [[ -n "$duration" ]] && args+=(--duration "$duration")
  [[ -n "$start_hour" ]] && args+=(--start-hour "$start_hour")
  [[ -n "$end_hour" ]] && args+=(--end-hour "$end_hour")
  printf '%q ' "${args[@]}"
}

run_foreground() {
  local args
  args="$(build_common_args)"
  echo
  echo "Running: $RUN_SCRIPT $args"
  # shellcheck disable=SC2086
  eval "$RUN_SCRIPT $args"
}

install_background() {
  local args
  args="$(build_common_args)"
  echo
  echo "Installing service: $INSTALL_SERVICE_SCRIPT $args"
  # shellcheck disable=SC2086
  eval "$INSTALL_SERVICE_SCRIPT $args"
}

quick_run() {
  local preset="$1"
  local extra="$2"
  echo
  echo "Running quick preset: $preset $extra"
  # shellcheck disable=SC2086
  eval "$RUN_SCRIPT --preset $preset $extra"
}

main_menu() {
  while true; do
    echo
    echo "==== traffic-burner menu ===="
    echo "1) Light slow burn (tiny)"
    echo "2) Long-running daily use (low)"
    echo "3) Burn 20GB today and stop"
    echo "4) Custom foreground run"
    echo "5) Install background service"
    echo "6) Stop background service"
    echo "7) Uninstall background service"
    echo "0) Exit"
    echo
    read -r -p "Choose: " choice

    case "$choice" in
      1) quick_run tiny "" ;;
      2) quick_run low "--mode mixed" ;;
      3) quick_run low "--target-per-day 20GB --mode mixed" ;;
      4) run_foreground ;;
      5) install_background ;;
      6) "$STOP_SERVICE_SCRIPT" ;;
      7) "$UNINSTALL_SERVICE_SCRIPT" ;;
      0) exit 0 ;;
      *) echo "Invalid option" ;;
    esac
  done
}

main_menu
