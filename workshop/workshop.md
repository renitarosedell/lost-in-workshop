
# Lost in Raleigh — Workshop Guide

Welcome! In this workshop you will build a Python AI agent that navigates a quest through
Raleigh, NC. Your agent will use **Microsoft Agent Framework**, **Azure OpenAI**, an **MCP
game server**, memory persistence, an **A2A transport expert**, and document search (RAG).

**Duration**: ~90 minutes   **Level**: Beginner–Intermediate Python

---

## Before you start

- Complete [azure-foundry-setup.md](azure-foundry-setup.md) to create your Azure OpenAI
  deployment and fill in your `.env` file.
- Your facilitator will provide the `MCP_SERVER_URL` for the game server.
- All step files are in `sample-agent/steps/`. Run each one from the `sample-agent/`
  directory: `python steps/step1_foundry_test.py`

---

## Step 1 — Connect to Azure OpenAI (baseline check)

### Concept

Before we use the agent framework, we verify that your Azure OpenAI credentials work.
This step uses the bare `openai` SDK — no agent framework, no tools.

### What to add

Create `steps/step1_foundry_test.py` (or open the provided fallback):

```python
import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AzureOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    api_version="2024-08-01-preview",
)

response = client.chat.completions.create(
    model=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
    messages=[{"role": "user", "content": "Say: I am ready to help you navigate Raleigh."}],
)

print("Connected to Azure OpenAI!")
print("Model response:", response.choices[0].message.content)
```

### How to test

```
python steps/step1_foundry_test.py
```

**Expected output**:
```
Connected to Azure OpenAI!
Model response: I am ready to help you navigate Raleigh.
```

### Fallback

The complete file is in `steps/step1_foundry_test.py`.

---

## Step 2 — Hello Raleigh (bare OpenAI, no framework)

### Concept

We send a real question about Raleigh to verify the model is working and that you
understand the chat completions API before adding the framework abstraction.

### What to add

Create `steps/step2_hello_world.py`:

```python
import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AzureOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    api_version="2024-08-01-preview",
)

response = client.chat.completions.create(
    model=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
    messages=[{"role": "user", "content": "What is Raleigh famous for?"}],
)

print(response.choices[0].message.content)
```

### How to test

```
python steps/step2_hello_world.py
```

**Expected output**: A short paragraph about Raleigh mentioning Research Triangle,
universities, or the tech scene.

### Fallback

`steps/step2_hello_world.py`

---

## Step 3 — Connect to the MCP Game Server

### Concept

Switch from the bare OpenAI SDK to **Microsoft Agent Framework**. Add an
`MCPStreamableHTTPTool` that connects your agent to the game server. Call
`register_player` to get your player ID and quest assignment.

### What to add

Create `steps/step3_mcp_connect.py`:

```python
import asyncio, os
from agent_framework import Agent, MCPStreamableHTTPTool
from agent_framework.openai import OpenAIChatClient
from dotenv import load_dotenv

load_dotenv()

MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8000/mcp")

async def main():
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
            "Register as a new player with the name 'Workshop Attendee' using "
            "register_player. Print the player_id, quest name, and A2A expert URL."
        ),
        tools=[game_mcp],
    )

    session = agent.create_session()
    response = await agent.run("Register me and print my quest details.", session=session)
    print(response.text)
    await game_mcp.close()

asyncio.run(main())
```

### How to test

```
python steps/step3_mcp_connect.py
```

**Expected output**:
```
Your player_id is PLR-XXXXXXXX.
Quest: Glenwood Getaway
A2A Expert: https://...
```

> **Tip**: You can see all registered players on the admin dashboard at
> `MCP_SERVER_URL` (replace `/mcp` with `/admin`).

### Fallback

`steps/step3_mcp_connect.py`

---

## Step 4 — Add Memory (persist your player ID)

### Concept

Agents are stateless by default. Add a `ContextProvider` that saves your `player_id` to a
local `memory.json` file and injects it back on subsequent runs — so you never register twice.

### What to add

Add a `FileContextProvider` class to your agent file:

```python
import json, re
from pathlib import Path
from agent_framework import ContextProvider, SessionContext

MEMORY_FILE = Path(__file__).parent.parent / "memory.json"

class FileContextProvider(ContextProvider):
    def __init__(self):
        super().__init__("player-memory")

    def _load(self):
        if MEMORY_FILE.exists():
            return json.loads(MEMORY_FILE.read_text())
        return {}

    def _save(self, data):
        MEMORY_FILE.write_text(json.dumps(data, indent=2))

    async def before_run(self, *, context: SessionContext, **_):
        data = self._load()
        player_id = data.get("player_id")
        if player_id:
            context.extend_instructions(
                self.source_id,
                f"Your player_id is {player_id}. Use it for all tool calls.",
            )

    async def after_run(self, *, context: SessionContext, **_):
        data = self._load()
        if data.get("player_id"):
            return
        for msg in context.output_messages:
            text = getattr(msg, "text", "") or ""
            match = re.search(r"PLR-[A-Z0-9]{8}", text)
            if match:
                data["player_id"] = match.group(0)
                self._save(data)
                break
```

Then pass it to your `Agent`:

```python
memory = FileContextProvider()
agent = Agent(
    client=client,
    name="RaleighAgent",
    instructions="...",
    tools=[game_mcp],
    context_providers=[memory],     # <-- add this
)
```

### How to test

Run `step4_memory.py` twice:

```
python steps/step4_memory.py
python steps/step4_memory.py
```

First run: registers you and saves the player_id.  
Second run: injects the player_id from `memory.json` — no second registration.

### Fallback

`steps/step4_memory.py`

---

## Step 5 — Complete the Quest

### Concept

Put it all together. Your agent will:

1. Register (or resume from memory).
2. Call the **A2A transport expert** via `httpx.post` to get route advice.
3. Call `declare_transport_stop1` to record your route choice and receive a **document
   bundle URL**.
4. **Download** the ZIP bundle and **search** the Markdown files for the secret code.
5. Call `submit_secret_code` with the code.
6. Call `declare_transport_final` to complete the quest and receive your **final score**.

### What to add

The A2A call (outside the agent framework — it is a direct HTTP call):

```python
import httpx

def ask_a2a_expert(a2a_url: str, question: str) -> str:
    with httpx.Client(timeout=30) as client:
        r = client.post(a2a_url, json={"message": question})
        r.raise_for_status()
        return r.json()["advice"]
```

The document RAG search:

```python
import io, zipfile, re, httpx

def find_secret_code(bundle_url: str) -> str:
    with httpx.Client(timeout=60, follow_redirects=True) as client:
        r = client.get(bundle_url)
        r.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
        for name in zf.namelist():
            if not name.endswith(".md"):
                continue
            text = zf.read(name).decode("utf-8", errors="replace")
            for word in re.findall(r"\b[A-Z]{3,}[A-Z0-9]*\b", text):
                if 5 <= len(word) <= 15 and word.isalnum():
                    return word
    raise RuntimeError("Code not found.")
```

### How to test

```
python steps/step5_quest.py
```

**Expected output** (approximate):

```
=== Phase 1: Register ===
player_id = PLR-XXXXXXXX

=== Phase 2: A2A Transport Advice ===
A2A advice: Rideshare is your fastest option at around 8 minutes...
Chosen transport: rideshare

=== Phase 3: Declare Transport → Stop 1 ===
Bundle URL: https://...

=== Phase 4: Document Bundle & Secret Code ===
Bundle downloaded (5 KB)
Secret code found: GLENWOOD42

=== Phase 5: Submit Code ===
Code accepted! Attempt 1.

=== Phase 6: Final Transport → NC Biotech Center ===
Quest complete! Final score: 920
```

### Fallback

`steps/step5_quest.py` — or the complete reference implementation at `agent.py`.

---

## You did it! 🎉

Your score is on the leaderboard. Ask your facilitator for the admin dashboard URL to see
where you rank.

### What you built

| Step | Capability |
|------|-----------|
| 1 | Azure OpenAI connectivity check |
| 2 | Bare chat completion (no framework) |
| 3 | Microsoft Agent Framework + MCP tools |
| 4 | ContextProvider for persistent memory |
| 5 | A2A HTTP call + RAG document search + full quest loop |

### Want to go further?

See [bonus-exercises.md](bonus-exercises.md) for four bonus challenges:
- Build your own A2A transport expert
- Add streaming responses
- Multi-agent orchestration (Planner + Runner)
- Eval harness (run the quest 3× and compare scores)

