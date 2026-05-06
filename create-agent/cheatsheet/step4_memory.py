"""
Step 4 — Add FileContextProvider to persist your player_id between runs.

What this adds:
  - FileContextProvider: saves your player_id to a local JSON file (memory.json).
  - On the first run: registers you and saves the player_id.
  - On subsequent runs: loads the saved player_id — no second registration needed.

Run it twice to see memory in action:
  python cheatsheet/step4_memory.py

Expected output (first run):
  Registered! player_id = PLR-XXXXXXXX
  Saved to memory.json — run this script again to see memory in action.

Expected output (second run):
  Already registered: PLR-XXXXXXXX
"""
from __future__ import annotations

import asyncio
import os
import re

from agent_framework import Agent, MCPStreamableHTTPTool
from agent_framework.openai import OpenAIChatClient
from dotenv import load_dotenv

from shared import FileContextProvider

load_dotenv()

MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8000/mcp")


async def main() -> None:
    memory = FileContextProvider()
    saved = memory._load()

    # If we already have a player_id, there is nothing to do.
    if saved.get("player_id"):
        print(f"Already registered: {saved['player_id']}")
        return

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

    agent = Agent(
        client=client,
        name="RaleighAgent",
        instructions=(
            "Register as a new player named 'Workshop Attendee' using register_player. "
            "Reply with ONLY the player_id in the format PLR-XXXXXXXX — nothing else."
        ),
        tools=[game_mcp],
        context_providers=[memory],
    )

    session = agent.create_session()
    response = await agent.run("Register me as a new player.", session=session)

    match = re.search(r"PLR-[A-Z0-9]{8}", response.text or "")
    if match:
        memory._save({"player_id": match.group(0)})
        print(f"Registered! player_id = {match.group(0)}")
        print("Saved to memory.json — run this script again to see memory in action.")
    else:
        print(response.text)

    await game_mcp.close()


if __name__ == "__main__":
    asyncio.run(main())
