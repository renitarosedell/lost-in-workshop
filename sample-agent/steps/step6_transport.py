"""
Step 6 — Declare transport to stop 1 and receive the document bundle URL.

What this adds:
  - Calls declare_transport_stop1 on the MCP game server.
  - Uses player_id (step 4) and transport_stop1 (step 5) from memory.
  - Saves document_bundle_url to memory for step 7.

Run it:
  python steps/step6_transport.py

Expected output:
  Player: PLR-XXXXXXXX  |  Transport: rideshare
  Stop 1 reached!
  Next stop: NC Museum of Natural Sciences
  Bundle URL: https://lostworkshop.blob.core.windows.net/bundles/...
  Saved bundle_url to memory.
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

    print(f"Player: {player_id}  |  Transport: {transport}")

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
            f"Call declare_transport_stop1 with player_id='{player_id}' and "
            f"transport='{transport}'. Return the full JSON response from the tool. "
            "Return ONLY valid JSON, no extra text."
        ),
        tools=[game_mcp],
    )
    session = agent.create_session()
    response = await agent.run("Declare my transport to stop 1.", session=session)

    text = response.text or ""
    json_match = re.search(r"\{.*\}", text, re.DOTALL)
    if json_match:
        data = json.loads(json_match.group(0))
        bundle_url = data.get("document_bundle_url", "")
        stop2 = data.get("stop2_location", "")
        print("\nStop 1 reached!")
        if stop2:
            print(f"Next stop: {stop2}")
        if bundle_url:
            print(f"Bundle URL: {bundle_url}")
            memory._save({"bundle_url": bundle_url})
            print("Saved bundle_url to memory.")
        else:
            print("Warning: no document_bundle_url in response.")
            print(text)
    else:
        print(text)

    await game_mcp.close()


if __name__ == "__main__":
    asyncio.run(main())
