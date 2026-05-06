---
title: "Step 3: Connect to the MCP Game Server"
description: Switch from raw API calls to Microsoft Agent Framework and connect to the quest game server via MCP.
---

# Step 3 — Connect to the MCP Game Server <Badge type="warning" text="~15 min" />

## The story so far

You know the model works. Now it's time to enter the game. The **Lost in Raleigh** game server manages players, quests, and scoring. Your agent will register with it using the **Model Context Protocol** (MCP) — the industry standard for connecting agents to external tools.

---

## What you'll learn

- What **MCP (Model Context Protocol)** is and why it exists
- How `MCPStreamableHTTPTool` exposes server tools to your agent
- How `Agent` wraps the model + tools into a reasoning loop
- How to register as a player and receive your quest assignment

---

## What is MCP?

MCP is an open standard (originally from Anthropic, now widely adopted) that lets any AI agent call any tool in a standardised way. Instead of writing custom HTTP client code for every API, you point your agent at an MCP server and it automatically discovers all available tools — their names, parameters, and descriptions.

**Why this is powerful:** Your agent doesn't just make API calls — it *reads the tool descriptions* and decides *which* tool to call, *when*, and with *what arguments*. You don't have to hardcode the logic. The model figures it out from the descriptions.

The game server exposes tools like:
- `register_player` — join the game and get assigned a quest
- `declare_transport_stop1` — record which transport you used to reach stop 1
- `submit_secret_code` — submit the code you found in the document bundle
- `declare_transport_final` — finish the quest and receive your score

---

## What is Microsoft Agent Framework?

The **Microsoft Agent Framework** (`agent_framework`) is an open-source Python library that wraps the OpenAI chat loop into a clean abstraction. Instead of manually:
1. Building the messages array
2. Calling the model
3. Parsing tool call requests out of the response
4. Calling the tool
5. Appending the result and calling the model again...

...you just write:

```python
response = await agent.run("My question", session=session)
```

The framework handles the tool-calling loop automatically. This is the **ReAct pattern** (Reason + Act) implemented for you.

---

## Write the code

Open `steps/step3_mcp_connect.py` and replace its contents with:

```python [steps/step3_mcp_connect.py]
import asyncio
import os

from agent_framework import Agent, MCPStreamableHTTPTool
from agent_framework.openai import OpenAIChatClient
from dotenv import load_dotenv

load_dotenv()

MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8000/mcp")


async def main() -> None:
    # 1. Create the model client
    client = OpenAIChatClient(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        model=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
    )

    # 2. Connect to the MCP game server
    game_mcp = MCPStreamableHTTPTool(
        name="Lost in Raleigh Game Server",
        url=MCP_SERVER_URL,
        description="MCP game server for the Lost in Raleigh workshop.",
    )
    await game_mcp.connect()

    # 3. Create the agent with MCP tools attached
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


asyncio.run(main())
```

### Why each block matters

**`OpenAIChatClient`** — wraps the Azure OpenAI endpoint. Think of it as the "brain" your agent uses. Swap this for a different client to use a different model provider.

**`MCPStreamableHTTPTool`** — connects to the game server and fetches its tool list. The agent can now "see" all the server's tools and call any of them. You don't need to write a single line of HTTP client code.

**`Agent(..., tools=[game_mcp])`** — creates the reasoning loop. The agent receives your message, thinks about what tools are available, calls the right one, and formulates a response.

**`agent.create_session()`** — creates a conversation context. The session holds the message history for this run. We'll explore sessions more in Step 6.

---

## Run it

```bash
python steps/step3_mcp_connect.py
```

::: tip Expected output
```
Your player_id is PLR-XXXXXXXX.
Quest: The Glenwood Getaway
Stop 1: Glenwood South
A2A Expert: https://a2a-expert.redriver-3b1b0600.eastus2.azurecontainerapps.io
```
Note your `player_id` — you'll need it in later steps.
:::

::: info Track your progress
Your registration appears on the admin dashboard immediately. Ask your facilitator for the dashboard URL — it's the `MCP_SERVER_URL` with `/mcp` replaced by `/admin`.
:::

::: details Stuck? Use the fallback
`steps/step3_mcp_connect.py` is already complete in the repo. Run it as-is.
:::

---

## What just happened?

Behind the scenes, your agent:
1. Connected to the MCP server and fetched the tool list
2. Read the description of `register_player` and understood its parameters
3. Called the tool with `name="Workshop Attendee"`
4. Received the response (player_id, quest, A2A URL)
5. Formatted a readable reply

All without you writing a single line of tool-calling logic.

::: info Next step
[Step 4 — Add Memory](step4) →
:::
