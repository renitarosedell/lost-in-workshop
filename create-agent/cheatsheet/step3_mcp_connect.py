"""
Step 3 — Connect to the MCP game server and register as a player.

What this adds:
  - MCPStreamableHTTPTool: connects your agent to the Lost in Raleigh game server.
  - register_player: registers you with the server and assigns you a quest.
  - Prints your player_id and quest details.

Run it:
  python cheatsheet/step3_mcp_connect.py

Expected output:
  Registered! player_id = PLR-XXXXXXXX
  Quest: The Glenwood Getaway
  A2A expert URL: https://<host>/a2a
  ...
"""
import asyncio
import os

from agent_framework import Agent, MCPStreamableHTTPTool
from agent_framework.openai import OpenAIChatClient
from dotenv import load_dotenv

from shared import get_base_endpoint

load_dotenv()

MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8000/mcp")


async def main() -> None:
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
            "You are a workshop participant in the Lost in Raleigh game. "
            "Register as a new player with the name 'Workshop Attendee', "
            "then print the player_id, quest name, and A2A expert URL exactly "
            "as returned by register_player. Do not start the quest yet."
        ),
        tools=[game_mcp],
    )

    session = agent.create_session()
    response = await agent.run("Register me as a new player.", session=session)
    print(response.text)

    await game_mcp.close()


if __name__ == "__main__":
    asyncio.run(main())
