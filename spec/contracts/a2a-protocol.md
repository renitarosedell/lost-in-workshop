# Contract: A2A Expert Protocol

**Version**: 1.0.0
**Endpoint**: `POST https://<host>/a2a`
**Content-Type**: `application/json`

This document defines the HTTP contract for the organiser-hosted A2A transport expert
agent. It is the interface boundary between an attendee's agent (the client) and the
organiser's A2A expert (the server).

The A2A expert URL is delivered to the attendee's agent in the `register_player` response
(`stop1.a2a_expert_url`). Attendees call it directly with `httpx.post`; they do not need
an A2A SDK for the core workshop path.

---

## Request

```http
POST /a2a
Content-Type: application/json

{
  "message": "<natural-language transport question>"
}
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `message` | `str` | ✅ | Non-empty; natural-language question about transport between two locations |

**Example request**:
```json
{
  "message": "What's the best way to get from Moore Square to Glenwood South?"
}
```

---

## Response (200 OK)

```json
{
  "advice": "<natural-language transport recommendation>"
}
```

| Field | Type | Guaranteed |
|-------|------|------------|
| `advice` | `str` | ✅ Always present on 200 |

**Example response**:
```json
{
  "advice": "Rideshare is fastest at around 8 minutes. The GoRaleigh Route 11 bus also stops right at Moore Square if you prefer public transit."
}
```

**Response guarantee**: The advice ALWAYS includes one primary transport recommendation
and one alternative. It NEVER references city-specific knowledge beyond what is in the
Raleigh transport system prompt.

---

## Error Responses

| HTTP Status | Condition | Body |
|-------------|-----------|------|
| 400 | `message` field missing or empty | `{"error": "message is required"}` |
| 500 | Internal agent error | `{"error": "expert unavailable, try again"}` |

---

## Agent Behaviour Contract

The expert agent behind `POST /a2a`:

1. **Stateless**: no session tracking; each request is independent.
2. **Transport-scoped**: answers questions about transport between Raleigh locations only.
3. **Recommendation format**: always recommends a primary option and one alternative.
4. **No tool calls**: the expert does not call any MCP tools or external services.
5. **Language**: responds in the same language as the request (English for Raleigh events).

The expert is powered by the Microsoft Agent Framework with a Raleigh transport system
prompt. Its system prompt knowledge includes:
- GoRaleigh route numbers and stop locations for the quest areas
- GoTriangle regional bus routes connecting Raleigh to RTP
- Capital Bikeshare station locations at quest start/stop points
- Typical rideshare wait times and pickup points
- Walking distances and times between quest locations

---

## Attendee Code Pattern (Step 5)

```python
import httpx

a2a_url = player_registration["stop1"]["a2a_expert_url"]

response = httpx.post(
    a2a_url,
    json={"message": "What's the best way to get from Moore Square to Glenwood South?"},
    timeout=30
)
advice = response.json()["advice"]
```

---

## Bonus A Extension

Attendees implementing Bonus A (Build Your Own A2A Expert) MUST implement the same
contract:
- `POST /a2a` endpoint
- Accept `{"message": str}` body
- Return `{"advice": str}` on 200
- No authentication required (workshop context)

The game server reads the A2A expert URL from `city_config.yaml`. To use a local expert,
the facilitator or advanced attendee updates the `a2a_expert_url` value in `city_config.yaml`
and restarts the server (or updates it via the admin quest editor at runtime).
