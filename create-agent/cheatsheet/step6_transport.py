"""
Step 6 — Multi-turn conversations: use session memory to declare transport.

What this adds:
  A single agent session is kept alive across two turns:
    Turn 1 — ask the agent to confirm the transport choice from step 5.
    Turn 2 — tell it to call declare_transport_stop1 with that choice.

  Because both turns share the same session, the agent remembers turn 1 when
  executing the tool call in turn 2. Without a session, each turn would start
  fresh and the agent would have no context about what transport was chosen.

Run it:
  python cheatsheet/step6_transport.py

Expected output:
  Player: PLR-XXXXXXXX  |  Transport: rideshare

  [Turn 1] Confirming transport choice...
  Agent: You have chosen rideshare to reach Glenwood South...

  [Turn 2] Declaring transport and collecting next stop...
  Stop 1 reached!
  Next stop: Cameron Village
  Saved stop2_location to memory.
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import re

from agent_framework import Agent, MCPStreamableHTTPTool
from agent_framework.openai import OpenAIChatClient
from dotenv import load_dotenv

from shared import FileContextProvider, get_base_endpoint

load_dotenv()

MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8000/mcp")


async def main() -> None:
    memory = FileContextProvider()
    saved = memory._load()

    player_id = saved.get("player_id")
    transport = saved.get("transport_stop1")

    if not player_id:
        print("No player_id found. Run step4_memory.py first.")
        return
    if not transport:
        print("No transport_stop1 found. Run step5_quest.py first.")
        return

    print(f"Player: {player_id}  |  Transport: {transport}\n")

    client = OpenAIChatClient(
        azure_endpoint=get_base_endpoint(),
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
            f"You are helping player_id='{player_id}' play the Lost in Raleigh quest. "
            "When asked to declare transport, call declare_transport_stop1 with the "
            "player_id and transport. Return the full JSON response from the tool."
        ),
        tools=[game_mcp],
    )

    # A single session spans both turns — the agent remembers what is said turn 1 in turn 2.
    session = agent.create_session()

    # Turn 1: establish context (no tool call yet)
    print("[Turn 1] Confirming transport choice...")
    turn1 = await agent.run(
        f"My transport choice for stop 1 is: {transport}. Confirm in one sentence.",
        session=session,
    )
    print(f"Agent: {turn1.text}\n")

    # Turn 2: agent uses turn 1 context to call the right tool with the right value
    print("[Turn 2] Declaring transport and collecting next stop...")
    turn2 = await agent.run(
        "Now declare my transport to stop 1 using the choice I just told you.",
        session=session,
    )
    print(turn2.text or "")

    # Extract next stop from the response for step 7
    text = turn2.text or ""
    stop2_match = re.search(r'"stop2_location"\s*:\s*"([^"]+)"', text)
    if stop2_match:
        stop2 = stop2_match.group(1)
        memory._save({"stop2_location": stop2})
        print(f"\nNext stop: {stop2}")
        print("Saved stop2_location to memory.")
    else:
        print("\n[FAILED] Could not parse stop2_location from the agent response.")
        print("The agent paraphrased the tool output instead of returning the raw JSON.")
        print("Fix: update the agent instructions to say something like:")
        print("  'Return the COMPLETE raw JSON response from the tool, do not summarise it.'")
        print("Then re-run this script.")

    await game_mcp.close()


if __name__ == "__main__":
    asyncio.run(main())
