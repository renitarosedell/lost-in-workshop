---
title: "Step 8: Complete the Quest"
description: Declare your final transport choice and claim your score on the leaderboard.
---

# Step 8 - Complete the Quest <Badge type="tip" text="~5 min" />

## The story so far

You've found the secret code and submitted it. There's one last step: declare how you're getting to the **NC Biotech Center** - the final destination. Once you do, the game server calculates your score and posts it to the leaderboard.

---

## What you'll learn

- How the quest scoring formula works
- How to make a final tool call that closes the loop

---

## Write the code

Create a new file `create-agent/my_step8.py` and paste in:

```python [my_step8.py]
import asyncio
import os

from agent_framework import Agent, MCPStreamableHTTPTool
from agent_framework.openai import OpenAIChatClient
from dotenv import load_dotenv

from shared import FileContextProvider

load_dotenv()

MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8000/mcp")

_FALLBACK_TRANSPORT = "rideshare"


async def main() -> None:
    memory = FileContextProvider()
    saved = memory._load()

    player_id = saved.get("player_id")
    if not player_id:
        print("No player_id found. Run step4_memory.py first.")
        return

    transport_final = saved.get("transport_final", _FALLBACK_TRANSPORT)
    print(f"Player: {player_id}")
    print(f"Declaring final transport: {transport_final}")

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
            f"Call declare_transport_final with player_id='{player_id}' and "
            f"transport='{transport_final}'. Print the final score and the quest "
            "completion message from the response."
        ),
        tools=[game_mcp],
    )
    session = agent.create_session()
    response = await agent.run("Complete the quest.", session=session)
    print(f"\n{response.text}")

    await game_mcp.close()


asyncio.run(main())
```

---

## Run it

```bash
python my_step8.py
```

::: tip Expected output
```
Player: PLR-A1B2C3D4
Declaring final transport: rideshare

Quest complete! Final score: 920
Well done, Workshop Attendee! You navigated Raleigh like a local.
```
:::

::: details Stuck? Use the fallback
`cheatsheet/step8_final.py` contains the complete working solution. Run it with `python cheatsheet/step8_final.py`.
:::

---

## How scoring works

$$\text{score} = \max\!\left(0,\ 1000 - (50 \times \text{failed\_code\_attempts}) - (10 \times \text{minutes\_taken})\right)$$

| Factor | Effect |
|---|---|
| Getting the code right first time | No penalty - full 1000 minus time |
| Each failed code attempt | −50 points |
| Each minute of elapsed time | −10 points |

**A perfect score is 1000.** The fastest player with zero failed attempts wins. Speed matters - but not as much as accuracy.

---

## You did it!

Your agent is on the leaderboard. Ask your facilitator for the dashboard URL to see your ranking.

### What you built - the complete picture

| Step | Concept | Technology |
|---|---|---|
| 1 | Azure OpenAI connectivity | `openai` SDK, `AzureOpenAI` |
| 2 | System prompts & chat completions | Role-based messages |
| 3 | Tool-calling via MCP | `MCPStreamableHTTPTool`, `Agent` |
| 4 | Persistent memory | `ContextProvider`, `FileContextProvider` |
| 5 | Agent-to-Agent communication | `A2AAgent`, `A2ACardResolver` |
| 6 | Multi-turn sessions | `agent.create_session()` |
| 7 | Multi-agent orchestration | Sequential A2A pipeline |
| 8 | Quest completion | `declare_transport_final` |

---

## Want to go further?

See [Bonus Exercises](bonus-exercises) for four additional challenges:

- **A** - Build your own A2A transport expert
- **B** - Add streaming responses
- **C** - Multi-agent orchestration with a Planner + Runner pattern
- **D** - Eval harness: run the quest multiple times and compare scores
