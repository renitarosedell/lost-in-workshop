---
title: "Step 4: Add Memory"
description: Use a ContextProvider to persist your player_id across runs so you never register twice.
---

# Step 4 - Add Memory <Badge type="tip" text="~10 min" />

## The story so far

You're registered and have your player ID. But if you restart the script, it would register you *again*, and you'd get a different player ID. Agents are stateless by default. This step fixes that.

---

## What you'll learn

- Why agents are stateless and what problems that causes
- What a `ContextProvider` is and how it hooks into the agent lifecycle
- How `FileContextProvider` saves state to disk and injects it back into future runs

---

## Why agents are stateless

Every time `Agent.run()` is called, it starts with a fresh context: just the `instructions` and the current message. There is no built-in persistence. This is intentional, as statelessness makes agents simple, composable, and easy to test.

But real workflows need state. You need to know:
- Who you are (`player_id`)
- What you've already done (which stops you've visited)
- What you've saved (secret codes, transport choices)

The solution is a **ContextProvider**, a hook that runs *before* and *after* each agent call to inject or extract state.

---

## How ContextProvider works

```
                    ┌─────────────────────────────┐
                    │         Agent.run()         │
                    └─────────────────────────────┘
                            │           │
                    before_run()    after_run()
                            │           │
                    ┌───────▼───────────▼───────┐
                    │    FileContextProvider     │
                    │    (reads/writes .json)    │
                    └───────────────────────────┘
```

`before_run()` is called *before* the model sees your message. It can add extra text to the agent's instructions, for example: `"Your player_id is PLR-XXXXXXXX. Use it for all tool calls."`.

`after_run()` is called *after* the model finishes. It can inspect the response and save any new information.

The `FileContextProvider` in `shared.py` implements this pattern using a local `memory.json` file.

---

## Write the code

The `FileContextProvider` is already defined in `cheatsheet/shared.py`. You just need to use it in your agent.

Create a new file `create-agent/my_step4.py` and paste in:

```python [my_step4.py]
import asyncio
import os
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

    # If we already have a player_id, there is nothing to do.
    if saved.get("player_id"):
        print(f"Already registered: {saved['player_id']}")
        return

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
            "Register as a new player named 'Workshop Attendee' using register_player. "
            "Reply with ONLY the player_id in the format PLR-XXXXXXXX - nothing else."
        ),
        tools=[game_mcp],
        context_providers=[memory],     # <-- the only new line
    )

    session = agent.create_session()
    response = await agent.run("Register me as a new player.", session=session)

    match = re.search(r"PLR-[A-Z0-9]{8}", response.text or "")
    if match:
        memory._save({"player_id": match.group(0)})
        print(f"Registered! player_id = {match.group(0)}")
        print("Saved to memory.json - run this script again to see memory in action.")
    else:
        print(response.text)

    await game_mcp.close()


asyncio.run(main())
```

### The only new line

```python
context_providers=[memory],
```

This single addition wires the `FileContextProvider` into the agent lifecycle. On the second run, `before_run()` injects the saved `player_id` into the instructions, so the agent knows it's already registered and won't call `register_player` again.

---

## Run it twice

```bash
# First run - registers you
python steps/step4_memory.py

# Second run - uses memory.json
python steps/step4_memory.py
```

::: tip Expected output - first run
```
Registered! player_id = PLR-A1B2C3D4
Saved to memory.json - run this script again to see memory in action.
```
:::

::: tip Expected output - second run
```
Already registered: PLR-A1B2C3D4
```
No second registration. Your `player_id` is safe across restarts.
:::

::: details Stuck? Use the fallback
`cheatsheet/step4_memory.py` contains the complete working solution. Run it with `python cheatsheet/step4_memory.py`.
:::

---

## What's in memory.json?

After the first run, open `create-agent/memory.json`:

```json
{
  "player_id": "PLR-A1B2C3D4"
}
```

Later steps will add more keys to this file, like `transport_stop1`, `stop2_location`, and `transport_final`, building up a complete record of your quest progress.

::: info Next step
[Step 5 - A2A: Consult the Transport Expert](step5) →
:::
