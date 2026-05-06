"""
Step 4 — Add FileContextProvider to persist your player_id between runs.

What this adds:
  - FileContextProvider: saves your player_id to a local JSON file (memory.json).
  - On the first run: registers you and saves the player_id.
  - On subsequent runs: loads the saved player_id and resumes from where you left off.

Run it (twice to see memory in action):
  python steps/step4_memory.py

Expected output (first run):
  Registered! player_id = PLR-XXXXXXXX  (saved to memory.json)

Expected output (second run):
  Resuming with saved player_id: PLR-XXXXXXXX
"""
from __future__ import annotations

import asyncio
import json
import os
import re
from pathlib import Path

from agent_framework import Agent, MCPStreamableHTTPTool, ContextProvider, SessionContext
from agent_framework.openai import OpenAIChatClient
from dotenv import load_dotenv

load_dotenv()

MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8000/mcp")
MEMORY_FILE = Path(__file__).parent.parent / "memory.json"


class FileContextProvider(ContextProvider):
    """Persists player_id to a local JSON file."""

    def __init__(self) -> None:
        super().__init__("player-memory")

    def _load(self) -> dict:
        if MEMORY_FILE.exists():
            return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
        return {}

    def _save(self, data: dict) -> None:
        MEMORY_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

    async def before_run(self, *, context: SessionContext, **_) -> None:
        data = self._load()
        player_id = data.get("player_id")
        if player_id:
            context.extend_instructions(
                self.source_id,
                f"Your player_id is {player_id}. You are already registered. "
                "Do not call register_player again.",
            )
            print(f"Resuming with saved player_id: {player_id}")

    async def after_run(self, *, context: SessionContext, **kwargs) -> None:
        pass  # player_id is saved from main() after agent.run() returns


async def main() -> None:
    client = OpenAIChatClient(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        model=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
    )

    game_mcp = MCPStreamableHTTPTool(
        name="Lost in Raleigh Game Server",
        url=MCP_SERVER_URL,
        description="MCP game server for the Lost in Raleigh workshop.",
    )
    await game_mcp.connect()

    memory = FileContextProvider()
    agent = Agent(
        client=client,
        name="RaleighAgent",
        instructions=(
            "You are a workshop participant in the Lost in Raleigh game. "
            "If you have a player_id in memory, confirm it and stop. "
            "If not, register as a new player with the name 'Workshop Attendee' "
            "using register_player and return a JSON object with: "
            "player_id, a2a_expert_url, stop1_location. Return ONLY valid JSON if registering."
        ),
        tools=[game_mcp],
        context_providers=[memory],
    )

    session = agent.create_session()
    response = await agent.run("Check my registration status.", session=session)
    print(response.text)

    # Save player_id (and quest data) if newly registered this run
    if not memory._load().get("player_id"):
        text = response.text or ""
        match = re.search(r"PLR-[A-Z0-9]{8}", text)
        if match:
            pid = match.group(0)
            save_data: dict = {"player_id": pid}
            # Try to extract quest data from JSON response
            json_match = re.search(r"\{.*\}", text, re.DOTALL)
            if json_match:
                try:
                    reg_data = json.loads(json_match.group(0))
                    if reg_data.get("a2a_expert_url"):
                        save_data["a2a_expert_url"] = reg_data["a2a_expert_url"]
                    if reg_data.get("stop1_location"):
                        save_data["stop1_location"] = reg_data["stop1_location"]
                except json.JSONDecodeError:
                    pass
            memory._save(save_data)
            print(f"Saved player_id: {pid}")

    await game_mcp.close()


if __name__ == "__main__":
    asyncio.run(main())
