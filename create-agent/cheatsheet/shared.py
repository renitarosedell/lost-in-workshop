"""Shared utilities used across all workshop agent steps."""
from __future__ import annotations

import json
from pathlib import Path

from agent_framework import ContextProvider, SessionContext

# memory.json lives alongside create-agent/ (one level up from steps/)
MEMORY_FILE = Path(__file__).parent.parent / "memory.json"


class FileContextProvider(ContextProvider):
    """Persists quest state (player_id, URLs, codes) across steps via memory.json.

    Each call to _save() *merges* new keys into the existing file so that data
    from earlier steps is never lost.
    """

    def __init__(self) -> None:
        super().__init__("player-memory")

    def _load(self) -> dict:
        if MEMORY_FILE.exists():
            return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
        return {}

    def _save(self, data: dict) -> None:
        """Merge *data* into memory.json — preserves all existing keys."""
        existing = self._load()
        existing.update(data)
        MEMORY_FILE.write_text(json.dumps(existing, indent=2), encoding="utf-8")

    async def before_run(self, *, context: SessionContext, **_) -> None:
        player_id = self._load().get("player_id")
        if player_id:
            context.extend_instructions(
                self.source_id,
                f"Your player_id is {player_id}. Use it for all tool calls.",
            )

    async def after_run(self, *, context: SessionContext, **_) -> None:
        pass
