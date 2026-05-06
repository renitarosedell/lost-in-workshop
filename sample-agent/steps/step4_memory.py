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

from agent_framework import Agent, MCPStreamableHTTPTool
from agent_framework.openai import OpenAIChatClient
from dotenv import load_dotenv

from shared import FileContextProvider, MEMORY_FILE

load_dotenv()

MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8000/mcp")


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
    saved = memory._load()
    if saved.get("player_id"):
        print(f"Resuming with saved player_id: {saved['player_id']}")

    agent = Agent(
        client=client,
        name="RaleighAgent",
        instructions=(
            "You are a workshop participant in the Lost in Raleigh game. "
            "If your player_id is already in memory, confirm it and stop — "
            "do NOT call register_player again. "
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
