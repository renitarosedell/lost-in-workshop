"""MCP game server for 'Lost in [City]' workshop — city-agnostic via city_config.yaml."""
from __future__ import annotations

import os
import random
import uuid
from pathlib import Path
from typing import Annotated, Any

import yaml
from fastmcp import FastMCP
from pydantic import Field

from storage import load_state, update_state, utcnow_iso

MCP_HOST = os.environ.get("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.environ.get("MCP_PORT", "8000"))

CONFIG_FILE = Path(__file__).resolve().parent / "city_config.yaml"

# ---------------------------------------------------------------------------
# City config loader (loaded once at startup; restart to reload)
# ---------------------------------------------------------------------------

def _load_config() -> dict[str, Any]:
    with CONFIG_FILE.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


_config: dict[str, Any] = _load_config()
_city: dict[str, Any] = _config["city"]
_quests: list[dict[str, Any]] = _config["quests"]
_quest_index: dict[str, dict[str, Any]] = {q["id"]: q for q in _quests}


# ---------------------------------------------------------------------------
# Scoring formula (immutable — constitution gate 8)
# ---------------------------------------------------------------------------

def _compute_score(failed_code_attempts: int, registered_at: str, finished_at: str) -> int:
    from datetime import datetime
    def _parse(s: str) -> datetime:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    minutes = max(0, int((_parse(finished_at) - _parse(registered_at)).total_seconds() // 60))
    return max(0, 1000 - (50 * failed_code_attempts) - (10 * minutes))


# ---------------------------------------------------------------------------
# MCP server
# ---------------------------------------------------------------------------

SERVER_INSTRUCTIONS = f"""\
You are playing the narrative game 'Lost in {_city["name"]}' on behalf of a human
player. This MCP server is the game master. Your job is to relay the story
faithfully and let the human make every real decision.

HOW THE GAME WORKS
1. Call register_player(player_name) first. It returns your player_id, the quest
   narrative, the A2A expert URL, and the first transport challenge.
2. Call the A2A expert at the URL provided with a natural-language question about
   the best transport. Then call declare_transport_stop1(player_id, transport).
3. You will receive a document bundle URL. Download the ZIP, find the secret code
   hidden in natural-language prose, and call submit_secret_code(player_id, code).
4. For the final leg call declare_transport_final(player_id, transport). Your score
   is calculated and the leaderboard is updated.

GROUND RULES
- NEVER invent or guess values for tool parameters. Always ask the human user.
- Before calling register_player, ask: "What name should I put on your badge?"
- Before calling declare_transport_stop1 or declare_transport_final, consult the
  A2A expert at the provided URL, then confirm the transport choice with the human.
- Before calling submit_secret_code, ask the human for the exact code from the
  documents. Do not try to derive it yourself.
"""

mcp = FastMCP(
    f"lost-in-{_city['name'].lower().replace(' ', '-')}",
    instructions=SERVER_INSTRUCTIONS,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _err(message: str) -> dict[str, Any]:
    return {"status": "error", "message": message}


def _get_player(state: dict[str, Any], player_id: str) -> dict[str, Any] | None:
    return state.get("players", {}).get(player_id)


def _rebuild_leaderboard(state: dict[str, Any]) -> None:
    entries = []
    for pid, p in state.get("players", {}).items():
        if p.get("final_score") is not None and p["milestones"].get("finished_at"):
            entries.append({
                "player_id": pid,
                "player_name": p["player_name"],
                "quest_id": p["quest_id"],
                "quest_name": _quest_index.get(p["quest_id"], {}).get("name", p["quest_id"]),
                "final_score": p["final_score"],
                "failed_code_attempts": p.get("failed_code_attempts", 0),
                "finished_at": p["milestones"]["finished_at"],
            })
    entries.sort(key=lambda e: (-e["final_score"], e["finished_at"] or ""))
    state["leaderboard"] = entries[:20]


# ---------------------------------------------------------------------------
# MCP tools
# ---------------------------------------------------------------------------

@mcp.tool()
def register_player(
    player_name: Annotated[str, Field(description="The human player's badge name. REQUIRED. Ask the human: 'What name should I put on your badge?' and pass their literal answer.", min_length=1, max_length=80)],
) -> dict[str, Any]:
    """Register a new player. Returns player_id, quest narrative, stop 1 location,
    transport options, and the A2A expert URL. Call this once per new player."""

    quest = random.choice(_quests)
    player_id = f"PLR-{uuid.uuid4().hex[:8].upper()}"
    now = utcnow_iso()

    player: dict[str, Any] = {
        "player_name": player_name,
        "quest_id": quest["id"],
        "milestones": {
            "registered_at": now,
            "stop1_at": None,
            "stop2_at": None,
            "finished_at": None,
        },
        "failed_code_attempts": 0,
        "final_score": None,
        "transport_stop1": None,
        "transport_final": None,
    }

    def _mutate(state: dict[str, Any]) -> None:
        state.setdefault("players", {})[player_id] = player
        if "leaderboard" not in state:
            state["leaderboard"] = []

    update_state(_mutate)

    stop1 = quest["stop1"]
    return {
        "status": "registered",
        "player_id": player_id,
        "quest_name": quest["name"],
        "city": _city["name"],
        "narrative": quest["start"]["description"],
        "stop1_location": stop1["location"]["name"],
        "stop1_description": stop1["location"]["description"],
        "stop1_narrative": stop1["narrative"],
        "transport_options": stop1["transport_options"],
        "a2a_expert_url": stop1["a2a_expert_url"],
        "next_action": (
            f"Use the A2A expert at {stop1['a2a_expert_url']} to ask about the best "
            f"transport to {stop1['location']['name']}, then call "
            f"declare_transport_stop1(player_id, transport)."
        ),
    }


@mcp.tool()
def declare_transport_stop1(
    player_id: Annotated[str, Field(description="The player_id returned by register_player. REQUIRED.", min_length=1)],
    transport: Annotated[str, Field(description="Transport mode chosen by the human player (e.g. 'rideshare', 'GoRaleigh bus', 'bike'). REQUIRED. Ask the human to confirm their choice.", min_length=1)],
) -> dict[str, Any]:
    """Record the player's transport choice for leg 1 (start → stop 1).
    Returns stop 2 location and the document bundle URL for the RAG challenge."""

    def _mutate(state: dict[str, Any]) -> dict[str, Any]:
        player = _get_player(state, player_id)
        if player is None:
            return _err(f"Unknown player_id: {player_id}")
        if player["milestones"]["stop1_at"] is not None:
            return _err("Stop 1 already declared.")
        player["transport_stop1"] = transport
        player["milestones"]["stop1_at"] = utcnow_iso()

        quest = _quest_index.get(player["quest_id"])
        if quest is None:
            return _err("Quest configuration not found.")

        stop2 = quest["stop2"]
        return {
            "status": "stop1_reached",
            "player_id": player_id,
            "transport_used": transport,
            "stop2_location": stop2["location"]["name"],
            "stop2_description": stop2["location"]["description"],
            "stop2_narrative": stop2["narrative"],
            "document_bundle_url": stop2["document_bundle_url"],
            "next_action": (
                f"Download the document bundle at {stop2['document_bundle_url']}. "
                "Read the Markdown files to find the secret code, then call "
                "submit_secret_code(player_id, code)."
            ),
        }

    return update_state(_mutate)


@mcp.tool()
def submit_secret_code(
    player_id: Annotated[str, Field(description="The player_id returned by register_player. REQUIRED.", min_length=1)],
    code: Annotated[str, Field(description="The secret code the human player found in the document bundle. REQUIRED. Ask the human for the exact code — do NOT guess.", min_length=1)],
) -> dict[str, Any]:
    """Submit the secret code found in the document bundle.
    Returns success/failure and the attempt count."""

    def _mutate(state: dict[str, Any]) -> dict[str, Any]:
        player = _get_player(state, player_id)
        if player is None:
            return _err(f"Unknown player_id: {player_id}")
        if player["milestones"]["stop1_at"] is None:
            return _err("Must declare transport to stop 1 first.")
        if player["milestones"]["stop2_at"] is not None:
            return _err("Secret code already accepted.")

        quest = _quest_index.get(player["quest_id"])
        if quest is None:
            return _err("Quest configuration not found.")

        correct = quest["stop2"]["secret_code"]
        if code.strip().upper() != correct.upper():
            player["failed_code_attempts"] = player.get("failed_code_attempts", 0) + 1
            return {
                "status": "wrong_code",
                "attempts": player["failed_code_attempts"],
                "message": "That code is not correct. Check the documents again.",
            }

        player["milestones"]["stop2_at"] = utcnow_iso()
        end = quest["end"]
        return {
            "status": "code_accepted",
            "attempts": player.get("failed_code_attempts", 0),
            "message": "Correct! Now choose your final transport to the destination.",
            "final_destination": _city["final_destination"]["name"],
            "final_narrative": end["narrative"],
            "transport_options": end["transport_options"],
            "next_action": (
                "Ask the human which final transport they want, then call "
                "declare_transport_final(player_id, transport)."
            ),
        }

    return update_state(_mutate)


@mcp.tool()
def declare_transport_final(
    player_id: Annotated[str, Field(description="The player_id returned by register_player. REQUIRED.", min_length=1)],
    transport: Annotated[str, Field(description="Final transport mode chosen by the human player. REQUIRED. Confirm with the human.", min_length=1)],
) -> dict[str, Any]:
    """Record the player's final transport choice and calculate their score.
    Score formula: max(0, 1000 − (50 × failed_code_attempts) − (10 × minutes_taken))."""

    def _mutate(state: dict[str, Any]) -> dict[str, Any]:
        player = _get_player(state, player_id)
        if player is None:
            return _err(f"Unknown player_id: {player_id}")
        if player["milestones"]["stop2_at"] is None:
            return _err("Must submit the correct secret code first.")
        if player["milestones"]["finished_at"] is not None:
            return _err("Quest already completed.")

        now = utcnow_iso()
        player["transport_final"] = transport
        player["milestones"]["finished_at"] = now

        score = _compute_score(
            player.get("failed_code_attempts", 0),
            player["milestones"]["registered_at"],
            now,
        )
        player["final_score"] = score

        _rebuild_leaderboard(state)

        quest = _quest_index.get(player["quest_id"], {})
        return {
            "status": "quest_complete",
            "player_id": player_id,
            "player_name": player["player_name"],
            "quest_name": quest.get("name", player["quest_id"]),
            "final_score": score,
            "failed_code_attempts": player.get("failed_code_attempts", 0),
            "transport_final": transport,
            "message": (
                f"Congratulations, {player['player_name']}! You completed "
                f"'{quest.get('name', player['quest_id'])}' with a score of {score}. "
                f"Your result is on the leaderboard."
            ),
        }

    return update_state(_mutate)


if __name__ == "__main__":
    import uvicorn
    from starlette.applications import Starlette
    from starlette.responses import RedirectResponse
    from starlette.routing import Mount, Route

    from admin import app as admin_app

    mcp_asgi = mcp.http_app(transport="streamable-http")

    app = Starlette(
        lifespan=mcp_asgi.lifespan,
        routes=[
            Route("/admin", lambda req: RedirectResponse(url="/admin/")),
            Mount("/admin", app=admin_app),
            Mount("/", app=mcp_asgi),
        ],
    )

    uvicorn.run(app, host=MCP_HOST, port=MCP_PORT)
