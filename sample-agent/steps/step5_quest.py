"""
Step 5 — A2A: Discover and query the Raleigh transport expert.

What this adds:
  - agent-framework-a2a: use A2AAgent to call a remote agent via the A2A protocol.
  - A2ACardResolver: discover the remote agent's capabilities via its AgentCard.
  - Reads player_id, a2a_expert_url, stop1_location from memory (saved in step 4).
  - Saves transport_stop1 to memory for step 6.

Install the A2A package first:
  pip install agent-framework-a2a --pre

Run it:
  python steps/step5_quest.py

Expected output:
  Player: PLR-XXXXXXXX
  Connecting to A2A expert at: https://...
  Remote agent: Raleigh Transport Expert
  A2A advice: Rideshare is your fastest option at around 8 minutes...
  Transport chosen: rideshare
  Saved transport_stop1 to memory.
"""
from __future__ import annotations

import asyncio
import os

import httpx
from a2a.client import A2ACardResolver
from agent_framework.a2a import A2AAgent
from dotenv import load_dotenv

from shared import FileContextProvider

load_dotenv()


async def main() -> None:
    memory = FileContextProvider()
    saved = memory._load()

    player_id = saved.get("player_id")
    a2a_url = saved.get("a2a_expert_url") or os.environ.get("A2A_SERVER_URL")
    stop1_location = saved.get("stop1_location", "your quest destination")

    if not player_id or not a2a_url:
        print("No registration found in memory. Run step4_memory.py first.")
        return

    print(f"Player: {player_id}")
    print(f"Connecting to A2A expert at: {a2a_url}")

    # 1. Discover the remote agent's capabilities via its AgentCard
    async with httpx.AsyncClient(timeout=30.0) as http_client:
        resolver = A2ACardResolver(httpx_client=http_client, base_url=a2a_url)
        agent_card = await resolver.get_agent_card()
        print(f"Remote agent: {agent_card.name}")

    # 2. Send a transport question to the A2A expert
    async with A2AAgent(
        name=agent_card.name,
        agent_card=agent_card,
        url=a2a_url,
    ) as agent:
        response = await agent.run(
            f"What is the fastest way to get to {stop1_location} from the city centre?"
        )

    advice = "\n".join(m.text for m in response.messages if m.text)
    print(f"\nA2A advice:\n{advice}\n")

    # 3. Pick a transport mode from the advice text
    transport = "rideshare"  # sensible default
    for transport_id, keyword in [
        ("goRaleigh_bus", "goraleigh"),
        ("goRaleigh_bus", "bus"),
        ("bike", "bike"),
        ("walk", "walk"),
        ("rideshare", "rideshare"),
        ("rideshare", "uber"),
        ("rideshare", "lyft"),
    ]:
        if keyword in advice.lower():
            transport = transport_id
            break

    print(f"Transport chosen: {transport}")
    memory._save({"transport_stop1": transport})
    print("Saved transport_stop1 to memory.")


if __name__ == "__main__":
    asyncio.run(main())
