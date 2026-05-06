"""Thread-safe JSON state persistence for Lost in [City] workshop game."""
from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Allow STATE_DIR to be overridden via env var (e.g. Azure Files mount point)
_state_dir = Path(os.environ.get("STATE_DIR", Path(__file__).resolve().parent))
STATE_FILE = _state_dir / "state.json"
CONFIG_FILE = Path(__file__).resolve().parent / "city_config.yaml"

_state_lock = threading.Lock()


def _atomic_write(path: Path, data: dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


def load_state() -> dict[str, Any]:
    with _state_lock:
        if not STATE_FILE.exists():
            return {"players": {}, "leaderboard": []}
        with STATE_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)


def save_state(data: dict[str, Any]) -> None:
    with _state_lock:
        _atomic_write(STATE_FILE, data)


def update_state(mutator) -> Any:
    """Load state, run mutator(state) -> result, save atomically, return result."""
    with _state_lock:
        if STATE_FILE.exists():
            with STATE_FILE.open("r", encoding="utf-8") as f:
                state = json.load(f)
        else:
            state = {"players": {}, "leaderboard": []}
        result = mutator(state)
        _atomic_write(STATE_FILE, state)
        return result


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")



def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
