#!/usr/bin/env python3
"""
Traffic Burner (network throughput consumer)

Default target rate: 0.5 MB/s
Default duration: 1 hour

Use only on networks/resources you own or are explicitly authorized to test.
"""

from __future__ import annotations

import argparse
import os
import signal
import sys
import time
from collections import deque
from dataclasses import dataclass
from typing import Iterable, List

import requests


DEFAULT_URLS = [
    # Public large test files / mirrors (examples; replace with your own if needed)
    "https://speed.hetzner.de/1GB.bin",
    "https://proof.ovh.net/files/1Gb.dat",
    "https://download.samplelib.com/mp4/sample-30s.mp4",
]

stop_requested = False


def _signal_handler(signum, frame):
    global stop_requested
    stop_requested = True


@dataclass
class Stats:
    bytes_total: int = 0
    started_at: float = 0.0


class RateLimiter:
    """Simple token bucket limiter (bytes/sec)."""

    def __init__(self, rate_bytes_per_sec: float, capacity_seconds: float = 1.5):
        self.rate = max(1.0, rate_bytes_per_sec)
        self.capacity = self.rate * max(0.1, capacity_seconds)
        self.tokens = self.capacity
        self.last = time.monotonic()

    def consume(self, amount: int):
        while amount > 0 and not stop_requested:
            now = time.monotonic()
            elapsed = now - self.last
            self.last = now

            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)

            if self.tokens >= amount:
                self.tokens -= amount
                return

            missing = amount - self.tokens
            self.tokens = 0
            sleep_s = missing / self.rate
            if sleep_s > 0:
                time.sleep(min(sleep_s, 0.25))


def load_urls(path: str | None) -> List[str]:
    if not path:
        return DEFAULT_URLS[:]

    urls: List[str] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            urls.append(line)

    if not urls:
        raise ValueError("urls file is empty")
    return urls


def human_bytes(n: float) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while n >= 1024 and i < len(units) - 1:
        n /= 1024
        i += 1
    return f"{n:.2f} {units[i]}"


def run(
    urls: Iterable[str],
    duration_hours: float,
    rate_mb_s: float,
    chunk_kb: int,
    connect_timeout: float,
    read_timeout: float,
    log_interval: float,
    stop_file: str,
) -> int:
    global stop_requested
    stats = Stats(started_at=time.time())
    end_at = stats.started_at + duration_hours * 3600
    rate_bps = rate_mb_s * 1024 * 1024
    limiter = RateLimiter(rate_bps)

    chunksize = max(1, chunk_kb) * 1024
    timeout = (connect_timeout, read_timeout)

    print(
        f"[start] rate={rate_mb_s:.3f} MB/s ({human_bytes(rate_bps)}/s), "
        f"duration={duration_hours:.3f} h, chunk={chunk_kb} KB"
    )

    rolling = deque(maxlen=120)
    last_log = time.time()

    session = requests.Session()
    url_list = list(urls)
    if not url_list:
        print("[error] no urls configured", file=sys.stderr)
        return 2

    url_index = 0
    retries = 0

    while not stop_requested and time.time() < end_at:
        if stop_file and os.path.exists(stop_file):
            print(f"[stop] stop file detected: {stop_file}")
            break

        url = url_list[url_index % len(url_list)]
        url_index += 1

        try:
            with session.get(url, stream=True, timeout=timeout, allow_redirects=True) as resp:
                if resp.status_code >= 400:
                    raise requests.HTTPError(f"HTTP {resp.status_code} from {url}")

                for chunk in resp.iter_content(chunk_size=chunksize):
                    if stop_requested or time.time() >= end_at:
                        break
                    if stop_file and os.path.exists(stop_file):
                        stop_requested = True
                        break
                    if not chunk:
                        continue

                    n = len(chunk)
                    limiter.consume(n)
                    stats.bytes_total += n
                    rolling.append((time.time(), n))

                    now = time.time()
                    if now - last_log >= log_interval:
                        window_start = now - min(30.0, now - stats.started_at)
                        win_bytes = sum(b for t, b in rolling if t >= window_start)
                        win_seconds = max(0.001, now - window_start)
                        speed = win_bytes / win_seconds

                        elapsed = now - stats.started_at
                        remain = max(0.0, end_at - now)
                        print(
                            f"[stat] elapsed={elapsed:.1f}s remain={remain:.1f}s "
                            f"used={human_bytes(stats.bytes_total)} "
                            f"speed≈{human_bytes(speed)}/s"
                        )
                        last_log = now

            retries = 0

        except Exception as e:
            retries += 1
            backoff = min(8, 2 ** min(retries, 3))
            print(f"[warn] source failed: {url} ({e}), retry in {backoff}s")
            time.sleep(backoff)

    total_time = max(0.001, time.time() - stats.started_at)
    avg = stats.bytes_total / total_time
    print("\n[done]")
    print(f"  total used: {human_bytes(stats.bytes_total)}")
    print(f"  total time: {total_time:.1f}s")
    print(f"  avg speed : {human_bytes(avg)}/s")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Consume network traffic at a target rate.")
    p.add_argument("--hours", type=float, default=1.0, help="Run duration in hours (default: 1)")
    p.add_argument(
        "--rate", type=float, default=0.5, help="Target rate in MB/s (default: 0.5)"
    )
    p.add_argument("--chunk-kb", type=int, default=64, help="Read chunk size in KB (default: 64)")
    p.add_argument(
        "--urls-file",
        type=str,
        default=None,
        help="Path to text file containing download URLs, one per line",
    )
    p.add_argument("--connect-timeout", type=float, default=10, help="Connect timeout seconds")
    p.add_argument("--read-timeout", type=float, default=20, help="Read timeout seconds")
    p.add_argument("--log-interval", type=float, default=5, help="Print stats every N seconds")
    p.add_argument(
        "--stop-file",
        type=str,
        default="stop.flag",
        help="If this file exists, script exits gracefully (default: stop.flag)",
    )
    return p


def main() -> int:
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    args = build_parser().parse_args()

    if args.hours <= 0:
        print("--hours must be > 0", file=sys.stderr)
        return 2
    if args.rate <= 0:
        print("--rate must be > 0", file=sys.stderr)
        return 2

    try:
        urls = load_urls(args.urls_file)
    except Exception as e:
        print(f"Failed to load URLs: {e}", file=sys.stderr)
        return 2

    return run(
        urls=urls,
        duration_hours=args.hours,
        rate_mb_s=args.rate,
        chunk_kb=args.chunk_kb,
        connect_timeout=args.connect_timeout,
        read_timeout=args.read_timeout,
        log_interval=args.log_interval,
        stop_file=args.stop_file,
    )


if __name__ == "__main__":
    raise SystemExit(main())
