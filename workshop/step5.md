---
title: "Step 5: A2A - Consult the Transport Expert"
description: Use the Agent-to-Agent (A2A) protocol to consult a remote expert agent about the best route.
---

# Step 5 - A2A: Consult the Transport Expert <Badge type="warning" text="~15 min" />

## The story so far

You know where you need to go - stop 1 of your quest. But how do you get there? Raleigh has buses, bikes, rideshare, and greenways. Rather than hardcoding the answer, your agent will consult a **remote expert agent** that specialises in Raleigh transport.

This is **Agent-to-Agent (A2A) communication**: one agent delegating to another.

---

## What you'll learn

- What the **A2A protocol** is and how it differs from MCP
- How `A2ACardResolver` discovers a remote agent's capabilities
- How `A2AAgent` sends a message and receives a reply
- Why specialist agents are a powerful architecture pattern

---

## MCP vs A2A - what's the difference?

| | MCP | A2A |
|---|---|---|
| **What it connects** | Agent to *tools* (functions) | Agent to *other agents* |
| **Capability unit** | A callable tool with parameters | A full AI agent with its own model and instructions |
| **Discovery** | Tool list fetched from the server | AgentCard (JSON descriptor) fetched from `/agent.json` |
| **When to use** | Calling APIs, databases, calculators | Delegating reasoning to a specialist |

**MCP** is for "do this specific thing" - call a function, write a record, fetch data.  
**A2A** is for "figure this out for me" - ask another agent to reason about a complex question.

The transport expert runs as a separate service with its own Azure OpenAI deployment, its own system prompt, and its own knowledge about Raleigh transit. Your agent doesn't know *how* it works - it just asks the question and trusts the answer.

---

## What is an AgentCard?

Before your agent can talk to the transport expert, it needs to know what the expert can do. The A2A standard defines an **AgentCard** - a JSON file hosted at `<base-url>/agent.json` that describes:
- The agent's name and description
- What kinds of questions it can answer
- What input/output formats it supports

`A2ACardResolver` fetches this card automatically. You give it a base URL; it returns a structured object you can pass to `A2AAgent`.

---

## Install the A2A package

```bash
pip install agent-framework-a2a --pre
```

---

## Write the code

Open `steps/step5_quest.py` and replace its contents with:

```python [steps/step5_quest.py]
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
    a2a_url = os.environ.get("A2A_SERVER_URL")
    stop1_location = saved.get("stop1_location", "Glenwood South")

    if not player_id:
        print("No player_id found. Run step4_memory.py first.")
        return
    if not a2a_url:
        print("A2A_SERVER_URL not set in .env. Ask your facilitator for the URL.")
        return

    print(f"Player: {player_id}")
    print(f"Connecting to A2A expert at: {a2a_url}")

    # 1. Discover the remote agent's capabilities via its AgentCard
    async with httpx.AsyncClient(timeout=30.0) as http_client:
        resolver = A2ACardResolver(httpx_client=http_client, base_url=a2a_url)
        agent_card = await resolver.get_agent_card()
    print(f"Remote agent: {agent_card.name}")

    # 2. Send a transport question to the A2A expert
    async with A2AAgent(name=agent_card.name, agent_card=agent_card, url=a2a_url) as agent:
        response = await agent.run(
            f"What is the fastest way to get to {stop1_location} from the city centre?"
        )

    advice = "\n".join(m.text for m in response.messages if m.text)
    print(f"\nA2A advice:\n{advice}\n")

    # 3. Pick a transport mode from the advice text
    transport = "rideshare"
    for transport_id, keyword in [
        ("goRaleigh_bus", "bus"),
        ("bike", "bike"),
        ("walk", "walk"),
        ("rideshare", "rideshare"),
    ]:
        if keyword in advice.lower():
            transport = transport_id
            break

    print(f"Transport chosen: {transport}")
    memory._save({"transport_stop1": transport})
    print("Saved transport_stop1 to memory.")


asyncio.run(main())
```

### Walking through the code

**Step 1 - AgentCard discovery:**
```python
resolver = A2ACardResolver(httpx_client=http_client, base_url=a2a_url)
agent_card = await resolver.get_agent_card()
```
This fetches `<a2a_url>/agent.json` and parses it into a structured object. It's the A2A equivalent of MCP's tool list discovery.

**Step 2 - Ask the expert:**
```python
async with A2AAgent(...) as agent:
    response = await agent.run("What is the fastest way to get to Glenwood South...")
```
`A2AAgent` is a *client-side* wrapper. It doesn't run a model locally - it sends your message to the remote expert agent over HTTP and waits for the reply.

**Step 3 - Parse the decision:**
```python
for transport_id, keyword in [...]:
    if keyword in advice.lower():
        transport = transport_id
        break
```
The expert returns natural language. You convert it to a structured value (`"rideshare"`, `"goRaleigh_bus"`, etc.) by scanning for keywords. This is a simple but effective pattern for extracting decisions from LLM text.

---

## Make sure A2A_SERVER_URL is set

Add this to your `.env` file (your facilitator provides the URL):

```ini [.env]
A2A_SERVER_URL=https://a2a-expert.redriver-3b1b0600.eastus2.azurecontainerapps.io
```

---

## Run it

```bash
python steps/step5_quest.py
```

::: tip Expected output
```
Player: PLR-A1B2C3D4
Connecting to A2A expert at: https://a2a-expert...
Remote agent: Raleigh Transport Expert

A2A advice:
Rideshare is your fastest option to reach Glenwood South from downtown —
approximately 8 minutes by Uber or Lyft from Moore Square...

Transport chosen: rideshare
Saved transport_stop1 to memory.
```
:::

::: details Stuck? Use the fallback
`steps/step5_quest.py` is already complete in the repo.
:::

---

## Key takeaway

You just called a *remote AI agent* as if it were a function. The transport expert has its own model, its own knowledge, and its own system prompt - you just asked a question and got an expert answer. This is the power of the A2A pattern: you compose specialists without knowing how they work internally.

::: info Next step
[Step 6 - Multi-turn Conversations](step6) →
:::
