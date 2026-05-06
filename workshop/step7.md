---
title: "Step 7: Orchestration"
description: Coordinate two specialist A2A agents inside a @workflow pipeline, then submit the secret code to the game server.
---

# Step 7 - Orchestration <Badge type="warning" text="~20 min" />

## The story so far

You've reached stop 1 and the game server has unlocked stop 2. To progress, you need to:
1. Figure out how to get from stop 2 to the NC Biotech Center (the final destination)
2. Find the secret code hidden somewhere in the city guide documents
3. Submit that code to the game server

You'll do this by **orchestrating two A2A agents in sequence inside a `@workflow`**, then calling an MCP agent to submit the code.

---

## What you'll learn

- What **multi-agent orchestration** means and when to use it
- How to use the `@workflow` decorator to build a structured pipeline
- The **sequential pipeline** pattern: output of agent A becomes input to agent B
- How to create agents at module level and call them inside a workflow
- How to combine A2A calls with MCP tool-calling in one pipeline

---

## What is a workflow?

The `@workflow` decorator from `agent_framework` turns a plain async function into a **tracked, structured pipeline**:

```python
from agent_framework import Agent, workflow

writer = Agent(name="WriterAgent", instructions="Write a short poem.", client=client)
reviewer = Agent(name="ReviewerAgent", instructions="Review the poem.", client=client)

@workflow
async def poem_workflow(topic: str) -> str:
    poem = (await writer.run(f"Write a poem about: {topic}")).text
    review = (await reviewer.run(f"Review this poem: {poem}")).text
    return f"Poem:\n{poem}\n\nReview: {review}"

result = await poem_workflow.run("a cat learning to code")
print(result.get_outputs()[0])
print(result.get_final_state())   # WorkflowRunState.IDLE
```

Key things to notice:
- **Agents are created outside** the workflow function (at module level)
- **Inside the workflow**, you call agents like any `await` — plain Python
- **No graph, no edges, no executor classes** — just async functions and native control flow (`if`, `for`, `await`)
- `workflow.run()` returns a result with `get_outputs()` and `get_final_state()`

---

## What is orchestration?

**Orchestration** is when your code coordinates multiple agents: deciding who to call, in what order, and what to do with each result. With `@workflow`, you write that logic as Python and get structured execution tracking for free.

```
@workflow quest_workflow(player_id, stop2_location)
    │
    ├─ Stage 1 ─▶ Transport Expert (A2A) ─▶ "Take rideshare to RTP"
    │
    ├─ Stage 2 ─▶ City Guide (A2A)       ─▶ "... CAMERON99 ..."
    │
    └─ Stage 3 ─▶ submit_agent (MCP)     ─▶ submit_secret_code("CAMERON99")
```

---

## Why specialist agents?

Each specialist has a **focused system prompt** and **relevant knowledge**:

- The **Transport Expert** knows Raleigh bus routes, bike lanes, and rideshare pricing — it doesn't care about city history
- The **City Guide** knows Raleigh neighbourhoods, landmarks, and the quest reference codes — it doesn't know about transport

Mixing their knowledge into a single agent would make both worse. Specialisation is a core principle of well-designed multi-agent systems.

---

## Install the A2A package (if not already done)

```bash
pip install agent-framework-a2a --pre
```

---

## Write the code

Create a new file `create-agent/my_step7.py` and paste in:

```python [my_step7.py]
import asyncio
import os
import re

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

# Agents created at module level — available to the workflow via closure
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


@workflow
async def quest_workflow(inputs: dict) -> tuple[str, str]:
    """Three-stage pipeline: transport → city guide → submit code."""
    player_id = inputs["player_id"]
    stop2_location = inputs["stop2_location"]

    # Stage 1: Transport Expert — best route for the final leg
    print("--- Stage 1: Transport Expert ---")
    transport_advice = await call_a2a(
        A2A_SERVER_URL,
        f"What is the fastest way to get from {stop2_location} to the NC Biotech Center?",
    )
    print(transport_advice)

    transport_final = "rideshare"
    for transport_id, keyword in [
        ("goTriangle", "gotriangle"), ("goRaleigh_bus", "bus"),
        ("bike", "bike"), ("walk", "walk"), ("rideshare", "rideshare"),
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

    # Stage 3: Submit the code — call submit_agent like any async function
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

    await game_mcp.connect()

    result = await quest_workflow.run({"player_id": player_id, "stop2_location": stop2_location})
    submit_result, transport_final = result.get_outputs()[0]

    print(f"\n{submit_result}")
    print(f"Workflow state: {result.get_final_state()}")

    await game_mcp.close()

    memory._save({"transport_final": transport_final})
    print(f"\nSaved transport_final={transport_final} to memory.")


asyncio.run(main())
```

### The key moment: `@workflow`

```python
@workflow
async def quest_workflow(inputs: dict) -> tuple[str, str]:
    player_id = inputs["player_id"]
    stop2_location = inputs["stop2_location"]
    transport_advice = await call_a2a(A2A_SERVER_URL, "...")    # Stage 1
    city_guide_response = await call_a2a(CITY_GUIDE_URL, "...")  # Stage 2
    submit_result = (await submit_agent.run("...")).text         # Stage 3
    return submit_result, transport_final

# Run it:
result = await quest_workflow.run({"player_id": player_id, "stop2_location": stop2_location})
```

The workflow is **just Python**. The `@workflow` decorator adds tracking and a structured result — `result.get_outputs()` gives you what the function returned, `result.get_final_state()` tells you whether it completed cleanly.

Agents are created **outside** the workflow at module level. Inside the workflow you capture them via closure, the same way you'd reference any module-level variable.

::: tip @workflow only accepts one input parameter
If you need to pass multiple values, wrap them in a single `dict` (or dataclass) and unpack inside the function. This is a current constraint of the functional workflow API.
:::

### Make sure CITY_GUIDE_URL is set

```ini [.env]
CITY_GUIDE_URL=https://a2a-expert.redriver-3b1b0600.eastus2.azurecontainerapps.io/city-guide
```

---

## Run it

```bash
python my_step7.py
```

::: tip Expected output
```
Player: PLR-A1B2C3D4

--- Stage 1: Transport Expert ---
  Connected to: Raleigh Transport Expert
Rideshare is your fastest option from Cameron Village to RTP...

Final transport chosen: rideshare

--- Stage 2: City Guide ---
  Connected to: Raleigh City Guide
Cameron Village is one of the oldest planned shopping centres in the US...
The archivist's reference code is: CAMERON99

Extracted code: CAMERON99

--- Stage 3: Submit code ---
Code accepted! Attempts: 1

Workflow state: WorkflowRunState.IDLE
Saved transport_final=rideshare to memory.
```
:::

::: details Stuck? Use the fallback
`cheatsheet/step7_orchestration.py` contains the complete working solution. Run it with `python cheatsheet/step7_orchestration.py`.
:::

---

## What happened?

You just ran a **three-stage `@workflow`** that:
1. Called a remote A2A transport expert and parsed its advice
2. Called a remote A2A city guide and extracted the secret code with regex
3. Called an MCP agent to submit that code — an `await` like any other in the pipeline

Your Python code was the orchestrator. No single component knew about the others. `@workflow` gave you a structured result and final state without changing how you write async code.

::: info Next step
[Step 8 - Complete the Quest](step8) →
:::

## The story so far

You've reached stop 1 and the game server has unlocked stop 2. To progress, you need to:
1. Figure out how to get from stop 2 to the NC Biotech Center (the final destination)
2. Find the secret code hidden somewhere in the city guide documents
3. Submit that code to the game server

You'll do this by **orchestrating two A2A agents in sequence**, the transport expert and a city guide expert, before using an MCP agent to submit the code.

---

## What you'll learn

- What **multi-agent orchestration** means and when to use it
- The **sequential pipeline** pattern: output of agent A becomes input to agent B
- How to extract structured data (a reference code) from LLM text using regex
- How to combine A2A calls with local MCP tool-calling in one workflow

---

## What is orchestration?

**Orchestration** is when your code coordinates multiple agents, deciding who to call, in what order, and what to do with each result. It's the difference between:

- A single agent that tries to do everything (brittle, hard to debug)
- A coordinator that routes tasks to specialists (composable, maintainable)

In this step your code acts as the orchestrator. It doesn't call a model to decide what to do next, you write that logic in Python. The agents you call are the ones that do the reasoning.

```
Your code (orchestrator)
    │
    ├─▶ Transport Expert (A2A) ─▶ "Take rideshare to RTP"
    │
    ├─▶ City Guide (A2A)       ─▶ "... GLENWOOD42 ..."
    │
    └─▶ Game Server (MCP)      ─▶ submit_secret_code("GLENWOOD42")
```

---

## Why specialist agents?

Each specialist has a **focused system prompt** and **relevant knowledge**:

- The **Transport Expert** knows Raleigh bus routes, bike lanes, and rideshare pricing - it doesn't care about city history
- The **City Guide** knows Raleigh neighbourhoods, landmarks, and has been trained on the quest reference codes - it doesn't know about transport

Mixing their knowledge into a single agent would make both worse. Specialisation is a fundamental principle of well-designed multi-agent systems.

---

## Install the A2A package (if not already done)

```bash
pip install agent-framework-a2a --pre
```

---

## Write the code

Create a new file `create-agent/my_step7.py` and paste in:

```python [my_step7.py]
import asyncio
import os
import re

import httpx
from a2a.client import A2ACardResolver
from agent_framework import Agent, MCPStreamableHTTPTool
from agent_framework.a2a import A2AAgent
from agent_framework.openai import OpenAIChatClient
from dotenv import load_dotenv

from shared import FileContextProvider, get_base_endpoint

load_dotenv()

MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8000/mcp")


async def call_a2a(url: str, message: str) -> str:
    """Discover an A2A agent and send it one message."""
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
    stop2_location = saved.get("stop2_location", "Cameron Village")
    transport_url = os.environ.get("A2A_SERVER_URL")
    city_guide_url = os.environ.get("CITY_GUIDE_URL")

    if not player_id:
        print("No player_id found. Run step4_memory.py first.")
        return
    if not transport_url or not city_guide_url:
        print("Missing A2A URLs. Set A2A_SERVER_URL and CITY_GUIDE_URL in .env")
        return

    print(f"Player: {player_id}\n")

    # ------------------------------------------------------------------
    # 1. Transport Expert - best route for the final leg
    # ------------------------------------------------------------------
    print("--- Transport Expert: final leg ---")
    transport_advice = await call_a2a(
        transport_url,
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

    # ------------------------------------------------------------------
    # 2. City Guide - neighbourhood history + quest reference code
    # ------------------------------------------------------------------
    print("\n--- City Guide: quest reference code ---")
    city_guide_response = await call_a2a(
        city_guide_url,
        f"I'm on a quest at {stop2_location}. Tell me about this neighbourhood "
        "and share the archivist's reference code for it.",
    )
    print(city_guide_response)

    # Extract the reference code - uppercase alphanumeric, 6+ characters
    code_match = re.search(r"\b([A-Z][A-Z0-9]{5,})\b", city_guide_response)
    if not code_match:
        print("\nCould not extract a reference code. Check the output above and retry.")
        return

    secret_code = code_match.group(1)
    print(f"\nExtracted code: {secret_code}")

    # ------------------------------------------------------------------
    # 3. Submit the code via MCP
    # ------------------------------------------------------------------
    print("\n--- Submitting code via MCP ---")
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
            f"Call submit_secret_code with player_id='{player_id}' and "
            f"code='{secret_code}'. Report whether the code was accepted."
        ),
        tools=[game_mcp],
    )
    session = agent.create_session()
    response = await agent.run("Submit the secret code.", session=session)
    print(f"\n{response.text}")
    await game_mcp.close()

    memory._save({"transport_final": transport_final})
    print(f"\nSaved transport_final={transport_final} to memory.")


asyncio.run(main())
```

### The `call_a2a` helper

```python
async def call_a2a(url: str, message: str) -> str:
    # 1. Discover: fetch AgentCard from <url>/agent.json
    agent_card = await resolver.get_agent_card()
    # 2. Ask: send message, get reply
    response = await agent.run(message)
    return text
```

This helper wraps the two-step A2A pattern (discover → ask) into a reusable function. You reuse it for both the transport expert and the city guide, using the same pattern but different URLs and questions.

### Make sure CITY_GUIDE_URL is set

```ini [.env]
CITY_GUIDE_URL=https://city-guide.redriver-3b1b0600.eastus2.azurecontainerapps.io
```

Your facilitator provides this URL at this step of the workshop.

---

## Run it

```bash
python my_step7.py
```

::: tip Expected output
```
Player: PLR-A1B2C3D4

--- Transport Expert: final leg ---
  Connected to: Raleigh Transport Expert
Rideshare is your fastest option from Cameron Village to RTP...

Final transport chosen: rideshare

--- City Guide: quest reference code ---
  Connected to: Raleigh City Guide
Cameron Village is one of the oldest planned shopping centres in the US...
The archivist's reference code is: CAMERON99

Extracted code: CAMERON99

--- Submitting code via MCP ---
Code accepted! Attempts: 1

Saved transport_final=rideshare to memory.
```
:::

::: details Stuck? Use the fallback
`cheatsheet/step7_orchestration.py` contains the complete working solution. Run it with `python cheatsheet/step7_orchestration.py`.
:::

---

## What happened?

You just ran a **three-stage workflow** involving:
1. An HTTP call to a remote A2A transport expert
2. An HTTP call to a remote A2A city guide
3. An MCP tool call to the local game server agent

No single component knew about the others. Your Python code was the orchestrator, directing traffic, passing outputs between stages, and deciding what to do with the results. This is exactly how production multi-agent systems are built.

::: info Next step
[Step 8 - Complete the Quest](step8) →
:::
