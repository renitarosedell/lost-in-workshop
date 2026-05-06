# Tasks: Lost in [City] Workshop

**Feature**: Lost in [City] Workshop
**Branch**: `001-lost-in-workshop` | **Date**: 2026-05-03
**Plan**: [plan.md](plan.md) | **Spec**: [spec.md](spec.md)

**Format**: `- [ ] [TaskID] [P?] [Story?] Description with file path`
- **[P]**: Parallelizable — different files, no incomplete dependencies
- **[Story]**: US1 / US2 / US3 — required for all user-story phase tasks

---

## Phase 1: Setup

**Purpose**: Remove stale content and establish repo hygiene before any story work begins.

- [X] T001 Remove all 20 San Francisco Markdown files from `city-guide/`; create empty `city-guide/raleigh/` directory
- [X] T002 [P] Add `lost-in-raleigh/` and `a2a-expert/` entries to `.gitignore` on the attendee branch

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Game server must be working before any user story can be built or validated.

**⚠️ CRITICAL**: US1, US2, and US3 all depend on this phase completing first.

- [X] T003 Define `city_config.yaml` schema (city metadata + quest array); write loader function in `lost-in-raleigh/server.py`; replace all hardcoded SF values with config-driven values; verify scoring formula `max(0, 1000 − (50 × failed_code_attempts) − (10 × minutes_taken))` present verbatim in `lost-in-raleigh/server.py`
- [X] T004 [P] Populate `lost-in-raleigh/city_config.yaml` with three Raleigh quest definitions: The Glenwood Getaway, The Museum Mile, The Warehouse Run — each with start, stop 1, stop 2, end, transport options, secret codes, placeholder bundle URLs, and narrative text
- [X] T005 [P] Add `milestones` object (`registered_at`, `stop1_at`, `stop2_at`, `finished_at`) to player schema in `lost-in-raleigh/storage.py`; update each tool handler in `lost-in-raleigh/server.py` to write the corresponding ISO timestamp on success

**Checkpoint**: Server starts cleanly with Raleigh config; milestones recorded; no SF values in code; scoring formula verified.

---

## Phase 3: User Story 1 — Attendee Completes the Core Workshop Path (Priority: P1) 🎯 MVP

**Goal**: A first-time attendee follows the five-step workshop guide, builds a working agent, completes the Raleigh quest, and has their final score appear on the leaderboard — in 60–90 minutes.

**Independent Test**: Given only `workshop/workshop.md` and a pre-filled `create-agent/.env.example`, a first-time attendee completes all five steps and sees their score on the leaderboard without facilitator intervention.

### Infrastructure needed by US1

- [X] T006 [P] [US1] Create `a2a-expert/expert.py` — FastAPI app with `POST /a2a` endpoint using Microsoft Agent Framework; Raleigh transport system prompt including GoRaleigh routes, GoTriangle, Capital Bikeshare, rideshare wait times, and walking distances between quest locations
- [X] T007 [P] [US1] Create `a2a-expert/requirements.txt` with FastAPI, uvicorn, and Microsoft Agent Framework; create `a2a-expert/Dockerfile`

### City content for US1

- [X] T008 [P] [US1] Write 20 Raleigh city-guide chapters (300–500 words each, travel-guide style) in `city-guide/raleigh/` — chapters 1–10: Welcome to Raleigh, Downtown & Moore Square, Glenwood South, Five Points & Neighbourhood Character, Cameron Village & Midtown, The Warehouse District, Boylan Heights, North Hills, Getting Around: GoRaleigh Buses, Getting Around: GoTriangle & Regional Transit
- [X] T009 [P] [US1] Write 10 remaining Raleigh city-guide chapters in `city-guide/raleigh/` — chapters 11–20: Getting Around: Biking & Greenways, Getting Around: Rideshare & Parking, Food & Drink Scene, Arts & Culture (NC Museum of Art / CAM Raleigh), Parks & Outdoors (Pullen Park / Umstead), Research Triangle & Innovation, History of Raleigh, Annual Events & Festivals, Practical Info (weather / safety / tipping), The NC Biotech Center & Research Triangle Park
- [X] T010 [US1] For each of the three Raleigh quests, select 5–8 thematically relevant chapters from `city-guide/raleigh/`; embed the secret code in natural prose in one chapter; package as ZIP; upload to Azure Blob Storage (public-read container); update `lost-in-raleigh/city_config.yaml` with real bundle URLs — each ZIP ≤5 MB

### Fallback step files for US1

- [X] T011 [P] [US1] Create `create-agent/steps/step1_foundry_test.py` — Azure OpenAI connectivity test using bare `AzureOpenAI` client; reads endpoint/key/deployment from `.env`; prints confirmation on success
- [X] T012 [P] [US1] Create `create-agent/steps/step2_hello_world.py` — bare `AzureOpenAI` client answering "What is Raleigh famous for?"; no agent framework (constitution principle 2 baseline exception)
- [X] T013 [US1] Create `create-agent/steps/step3_mcp_connect.py` — `MCPToolProvider` pointing at game server URL; calls `register_player`; prints returned `player_id` and quest assignment including A2A expert URL
- [X] T014 [US1] Create `create-agent/steps/step4_memory.py` — adds `FileContextProvider` persisting `player_id` to local JSON; verifies resume works after agent restart
- [X] T015 [US1] Create `create-agent/steps/step5_quest.py` — full quest loop: A2A call via `httpx.post` to `a2a_expert_url`, `declare_transport_stop1`, ZIP download + secret code extraction, `submit_secret_code`, `declare_transport_final`; prints final score
- [X] T016 [US1] Create `create-agent/agent.py` — single runnable reference agent combining all five steps in sequence; all constitution compliance gates satisfied
- [X] T017 [P] [US1] Create `create-agent/requirements.txt` (Microsoft Agent Framework, python-dotenv, httpx, requests) and `create-agent/.env.example` with `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_DEPLOYMENT_NAME`, `MCP_SERVER_URL` pre-filled with live Raleigh server URL

### Workshop documentation for US1

- [X] T018 [P] [US1] Write `workshop/azure-foundry-setup.md` — Step 1 guide covering: subscription code redemption, `ai.azure.com` sign-in, Resource Group (East US 2), Foundry Hub, Project, `gpt-4o-mini` deployment, endpoint/key/deployment-name retrieval, `.env` creation, one-line verification test; numbered sub-steps with expected visual outcome and troubleshooting note each; zero prior Azure experience assumed
- [X] T019 [US1] Write `workshop/workshop.md` — full five-step guide; for each step: Concept (2–3 sentences), What to add (specific code changes), How to test it (exact command + expected output), Complete code (full copy-pasteable fallback); Step 2 uses bare `AzureOpenAI`; steps 3–5 use Microsoft Agent Framework; content must match the fallback files in `create-agent/steps/`

### Validation for US1

- [ ] T020 [US1] Run full fallback validation: execute `step1_foundry_test.py` through `step5_quest.py` in sequence against the live Raleigh server; verify model responds, player registers, quest advances through all three legs, score appears on leaderboard; fix any errors found in step files or instructions

**Checkpoint**: US1 complete — a first-time attendee can independently complete all five steps and finish the quest using only `workshop/workshop.md` and the fallback step files.

---

## Phase 4: User Story 2 — Facilitator Manages the Event via the Admin Dashboard (Priority: P2)

**Goal**: A facilitator monitors all player progress in real time and can reset individual or all players from a browser — without file system access or server restarts.

**Independent Test**: Given only the dashboard URL, a facilitator locates a specific player, resets their progress, and confirms the reset within 2 minutes.

- [X] T021 [P] [US2] Update `lost-in-raleigh/admin.py` milestone feed: add milestone summary bar (counts at each stage); update player table to show current milestone status and time since registration; update leaderboard to show top 20; implement 5-second auto-refresh via `setInterval` polling of `/api/players` and `/api/leaderboard`
- [X] T022 [US2] Add admin controls to `lost-in-raleigh/admin.py`: per-row "Reset player" button; "Reset all players" button with browser confirmation prompt; both call server reset endpoints and refresh the UI without page reload

**Checkpoint**: US2 complete — facilitator can view live milestone progress and reset any player from the dashboard within 5 seconds of an update.

---

## Phase 5: User Story 3 — Attendee Explores Bonus Exercises (Priority: P3)

**Goal**: An attendee who finishes the core path early can pick any single bonus exercise, follow its instructions, and have a demonstrably working result — without modifying their core quest code.

**Independent Test**: Given a completed Step 5 agent, an attendee follows Bonus A, B, C, or D instructions and produces a working result independently.

- [X] T023 [P] [US3] Write `workshop/bonus-exercises.md` Bonus A — Build Your Own A2A Expert: explain `POST /a2a` contract; provide FastAPI + Microsoft Agent Framework starter code; document the ngrok tunnel override mechanism (attendee gets public URL → facilitator updates `a2a_expert_url` in `city_config.yaml` or via admin quest editor); reference `spec/contracts/a2a-protocol.md` Bonus A Extension section
- [X] T024 [P] [US3] Write `workshop/bonus-exercises.md` Bonus B — Streaming Responses: show before/after diff for Microsoft Agent Framework streaming API; include console test that prints tokens as they arrive
- [X] T025 [P] [US3] Write `workshop/bonus-exercises.md` Bonus C — Multi-Agent Orchestration: design Planner + Runner agents; explain message-passing interface; provide complete code for both agents completing the quest cooperatively
- [X] T026 [P] [US3] Write `workshop/bonus-exercises.md` Bonus D — Evaluate Your Agent: provide `create-agent/eval_harness.py` that runs the quest three times (resetting the player between runs); outputs table of run number, time to completion, failed code attempts, final score

**Checkpoint**: US3 complete — all four bonus exercises independently testable; none require modifying core quest code.

---

## Phase 6: Polish & Deployment

**Purpose**: Operational readiness — packaging, deployment, and pre-event verification.

- [X] T027 [P] Write `lost-in-raleigh/Dockerfile` for game server; document `az containerapp create` commands (or equivalent Portal steps) in `workshop/deployment-guide.md`; verify server reachable at `https://<host>/mcp` and `register_player` returns a `player_id`
- [X] T028 [P] Write `a2a-expert/Dockerfile`; deploy to same Azure Container Apps environment as game server; update `a2a_expert_url` in `lost-in-raleigh/city_config.yaml` with live URL; verify `POST https://<host>/a2a` returns Raleigh transport advice
- [X] T029 [P] Write `lost-in-raleigh/load_test.py` — Python `threading` harness: 150 threads each calling `register_player` with a unique name; verify all 150 receive a distinct `player_id`; inspect `state.json` and confirm 150 valid uncorrupted player records (constitution gate 10)
- [X] T030 Write `workshop/pre-event-checklist.md` — 10-minute facilitator readiness checklist covering: MCP server reachable + all three quests playable end-to-end; leaderboard updates within 5 seconds; all three bundle ZIPs downloadable with findable secrets; A2A expert returning accurate Raleigh advice; admin dashboard reset functions; `step5_quest.py` runs clean against live server

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — **BLOCKS all user stories**
- **Phase 3 (US1)**: Depends on Phase 2 completion
- **Phase 4 (US2)**: Depends on Phase 2 completion — can run in parallel with US1
- **Phase 5 (US3)**: Depends on US1 completion (T020 fallback validation must pass first)
- **Phase 6 (Polish)**: T027–T028 depend on Foundational; T029 depends on T027; T030 depends on T027+T028+T020

### User Story Dependencies

```
T001 ──→ T002 (can parallel)

T003 ──→ T004 (can parallel)
T003 ──→ T005 (can parallel)

Phase 2 complete ──→ US1 (Phase 3) ──→ US3 (Phase 5)
Phase 2 complete ──→ US2 (Phase 4)  [parallel with US1]

T006+T007 (A2A expert) ──→ T015 (step5 needs A2A)
T008+T009 (city guide) ──→ T010 (bundles need chapters)
T010 (bundles) ──→ T015 (step5 needs bundle URL)
T011+T012+T013+T014+T015 ──→ T016 (agent.py combines all)
T016+T018+T019 ──→ T020 (validation needs all files)

T020 ──→ T023–T026 (bonus exercises need validated agent)

T027 ──→ T028 (same Container Apps environment)
T027+T028+T020 ──→ T030 (smoke test needs all live)
T027 ──→ T029 (load test needs deployed server)
```

### Parallel Opportunities

**Phase 2**: T004 and T005 can run in parallel once T003 is complete.

**Phase 3 (US1)**:
```
# These can run in parallel immediately after Phase 2:
T006  a2a-expert/expert.py
T007  a2a-expert/requirements.txt + Dockerfile
T008  city-guide/raleigh/ chapters 1–10
T009  city-guide/raleigh/ chapters 11–20
T011  create-agent/steps/step1_foundry_test.py
T012  create-agent/steps/step2_hello_world.py
T017  create-agent/requirements.txt + .env.example
T018  workshop/azure-foundry-setup.md

# These run after T008+T009 complete:
T010  Document bundles (needs all 20 chapters)

# These run in dependency order:
T013  step3_mcp_connect.py
T014  step4_memory.py  
T015  step5_quest.py (needs T006, T010, T013, T014)
T016  agent.py (needs T011–T015)
T019  workshop/workshop.md (needs T011–T016)
T020  Validation (needs T016, T018, T019)
```

**Phase 4 (US2)**: T021 and T022 are sequential (T022 builds on T021).

**Phase 5 (US3)**: T023, T024, T025, T026 all parallel (different sections of bonus-exercises.md).

**Phase 6**: T027 and T028 parallel; T029 and T030 parallel after T027+T028.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T002)
2. Complete Phase 2: Foundational (T003–T005) — **CRITICAL BLOCKER**
3. Complete Phase 3: User Story 1 (T006–T020)
4. **STOP and VALIDATE**: Run T020 — entire workshop path must complete end-to-end
5. Demo / run first event with US1 only; US2 and US3 can follow

### Full Feature Delivery

After US1 validation passes (T020):
- Staff US2 in parallel with US3 (independent)
- Complete Phase 6 deployment tasks before first live event
- T029 (load test) must pass before event with ≥50 attendees

---

## Task Summary

| Phase | Tasks | Count |
|-------|-------|-------|
| Phase 1: Setup | T001–T002 | 2 |
| Phase 2: Foundational | T003–T005 | 3 |
| Phase 3: US1 (P1) | T006–T020 | 15 |
| Phase 4: US2 (P2) | T021–T022 | 2 |
| Phase 5: US3 (P3) | T023–T026 | 4 |
| Phase 6: Polish | T027–T030 | 4 |
| **Total** | | **30** |
