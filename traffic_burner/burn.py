#!/usr/bin/env python3
import argparse
import os
import signal
import sys
import threading
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from presets import PRESETS
from sources import DEFAULT_DOWNLOAD_SOURCES, DEFAULT_UPLOAD_TARGETS
from state import add_today_bytes, get_today_total

stop_event = threading.Event()
stats_lock = threading.Lock()
STATS = {
    "download_bytes": 0,
    "upload_bytes": 0,
    "started_at": time.time(),
}


def kbps_to_chunk_bytes(kbps: int, interval: float) -> int:
    return max(1024, int((kbps * 1024 / 8) * interval))


def human_bytes(num: float) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    idx = 0
    while num >= 1024 and idx < len(units) - 1:
        num /= 1024.0
        idx += 1
    return f"{num:.2f} {units[idx]}"


def add_stat(kind: str, size: int):
    with stats_lock:
        STATS[kind] += size


def total_bytes() -> int:
    with stats_lock:
        return STATS["download_bytes"] + STATS["upload_bytes"]


def cycle_items(items: Iterable[str]):
    while True:
        for item in items:
            yield item


def throttled_download(url: str, rate_kbps: int, interval: float):
    chunk_size = kbps_to_chunk_bytes(rate_kbps, interval)
    req = urllib.request.Request(url, headers={"User-Agent": "traffic-burner/0.1"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        while not stop_event.is_set():
            chunk = resp.read(chunk_size)
            if not chunk:
                break
            add_stat("download_bytes", len(chunk))
            time.sleep(interval)


def throttled_upload(url: str, rate_kbps: int, interval: float):
    chunk_size = kbps_to_chunk_bytes(rate_kbps, interval)
    payload = os.urandom(chunk_size)
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"User-Agent": "traffic-burner/0.1", "Content-Type": "application/octet-stream"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        resp.read(64)
    add_stat("upload_bytes", len(payload))
    time.sleep(interval)


def download_worker(urls: Iterable[str], rate_kbps: int, interval: float):
    for url in cycle_items(urls):
        if stop_event.is_set():
            return
        try:
            throttled_download(url, rate_kbps, interval)
        except Exception:
            time.sleep(interval)


def upload_worker(urls: Iterable[str], rate_kbps: int, interval: float):
    for url in cycle_items(urls):
        if stop_event.is_set():
            return
        try:
            throttled_upload(url, rate_kbps, interval)
        except Exception:
            time.sleep(interval)


def stats_worker(stats_interval: int, target_bytes: Optional[int], target_per_day: Optional[int], state_file: Optional[str]):
    last_total = 0
    last_time = time.time()
    while not stop_event.is_set():
        time.sleep(stats_interval)
        now = time.time()
        current_total = total_bytes()
        delta_bytes = current_total - last_total
        delta_time = max(1e-6, now - last_time)
        rate_bps = delta_bytes / delta_time
        with stats_lock:
            down = STATS["download_bytes"]
            up = STATS["upload_bytes"]

        if delta_bytes > 0:
            add_today_bytes(delta_bytes, state_file)
        today_total = get_today_total(state_file)

        print(
            f"[stats] down={human_bytes(down)} up={human_bytes(up)} total={human_bytes(current_total)} "
            f"today={human_bytes(today_total)} rate={human_bytes(rate_bps)}/s",
            flush=True,
        )
        last_total = current_total
        last_time = now
        if target_bytes is not None and current_total >= target_bytes:
            print(f"[target] reached {human_bytes(target_bytes)}, stopping.", flush=True)
            stop_event.set()
            return
        if target_per_day is not None and today_total >= target_per_day:
            print(f"[target-per-day] reached {human_bytes(target_per_day)} today, stopping.", flush=True)
            stop_event.set()
            return


def parse_bytes_target(raw: Optional[str]) -> Optional[int]:
    if not raw:
        return None
    raw = raw.strip().lower()
    multipliers = {
        "kb": 1024,
        "mb": 1024 ** 2,
        "gb": 1024 ** 3,
        "tb": 1024 ** 4,
        "k": 1024,
        "m": 1024 ** 2,
        "g": 1024 ** 3,
        "t": 1024 ** 4,
        "b": 1,
    }
    for suffix, mult in multipliers.items():
        if raw.endswith(suffix):
            return int(float(raw[: -len(suffix)]) * mult)
    return int(raw)


def parse_args():
    parser = argparse.ArgumentParser(description="Slow traffic burner with presets")
    parser.add_argument("--preset", choices=PRESETS.keys(), default="low")
    parser.add_argument("--mode", choices=["download", "upload", "mixed"], help="Override preset mode")
    parser.add_argument("--download-rate-kbps", type=int, help="Per worker download rate")
    parser.add_argument("--upload-rate-kbps", type=int, help="Per worker upload rate")
    parser.add_argument("--concurrency", type=int, help="Number of workers")
    parser.add_argument("--interval", type=float, help="Sleep interval between chunks")
    parser.add_argument("--target", help="Stop automatically after target traffic, e.g. 5GB, 800MB")
    parser.add_argument("--target-per-day", help="Stop when today's total traffic reaches target, e.g. 20GB")
    parser.add_argument("--state-file", help="State file path for daily counters")
    parser.add_argument("--start-hour", type=int, help="Only run after this hour (0-23)")
    parser.add_argument("--end-hour", type=int, help="Only run before this hour (0-23)")
    parser.add_argument("--stats-interval", type=int, default=5, help="Print stats every N seconds")
    parser.add_argument("--duration", type=int, help="Stop automatically after N seconds")
    return parser.parse_args()


def apply_args_to_preset(args):
    preset = PRESETS[args.preset].copy()
    if args.mode:
        preset["mode"] = args.mode
    if args.download_rate_kbps:
        preset["download_rate_kbps"] = args.download_rate_kbps
    if args.upload_rate_kbps:
        preset["upload_rate_kbps"] = args.upload_rate_kbps
    if args.concurrency:
        preset["concurrency"] = args.concurrency
    if args.interval:
        preset["interval_seconds"] = args.interval
    return preset


def schedule_duration_stop(seconds: Optional[int]):
    if not seconds:
        return None

    def _stop_later():
        time.sleep(seconds)
        if not stop_event.is_set():
            print(f"[duration] reached {seconds}s, stopping.", flush=True)
            stop_event.set()

    t = threading.Thread(target=_stop_later, daemon=True)
    t.start()
    return t


def hour_allowed(start_hour: Optional[int], end_hour: Optional[int]) -> bool:
    if start_hour is None and end_hour is None:
        return True
    now_hour = datetime.now().hour
    if start_hour is not None and end_hour is not None:
        if start_hour == end_hour:
            return True
        if start_hour < end_hour:
            return start_hour <= now_hour < end_hour
        return now_hour >= start_hour or now_hour < end_hour
    if start_hour is not None:
        return now_hour >= start_hour
    return now_hour < int(end_hour)


def handle_signal(signum, frame):
    stop_event.set()


def main():
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    args = parse_args()
    preset = apply_args_to_preset(args)
    target_bytes = parse_bytes_target(args.target)
    target_per_day = parse_bytes_target(args.target_per_day)

    if not hour_allowed(args.start_hour, args.end_hour):
        print(
            f"[schedule] current hour is outside allowed window start={args.start_hour} end={args.end_hour}, exiting.",
            flush=True,
        )
        return

    threads = []
    mode = preset["mode"]
    concurrency = preset["concurrency"]

    try:
        if mode in ("download", "mixed"):
            workers = concurrency if mode == "download" else max(1, concurrency // 2)
            for _ in range(workers):
                t = threading.Thread(
                    target=download_worker,
                    args=(DEFAULT_DOWNLOAD_SOURCES, preset["download_rate_kbps"], preset["interval_seconds"]),
                    daemon=True,
                )
                threads.append(t)
                t.start()

        if mode in ("upload", "mixed"):
            workers = concurrency if mode == "upload" else max(1, concurrency - max(1, concurrency // 2))
            for _ in range(workers):
                t = threading.Thread(
                    target=upload_worker,
                    args=(DEFAULT_UPLOAD_TARGETS, preset["upload_rate_kbps"], preset["interval_seconds"]),
                    daemon=True,
                )
                threads.append(t)
                t.start()

        today_existing = get_today_total(args.state_file)
        if target_per_day is not None and today_existing >= target_per_day:
            print(
                f"[target-per-day] already reached today: {human_bytes(today_existing)} >= {human_bytes(target_per_day)}",
                flush=True,
            )
            return

        stats_thread = threading.Thread(
            target=stats_worker,
            args=(args.stats_interval, target_bytes, target_per_day, args.state_file),
            daemon=True,
        )
        stats_thread.start()
        schedule_duration_stop(args.duration)

        print(
            f"traffic-burner started preset={args.preset} mode={mode} concurrency={concurrency} "
            f"target={args.target or 'none'} target_per_day={args.target_per_day or 'none'} duration={args.duration or 'none'}s",
            flush=True,
        )
        print("Press Ctrl+C to stop", flush=True)
        while not stop_event.is_set():
            time.sleep(1)
    finally:
        stop_event.set()
        for t in threads:
            t.join(timeout=1)
        print("stopped", flush=True)


if __name__ == "__main__":
    main()
