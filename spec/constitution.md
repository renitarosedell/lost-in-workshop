# Constitution: Lost in [City] Workshop

These rules are immutable. Every implementation decision, workshop instruction, and piece of sample code must comply. No exceptions.

---

## 1. Language & Runtime

- ALL code in this workshop MUST be Python 3.11 or higher.
- No other programming language is permitted in workshop materials.
- Dependency management uses `pip` and `requirements.txt`. No Poetry, conda, or uv.

## 2. Agent Framework

- ALL agent code MUST use the Microsoft Agent Framework.
- A bare `openai` SDK call is permitted only in Step 2 (Hello World) to establish baseline comprehension before the framework is introduced — nowhere else.
- No LangChain, AutoGen, LlamaIndex, Semantic Kernel, or any other agent framework may appear in workshop materials.

## 3. Model Provider

- ALL model inference MUST go through Azure OpenAI, accessed via Azure AI Foundry.
- Setup instructions MUST target the **new Azure AI Foundry experience** (accessed from the Azure Portal or `ai.azure.com`). The legacy `ml.azure.com` studio must not be referenced.
- East US 2 is the default recommended region. Other regions are acceptable when explicitly stated.
- No direct `api.openai.com` (non-Azure) calls in any workshop material.

## 4. City-Agnostic Architecture

- City name, neighbourhood names, transport options, quest locations, secret codes, document bundle URLs, and the final destination MUST live in a city configuration file (`city_config.yaml`).
- These values MUST NEVER be hardcoded in server logic, agent logic, or workshop instructions.
- Swapping to a new city MUST require only editing the config file — no code changes.

## 5. Fallback Code Guarantee

- Every workshop step MUST include complete, tested, copy-paste-ready Python code.
- Fallback code must be functionally equivalent to what the attendee is building.
- No step may leave an attendee unable to proceed due to a coding failure.

## 6. Non-Blocking Step Design

- Steps must be ordered so that a failure in step N does not prevent participation in step N+1.
- Where a step N produces an artifact (e.g. a `player_id`), the fallback code for step N must produce the same artifact so step N+1 can consume it.

## 7. Infrastructure Boundary

- The MCP game server, A2A expert agent, and admin dashboard are ALWAYS organiser-hosted.
- Attendees NEVER set up or run server infrastructure during the workshop.
- All server and admin code lives on a separate git branch (`admin`) and MUST be listed in `.gitignore` on the attendee-facing branch.

## 8. Scoring Formula

- `score = max(0, 1000 − (50 × failed_code_attempts) − (10 × minutes_taken))`
- This formula is immutable. It must not be altered for any city, event, or configuration variant.

## 9. Workshop Timing

- The core path (Steps 1–5) MUST be completable in 60–90 minutes by an attendee with basic Python knowledge and no prior Azure or agent-framework experience.
- Bonus exercises are additive and optional. They MUST NOT gate core quest completion.

## 10. Leaderboard & Concurrency

- The leaderboard MUST display progress milestones (registered → stop 1 complete → stop 2 complete → quest finished), not only final scores.
- The system MUST support at least 150 concurrent players without data corruption or race conditions.
- Top scores displayed need not list every participant; top 10–20 is the target display size.

## 11. Documentation Tone & Assumptions

- Workshop instructions address the reader as "you".
- Azure setup instructions MUST assume zero prior Azure experience.
- All other instructions MUST assume basic Python knowledge (variables, functions, imports, virtual environments) and nothing more.
- No jargon may appear without a brief plain-English explanation on first use.
