# Lost in San Francisco — MCP Game Server

A **Model Context Protocol (MCP)** server that powers the *Lost in San Francisco* workshop game. Attendees build agents that connect to this server and play a three-stop narrative quest ending at Fort Mason.

Ships with a small FastAPI **admin UI** for editing quest content, watching the leaderboard, and resetting state between sessions.

## Project layout

```
lost-in-sf/
├── server.py         # MCP server (stdio transport)
├── admin.py          # FastAPI admin UI (port 8080)
├── storage.py        # Shared JSON state / quest helpers
├── quests.json       # Quest definitions (editable via admin UI)
├── state.json        # Live game state
├── requirements.txt
└── README.md
```

## Install

```bash
cd lost-in-sf
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run the MCP server

By default the server uses the **Streamable HTTP** MCP transport and listens on `0.0.0.0:8000`. The MCP endpoint is `POST /mcp`.

```bash
python server.py
# -> http://localhost:8000/mcp
```

Configuration via environment variables:

| Variable | Default | Notes |
| --- | --- | --- |
| `MCP_TRANSPORT` | `streamable-http` | Also accepts `sse` or `stdio` |
| `MCP_HOST` | `0.0.0.0` | HTTP bind address |
| `MCP_PORT` | `8000` | HTTP bind port |

For local stdio testing with the MCP inspector:

```bash
MCP_TRANSPORT=stdio mcp dev server.py
```

## Run the admin UI

```bash
python admin.py
# open http://localhost:8080
```

The admin UI lets you:

- View and edit `quests.json` as raw JSON, then save
- Watch the live leaderboard (auto-refreshes every 10 s)
- See all registered players and their current status
- Reset an individual player
- Nuke all players and the leaderboard

## Connect an agent (MCP client config)

**Streamable HTTP** (recommended) — point your client at the running server's `/mcp` endpoint:

```json
{
  "mcpServers": {
    "lost-in-sf": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

**stdio** (local-only clients like Claude Desktop):

```json
{
  "mcpServers": {
    "lost-in-sf": {
      "command": "python",
      "args": ["/absolute/path/to/lost-in-sf/server.py"],
      "env": { "MCP_TRANSPORT": "stdio" }
    }
  }
}
```

## MCP tools exposed

| Tool | Purpose |
| --- | --- |
| `register_player(name)` | Register a player and randomly assign a quest |
| `start_quest(player_id)` | Begin the quest, returns the stop-1 A2A challenge |
| `declare_transport_stop1(player_id, transport)` | Submit transport choice for leg 1, get the stop-2 RAG challenge |
| `submit_secret_code(player_id, code)` | Submit the code found in the documents |
| `declare_transport_final(player_id, transport)` | Complete the quest, receive score & leaderboard position |
| `get_leaderboard()` | Top 10 players |
| `get_player_status(player_id)` | Inspect a player's current state (debugging) |

## Scoring

`score = 1000 − 50 × failed_code_attempts − 10 × minutes_taken` (floored at 0).

## Updating quest content

- **Via the admin UI** (recommended during the workshop) — edit the quest JSON in the textarea and click *Save quests.json*.
- **Manually** — edit `quests.json` and restart nothing; the MCP server reads it per call.

The `documents_zip_url` fields are placeholders. Fill them with real URLs before the workshop.

## Resetting game state

- In the admin UI click **Reset ALL players** for a clean slate.
- Or stop the server and replace `state.json` with `{"players": {}, "leaderboard": []}`.

## Notes

- State is persisted to `state.json` on every write, guarded by a process-level lock.
- All error conditions are returned in-narrative where possible — agents never see raw stack traces.
- The server is intended for short-lived, single-host workshop use. Not hardened for production.
