# Claude Code Prompt: Build the Lost in San Francisco MCP Game Server

## What you are building

A **Model Context Protocol (MCP) server** that powers a workshop game called *Lost in San Francisco*. Attendees build AI agents that connect to this server to play a narrative quest game. The server manages game state, player registration, movement, and challenge validation.

Also build a **simple web-based quest editor UI** so the facilitator can edit quest content without touching code.

---

## Tech stack

- **Runtime**: Python 3.11+
- **MCP framework**: `mcp` SDK (the official Anthropic MCP Python SDK)
- **State storage**: JSON file on disk (simple, no database needed)
- **Quest config**: JSON file, editable via the admin UI
- **Admin UI**: Single-file FastAPI app serving a minimal HTML page
- **Transport**: stdio (standard MCP transport for local use) + optional SSE for remote

---

## Project structure

```
lost-in-sf/
├── server.py              # MCP server (main entry point)
├── admin.py               # FastAPI admin UI server
├── quests.json            # Quest definitions (editable via admin UI)
├── state.json             # Live game state (players, progress)
├── requirements.txt
└── README.md
```

---

## quests.json structure

This file defines all quest content. The admin UI reads and writes this file.

```json
{
  "quests": [
    {
      "id": 1,
      "name": "The Mission Run",
      "start": {
        "neighborhood": "The Mission",
        "description": "You wake up disoriented outside a taqueria on Valencia Street. The smell of carnitas is everywhere. Your phone says it's 9:15am. Build starts at 10:00. You need to get to Fort Mason — but you have no idea how.",
        "flavor": "A street musician is playing outside. A mural covers the wall behind you."
      },
      "stop1": {
        "neighborhood": "Hayes Valley",
        "arrival_description": "You arrive at Hayes Valley. A vintage shop owner waves at you from the doorway. 'You must be the one Agent42 sent. Come in.'",
        "challenge_type": "a2a",
        "a2a_context": "You are lost in The Mission and need to get to Hayes Valley. Ask the local expert (agent42) for the best transport option: taxi, walking, or bike.",
        "transport_prompt": "What transport are you taking to Hayes Valley? (taxi / walking / bike)",
        "valid_transports": ["taxi", "walking", "bike"]
      },
      "stop2": {
        "neighborhood": "Hayes Valley",
        "challenge_type": "rag",
        "setup_description": "The shop owner hands you a heavy bag. 'Someone left these for you. The code you need is in there somewhere.' Inside are stacks of documents — zines, flyers, local event programs.",
        "documents_zip_url": "https://your-storage-url/quest1-documents.zip",
        "secret_code": "VALENCIA42",
        "code_hint": "What is the secret code written in the documents?"
      },
      "end": {
        "transport_prompt": "Time to go to Build! What transport are you taking to Fort Mason? (taxi / walking / bike)",
        "valid_transports": ["taxi", "walking", "bike"],
        "arrival_message": "You arrive at Fort Mason. The doors open. Welcome to Build!"
      }
    },
    {
      "id": 2,
      "name": "Chinatown Express",
      "start": {
        "neighborhood": "Chinatown",
        "description": "You find yourself on Grant Avenue in Chinatown. Paper lanterns sway overhead. Market stalls crowd the sidewalk. A sign says Fort Mason is 2.3 miles away. Build starts in 45 minutes.",
        "flavor": "A cable car bell rings in the distance."
      },
      "stop1": {
        "neighborhood": "North Beach",
        "arrival_description": "You step into North Beach. The smell of coffee and old books. A figure leans against the wall outside City Lights bookstore. 'You made it. I was starting to worry.'",
        "challenge_type": "a2a",
        "a2a_context": "You are in Chinatown and need to get to North Beach. Ask the local expert (agent42) for the best transport option: taxi, walking, or bike.",
        "transport_prompt": "What transport are you taking to North Beach? (taxi / walking / bike)",
        "valid_transports": ["taxi", "walking", "bike"]
      },
      "stop2": {
        "neighborhood": "North Beach",
        "challenge_type": "rag",
        "setup_description": "The stranger unzips a weathered bag and tips it out — photocopied manuscripts, bookstore receipts, handwritten notes on napkins. 'The code is in there. Somewhere. Good luck.'",
        "documents_zip_url": "https://your-storage-url/quest2-documents.zip",
        "secret_code": "BEATNIK99",
        "code_hint": "What is the secret code written in the documents?"
      },
      "end": {
        "transport_prompt": "Time to go to Build! What transport are you taking to Fort Mason? (taxi / walking / bike)",
        "valid_transports": ["taxi", "walking", "bike"],
        "arrival_message": "You walk through the gates of Fort Mason. A volunteer scans your badge. Welcome to Build!"
      }
    },
    {
      "id": 3,
      "name": "Waterfront Route",
      "start": {
        "neighborhood": "Embarcadero",
        "description": "You're standing at the Ferry Building. Fog rolls in off the bay. Seagulls argue overhead. The clock tower reads 9:18am. Fort Mason is up the waterfront. Build starts in 42 minutes.",
        "flavor": "A ferry horn echoes across the water."
      },
      "stop1": {
        "neighborhood": "Fisherman's Wharf",
        "arrival_description": "You reach Fisherman's Wharf. The smell of sourdough and sea air. A fisherman in waders spots you immediately. 'Agent42 radioed ahead. Been expecting you.'",
        "challenge_type": "a2a",
        "a2a_context": "You are at the Embarcadero and need to get to Fisherman's Wharf along the waterfront. Ask the local expert (agent42) for the best transport option: taxi, walking, or bike.",
        "transport_prompt": "What transport are you taking to Fisherman's Wharf? (taxi / walking / bike)",
        "valid_transports": ["taxi", "walking", "bike"]
      },
      "stop2": {
        "neighborhood": "Fisherman's Wharf",
        "challenge_type": "rag",
        "setup_description": "The fisherman hauls a salt-stained satchel from his boat. 'Logbooks, manifests, dock reports. Messy bunch of papers. But the code you need — it's in there.'",
        "documents_zip_url": "https://your-storage-url/quest3-documents.zip",
        "secret_code": "ANCHOR77",
        "code_hint": "What is the secret code written in the documents?"
      },
      "end": {
        "transport_prompt": "Time to go to Build! What transport are you taking to Fort Mason? (taxi / walking / bike)",
        "valid_transports": ["taxi", "walking", "bike"],
        "arrival_message": "Fort Mason comes into view. The bay glittering behind you. You made it. Welcome to Build!"
      }
    }
  ]
}
```

---

## MCP server tools to implement

Implement these as MCP tools in `server.py`:

### `register_player(name: str) -> dict`
- Randomly assign a quest_id (1, 2, or 3)
- Generate a unique player_id (e.g. UUID short)
- Save player state to state.json
- Return:
  ```json
  {
    "player_id": "abc123",
    "quest_id": 1,
    "quest_name": "The Mission Run",
    "start_neighborhood": "The Mission",
    "start_description": "...",
    "start_flavor": "...",
    "message": "Your quest has begun. Say START when you are ready."
  }
  ```

### `start_quest(player_id: str) -> dict`
- Mark quest as started, record start timestamp
- Return the stop1 a2a challenge setup:
  ```json
  {
    "status": "quest_started",
    "current_location": "The Mission",
    "next_destination": "Hayes Valley",
    "challenge": "You need to get to Hayes Valley. Consult your local expert to decide how.",
    "a2a_context": "..."
  }
  ```

### `declare_transport_stop1(player_id: str, transport: str) -> dict`
- Validate transport is one of the valid options for the quest
- If invalid, return an error message in-narrative ("The locals look at you blankly")
- If valid, advance player state to stop2, record transport choice
- Return stop2 RAG challenge setup:
  ```json
  {
    "status": "arrived_stop1",
    "transport_used": "bike",
    "arrival_description": "...",
    "challenge_setup": "...",
    "documents_zip_url": "https://..."
  }
  ```

### `submit_secret_code(player_id: str, code: str) -> dict`
- Case-insensitive comparison against quest's secret_code
- If wrong: return in-narrative failure ("The stranger shakes their head. That's not it.")
- Track number of attempts
- If correct: advance player state to final leg
- Return:
  ```json
  {
    "status": "code_accepted",
    "message": "The stranger nods. That's the one. Time to move.",
    "next_challenge": "Pick your transport to Fort Mason."
  }
  ```

### `declare_transport_final(player_id: str, transport: str) -> dict`
- Validate transport
- Complete the quest, record end timestamp
- Calculate score: base 1000 points, minus 50 per failed code attempt, minus 10 per minute taken
- Update leaderboard in state.json
- Return:
  ```json
  {
    "status": "quest_complete",
    "arrival_message": "Welcome to Build!",
    "score": 850,
    "time_taken_minutes": 12,
    "code_attempts": 1,
    "leaderboard_position": 3
  }
  ```

### `get_leaderboard() -> dict`
- Return top 10 players sorted by score
- Include: player name, quest name, score, time taken, code attempts

### `get_player_status(player_id: str) -> dict`
- Return current state of a player (useful for debugging during the workshop)

---

## state.json structure

```json
{
  "players": {
    "abc123": {
      "name": "Henk",
      "quest_id": 1,
      "status": "stop2",
      "started_at": "2025-05-04T09:15:00Z",
      "completed_at": null,
      "transport_stop1": "bike",
      "transport_final": null,
      "code_attempts": 0,
      "score": null
    }
  },
  "leaderboard": []
}
```

---

## Admin UI (admin.py)

A FastAPI app serving a single HTML page. Keep it simple and functional.

**Features:**
- View all quests in a table
- Click a quest to edit it inline (all fields editable)
- Save button writes back to quests.json
- View live leaderboard (auto-refreshes every 10 seconds)
- View all active players and their current status
- Reset a player (for testing)
- Reset all players (nuclear option, with confirmation)

**Run on port 8080** separately from the MCP server.

---

## Error handling

All tool responses should be in-narrative where possible. Never return a raw error. Examples:

- Unknown player_id → `"Your player badge doesn't seem to exist. Did you register?"`
- Quest already complete → `"You've already made it to Build. Enjoy the conference."`
- Invalid state transition → `"You can't do that yet. Focus on the task at hand."`

---

## requirements.txt

```
mcp>=1.0.0
fastapi>=0.110.0
uvicorn>=0.29.0
```

---

## README.md should include

- How to run the MCP server
- How to run the admin UI
- How to connect an agent to the server (MCP config snippet)
- How to update quests.json manually
- How to reset game state for a new session

---

## Implementation notes

- All state is in-memory + written to JSON files. No database.
- Thread safety: use a simple file lock when writing state.json
- The server should work with `mcp dev server.py` for local testing
- Document zip URLs in quests.json are placeholders — the facilitator fills these in via the admin UI before the workshop
- Keep the MCP tool signatures simple — attendees will be calling these from their agents
