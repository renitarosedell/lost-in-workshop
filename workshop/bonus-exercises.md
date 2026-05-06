---
title: Bonus Exercises
description: Five additional challenges to extend your Lost in Raleigh agent after completing the main quest.
---

# Bonus Exercises

Finished the main quest? Here are five bonus challenges. Each is self-contained, so do them in any order.

| Bonus | Challenge | Skill |
|-------|-----------|-------|
| A | Build your own A2A transport expert | FastAPI + Agent Framework |
| B | Add streaming responses | Async token streaming |
| C | Eval harness | Parallel quest runs + scoring |
| D | Swap model deployments | `OpenAIChatClient`, AI Foundry |
| E | Rewrite with WorkflowBuilder | Graph-based orchestration |

---

## Bonus A - Build Your Own A2A Transport Expert <Badge type="tip" text="Intermediate" />

::: info What you'll build
Your own transport advice service, deployed locally and hooked into the game server.
When attendees call `declare_transport_stop1`, the game will call **your** `/a2a` endpoint
instead of the facilitator's.
:::

### A2A contract

Any service that accepts:

```
POST /a2a
Content-Type: application/json

{ "message": "What is the best way to get to Glenwood South?" }
```

and responds with:

```json
{ "advice": "Rideshare is fastest at around 8 minutes from Moore Square..." }
```

is a valid A2A expert.

::: details Starter: FastAPI + Microsoft Agent Framework
```python [bonus_a2a_expert.py]
# bonus_a2a_expert.py
import os
from fastapi import FastAPI
from pydantic import BaseModel
from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

SYSTEM_PROMPT = """You are a Raleigh transport expert. Answer transport questions
concisely. Focus on GoRaleigh buses, Capital Bikeshare, rideshare, and walking times
between: Moore Square, Glenwood South, Warehouse District, Five Points, NC Biotech Center.
"""

class A2ARequest(BaseModel):
    message: str

class A2AResponse(BaseModel):
    advice: str

@app.post("/a2a", response_model=A2AResponse)
async def a2a(req: A2ARequest) -> A2AResponse:
    client = OpenAIChatClient(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        model=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
    )
    agent = Agent(
        client=client,
        name="TransportExpert",
        instructions=SYSTEM_PROMPT,
    )
    session = agent.create_session()
    response = await agent.run(req.message, session=session)
    return A2AResponse(advice=response.text or "")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
```

### Run it

```bash
uvicorn bonus_a2a_expert:app --port 9000
```

### Expose it with ngrok

```bash
ngrok http 9000
```

Copy the `https://...ngrok.io` URL from the output.

### Override the A2A URL for your player

Ask your facilitator to update `city_config.yaml` with your ngrok URL, or call the
admin API directly:

```
PUT /api/players/<your-player-id>/a2a_url
{ "url": "https://your-ngrok-id.ngrok.io/a2a" }
```

Then re-run `step5_quest.py` - your transport call now hits your own service.

::: tip Challenge
Add a tool to your A2A expert that fetches the [GoRaleigh trip planner](https://goraleigh.org)
and uses the live schedule data to answer.
:::

---

## Bonus B - Streaming Responses <Badge type="tip" text="Beginner" />

::: info What you'll add
Stream tokens to the console as they arrive instead of waiting for the full response.
:::

### Before (blocking)

```python
response = await agent.run("Register me.", session=session)
print(response.text)
```

### After (streaming)

```python
async for chunk in agent.run_stream("Register me.", session=session):
    print(chunk.delta, end="", flush=True)
print()   # newline at end
```

### How to test

Add streaming to `step3_mcp_connect.py`:

1. Replace the `response = await agent.run(...)` line with the streaming version above.
2. Run it:
   ```
   python cheatsheet/step3_mcp_connect.py
   ```
3. **Expected**: You see tokens printing character-by-character (or word-by-word) rather
   than all at once.

### Challenge

Build a progress bar in the terminal that updates as tokens arrive. Use the `rich` library:

```python
from rich.live import Live
from rich.text import Text

text = Text()
with Live(text, refresh_per_second=20) as live:
    async for chunk in agent.run_stream("...", session=session):
        text.append(chunk.delta or "")
        live.update(text)
```

---

## Bonus C - Eval Harness <Badge type="warning" text="Advanced" />

::: info What you'll build
Run the full quest three times in parallel and produce a score comparison table.
Useful for testing prompt changes or transport strategy variations.
:::

### Starter: `create-agent/eval_harness.py`

```python
"""Run the quest 3 times and compare scores."""
import asyncio, os, re, json
from agent_framework import Agent, MCPStreamableHTTPTool
from agent_framework.openai import OpenAIChatClient
from dotenv import load_dotenv

load_dotenv()

MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8000/mcp")
RUNS = 3

async def run_once(run_id: int) -> dict:
    """Register a fresh player and complete the quest. Returns score metadata."""
    client = OpenAIChatClient(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        model=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
    )
    game_mcp = MCPStreamableHTTPTool(
        name="Lost in Raleigh Game Server",
        url=MCP_SERVER_URL,
        description="",
    )
    await game_mcp.connect()

    agent = Agent(
        client=client,
        name=f"EvalAgent-{run_id}",
        instructions=(
            f"Register as 'Eval Run {run_id}' using register_player. "
            "Then complete the full quest: declare_transport_stop1 with 'rideshare', "
            "submit_secret_code with the code you find, declare_transport_final with 'rideshare'. "
            "Return a JSON object with: player_id, quest_name, score, code_attempts, time_minutes."
        ),
        tools=[game_mcp],
    )
    session = agent.create_session()
    result = await agent.run("Complete the quest and return results as JSON.", session=session)
    await game_mcp.close()

    text = result.text or "{}"
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return json.loads(match.group(0)) if match else {"run_id": run_id, "error": text[:100]}

async def main():
    results = await asyncio.gather(*[run_once(i + 1) for i in range(RUNS)])

    print(f"\n{'Run':<6} {'Quest':<22} {'Score':<8} {'Attempts':<10} {'Minutes'}")
    print("-" * 60)
    for i, r in enumerate(results, 1):
        print(
            f"{i:<6} {str(r.get('quest_name', '?')):<22} "
            f"{str(r.get('score', '?')):<8} "
            f"{str(r.get('code_attempts', '?')):<10} "
            f"{r.get('time_minutes', '?')}"
        )
    scores = [r.get("score") for r in results if isinstance(r.get("score"), (int, float))]
    if scores:
        print(f"\nAverage score: {sum(scores) / len(scores):.1f}")

asyncio.run(main())
```

### How to test

```
python eval_harness.py
```

**Expected output**:

```
Run    Quest                  Score    Attempts   Minutes
------------------------------------------------------------
1      glenwood_getaway       920      1          8.0
2      museum_mile            870      2          13.0
3      warehouse_run          940      1          6.0

Average score: 910.0
```

### Challenge

Add a `--strategy` flag that switches between transport choices (`rideshare`, `bus`, `bike`,
`walk`) and compares average scores across 3 runs per strategy. Which transport choice
maximises the score?

```
python eval_harness.py --strategy rideshare
python eval_harness.py --strategy bike
```

---

## Bonus D - Swap Model Deployments <Badge type="tip" text="Beginner" />

::: info What you'll explore
Change the model your agent uses — without touching any agent logic. Because `OpenAIChatClient` is just a config object, swapping models is a one-line change.
:::

### How to add a second deployment

1. Open [ai.azure.com](https://ai.azure.com) and go to your project
2. Click **Models + endpoints → Deploy model**
3. Pick a different model — for example `gpt-4o` or `o3-mini`
4. Give it a deployment name, for example `gpt-4o`

### How to switch models in your code

Everywhere you create an `OpenAIChatClient`, the `model=` parameter is the deployment name from AI Foundry:

```python
# Uses gpt-4o-mini (your original deployment)
client = OpenAIChatClient(
    azure_endpoint=get_base_endpoint(),
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    model=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],  # e.g. "gpt-4o-mini"
)

# Switch to a different deployment by changing the model name
client_fast = OpenAIChatClient(
    azure_endpoint=get_base_endpoint(),
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    model="gpt-4o",   # your second deployment name
)
```

You can create **multiple clients** and pass them to different agents in the same workflow — for example, use a cheaper model for simple tool calls and a more capable model for reasoning.

### Try it

Copy `create-agent/cheatsheet/step7_orchestration.py` to `my_step7_models.py` and make these two changes:

1. Create a second client pointing at your new deployment:
   ```python
   client_powerful = OpenAIChatClient(
       azure_endpoint=get_base_endpoint(),
       api_key=os.environ["AZURE_OPENAI_API_KEY"],
       model="gpt-4o",  # your new deployment name
   )
   ```
2. Pass `client_powerful` to `submit_agent` so the code-submission stage uses the stronger model:
   ```python
   submit_agent = Agent(
       client=client_powerful,   # upgraded for the final stage
       name="RaleighAgent",
       ...
   )
   ```

Run both versions and compare the outputs. Does the stronger model produce a cleaner submission response? Does it extract the secret code more reliably?

::: tip Challenge
Add a third client using `o3-mini` (a reasoning model). Use it for Stage 2 of the workflow (the city guide stage) where the agent has to find a reference code buried in a long document. Does a reasoning model perform better at extraction?
:::

---

## Bonus E - Rewrite with WorkflowBuilder <Badge type="warning" text="Advanced" />

::: info What you'll explore
Replace the `@workflow` functional pipeline with a **graph-based workflow** using `WorkflowBuilder`. Both produce the same result — this exercise shows you the trade-offs between the two APIs.
:::

### The difference in one sentence

`@workflow` is **Python control flow** — you write `if`, `for`, and `await` and get tracking for free. `WorkflowBuilder` is a **directed graph** — you declare nodes (executors) and edges, and the framework manages execution and message routing between them.

See the [full workflow docs](https://learn.microsoft.com/en-us/agent-framework/workflows/) for a detailed comparison.

### Starting point

Copy `create-agent/cheatsheet/step7_orchestration.py` to `my_bonus_e.py`, then replace the `@workflow` block with this:

```python [my_bonus_e.py]
from typing import cast
from agent_framework import Agent, AgentResponse, WorkflowBuilder

# Re-use your existing `client` and `game_mcp` from the module level.
# Define three agents — each receives the previous agent's text output as input.

transport_agent = Agent(
    client=client,
    name="TransportExpert",
    instructions=(
        f"You are a Raleigh transport expert. "
        f"What is the fastest way from {stop2_location} to the NC Biotech Center? "
        "Name the transport mode in your very first sentence."
    ),
)

city_guide_agent = Agent(
    client=client,
    name="CityGuide",
    instructions=(
        "You are a Raleigh city guide. Describe the neighbourhood the user mentions "
        "and include the archivist's reference code for it. "
        "Always state it as: 'The reference code is: XXXXXX'."
    ),
)

submit_agent = Agent(
    client=client,
    name="SubmitAgent",
    instructions=(
        f"Extract the reference code from the message you receive and call "
        f"submit_secret_code with player_id='{player_id}' and that code. "
        "Report whether it was accepted."
    ),
    tools=[game_mcp],
)

# Build the linear graph: transport → city guide → submit
workflow = (
    WorkflowBuilder(start_executor=transport_agent)
    .add_edge(transport_agent, city_guide_agent)
    .add_edge(city_guide_agent, submit_agent)
    .build()
)

events = await workflow.run(
    f"What is the best route from {stop2_location} to the NC Biotech Center?"
)
outputs = cast(list[AgentResponse], events.get_outputs())
for output in outputs:
    print(f"{output.messages[0].author_name}:\n{output.text}\n")
print("Final state:", events.get_final_state())
```

### What to notice

- **No Python between stages** — each agent receives the previous agent's full text as its prompt. There is no regex extraction; the submit agent has to find the code from the city guide's prose.
- **Prompt engineering replaces code** — the `"Always state it as: 'The reference code is: XXXXXX'"` instruction is doing the work that the regex did in the `@workflow` version. If the model doesn't follow it exactly, the submit call may fail.
- **Trade-off** — `WorkflowBuilder` is cleaner for pure reasoning pipelines. `@workflow` is more reliable when you need structured data extracted between stages.

::: tip Challenge
Add a **conditional edge** so that if the city guide agent's output does not contain a reference code (no `XXXXXX` pattern), the workflow routes back to the city guide agent and asks it to try again. See the [WorkflowBuilder docs](https://learn.microsoft.com/en-us/agent-framework/workflows/) for how to add conditional routing.
:::
