# Contract: MCP Game Server Tools

**Version**: 1.0.0
**Server**: `https://<host>/mcp` (FastMCP streamable HTTP transport)
**Attendee connection**: `MCPToolProvider(url="https://<host>/mcp")`

This document defines the exact MCP tool contracts exposed by the Lost in [City] game
server. Attendee agents interact with the game exclusively through these four tools.

---

## Tool: `register_player`

Registers a new player and returns the full quest assignment, including stop 1 content and
the A2A expert URL. This is the only tool that does not require a `player_id`.

### Input

| Parameter | Type | Required | Constraints |
|-----------|------|----------|-------------|
| `player_name` | `str` | ✅ | Non-empty; max 64 chars; displayed on leaderboard |

### Output (on success)

```json
{
  "player_id": "3f2a1b4c-...",
  "quest_name": "The Glenwood Getaway",
  "start_narrative": "You find yourself at Moore Square, the historic heart of downtown Raleigh...",
  "stop1": {
    "location_name": "Glenwood South",
    "location_description": "Raleigh's premier entertainment and dining district...",
    "transport_options": [
      { "id": "goRaleigh_bus", "label": "GoRaleigh bus", "description": "Route 11 from Moore Square." },
      { "id": "rideshare",     "label": "Rideshare",     "description": "8-min drive; pickup on Fayetteville St." },
      { "id": "bike",          "label": "Bike",          "description": "Capital Bikeshare at Moore Square. 12-min ride." },
      { "id": "walk",          "label": "Walk",          "description": "15-min walk along Glenwood Avenue." }
    ],
    "a2a_expert_url": "https://<host>/a2a",
    "narrative": "You need to get to Glenwood South. Ask the local transport expert for the best route..."
  }
}
```

### Error responses

| Condition | Response |
|-----------|----------|
| `player_name` empty or missing | `{"error": "player_name is required"}` |

### State effect

Creates a new `Player` record in `state.json` with `milestones.registered_at` set to
current UTC timestamp. Quest is assigned uniformly at random from the config quest list.

---

## Tool: `declare_transport_stop1`

Records the player's transport choice for the first leg and returns stop 2 content.

### Input

| Parameter | Type | Required | Constraints |
|-----------|------|----------|-------------|
| `player_id` | `str` | ✅ | Must be a registered, not-yet-advanced-past-stop1 player |
| `transport` | `str` | ✅ | Must match one of the `id` values in the quest's stop1 `transport_options` |

### Output (on success)

```json
{
  "stop2": {
    "location_name": "Cameron Village",
    "location_description": "One of the first planned shopping centres in the US South...",
    "document_bundle_url": "https://<host>/bundles/raleigh/glenwood_getaway.zip",
    "narrative": "Hidden in the district's history is the code you need..."
  }
}
```

### Error responses

| Condition | Response |
|-----------|----------|
| `player_id` not found | `{"error": "player not found"}` |
| Player already past stop 1 | `{"error": "stop 1 already complete"}` |
| `transport` not a valid option id | `{"error": "invalid transport choice"}` |

### State effect

Sets `Player.milestones.stop1_at` to current UTC timestamp. Sets `Player.transport_stop1`.

---

## Tool: `submit_secret_code`

Checks the player's secret code guess for the RAG challenge.

### Input

| Parameter | Type | Required | Constraints |
|-----------|------|----------|-------------|
| `player_id` | `str` | ✅ | Must be a registered player who has completed stop 1 |
| `code` | `str` | ✅ | The attendee's code guess; compared case-insensitively, whitespace-trimmed |

### Output (on success — correct code)

```json
{
  "success": true,
  "message": "Correct! You've cracked the code.",
  "attempts": 1
}
```

### Output (on failure — wrong code)

```json
{
  "success": false,
  "message": "That's not the right code. Try again.",
  "attempts": 2
}
```

### Error responses

| Condition | Response |
|-----------|----------|
| `player_id` not found | `{"error": "player not found"}` |
| Player has not completed stop 1 | `{"error": "stop 1 not yet complete"}` |
| Player already completed stop 2 | `{"error": "stop 2 already complete"}` |

### State effect

**Wrong code**: increments `Player.failed_code_attempts`. No milestone change.
**Correct code**: sets `Player.milestones.stop2_at` to current UTC. No attempt limit.

---

## Tool: `declare_transport_final`

Records the player's final transport choice and calculates + stores the final score.

### Input

| Parameter | Type | Required | Constraints |
|-----------|------|----------|-------------|
| `player_id` | `str` | ✅ | Must have completed stop 2 |
| `transport` | `str` | ✅ | Must match one of the `id` values in the quest's `end.transport_options` |

### Output (on success)

```json
{
  "message": "Quest complete! You've arrived at the NC Biotech Center.",
  "quest_name": "The Glenwood Getaway",
  "final_score": 920,
  "completion_time": "2026-05-03T10:42:17Z"
}
```

### Error responses

| Condition | Response |
|-----------|----------|
| `player_id` not found | `{"error": "player not found"}` |
| Player has not completed stop 2 | `{"error": "stop 2 not yet complete"}` |
| Player already finished | `{"error": "quest already finished"}` |
| `transport` not a valid option id | `{"error": "invalid transport choice"}` |

### State effect

Sets `Player.milestones.finished_at`. Sets `Player.transport_final`. Calculates and stores
`Player.final_score` using the immutable formula:
`max(0, 1000 − (50 × failed_code_attempts) − (10 × floor(minutes_taken)))`.

---

## Admin API (non-MCP, not used by attendee agents)

| Method | Route | Purpose |
|--------|-------|---------|
| GET | `/api/players` | All player states |
| GET | `/api/leaderboard` | Top 20 final scores |
| PUT | `/api/quests/{id}` | Update quest config at runtime |
| DELETE | `/api/players/{id}` | Full-reset single player |
| DELETE | `/api/players` | Full-reset all players |

These endpoints are called by the dashboard's JavaScript polling loop and by facilitators.
They are not MCP tools and are not accessible from the attendee's `MCPToolProvider`.
