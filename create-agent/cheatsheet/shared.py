"""Shared utilities used across all workshop agent steps."""
from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import urlparse

from agent_framework import ContextProvider, SessionContext


def get_base_endpoint(endpoint: str | None = None) -> str:
    """Return just the scheme+host of an Azure OpenAI endpoint URL.

    Normalises both the short form (``https://host/``) and the full Target URI
    that Azure AI Foundry shows by default::

        https://host/openai/deployments/model/chat/completions?api-version=...

    Both forms are accepted so attendees can paste the Target URI directly
    from AI Foundry without having to trim it.
    """
    if endpoint is None:
        endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
    parsed = urlparse(endpoint)
    return f"{parsed.scheme}://{parsed.netloc}/"

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
