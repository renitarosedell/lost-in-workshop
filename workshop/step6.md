---
title: "Step 6: Multi-turn Conversations"
description: Use a shared session to declare your transport choice across two conversational turns.
---

# Step 6 - Multi-turn Conversations <Badge type="tip" text="~10 min" />

## The story so far

You've picked your transport to stop 1. Now you need to officially declare it to the game server using the `declare_transport_stop1` tool. But you'll do it in a specific way: across **two conversational turns**, to learn how sessions carry context between calls.

---

## What you'll learn

- What a **session** is and why it exists
- How context flows from one turn to the next within a session
- Why multi-turn conversations unlock more reliable agent behaviour
- How the server responds with your next stop location

---

## What is a session?

When you call `agent.create_session()`, you get an object that holds the **message history** for a conversation. Every time you call `agent.run(..., session=session)`, that run appends to the same history.

```
Turn 1                          Turn 2
──────                          ──────
[system: instructions]          [system: instructions]
[user: "My transport is..."]    [user: "My transport is..."]
[assistant: "You chose..."]     [assistant: "You chose..."]
                                [user: "Now declare it"]
                                [assistant: → calls declare_transport_stop1]
```

Without a session, Turn 2 would start with only `[system]` and the new `[user]` message. The agent would have no idea what transport you chose in Turn 1.

**With** a session, Turn 2 sees the full history. When you say "using the choice I just told you", the agent knows exactly what that means.

---

## Why use two turns here?

You could collapse this into a single turn:

```python
await agent.run(f"Declare transport={transport} for player {player_id}.", session=session)
```

But the two-turn pattern is more realistic for real applications:
1. **Turn 1**: establish context or let the user confirm something
2. **Turn 2**: take action based on that confirmed context

This mirrors how users actually interact with AI assistants: they say something, get confirmation, then say "yes, do it". The session makes that workflow work.

---

## Write the code

Create a new file `create-agent/my_step6.py` and paste in:

```python [my_step6.py]
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
            "player_id and transport. Return the full JSON response from the tool."
        ),
        tools=[game_mcp],
    )

    # A single session spans both turns - the agent remembers turn 1 in turn 2.
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
    stop2_match = re.search(r'"stop2_location"\s*:\s*"([^"]+)"', turn2.text or "")
    if stop2_match:
        stop2 = stop2_match.group(1)
        memory._save({"stop2_location": stop2})
        print(f"\nNext stop: {stop2}")
        print("Saved stop2_location to memory.")

    await game_mcp.close()


asyncio.run(main())
```

### The key moment

```python
# Same session object used for both turns
session = agent.create_session()

turn1 = await agent.run("My transport choice is: rideshare. Confirm.", session=session)
turn2 = await agent.run("Now declare it.", session=session)  # knows from turn 1!
```

Without `session=session` on turn 2, the agent would ask "declare what?", as it would have no context. With the shared session, it knows exactly what to declare.

---

## Run it

```bash
python my_step6.py
```

::: tip Expected output
```
Player: PLR-A1B2C3D4  |  Transport: rideshare

[Turn 1] Confirming transport choice...
Agent: You have chosen rideshare to reach your first stop.

[Turn 2] Declaring transport and collecting next stop...
{"status": "ok", "stop2_location": "Cameron Village", ...}

Next stop: Cameron Village
Saved stop2_location to memory.
```
:::

::: details Stuck? Use the fallback
`cheatsheet/step6_transport.py` contains the complete working solution. Run it with `python cheatsheet/step6_transport.py`.
:::

---

## What's in memory.json now?

```json
{
  "player_id": "PLR-A1B2C3D4",
  "transport_stop1": "rideshare",
  "stop2_location": "Cameron Village"
}
```

The quest is progressing. Next you'll coordinate two specialist agents to gather the information you need to complete it.

::: info Next step
[Step 7 - Orchestration](step7) →
:::
