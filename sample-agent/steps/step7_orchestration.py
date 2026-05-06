"""
Step 7 — Orchestration: query two A2A agents in sequence, then submit the code.

What this adds (tutorial: Step 5 — Workflows / multi-agent orchestration):
  Two remote A2A agents are called in sequence — a real multi-agent workflow:

  1. Transport Expert  → advises on the final leg (stop 2 → NC Biotech Center).
  2. City Guide        → knows the neighbourhood history + the quest reference code.

  The reference code extracted from the city guide's response is then submitted
  to the MCP game server via a local Agent with tool-calling. The chosen final
  transport is saved to memory so step 8 can use it without re-asking.

Install the A2A package first:
  pip install agent-framework-a2a --pre

Run it:
  python steps/step7_orchestration.py

Expected output:
  Player: PLR-XXXXXXXX
  --- Transport Expert: final leg ---
    Connected to: Raleigh Transport Expert
  Rideshare is your fastest option from Cameron Village to RTP...
  Final transport chosen: rideshare

  --- City Guide: quest reference code ---
    Connected to: Raleigh City Guide
  Cameron Village is one of the first planned shopping centres...
  Archivist reference code for quest players: GLENWOOD42

  Extracted code: GLENWOOD42

  --- Submitting code via MCP ---
  Code accepted! Attempts: 1

  Saved transport_final=rideshare to memory.
"""
from __future__ import annotations

import asyncio
import os
import re

import httpx
from a2a.client import A2ACardResolver
from agent_framework import Agent, MCPStreamableHTTPTool
from agent_framework.a2a import A2AAgent
from agent_framework.openai import OpenAIChatClient
from dotenv import load_dotenv

from shared import FileContextProvider

load_dotenv()

MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8000/mcp")


async def call_a2a(url: str, message: str) -> str:
    """Discover an A2A agent via its AgentCard and send it one message."""
    async with httpx.AsyncClient(timeout=30.0) as http_client:
        resolver = A2ACardResolver(httpx_client=http_client, base_url=url)
        agent_card = await resolver.get_agent_card()
        print(f"  Connected to: {agent_card.name}")
    async with A2AAgent(name=agent_card.name, agent_card=agent_card, url=url) as agent:
        response = await agent.run(message)
    return "\n".join(m.text for m in response.messages if m.text)


async def main() -> None:
    memory = FileContextProvider()
    saved = memory._load()

    player_id = saved.get("player_id")
    stop2_location = saved.get("stop2_location", "your next stop")

    # Env vars take priority over stale memory values
    transport_url = os.environ.get("A2A_SERVER_URL") or saved.get("a2a_expert_url")
    city_guide_url = os.environ.get("CITY_GUIDE_URL")

    if not player_id:
        print("No player_id found. Run step4_memory.py first.")
        return
    if not transport_url or not city_guide_url:
        print("Missing A2A URLs. Set A2A_SERVER_URL and CITY_GUIDE_URL in .env")
        return

    print(f"Player: {player_id}")
    print(f"Stop 2:  {stop2_location}\n")

    # ------------------------------------------------------------------
    # 1. Transport Expert — best route for the final leg
    # ------------------------------------------------------------------
    print("--- Transport Expert: final leg ---")
    transport_advice = await call_a2a(
        transport_url,
        f"What is the fastest way to get from {stop2_location} to the "
        "NC Biotech Center in Research Triangle Park?",
    )
    print(transport_advice)

    transport_final = "rideshare"
    for tid, kw in [
        ("goTriangle", "gotriangle"),
        ("goTriangle", "triangle"),
        ("goRaleigh_bus", "goraleigh"),
        ("goRaleigh_bus", "bus"),
        ("bike", "bike"),
        ("walk", "walk"),
        ("rideshare", "rideshare"),
        ("rideshare", "uber"),
        ("rideshare", "lyft"),
    ]:
        if kw in transport_advice.lower():
            transport_final = tid
            break

    print(f"\nFinal transport chosen: {transport_final}")

    # ------------------------------------------------------------------
    # 2. City Guide — neighbourhood history + quest reference code
    # ------------------------------------------------------------------
    print("\n--- City Guide: quest reference code ---")
    city_guide_response = await call_a2a(
        city_guide_url,
        f"I'm on a quest at {stop2_location}. Tell me about this neighbourhood "
        "and share the archivist's reference code for it.",
    )
    print(city_guide_response)

    # Extract the reference code — uppercase alphanumeric word, 6+ characters
    code_match = re.search(r"\b([A-Z][A-Z0-9]{5,})\b", city_guide_response)
    if not code_match:
        print(
            "\nCould not extract a reference code from the city guide response. "
            "Check the output above and run again."
        )
        return

    secret_code = code_match.group(1)
    print(f"\nExtracted code: {secret_code}")

    # ------------------------------------------------------------------
    # 3. Submit the code via MCP
    # ------------------------------------------------------------------
    print("\n--- Submitting code via MCP ---")
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
            f"Call submit_secret_code with player_id='{player_id}' and "
            f"code='{secret_code}'. Report whether the code was accepted."
        ),
        tools=[game_mcp],
    )
    session = agent.create_session()
    response = await agent.run("Submit the secret code.", session=session)
    print(f"\n{response.text}")
    await game_mcp.close()

    # Save for step 8
    memory._save({"transport_final": transport_final})
    print(f"\nSaved transport_final={transport_final} to memory.")


if __name__ == "__main__":
    asyncio.run(main())
