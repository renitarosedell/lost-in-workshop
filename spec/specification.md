# Specification: Lost in [City] Workshop

> **Superseded**: This is the original informal specification. The authoritative formal
> specification is at [`specs/001-lost-in-workshop/spec.md`](../specs/001-lost-in-workshop/spec.md).
> This file is retained for reference only.

This document defines **what** the workshop is and **why** each part exists. Technology choices are deliberately excluded — see `plan.md` for those.

---

## Vision

A 60–90-minute hands-on AI workshop where attendees build a Python agent from scratch. The agent connects to a centrally-hosted game server and navigates a narrative quest through a real city, learning core agentic concepts — tool use, memory, agent-to-agent (A2A) communication, and retrieval-augmented generation (RAG) — by actually using them, not by watching a demo.

The city and final destination change per event. The learning arc, game mechanics, and code structure remain constant.

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

## Core Workshop Steps (60–90 min)

### Step 1 — Azure AI Foundry Setup (~15 min)

**What:** Attendee activates their education subscription, creates an Azure AI Foundry project, and deploys a chat model.

**Why:** Establishes the model endpoint that all subsequent steps depend on. Doing it first ensures Azure provisioning time doesn't block later steps.

**Success criteria:**
- Attendee has a working `.env` file containing endpoint URL, API key, and deployment name.
- A test call to the model returns a response.

---

### Step 2 — Hello World Agent (~10 min)

**What:** Attendee writes the smallest possible Python agent that answers a single question using their Azure model.

**Why:** Introduces the Microsoft Agent Framework's core concepts (chat client, agent loop, message structure) before adding MCP tools or game mechanics. Keeps the first coding success fast and visible.

**Success criteria:**
- Agent answers "What is [city] famous for?" without errors.
- Attendee understands what a `ChatCompletionAgent` is and how a conversation turn works.

---

### Step 3 — Connect to the MCP Server (~15 min)

**What:** Attendee adds MCP tool-use to their agent, points it at the organiser-hosted game server URL, and calls `register_player`.

**Why:** Introduces tool use — the mechanism by which an agent reaches outside itself to interact with external systems. `register_player` is the simplest possible tool call: one input, one meaningful output.

**Success criteria:**
- Agent prints a `player_id` returned by the server.
- Attendee understands the relationship between an MCP server, tools, and the agent.

---

### Step 4 — Add Player Memory (~10 min)

**What:** Attendee adds a context provider that persists the `player_id` across agent restarts, so the agent can resume a quest without re-registering.

**Why:** Introduces agent memory — the mechanism by which agents maintain state across interactions. This is a foundational concept with direct practical value (nobody wants to lose their quest progress).

**Success criteria:**
- Agent is stopped and restarted; it continues the quest with the same `player_id`.
- Attendee understands what a context provider is and why statefulness matters.

---

### Step 5 — Play the Quest (~20 min)

**What:** Attendee extends the agent to autonomously complete all three quest legs:
1. **Stop 1 (A2A):** Ask the organiser-hosted transport expert agent for advice, then declare a transport choice.
2. **Stop 2 (RAG):** Download the document bundle, read through the documents, extract the secret code, submit it (wrong guesses cost points).
3. **Final leg:** Declare transport to the final destination and complete the quest.

**Why:** Each leg targets a distinct skill — A2A communication, document retrieval and extraction, and autonomous decision-making — in a narrative context that makes the mechanics memorable.

**Success criteria:**
- Agent completes the quest end-to-end without human intervention.
- Attendee's score appears on the live leaderboard.

---

## Bonus Exercises (post-quest, optional)

These are available to attendees who finish the core path early. Each teaches a concept beyond the basics.

### Bonus A — Build Your Own A2A Expert
Replace the organiser-hosted transport expert with your own locally-run agent. The game server calls your endpoint instead.

*Teaches: A2A server-side design; the difference between being an A2A client and an A2A host.*

### Bonus B — Streaming Responses
Modify your agent to stream token-by-token output to the console instead of waiting for the full response.

*Teaches: streaming APIs; perceived responsiveness in interactive agents.*

### Bonus C — Multi-Agent Orchestration
Split your agent into a Planner (decides the next action) and a Runner (executes tool calls). Both cooperate to complete the quest.

*Teaches: orchestrator/worker patterns; how production agentic systems decompose complex tasks.*

### Bonus D — Evaluate Your Agent
Write a harness that runs your agent through the quest three times and reports: average time to completion and average failed code attempts.

*Teaches: evaluation practices — a critical and often-skipped step in agentic development.*

---

## Game Mechanics

### Registration
- Agent calls `register_player(player_name)` → receives `player_id` and a randomly assigned quest.
- Each quest has a start location, stop 1, stop 2, and a final destination (the event venue).

### Stop 1 — A2A Challenge
- Agent sends a natural-language question to the organiser-hosted A2A transport expert.
- Expert returns transport advice for the current leg.
- Agent calls `declare_transport_stop1(player_id, transport_choice)` to advance.

### Stop 2 — RAG Challenge
- Server provides a URL to a ZIP of city-guide documents.
- One document contains a hidden secret code embedded in natural language.
- Agent calls `submit_secret_code(player_id, code)`.
  - Correct → quest advances.
  - Wrong → −50 points per attempt; agent may try again.

### Final Leg
- Agent calls `declare_transport_final(player_id, transport_choice)` to reach the event venue.
- Server records the completion timestamp and calculates the final score.

### Scoring
`score = max(0, 1000 − (50 × failed_code_attempts) − (10 × minutes_taken))`

---

## Leaderboard & Dashboard

### Milestones tracked (visible to all on the dashboard)
| Milestone | Trigger |
|-----------|---------|
| Registered | `register_player` succeeds |
| Stop 1 complete | `declare_transport_stop1` succeeds |
| Stop 2 complete | `submit_secret_code` succeeds |
| Quest finished | `declare_transport_final` succeeds |

### Dashboard views
- **Milestone feed:** all players with their current progress status and elapsed time. Refreshes every ≤5 seconds.
- **Leaderboard:** top 20 final scores with player name, quest name, score, and completion time.
- **Admin panel (facilitator only):** quest editor, individual/bulk player reset, server status.

---

## City Configuration

Each event city requires:

1. A `city_config.yaml` defining the city name, final destination, and three quest definitions (each with: start location, stop 1, stop 2, transport options, secret code, document bundle URL, narrative text).
2. A set of city-guide Markdown documents (≥20 chapters covering the city's neighbourhoods, transport, culture, history, food, and events).
3. Three document ZIPs (one per quest) assembled from the city-guide chapters, with the secret code embedded in one document per ZIP.

### Raleigh quests (initial set)

| Quest | Start | Stop 1 | Stop 2 | End |
|-------|-------|--------|--------|-----|
| The Glenwood Getaway | Moore Square | Glenwood South | Cameron Village | NC Biotech Center |
| The Museum Mile | City Market | NC Museum of Art area | North Hills | NC Biotech Center |
| The Warehouse Run | Warehouse District | Five Points | Boylan Heights | NC Biotech Center |

---

## Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| Concurrent players | ≥150 without data corruption |
| Dashboard refresh | ≤5 seconds |
| Document bundle size | ≤5 MB per quest |
| Core workshop duration | 60–90 minutes |
| Azure setup duration | ≤15 minutes |
| First successful agent response | ≤25 minutes from start |
