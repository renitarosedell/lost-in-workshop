"""
Step 6 — Multi-turn conversations: use session memory to declare transport.

What this adds (tutorial: Step 3 — Multi-Turn Conversations):
  A single agent session is kept alive across two turns:
    Turn 1 — ask the agent to summarise the transport choice from step 5.
    Turn 2 — tell it to call declare_transport_stop1 with that choice.

  Because both turns share the same session, the agent remembers the transport
  from turn 1 when executing the tool call in turn 2. Without a session each
  turn would start from scratch and the agent would have no context.

  The response includes the next stop and the bundle URL, both saved to memory
  for step 7.

Run it:
  python steps/step6_transport.py

Expected output:
  Player: PLR-XXXXXXXX  |  Transport: rideshare

  [Turn 1] Summarising transport choice...
  Agent: You have chosen rideshare to reach Glenwood South...

  [Turn 2] Declaring transport and collecting next stop...
  Stop 1 reached!
  Next stop: Cameron Village
  Saved stop2_location and bundle_url to memory.
"""
from __future__ import annotations

import asyncio
import json
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
            f"You are helping player_id='{player_id}' play the Lost in Raleigh quest. "
            "When asked to declare transport, call declare_transport_stop1 with the "
            "player_id and the transport the player chose. Return the full JSON "
            "response from the tool as-is."
        ),
        tools=[game_mcp],
    )

    # A single session spans both turns — the agent remembers turn 1 in turn 2.
    session = agent.create_session()

    # Turn 1: establish context (no tool call yet)
    print("[Turn 1] Summarising transport choice...")
    turn1 = await agent.run(
        f"My transport choice for stop 1 is: {transport}. "
        "Confirm what I have chosen in one sentence.",
        session=session,
    )
    print(f"Agent: {turn1.text}\n")

    # Turn 2: agent still has turn 1 in its context — uses it to call the tool
    print("[Turn 2] Declaring transport and collecting next stop...")
    turn2 = await agent.run(
        "Now declare my transport to stop 1 using the choice I just told you.",
        session=session,
    )

    text = turn2.text or ""
    json_match = re.search(r"\{.*\}", text, re.DOTALL)
    if json_match:
        data = json.loads(json_match.group(0))
        stop2 = data.get("stop2_location", "")
        bundle_url = data.get("document_bundle_url", "")
        print("Stop 1 reached!")
        if stop2:
            print(f"Next stop: {stop2}")
            memory._save({"stop2_location": stop2})
        if bundle_url:
            memory._save({"bundle_url": bundle_url})
            print("Saved stop2_location and bundle_url to memory.")
        else:
            print("Warning: no document_bundle_url in response.")
            print(text)
    else:
        print(text)

    await game_mcp.close()


if __name__ == "__main__":
    asyncio.run(main())
