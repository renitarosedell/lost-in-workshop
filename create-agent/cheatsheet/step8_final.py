"""
Step 8 — Declare final transport and complete the quest.

What this adds:
  - Calls declare_transport_final to record the last leg of the journey.
  - Reads transport_final from memory (saved by step7_orchestration.py).
  - Prints the final score and quest completion message.

Run it:
  python cheatsheet/step8_final.py

Expected output:
  Player: PLR-XXXXXXXX
  Quest complete! Final score: 920
  Well done, Workshop Attendee!
"""
from __future__ import annotations

import asyncio
import os

from agent_framework import Agent, MCPStreamableHTTPTool
from agent_framework.openai import OpenAIChatClient
from dotenv import load_dotenv

from shared import FileContextProvider

load_dotenv()

MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8000/mcp")

# Fallback transport if step7_orchestration.py hasn't been run
_FALLBACK_TRANSPORT = "rideshare"


async def main() -> None:
    memory = FileContextProvider()
    saved = memory._load()

    player_id = saved.get("player_id")
    if not player_id:
        print("No player_id found. Run step4_memory.py first.")
        return

    # Use transport chosen by the city guide orchestration (step 7), or fallback
    transport_final = saved.get("transport_final", _FALLBACK_TRANSPORT)
    print(f"Player: {player_id}")
    print(f"Declaring final transport: {transport_final}")

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
            f"Call declare_transport_final with player_id='{player_id}' and "
            f"transport='{transport_final}'. Print the final score and the quest "
            "completion message from the response."
        ),
        tools=[game_mcp],
    )
    session = agent.create_session()
    response = await agent.run("Complete the quest.", session=session)
    print(f"\n{response.text}")

    await game_mcp.close()


if __name__ == "__main__":
    asyncio.run(main())
