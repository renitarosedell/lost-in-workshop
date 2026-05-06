# Lost in Workshop - Raleigh

A hands-on workshop for building AI agents that connect to a Model Context Protocol (MCP) server to play **Lost in San Francisco** — a narrative quest game where attendees guide their agent across the city to reach Fort Mason in time for Build.

## What's in this repo

| Folder | Purpose |
| --- | --- |
| [lost-in-sf/](lost-in-sf/) | The MCP game server + FastAPI admin UI that powers the quest. |
| [sample-agent/](sample-agent/) | A reference Python agent (Microsoft Agent Framework) that plays the game. |
| [city-guide/](city-guide/) | 20-chapter San Francisco guide used as source material for the RAG challenge. |
| [workshop/](workshop/) | Workshop outline and facilitator notes. |
| [instructions/](instructions/) | Build prompt that specifies the MCP server behaviour. |

## How the game works

1. An attendee runs their agent, which connects to the MCP server.
2. The agent calls `register_player` and is randomly assigned a quest (e.g. *The Mission Run*, *Chinatown Express*).
3. The quest has three legs:
   - **Stop 1 — A2A challenge:** agent asks a local "expert" for the best transport option.
   - **Stop 2 — RAG challenge:** agent reads a bundle of documents and extracts a secret code.
   - **Final leg:** agent chooses transport to Fort Mason and finishes the quest.
4. Score = `1000 − 50 × failed_code_attempts − 10 × minutes_taken` (floored at 0).
5. Top 10 appear on the leaderboard in the admin UI.

## Quick start

### 1. Run the MCP server

```bash
cd lost-in-sf
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python server.py       # serves MCP at http://localhost:8000/mcp
```

In another terminal, launch the admin UI to edit quests and watch the leaderboard:

```bash
python admin.py        # http://localhost:8080
```

See [lost-in-sf/README.md](lost-in-sf/README.md) for the full tool reference and config options.

### 2. Run the sample agent

The sample agent uses Azure OpenAI via the Microsoft Agent Framework. Create a `.env` in `sample-agent/` with:

```env
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com
AZURE_OPENAI_API_KEY=<your-key>
AZURE_OPENAI_DEPLOYMENT_NAME=<your-deployment>
```

Then:

```bash
cd sample-agent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python agent.py
```

The agent connects to the MCP server at `http://localhost:8000/mcp`, registers a player, and plays the quest interactively. It demonstrates a `ContextProvider` that persists the assigned `player_id` across turns.

## Workshop flow

High-level workshop steps (see [workshop/workshop.md](workshop/workshop.md)):

1. Create a hello-world agent.
2. Connect it to the gaming MCP server.
3. Add memory so the agent remembers its `player_id`.

## Prerequisites

- Python 3.11+
- An Azure OpenAI deployment (or swap in `FoundryChatClient` — see [sample-agent/agent.py](sample-agent/agent.py))
- Network access to the MCP server (local by default)

## Repository notes

- Game state lives in `lost-in-sf/state.json` and is gitignored — reset it from the admin UI or by deleting the file.
- Quest content lives in `lost-in-sf/quests.json` and can be edited live through the admin UI.
- The server is intended for short-lived workshop use, not production.
