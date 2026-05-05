# Data Model: Lost in [City] Workshop

**Generated**: 2026-05-03
**Plan**: [plan.md](plan.md)

---

## Entity Overview

```
CityConfig ──────────────── Quest (1..n)
                               │
                               ├── Stop (start, stop1, stop2, end)
                               ├── TransportOption (0..n per stop)
                               └── DocumentBundle (0..1, at stop2)

Player ──── Milestone (exactly 4)
       ──── LeaderboardEntry (0..1, created on quest finish)
```

---

## CityConfig

The runtime-loaded configuration file. One per deployed event.

**Source**: `city_config.yaml`
**Loaded**: once at server startup into an in-memory dict

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `city.name` | `str` | ✅ | Non-empty; used in A2A system prompt |
| `city.final_destination.name` | `str` | ✅ | Non-empty; displayed in completion message |
| `city.final_destination.address` | `str` | ✅ | Free text |
| `city.final_destination.narrative` | `str` | ✅ | Free text displayed to agent |
| `quests` | `list[Quest]` | ✅ | 1..n quests; randomly assigned on registration |

**Validation at startup**: if `city_config.yaml` is missing or malformed, the server MUST
refuse to start and log a clear error.

---

## Quest

One narrative path through the city.

**Source**: `city_config.yaml` → `quests[]`
**Cardinality**: 1..n per CityConfig (Raleigh has 3)

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `id` | `str` | ✅ | Snake_case; unique within config; used as `quest_id` in state |
| `name` | `str` | ✅ | Human-readable; shown on leaderboard |
| `start` | `Stop` | ✅ | No transport options; narrative only |
| `stop1` | `Stop` | ✅ | Includes `transport_options` and `a2a_expert_url` |
| `stop2` | `Stop` | ✅ | Includes `document_bundle_url` and `secret_code` |
| `end` | `Stop` | ✅ | Includes `transport_options`; final leg to event venue |

---

## Stop

A single location in a quest leg.

| Field | Type | Required | At |
|-------|------|----------|----|
| `location.name` | `str` | ✅ | All stops |
| `location.description` | `str` | ✅ | All stops |
| `narrative` | `str` | ✅ | All stops; delivered to agent with tool response |
| `transport_options` | `list[TransportOption]` | ✅ | stop1 and end only |
| `a2a_expert_url` | `str` | ✅ | stop1 only; HTTP URL |
| `document_bundle_url` | `str` | ✅ | stop2 only; publicly accessible URL to ZIP |
| `secret_code` | `str` | ✅ | stop2 only; uppercase alphanumeric; embedded in bundle |

---

## TransportOption

A transport choice an agent can select.

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `id` | `str` | ✅ | Lowercase snake_case; what the agent passes to `declare_transport_*` |
| `label` | `str` | ✅ | Human-readable option name |
| `description` | `str` | ✅ | Route detail used in A2A expert's system prompt |

**Validation**: `transport` argument to `declare_transport_stop1` / `declare_transport_final`
MUST match one of the `id` values in the quest's transport options for that leg. Server
returns an error on mismatch.

---

## DocumentBundle

A ZIP of city-guide Markdown files used in the RAG challenge.

| Field | Type | Notes |
|-------|------|-------|
| URL | `str` | Stored in `city_config.yaml`; returned in `declare_transport_stop1` response |
| Contents | `list[MarkdownFile]` | 5–8 files per bundle; drawn from `city-guide/<city>/` |
| Size constraint | `int` | ≤5 MB compressed (SC-008; checked in T2.2) |
| Secret embedding | `str` | Secret code embedded in natural prose in exactly one file |

The bundle URL is the only field persisted in state; the bundle itself is downloaded
transiently by the attendee's agent at runtime.

---

## Player

Runtime state for a single registered attendee.

**Source**: `state.json` → `players.<player_id>`
**Created**: by `register_player`
**Mutated**: by `declare_transport_stop1`, `submit_secret_code`, `declare_transport_final`
**Deleted (reset)**: by admin `DELETE /api/players/{id}`

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `player_name` | `str` | ✅ | From registration; non-empty; displayed on leaderboard |
| `quest_id` | `str` | ✅ | Randomly assigned from `city_config.yaml` quests list |
| `milestones.registered_at` | `str \| null` | ✅ | ISO 8601 UTC; set on `register_player` |
| `milestones.stop1_at` | `str \| null` | — | Set on successful `declare_transport_stop1` |
| `milestones.stop2_at` | `str \| null` | — | Set on successful `submit_secret_code` |
| `milestones.finished_at` | `str \| null` | — | Set on successful `declare_transport_final` |
| `failed_code_attempts` | `int` | ✅ | Starts at 0; incremented on wrong `submit_secret_code` |
| `final_score` | `int \| null` | — | Set on quest finish; `max(0, 1000 − 50×failures − 10×minutes)` |
| `transport_stop1` | `str \| null` | — | Transport `id` chosen at stop 1 |
| `transport_final` | `str \| null` | — | Transport `id` chosen at final leg |

**player_id generation**: UUID4, generated server-side on registration.

**State transitions**:
```
[unregistered]
    │ register_player
    ▼
registered (stop1_at=null)
    │ declare_transport_stop1
    ▼
stop1_complete (stop2_at=null)
    │ submit_secret_code (correct)
    ▼
stop2_complete (finished_at=null)
    │ declare_transport_final
    ▼
quest_finished (final_score set)
```

**Error states**: A player cannot advance a milestone they have not reached (server returns
an error). Wrong secret codes do not change the player's milestone state.

---

## Milestone

Embedded sub-object in Player. Four fixed keys:

| Key | Set by |
|-----|--------|
| `registered_at` | `register_player` success |
| `stop1_at` | `declare_transport_stop1` success |
| `stop2_at` | `submit_secret_code` correct answer |
| `finished_at` | `declare_transport_final` success |

All values are ISO 8601 UTC strings or `null`. Used by the dashboard feed and for final
score calculation (`minutes_taken = (finished_at − registered_at).total_seconds() / 60`).

---

## LeaderboardEntry

A read projection — not stored separately. The leaderboard is computed on-demand from all
players where `final_score is not null`, sorted descending by score, capped at top 20.

| Projected field | Source |
|-----------------|--------|
| `player_name` | `Player.player_name` |
| `quest_name` | `CityConfig.quests[quest_id].name` |
| `final_score` | `Player.final_score` |
| `completion_time` | `Player.milestones.finished_at` |

---

## Scoring Formula

```
score = max(0, 1000 − (50 × failed_code_attempts) − (10 × minutes_taken))
```

Where `minutes_taken = floor((finished_at − registered_at).total_seconds() / 60)`.

The formula is immutable (Constitution §8). It is evaluated once inside
`declare_transport_final` and stored in `Player.final_score`.

---

## city_config.yaml → state.json Mapping

```
city_config.yaml                    state.json
────────────────────────────────    ────────────────────────────────────
quests[].id              ──────────▶ players.<pid>.quest_id
(random assignment)      ──────────▶ players.<pid>.quest_id (set on register)
(server-generated UUID4) ──────────▶ players.<pid> key
(request param)          ──────────▶ players.<pid>.player_name
stop1.transport_options[].id ─────▶ players.<pid>.transport_stop1 (on declare_stop1)
end.transport_options[].id ───────▶ players.<pid>.transport_final (on declare_final)
stop2.secret_code        ──────── compared server-side; not stored in player state
```

---

## Validation Rules

| Rule | Where enforced |
|------|----------------|
| `player_id` must exist in state | All tools except `register_player` |
| Player must not have already completed the milestone | Each tool handler |
| `transport` value must match a config transport option id | `declare_transport_stop1`, `declare_transport_final` |
| `code` comparison is case-insensitive, whitespace-trimmed | `submit_secret_code` |
| `city_config.yaml` must be present and schema-valid | Server startup |
| ZIP bundle size ≤5 MB | Verified during T2.2 bundle creation (not runtime) |
