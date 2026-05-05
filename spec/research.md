# Research: Lost in [City] Workshop

**Generated**: 2026-05-03
**Plan**: [plan.md](plan.md)
**Purpose**: Resolve all technical unknowns identified during Technical Context analysis.

No NEEDS CLARIFICATION items remained in the Technical Context — the provided plan input
contained comprehensive technical decisions. This document records the research and
rationale for each decision area so future contributors understand why choices were made.

---

## Decision 1 — MCP Framework: FastMCP

**Decision**: Use FastMCP for the game server.

**Rationale**:
- FastMCP provides a high-level Python API for exposing tools via the MCP protocol;
  attendees connect to it using the standard `MCPToolProvider` in the Microsoft Agent
  Framework with no special configuration.
- It is built on FastAPI/Starlette, which means the admin dashboard can live in the same
  process (or a separate FastAPI sub-app), sharing a single port and container.
- No external broker or protocol gateway required; the server is a single Python file.

**Alternatives considered**:
- Raw FastAPI + custom MCP serialisation: more control, but far more boilerplate; would
  complicate the server-side task and add no benefit at workshop scale.
- LangChain tool-server: excluded by Constitution §2 (no LangChain in workshop materials).

---

## Decision 2 — Agent Framework: Microsoft Agent Framework

**Decision**: All agent code uses the Microsoft Agent Framework.

**Rationale**: Mandated by Constitution §2. The framework provides:
- `ChatCompletionAgent` — a thin, comprehensible wrapper over the chat-completion loop.
- `MCPToolProvider` — connects to any MCP server by URL; one line of code for attendees.
- `FileContextProvider` — persists arbitrary key-value context to a local JSON file; ideal
  for the Step 4 memory exercise.
- `AzureChatCompletionClient` — Azure OpenAI backend; works with the `.env` values from
  Step 1 without extra configuration.

**Alternatives considered**:
- Semantic Kernel: feature-rich but heavier; excluded by constitution.
- AutoGen: excluded by constitution.
- Raw OpenAI SDK: permitted only in Step 2 to establish baseline comprehension.

---

## Decision 3 — Tool Surface: 4 Tools (drop begin_session / start_quest)

**Decision**: The MCP game server exposes exactly four tools:
`register_player`, `declare_transport_stop1`, `submit_secret_code`,
`declare_transport_final`.

**Rationale**:
- `begin_session` had no spec requirement and no attendee-facing value; removed (issue I1).
- `start_quest` was a second round-trip after `register_player` returning the same data
  the spec already attributed to `register_player`; merged (issue I2).
- Delivering stop 1 content, transport options, and A2A expert URL in the
  `register_player` response satisfies FR-001 and FR-009 in one call, simplifying
  Step 3 code significantly (attendee does not need to call a second tool before Step 5).
- Four tools maps cleanly to the four quest phases described in the spec.

**Alternatives considered**:
- Keep `start_quest` as a separate call: adds attendee complexity in Step 5 without
  teaching a new concept; rejected.
- Lazy-load stop 1 data (attendee fetches on demand): increases Step 5 complexity;
  rejected.

---

## Decision 4 — State Persistence: Thread-Safe JSON File

**Decision**: `storage.py` uses a module-level `threading.Lock` and `os.replace` for
atomic file writes. No database.

**Rationale**:
- 150 concurrent players is the target maximum; all writes are short lock-held operations
  (read JSON, mutate dict, write to temp, `os.replace`). P99 latency under load is well
  under 1 ms for this pattern.
- A SQLite or PostgreSQL database would require attendees to understand database
  configuration — or require the facilitator to provision one — for no benefit at this
  scale.
- `os.replace` is atomic on POSIX (Linux/Azure Container Apps); on Windows it is
  effectively atomic for single-file state of this size.
- `quests.json` and `state.json` are gitignored at runtime; the container starts with an
  empty state derived from `city_config.yaml`.

**Alternatives considered**:
- SQLite: adds `sqlite3` or SQLAlchemy dependency; migration burden for config changes;
  rejected.
- Redis: adds infrastructure complexity; rejected.
- Per-player files: fan-out write pattern avoids a global lock but complicates leaderboard
  reads; rejected.

---

## Decision 5 — A2A Protocol: Simple HTTP POST (no A2A SDK)

**Decision**: The A2A expert exposes `POST /a2a` accepting `{"message": str}` and
returning `{"advice": str}`. Attendee agents call it with `httpx.post`.

**Rationale**:
- The workshop's A2A teaching moment is about *calling* an external agent, not about
  implementing the A2A protocol specification. A simple JSON endpoint teaches the concept
  without A2A SDK overhead.
- The Microsoft Agent Framework's A2A SDK is not yet stable enough to mandate as a
  teaching dependency (as of 2026-05-03).
- `httpx.post` is one line of synchronous code — appropriate for the 10-minute Step 5
  sub-task budget.
- Bonus A (Build Your Own A2A Expert) teaches the server side; `POST /a2a` is the
  simplest possible contract to implement.

**Alternatives considered**:
- Use the official A2A Python SDK: adds installation and auth complexity; not yet
  production-stable; rejected for core path (acceptable for Bonus A advanced guide).
- gRPC: significantly more complex; no benefit at workshop scale; rejected.

---

## Decision 6 — Document Bundle Hosting: Azure Blob Storage

**Decision**: Document bundle ZIPs are hosted on Azure Blob Storage in a public-read
container. URLs stored in `city_config.yaml`.

**Rationale**:
- Attendees need to download ZIPs without authentication; public-read blob URLs are the
  simplest way to serve static files from Azure infrastructure the facilitator already
  controls.
- GitHub Release assets are a viable alternative but couple bundle management to git
  releases; rejected.
- Bundles are static after creation; no CDN or dynamic serving required.

**Alternatives considered**:
- GitHub Releases: viable but couples content updates to git; harder to update before an
  event; rejected.
- Azure Static Web Apps / CDN: overkill for ~5 MB files; rejected.

---

## Decision 7 — Admin Dashboard: Embedded HTML/JS, No Build Step

**Decision**: Dashboard HTML and JavaScript are embedded as Python string literals inside
`admin.py`. Vanilla JS, no framework, no build step.

**Rationale**:
- Facilitators interact with the dashboard via browser; they do not need to build or
  deploy a separate frontend asset.
- Auto-refresh via `setInterval` polling of existing REST endpoints satisfies the ≤5
  second refresh NFR with zero infrastructure additions.
- Keeping all admin code in one file (`admin.py`) reduces deployment complexity and makes
  the admin branch trivially maintainable.

**Alternatives considered**:
- React/Vue SPA: requires a build step and separate static file serving; no benefit for
  a facilitator-only dashboard; rejected.
- Server-sent events / WebSockets: more complex than polling; polling is sufficient for
  ≤5 s refresh at ≤150 players; rejected.

---

## Decision 8 — Deployment: Azure Container Apps

**Decision**: Both server containers deploy to Azure Container Apps in the same
environment. 1–3 replicas. State stored in a mounted persistent volume (or single-replica
for simplicity).

**Rationale**:
- Azure Container Apps is the lightest-weight Azure hosting option that supports container
  images, custom domains, and scale-to-zero (cost-saving between events).
- The workshop's Azure theme means the facilitator already has Azure access and
  familiarity.
- File-based state works with single-replica or with a shared persistent volume; the
  simplest configuration (single replica, local file) avoids distributed state complexity.

**Alternatives considered**:
- Azure App Service (containers): slightly heavier, similar cost; no advantage; not used.
- Azure Kubernetes Service: significant overhead for two containers; rejected.
- Local Docker Compose: insufficient for multi-attendee events; used only for local
  development / Bonus E.

---

## Decision 9 — Raleigh City Guide: Reorganise city-guide/ to city-guide/raleigh/

**Decision**: The 20 city-guide Markdown chapters must live at `city-guide/raleigh/` (not
the flat `city-guide/` that currently holds San Francisco content).

**Rationale**:
- The city-agnostic architecture (Constitution §4) requires each city's content to be
  isolated so that adding a second city creates `city-guide/<city>/` without conflict.
- The existing flat `city-guide/` content is for San Francisco (visible from
  `14_bay_and_waterfront.md`); it must be removed and replaced with Raleigh content
  (issue I3 from analysis).
- The plan task list must include a reorganisation task before T2.1.

**Implementation note**: Add task T0.1 to tasks.md — migrate `city-guide/` to
`city-guide/raleigh/` and remove SF content before writing Raleigh chapters.

---

## Decision 10 — Scoring: Immutable Formula in server.py

**Decision**: The scoring formula is implemented as a single expression in
`declare_transport_final` and is not configurable via `city_config.yaml`.

**Rationale**: Constitution §8 declares the formula immutable; making it a config value
would allow accidental mutation. Hard-coding the formula in the handler is the simplest
compliant implementation. The compliance gate requires a `grep` match of the exact
expression before merge.

---

## Open Questions Closed

All issues from the prior `speckit.analyze` report are resolved:

| Issue | Resolution |
|-------|-----------|
| I1 — `begin_session` unexplained | Removed; not in spec or plan |
| I2 — `start_quest` not in spec | Removed; data merged into `register_player` response |
| I5 — A2A URL delivery | `register_player` response includes `a2a_expert_url` from config |
| G1 — `sample-agent/steps/` not tasked | Add to tasks as sub-task under T4.2 |
| I3 — SF content in city-guide/ | Add T0.1: reorganise to `city-guide/raleigh/` |
| I4 — lost-in-sf/ migration | `lost-in-sf/` on `lost-in-raleigh` branch; refactor in T1.1 |
| G2 — Scoring not explicitly tasked | Add bullet to T1.3; compliance gate covers it |
| G3 — T5.5 truncated | Complete in tasks.md |
| G4 — No concurrency test | Add to T6.4 smoke-test checklist |
| A1 — Bundle size not in T2.2 Done-when | Add "each ZIP ≤5 MB" to T2.2 |
| G5 — agent.py not tasked | Add sub-task to T4.2 or T4.3 |
| A2 — Reset semantics ambiguous | Full state wipe; documented in plan Reset semantics section |
