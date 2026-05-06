"""
Step 7 — Orchestration: a @workflow that calls two A2A agents then submits the code.

What this adds:
  Three stages wrapped in a @workflow function — a structured multi-agent pipeline:

  1. Transport Expert (A2A) → advises on the final leg (stop 2 → NC Biotech Center).
  2. City Guide (A2A)       → neighbourhood history + the quest reference code.
  3. Submit agent (MCP)     → submits the extracted code to the game server.

  The @workflow decorator turns a plain async function into a tracked pipeline.
  Inside the workflow, agents are called exactly like normal Python async functions —
  no special wrappers needed. Agents are created at module level (outside the workflow)
  and captured via closure, just like the framework sample 05.

Install the A2A package first:
  pip install agent-framework-a2a --pre

Run it:
  python cheatsheet/step7_orchestration.py

Expected output:
  Player: PLR-XXXXXXXX

  --- Stage 1: Transport Expert ---
    Connected to: Raleigh Transport Expert
  Rideshare is your fastest option from Cameron Village to RTP...
  Final transport chosen: rideshare

  --- Stage 2: City Guide ---
    Connected to: Raleigh City Guide
  Cameron Village is one of the first planned shopping centres...
  Extracted code: CAMERON99

  --- Stage 3: Submit code ---
  Code accepted! Attempts: 1

  Workflow state: WorkflowRunState.IDLE
  Saved transport_final=rideshare to memory.
"""
from __future__ import annotations

import asyncio
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from a2a.client import A2ACardResolver
from agent_framework import Agent, MCPStreamableHTTPTool, workflow
from agent_framework.a2a import A2AAgent
from agent_framework.openai import OpenAIChatClient
from dotenv import load_dotenv

from shared import FileContextProvider, get_base_endpoint

load_dotenv()

MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8000/mcp")
A2A_SERVER_URL = os.environ.get("A2A_SERVER_URL", "")
CITY_GUIDE_URL = os.environ.get("CITY_GUIDE_URL", "")

# -------------------------------------------------------------------
# Agents created at module level — available to the workflow via closure.
# This mirrors the framework sample: create agents once, call them many times.
# -------------------------------------------------------------------
client = OpenAIChatClient(
    azure_endpoint=get_base_endpoint(),
    api_key=os.environ.get("AZURE_OPENAI_API_KEY", ""),
    model=os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", ""),
)
game_mcp = MCPStreamableHTTPTool(
    name="Lost in Raleigh Game Server",
    url=MCP_SERVER_URL,
    description="MCP game server for the Lost in Raleigh workshop.",
)
submit_agent = Agent(
    client=client,
    name="RaleighAgent",
    instructions=(
        "You are a game assistant. When asked to submit a code, "
        "call submit_secret_code with the provided player_id and code. "
        "Report whether it was accepted."
    ),
    tools=[game_mcp],
)


async def call_a2a(url: str, message: str) -> str:
    """Discover an A2A agent via its AgentCard and send it one message."""
    async with httpx.AsyncClient(timeout=30.0) as http_client:
        resolver = A2ACardResolver(httpx_client=http_client, base_url=url)
        agent_card = await resolver.get_agent_card()
        print(f"  Connected to: {agent_card.name}")
    async with A2AAgent(name=agent_card.name, agent_card=agent_card, url=url) as agent:
        response = await agent.run(message)
    return "\n".join(m.text for m in response.messages if m.text)


# -------------------------------------------------------------------
# The workflow — three stages as plain async Python.
# @workflow turns this into a tracked, structured pipeline.
# Inside: call agents (or any async function) exactly like normal Python.
# -------------------------------------------------------------------
@workflow
async def quest_workflow(inputs: dict) -> tuple[str, str]:
    """Three-stage pipeline: transport → city guide → submit code.

    Accepts a single dict with keys 'player_id' and 'stop2_location'.
    Returns (submit_result, transport_final).
    """
    player_id: str = inputs["player_id"]
    stop2_location: str = inputs["stop2_location"]
    # Stage 1: Transport Expert — best route for the final leg
    print("--- Stage 1: Transport Expert ---")
    transport_advice = await call_a2a(
        A2A_SERVER_URL,
        f"What is the fastest way to get from {stop2_location} to the NC Biotech Center?",
    )
    print(transport_advice)

    transport_final = "rideshare"
    for transport_id, keyword in [
        ("goTriangle", "gotriangle"),
        ("goRaleigh_bus", "bus"),
        ("bike", "bike"),
        ("walk", "walk"),
        ("rideshare", "rideshare"),
    ]:
        if keyword in transport_advice.lower():
            transport_final = transport_id
            break
    print(f"\nFinal transport chosen: {transport_final}")

    # Stage 2: City Guide — neighbourhood history + quest reference code
    print("\n--- Stage 2: City Guide ---")
    city_guide_response = await call_a2a(
        CITY_GUIDE_URL,
        f"I'm on a quest at {stop2_location}. Tell me about this neighbourhood "
        "and share the archivist's reference code for it.",
    )
    print(city_guide_response)

    code_match = re.search(r"\b([A-Z][A-Z0-9]{5,})\b", city_guide_response)
    if not code_match:
        return "[FAILED] Could not extract a reference code.", transport_final
    secret_code = code_match.group(1)
    print(f"\nExtracted code: {secret_code}")

    # Stage 3: Submit the code — call submit_agent just like a plain async function
    print("\n--- Stage 3: Submit code ---")
    submit_result = (
        await submit_agent.run(f"Submit code='{secret_code}' for player_id='{player_id}'.")
    ).text or "[no response]"

    return submit_result, transport_final


async def main() -> None:
    memory = FileContextProvider()
    saved = memory._load()

    player_id = saved.get("player_id")
    stop2_location = saved.get("stop2_location", "Cameron Village")

    if not player_id:
        print("No player_id found. Run step4_memory.py first.")
        return
    if not A2A_SERVER_URL or not CITY_GUIDE_URL:
        print("Missing A2A URLs. Set A2A_SERVER_URL and CITY_GUIDE_URL in .env")
        return

    print(f"Player: {player_id}\n")

    # Connect MCP before the workflow runs so submit_agent can use game_mcp
    await game_mcp.connect()

    # Run the workflow — same as calling any async function, but tracked
    result = await quest_workflow.run({"player_id": player_id, "stop2_location": stop2_location})

    submit_result, transport_final = result.get_outputs()[0]
    print(f"\n{submit_result}")
    print(f"Workflow state: {result.get_final_state()}")

    await game_mcp.close()

    memory._save({"transport_final": transport_final})
    print(f"\nSaved transport_final={transport_final} to memory.")


if __name__ == "__main__":
    asyncio.run(main())
