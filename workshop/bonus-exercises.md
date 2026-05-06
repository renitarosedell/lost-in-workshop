---
title: Bonus Exercises
description: Three additional challenges to extend your Lost in Raleigh agent after completing the main quest.
---

# Bonus Exercises

Finished the main quest? Here are three bonus challenges. Each is self-contained, so do them in any order.

| Bonus | Challenge | Skill |
|-------|-----------|-------|
| A | Build your own A2A transport expert | FastAPI + Agent Framework |
| B | Add streaming responses | Async token streaming |
| C | Eval harness | Parallel quest runs + scoring |

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
