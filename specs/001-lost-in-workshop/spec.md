# Feature Specification: Lost in [City] Workshop

**Feature Branch**: `001-lost-in-workshop`
**Created**: 2026-05-03
**Status**: Draft

---

## Vision

A 60–90-minute hands-on AI workshop where attendees build a Python agent from scratch. The
agent connects to a centrally-hosted game server and navigates a narrative quest through a
real city, learning core agentic concepts — tool use, memory, agent-to-agent (A2A)
communication, and retrieval-augmented generation (RAG) — by actually using them, not by
watching a demo.

The city and final destination change per event. The learning arc, game mechanics, and code
structure remain constant.

---

## Personas

### Attendee
- Basic Python knowledge; may have never used Azure, an LLM API, or an agent framework.
- Has a laptop with Python 3.11+ installed and an internet connection.
- Receives a temporary Azure education subscription at the start of the event.
- **Goal:** build a working agent, complete the quest, appear on the leaderboard.

### Facilitator
- Sets up and monitors the organiser-hosted infrastructure before and during the event.
- Manages the game via an admin dashboard (no file editing during the event).
- **Goal:** smooth event with all attendees able to connect and play.

---

## User Scenarios & Testing

### User Story 1 — Attendee Completes the Core Workshop Path (Priority: P1)

An attendee with basic Python knowledge follows the five-step workshop path, building a
working agent that registers with the game server, navigates three quest legs (tool use,
memory, A2A communication, RAG), and finishes with their score on the leaderboard — all
within 60–90 minutes.

**Why this priority**: This is the primary deliverable of the workshop. Everything else
(bonus exercises, admin tools, city configuration) exists to support this outcome.

**Independent Test**: Given only the workshop guide and a pre-filled `.env` template, a
first-time attendee can complete all five steps and have their final score appear on the
leaderboard without facilitator intervention.

**Acceptance Scenarios**:

1. **Given** an attendee with a fresh Azure education subscription code, **When** they
   follow the Azure AI Foundry setup guide (Step 1), **Then** they have a working `.env`
   file and a test call to the model returns a response — within 15 minutes.

2. **Given** a working `.env` file, **When** the attendee completes Step 2 (Hello World
   Agent), **Then** their agent answers "What is [city] famous for?" without errors —
   within 10 minutes.

3. **Given** a Hello World agent, **When** the attendee completes Step 3 (Connect to MCP
   Server), **Then** their agent prints a `player_id` returned by the game server —
   within 15 minutes.

4. **Given** a `player_id`, **When** the attendee completes Step 4 (Add Player Memory)
   and restarts the agent, **Then** the agent resumes the quest with the same `player_id`
   without re-registering — within 10 minutes.

5. **Given** a memory-enabled, registered agent, **When** the attendee completes Step 5
   (Play the Quest), **Then** the agent autonomously completes all three quest legs (A2A
   stop, RAG stop, final leg) and the attendee's score appears on the live leaderboard —
   within 20 minutes.

---

### User Story 2 — Facilitator Manages the Event via the Admin Dashboard (Priority: P2)

A facilitator monitors all player progress in real time and can reset individual players or
all players from a browser, without editing any files or restarting the server.

**Why this priority**: Facilitator control is essential to event reliability. Stuck players
must be unblocked quickly; the facilitator must have tools to do this without developer help.

**Independent Test**: Given only the dashboard URL, a facilitator can locate a specific
player, reset their progress, and confirm the reset within 2 minutes — without any file
system access.

**Acceptance Scenarios**:

1. **Given** the event is running with active players, **When** the facilitator opens the
   dashboard, **Then** they see a live milestone feed with all players, their current
   progress status, and elapsed time — refreshed within ≤5 seconds.

2. **Given** a player is stuck, **When** the facilitator clicks "Reset player" next to
   that player's row, **Then** the player's progress is cleared and they can re-register
   as if new — without any server restart.

3. **Given** the event needs a full reset, **When** the facilitator clicks "Reset all
   players" and confirms the prompt, **Then** all player state is cleared within 5 seconds.

4. **Given** players are finishing the quest, **When** the facilitator views the
   leaderboard, **Then** it shows up to the top 20 final scores with player name, quest
   name, score, and completion time — updated within ≤5 seconds of a player finishing.

---

### User Story 3 — Attendee Explores Bonus Exercises After Completing the Core Path (Priority: P3)

An attendee who finishes the five-step core path early can work through one or more bonus
exercises, each teaching a distinct advanced concept, without interfering with the live
game server or other attendees' sessions.

**Why this priority**: Bonus exercises deepen learning for fast finishers but are entirely
optional. They MUST NOT block core quest completion for any attendee.

**Independent Test**: Given a completed Step 5 agent, an attendee can pick any single
bonus exercise, follow its instructions, and have a demonstrably working result — without
modifying their core quest code.

**Acceptance Scenarios**:

1. **Given** a completed core agent, **When** the attendee follows Bonus A (Build Your Own
   A2A Expert), **Then** they have a locally-running agent endpoint the game server calls
   in place of the organiser's expert.

2. **Given** a completed core agent, **When** the attendee follows Bonus B (Streaming
   Responses), **Then** their agent outputs tokens to the console as they arrive, not as a
   complete response.

3. **Given** a completed core agent, **When** the attendee follows Bonus C (Multi-Agent
   Orchestration), **Then** a Planner agent and a Runner agent cooperate to complete the
   quest end-to-end.

4. **Given** a completed core agent, **When** the attendee follows Bonus D (Evaluate Your
   Agent), **Then** a harness script runs the quest three times and outputs a summary table
   with time to completion, failed code attempts, and final score per run.

---

### Edge Cases

- What happens when Azure provisioning takes longer than 15 minutes? The facilitator has
  pre-provisioned fallback credentials or a demo `.env` an attendee can borrow to proceed.
- What happens when an agent submits a wrong secret code? The server returns a failure
  response, deducts 50 points from the final score, and allows the agent to try again with
  no attempt limit.
- What happens when two attendees register at exactly the same time? The server assigns
  distinct `player_id` values and quest assignments without data corruption.
- What happens when an attendee's agent is disconnected mid-quest? Player memory preserves
  the `player_id`; re-running the agent resumes from the last recorded milestone.
- What happens if a Bonus A attendee's local expert goes offline? The game server should
  document a fallback path to the organiser-hosted expert URL.

---

## Requirements

### Functional Requirements

**Registration & Quest Assignment**

- **FR-001**: An agent MUST be able to register a player by name and receive a unique
  `player_id` and a randomly assigned quest (including start location, stop 1, transport
  options, and the A2A expert URL) in return.
- **FR-002**: Each quest MUST include: start location, stop 1 location, stop 2 location,
  transport options (with labels and descriptions), secret code, document bundle URL, final
  destination, and narrative text per leg — all sourced exclusively from the city
  configuration file.

**Step Progression (Quest Legs)**

- **FR-003**: An agent MUST be able to query the A2A expert with a natural-language
  transport question and receive natural-language advice in return before declaring a
  transport choice.
- **FR-004**: An agent MUST be able to declare a transport choice for stop 1 and receive
  the stop 2 location and document bundle URL in return.
- **FR-005**: An agent MUST be able to download a ZIP of city-guide documents from the
  server-provided URL and search them to extract a hidden secret code embedded in natural
  prose.
- **FR-006**: An agent MUST be able to submit a secret code; a correct submission MUST
  advance the quest, and an incorrect submission MUST return a failure indicator and deduct
  50 points from the final score while allowing retry.
- **FR-007**: An agent MUST be able to declare a transport choice for the final leg and
  receive a final score and completion message in return.

**Player Memory**

- **FR-008**: The agent MUST persist the `player_id` locally so that stopping and
  restarting the agent resumes the same quest session without re-registering.

**A2A Communication**

- **FR-009**: The A2A expert URL MUST be delivered to the agent by the game server (not
  hardcoded in attendee code), so swapping the A2A expert requires no attendee-side change.

**Scoring**

- **FR-010**: The server MUST calculate the final score as
  `max(0, 1000 − (50 × failed_code_attempts) − (10 × minutes_taken))` and record it at
  quest completion. This formula is immutable and applies to every city and event.

**Leaderboard & Dashboard**

- **FR-011**: The dashboard MUST display a milestone feed listing all players, their
  current milestone status (`registered → stop 1 complete → stop 2 complete →
  quest finished`), and elapsed time since registration — auto-refreshed every ≤5 seconds.
- **FR-012**: The dashboard MUST display a leaderboard of up to the top 20 final scores,
  showing player name, quest name, score, and completion time.
- **FR-013**: The admin panel MUST allow the facilitator to reset an individual player's
  progress or all players' progress from the browser without file system access or server
  restarts.

**City Configuration**

- **FR-014**: All city-specific values (city name, neighbourhood names, quest locations,
  transport options, secret codes, document bundle URLs, final destination, narrative text)
  MUST be sourced from a single city configuration file.
- **FR-015**: Changing the event city MUST require only editing the city configuration
  file — no changes to server code, agent code, or workshop instructions.

**Infrastructure Boundary**

- **FR-016**: The MCP game server, A2A expert agent, and admin dashboard MUST be
  organiser-hosted. Attendees MUST NOT be required to run any server infrastructure.
- **FR-017**: All server and admin code MUST be absent from the attendee-facing repository
  branch.

**Fallback Code**

- **FR-018**: Every workshop step (1–5) MUST include complete, tested, copy-paste-ready
  code that is functionally equivalent to what the attendee is building, so any attendee
  can proceed to the next step regardless of whether they successfully completed the
  prior one.

**Bonus Exercises**

- **FR-019**: Bonus A MUST provide instructions and starter code enabling an attendee to
  build a locally-running A2A expert endpoint that the game server can call.
- **FR-020**: Bonus B MUST provide instructions and code showing streaming token-by-token
  output in the console.
- **FR-021**: Bonus C MUST provide instructions and code for a Planner + Runner multi-agent
  system that completes the quest cooperatively.
- **FR-022**: Bonus D MUST provide an evaluation harness that runs the quest three times
  and reports time to completion, failed code attempts, and final score per run.

---

### Key Entities

- **Player**: An attendee registered with the game server. Attributes: `player_id`,
  `player_name`, assigned quest, milestone timestamps (`registered_at`, `stop1_at`,
  `stop2_at`, `finished_at`), failed code attempt count, final score, transport choices.
- **Quest**: A city-specific narrative path. Attributes: quest ID, name, start location,
  stop 1, stop 2, end (final destination), transport options per leg, secret code,
  document bundle URL, narrative text per leg.
- **City Config**: The single configuration file that defines all quests for an event city.
  One per event; swapping cities means swapping this file.
- **Milestone**: A tracked event in a player's journey, recording a UTC timestamp:
  `registered`, `stop_1_complete`, `stop_2_complete`, `quest_finished`.
- **Leaderboard Entry**: Persisted on quest completion. Contains: player name, quest name,
  final score, completion timestamp.
- **Document Bundle**: A ZIP of city-guide Markdown chapters for a specific quest. Exactly
  one chapter in each bundle contains the secret code embedded in natural prose.
- **A2A Expert**: The organiser-hosted transport advisor. Stateless. Accepts a
  natural-language question about transport options and returns natural-language advice.

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: Every attendee who reaches Step 3 successfully receives a `player_id` and
  quest assignment from the game server (0% registration failure rate).
- **SC-002**: Every attendee who reaches Step 5 can proceed — either with their own agent
  code or the provided fallback — without facilitator intervention (0% blocked rate).
- **SC-003**: The core path (Steps 1–5) is completable in 60–90 minutes by an attendee
  with basic Python knowledge and no prior cloud or agent-framework experience.
- **SC-004**: Azure AI Foundry setup (Step 1) is completable in ≤15 minutes from
  subscription code to first successful model response.
- **SC-005**: The first agent response (Step 2) is achievable within 25 minutes of the
  workshop start.
- **SC-006**: The game server supports ≥150 concurrent players without data corruption,
  duplicate `player_id` assignments, or lost milestone updates.
- **SC-007**: The dashboard milestone feed updates within ≤5 seconds of any player
  advancing a milestone.
- **SC-008**: Each document bundle ZIP is ≤5 MB in size.
- **SC-009**: An agent that reads all documents in its assigned bundle can locate and
  extract the secret code without human assistance.
- **SC-010**: The facilitator can reset any individual player or all players from the
  dashboard in ≤2 minutes, with no file system access required.

---

## Assumptions

- Attendees arrive with Python 3.11+ installed on their laptop and a working internet
  connection. Python installation is not part of the workshop.
- Attendees receive a temporary Azure education subscription code at the event start;
  subscription code redemption time is not counted in the 60–90-minute window.
- The game server, A2A expert, and admin dashboard are deployed and verified by the
  facilitator before the event starts (see pre-event checklist).
- Document bundle ZIP files are publicly accessible at their URLs — no authentication
  required for download.
- The game server delivers the A2A expert URL to the attendee's agent as part of the
  registration or quest-start response, so attendees do not configure it manually.
- Wrong secret code attempts are retryable; there is no maximum attempt limit, but each
  wrong attempt deducts 50 points.
- "Reset player" clears all progress (milestones, failed attempts, score, transport
  choices) so the player can re-register as a fresh participant — partial state is not
  preserved.
- Raleigh is the initial event city; the three Raleigh quests and all 20 city-guide
  chapters must be in place before the first event runs.
- The Raleigh final destination for all three quests is the NC Biotech Center.

---

## City Configuration: Raleigh (Initial Event)

### Raleigh Quests

| Quest | Start | Stop 1 | Stop 2 | End |
|-------|-------|--------|--------|-----|
| The Glenwood Getaway | Moore Square | Glenwood South | Cameron Village | NC Biotech Center |
| The Museum Mile | City Market | NC Museum of Art area | North Hills | NC Biotech Center |
| The Warehouse Run | Warehouse District | Five Points | Boylan Heights | NC Biotech Center |

### City Content Requirements

Each event city requires:

1. A city configuration file defining the city name, final destination, and quest
   definitions (each with: start location, stop 1, stop 2, transport options, secret code,
   document bundle URL, narrative text).
2. A set of city-guide Markdown documents (≥20 chapters covering the city's
   neighbourhoods, transport, culture, history, food, and events).
3. One document ZIP per quest, assembled from the city-guide chapters, with the secret
   code embedded in natural prose in exactly one document per ZIP.

---

## Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| Concurrent players | ≥150 without data corruption |
| Dashboard refresh | ≤5 seconds |
| Document bundle size | ≤5 MB per quest |
| Core workshop duration | 60–90 minutes |
| Azure setup duration | ≤15 minutes |
| First successful agent response | ≤25 minutes from workshop start |
