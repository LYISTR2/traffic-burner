#!/usr/bin/env python3
import json
import time
from pathlib import Path
from typing import Optional

DEFAULT_STATE_FILE = Path.home() / ".traffic-burner-state.json"


def today_key() -> str:
    return time.strftime("%Y-%m-%d")


def load_state(path: Optional[str] = None) -> dict:
    state_path = Path(path) if path else DEFAULT_STATE_FILE
    if not state_path.exists():
        return {"days": {}}
    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except Exception:
        return {"days": {}}


def save_state(state: dict, path: Optional[str] = None):
    state_path = Path(path) if path else DEFAULT_STATE_FILE
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def get_today_total(path: Optional[str] = None) -> int:
    state = load_state(path)
    return int(state.get("days", {}).get(today_key(), {}).get("bytes", 0))


def add_today_bytes(num_bytes: int, path: Optional[str] = None):
    state = load_state(path)
    days = state.setdefault("days", {})
    entry = days.setdefault(today_key(), {"bytes": 0, "updated_at": 0})
    entry["bytes"] = int(entry.get("bytes", 0)) + int(num_bytes)
    entry["updated_at"] = int(time.time())
    save_state(state, path)
