# Implementation Plan: Lost in [City] Workshop

**Branch**: `001-lost-in-workshop` | **Date**: 2026-05-03 | **Spec**: [specification.md](specification.md)
**Input**: Feature specification from `spec/specification.md`

## Summary

Build a 60–90 minute hands-on AI workshop where attendees construct a Python agent that
connects to an organiser-hosted MCP game server and navigates a narrative city quest,
covering tool use (MCP), memory (context provider), A2A communication, and RAG. The
initial city is Raleigh, NC. The system is designed to be city-agnostic: all city-specific
values live in `city_config.yaml`; swapping cities requires only editing that file.

Technical approach: FastMCP game server + FastAPI admin dashboard on Azure Container Apps;
Microsoft Agent Framework for all agent code; thread-safe JSON for state; Azure Blob
Storage for document bundles.

---

## Technical Context

**Language/Version**: Python 3.11 (all components — game server, A2A expert, sample agent)
**Primary Dependencies**:
- Game server / admin: `fastmcp`, `fastapi`, `uvicorn`, `pyyaml`
- A2A expert: `fastapi`, `uvicorn`, Microsoft Agent Framework
- Sample agent: Microsoft Agent Framework, `python-dotenv`, `requests`

**Storage**: Thread-safe JSON file (`state.json`) via atomic-write + threading lock in
`storage.py`. Sufficient for ≤150 concurrent players; no database required.

**Testing**: Manual end-to-end (T4.3 dry-run); no automated test suite required for
workshop materials. The Fallback Code Guarantee is the primary correctness gate.

**Target Platform**: Azure Container Apps (Linux) for server components; developer laptop
(Windows/macOS/Linux, Python 3.11+) for attendee agent code.

**Project Type**: Workshop / educational materials + organiser-hosted web services.

**Performance Goals**: ≥150 concurrent players without data corruption; dashboard refresh
≤5 seconds; document bundle ≤5 MB per quest.

**Constraints**:
- Core workshop path completable in 60–90 minutes by a Python beginner with no Azure or
  agent-framework experience.
- Azure setup (Step 1) ≤15 minutes. First agent response ≤25 minutes from workshop start.
- Server code never present on the attendee-facing git branch.

**Scale/Scope**: ~150 concurrent users per event; 3 Raleigh quests (initial); 20 city-guide
chapters; 4 bonus exercises; 5 workshop steps + Step 1 standalone guide.

---

## Constitution Check

*GATE: Evaluated before Phase 0 research and re-checked after Phase 1 design.*

| # | Gate | Status | Notes |
|---|------|--------|-------|
| 1 | **Language & Runtime**: all `.py` files use Python 3.11+; `requirements.txt` for all deps | ✅ PASS | Mandated by constitution; enforced in all step files, server, and A2A expert |
| 2 | **Agent Framework**: Microsoft Agent Framework only; bare `openai` permitted only in `step2_hello_world.py` | ✅ PASS | No other framework appears; Step 2 raw-OpenAI exception documented |
| 3 | **Model Provider**: Azure OpenAI via AI Foundry only; no `api.openai.com` or `ml.azure.com` | ✅ PASS | `ai.azure.com` is the sole entry point; East US 2 default region |
| 4 | **City-Agnostic Architecture**: all city-specific values in `city_config.yaml`; none hardcoded in server or agent code | ✅ PASS | Verified in server design; enforced by compliance gate `grep` check |
| 5 | **Fallback Code Guarantee**: every step (1–5) has complete, tested, copy-paste-ready Python | ✅ PASS | `sample-agent/steps/step[1-5]_*.py` files; validated by T4.3 |
| 6 | **Non-Blocking Step Design**: fallback for step N produces same artifact as live path | ✅ PASS | `player_id` and all downstream artifacts produced by fallback steps |
| 7 | **Infrastructure Boundary**: server/admin code on separate branch; in `.gitignore` on attendee branch | ✅ PASS | `lost-in-raleigh/` and `a2a-expert/` gitignored on `lost-in-raleigh` branch |
| 8 | **Scoring Formula**: `max(0, 1000 − (50 × failed_code_attempts) − (10 × minutes_taken))` immutable | ✅ PASS | Implemented in `server.py` `declare_transport_final` handler; formula not configurable |
| 9 | **Workshop Timing**: core path ≤90 minutes | ✅ PASS | Step budgets: 15 + 10 + 15 + 10 + 20 = 70 min; validated by T4.3 dry-run |
| 10 | **Leaderboard & Concurrency**: milestone feed; ≥150 concurrent players; top 10–20 | ✅ PASS | Atomic writes + threading lock in `storage.py`; dashboard auto-refresh ≤5 s |
| 11 | **Documentation Tone**: second-person "you"; no unexplained jargon; zero prior Azure assumed for Step 1 | ✅ PASS | Tone enforced in workshop guide and Azure setup guide |

**Pre-research gate**: All 11 gates PASS. Proceeding to Phase 0.

---

## Project Structure

### Documentation (this feature)

```text
spec/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── mcp-tools.md
│   └── a2a-protocol.md
├── specification.md     # Feature spec
├── tasks.md             # Implementation tasks
└── constitution.md      # Project constitution
```

### Source Code (repository root)

```text
lost-in-workshop-v2/
├── .gitignore                        # gitignores lost-in-<city>/ and a2a-expert/
├── city-guide/
│   └── raleigh/                      # 20 Markdown chapters about Raleigh
├── sample-agent/
│   ├── steps/
│   │   ├── step1_foundry_test.py     # Azure connectivity test (Step 1)
│   │   ├── step2_hello_world.py      # Bare OpenAI hello-world (Step 2 only)
│   │   ├── step3_mcp_connect.py      # MCP + register_player (Step 3)
│   │   ├── step4_memory.py           # FileContextProvider (Step 4)
│   │   └── step5_quest.py            # Full quest loop (Step 5)
│   ├── agent.py                      # Reference agent (all steps combined)
│   ├── requirements.txt
│   └── .env.example
├── workshop/
│   ├── workshop.md                   # Master attendee guide (Steps 1–5)
│   ├── azure-foundry-setup.md        # Standalone Azure setup guide (Step 1)
│   └── bonus-exercises.md            # Bonus A–D instructions + code
└── instructions/
    └── mcp-server-prompt.md

# Admin branch only (gitignored on attendee branches):
lost-in-raleigh/
├── server.py                         # FastMCP game server
├── admin.py                          # FastAPI admin + embedded HTML/JS
├── storage.py                        # Atomic-write JSON persistence
├── city_config.yaml                  # Raleigh city + quest configuration
├── quests.json                       # Runtime quest state (gitignored at runtime)
├── state.json                        # Runtime player state (gitignored at runtime)
├── requirements.txt
└── Dockerfile
a2a-expert/
├── expert.py                         # FastAPI A2A transport endpoint
├── requirements.txt
└── Dockerfile
```

**Structure Decision**: Multi-component project (game server, A2A expert, sample agent,
workshop docs) sharing a single repo. Attendee-visible code lives at root level;
organiser-only code lives on the `admin` branch, gitignored on all other branches. No
`src/` or `tests/` wrapper — files are shallow and directly accessible for workshop use.

---

## MCP Game Server Design

**File:** `lost-in-raleigh/server.py`
**Framework:** FastMCP
**State:** Thread-safe JSON (`state.json`) via `storage.py`

### Resolved tool surface (I1/I2 from prior analysis)

`begin_session` and `start_quest` are **removed**. The spec workflow is:

1. `register_player(player_name)` → `player_id`, quest narrative, **A2A expert URL**,
   stop 1 location, and transport options all returned in one response.
2. `declare_transport_stop1(player_id, transport)` → stop 2 location, document bundle URL.
3. `submit_secret_code(player_id, code)` → success/failure + attempt count.
4. `declare_transport_final(player_id, transport)` → final score, completion message.

Embedding the A2A URL and stop 1 content in `register_player` eliminates an extra round
trip, aligns with the spec (FR-009), and makes Step 3 / Step 5 simpler for attendees.

### Tools exposed

| Tool | Input | Output |
|------|-------|--------|
| `register_player` | `player_name: str` | `player_id`, quest name, start narrative, stop 1 location + transport options, **A2A expert URL** |
| `declare_transport_stop1` | `player_id: str`, `transport: str` | stop 2 location + narrative, document bundle URL |
| `submit_secret_code` | `player_id: str`, `code: str` | `{"success": bool, "attempts": int, "message": str}` |
| `declare_transport_final` | `player_id: str`, `transport: str` | final score, completion message, quest name |

### State schema (`state.json`)

```json
{
  "players": {
    "<player_id>": {
      "player_name": "Alice",
      "quest_id": "glenwood_getaway",
      "milestones": {
        "registered_at": "2026-05-03T10:00:00Z",
        "stop1_at": null,
        "stop2_at": null,
        "finished_at": null
      },
      "failed_code_attempts": 0,
      "final_score": null,
      "transport_stop1": null,
      "transport_final": null
    }
  }
}
```

### Concurrency

`storage.py` uses atomic writes (write to temp file, `os.replace`) and a module-level
`threading.Lock`. All read-modify-write sequences acquire the lock. Sufficient for ≤150
concurrent players without a database.

---

## A2A Expert Agent Design

**File:** `a2a-expert/expert.py`
**Framework:** FastAPI + Microsoft Agent Framework
**Endpoint:** `POST /a2a`

Stateless agent with a Raleigh transport-expert system prompt. Receives a natural-language
question; returns natural-language advice. Calls no MCP tools.

```python
# Request
{ "message": "What's the best way to get from Moore Square to Glenwood South?" }

# Response
{ "advice": "Rideshare is fastest at around 8 minutes. The GoRaleigh Route 11 bus also stops right at Moore Square if you prefer public transit." }
```

System prompt includes: GoRaleigh route knowledge, GoTriangle options, Capital Bikeshare
station locations, typical rideshare wait times, walking distances between quest locations.
Always recommends one primary option and one alternative. City knowledge sourced from
`city-guide/raleigh/`.

---

## Admin Dashboard Design

**File:** `lost-in-raleigh/admin.py`
**Framework:** FastAPI with embedded HTML/JS (no build step)

### Endpoints

| Route | Method | Purpose |
|-------|--------|---------|
| `/` | GET | Dashboard HTML (single-page embedded) |
| `/api/players` | GET | All player states with milestone timestamps |
| `/api/leaderboard` | GET | Top 20 final scores |
| `/api/quests/{id}` | PUT | Edit quest content at runtime |
| `/api/players/{id}` | DELETE | Reset individual player (full state wipe) |
| `/api/players` | DELETE | Reset all players (with confirmation required from caller) |

### Dashboard panels

1. **Summary bar** — counts: registered / stop1 / stop2 / finished.
2. **Milestone feed** — all players, current milestone status, elapsed time. Auto-refreshes
   every 5 seconds via `setInterval` polling of `/api/players`.
3. **Leaderboard** — top 20, player name, quest name, score, completion time. Refreshes
   with milestone feed.
4. **Quest editor** — JSON textarea per quest; PUT on save.
5. **Admin controls** — "Reset player" button per row; "Reset all" button with confirm
   dialog.

**Reset semantics**: DELETE clears all milestones, failed_code_attempts, final_score,
transport choices. The player_id key is removed. The player can re-register as a fresh
participant with a new player_id.

---

## Workshop Agent Architecture

Progressive reveal: each step file is self-contained, runnable, and functionally equivalent
to the attendee's live code. Fallback = copy the appropriate step file.

| Step | File | Agent capabilities |
|------|------|-------------------|
| 1 | `step1_foundry_test.py` | Bare `openai` SDK call; proves Azure connectivity |
| 2 | `step2_hello_world.py` | `ChatCompletionAgent`; answers one city question |
| 3 | `step3_mcp_connect.py` | + `MCPToolProvider`; calls `register_player` |
| 4 | `step4_memory.py` | + `FileContextProvider`; persists `player_id` |
| 5 | `step5_quest.py` | + A2A HTTP call + document download/parse; autonomous quest loop |

`agent.py` — complete reference agent combining all steps. Used by facilitators and as
the gold-standard fallback for Step 5.

**A2A pattern in Step 5**: The agent receives the A2A expert URL from the `register_player`
response (stored in memory). It makes a direct `httpx.post` call to the A2A endpoint with a
natural-language transport question, then parses the `advice` field and passes that to
`declare_transport_stop1`.

---

## City Configuration Schema

`city_config.yaml` is the single source of truth for all city-specific content. Loaded at
server startup; never reloaded at runtime (restart required to pick up changes).

```yaml
city:
  name: "Raleigh"
  final_destination:
    name: "NC Biotech Center"
    address: "1 Alexander Drive, Research Triangle Park, NC"
    narrative: "The NC Biotech Center is the hub of the region's life sciences..."

quests:
  - id: glenwood_getaway
    name: "The Glenwood Getaway"
    start:
      name: "Moore Square"
      description: "A historic public square in downtown Raleigh..."
    stop1:
      location:
        name: "Glenwood South"
        description: "Raleigh's premier entertainment and dining district..."
      transport_options:
        - { id: goRaleigh_bus, label: "GoRaleigh bus", description: "Route 11 from Moore Square." }
        - { id: rideshare, label: "Rideshare", description: "8-min drive; pickup on Fayetteville St." }
        - { id: bike, label: "Bike", description: "Capital Bikeshare at Moore Square. 12-min ride." }
        - { id: walk, label: "Walk", description: "15-min walk along Glenwood Avenue." }
      a2a_expert_url: "https://<host>/a2a"
      narrative: "You need to get to Glenwood South. Ask the local transport expert..."
    stop2:
      location:
        name: "Cameron Village"
        description: "One of the first planned shopping centres in the US South..."
      document_bundle_url: "https://<host>/bundles/raleigh/glenwood_getaway.zip"
      secret_code: "GLENWOOD42"
      narrative: "Hidden in the district's history is the code you need..."
    end:
      transport_options:
        - { id: rideshare, label: "Rideshare", description: "Direct ride, ~20 minutes." }
        - { id: goTriangle, label: "GoTriangle bus", description: "Route 100 to RTP." }
      narrative: "Final sprint to the NC Biotech Center — choose your transport wisely."
  # museum_mile and warehouse_run follow the same structure
```

Note: `a2a_expert_url` is stored per stop1 in the config, allowing per-quest A2A expert
routing for future multi-city support. For Raleigh all three quests share the same URL.

---

## Document Bundles (RAG Challenge)

Each quest has a ZIP containing 5–8 Markdown files from `city-guide/raleigh/`. Exactly one
file per ZIP contains the secret code embedded in natural-language prose.

**Example embedding:**
> *"The founding committee of the Glenwood South Business Association adopted the rally code GLENWOOD42 at their inaugural meeting in 1987."*

Bundles are hosted on Azure Blob Storage (public read container). Bundle URLs are stored in
`city_config.yaml` and returned by `declare_transport_stop1`.

**Size constraint**: each ZIP ≤5 MB (SC-008 / constitution NFR). Checked as part of T2.2
Done-when criteria.

---

## Azure AI Foundry Setup (Step 1)

Documented in `workshop/azure-foundry-setup.md`. Flow:

1. Redeem education code at the event-provided link.
2. Sign in to `ai.azure.com`.
3. Create Resource Group: `raleigh-workshop`, region East US 2.
4. Create Foundry Hub in the resource group.
5. Create a Project inside the Hub.
6. Deploy `gpt-4o-mini` (Models → Deploy). Note the deployment name.
7. Copy endpoint URL and API key from the project Connections page.
8. Copy `.env.example` → `.env`; fill in three values.
9. Run `step1_foundry_test.py` to verify the connection.

Each sub-step: action, expected visual result, one-line troubleshooting note.

---

## Deployment Architecture

```
Internet
  │
  ├── https://<host>/mcp    → lost-in-raleigh container (FastMCP + admin on :8000)
  └── https://<host>/a2a    → a2a-expert container (FastAPI on :8000)

Document ZIPs: Azure Blob Storage (public read container)
```

Both containers on the same Azure Container Apps environment. 1–3 replicas (bursty but
low-volume workshop traffic). State is file-based; single replica recommended unless a
shared persistent volume is configured.

---

## Tech Stack Summary

| Component | Technology |
|-----------|------------|
| MCP game server | FastMCP + FastAPI, Python 3.11 |
| Admin dashboard | FastAPI + vanilla JS (no build step) |
| A2A expert | FastAPI + Microsoft Agent Framework, Python 3.11 |
| Attendee agent | Microsoft Agent Framework + Azure OpenAI |
| State persistence | Thread-safe JSON file (≤150 players) |
| Hosting | Azure Container Apps |
| Model | Azure OpenAI `gpt-4o-mini` (default) or `gpt-4o` via Foundry |
| Document storage | Azure Blob Storage (public container) |
| City config | YAML file loaded at server startup |
