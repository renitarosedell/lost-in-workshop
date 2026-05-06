"""Shared state and quest storage helpers for Lost in San Francisco."""
from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
QUESTS_FILE = BASE_DIR / "quests.json"
STATE_FILE = BASE_DIR / "state.json"

_state_lock = threading.Lock()
_quests_lock = threading.Lock()


def _atomic_write(path: Path, data: dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


def load_quests() -> dict[str, Any]:
    with _quests_lock:
        with QUESTS_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)


def save_quests(data: dict[str, Any]) -> None:
    with _quests_lock:
        _atomic_write(QUESTS_FILE, data)


def get_quest(quest_id: int) -> dict[str, Any] | None:
    for q in load_quests().get("quests", []):
        if int(q.get("id")) == int(quest_id):
            return q
    return None


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
    """Load state, run mutator(state) -> result, save, return result."""
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
