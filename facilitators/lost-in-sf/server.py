"""MCP server for 'Lost in San Francisco' workshop game."""
from __future__ import annotations

import os
import random
import uuid
from datetime import datetime
from typing import Annotated, Any

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from storage import get_quest, load_quests, load_state, update_state, utcnow_iso

MCP_HOST = os.environ.get("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.environ.get("MCP_PORT", "8000"))

SERVER_INSTRUCTIONS = """\
You are playing the narrative game 'Lost in San Francisco' on behalf of a human
player. This MCP server is the game master. Your job is to relay the story
faithfully and let the human make every real decision.

FIRST STEP WHEN A SESSION STARTS
Always call 'begin_session' first. It returns the two questions you must ask
the human user:
  1. Do you already have a player_id from a previous session? If yes, pass it
     to 'resume_player(player_id)' to pick up where they left off.
  2. If no, ask for the name to put on their badge, then call
     'register_player(name)'.
NEVER skip this step. NEVER assume the user is new. NEVER reuse a player_id
from earlier in the same conversation without confirming with the human.

HOW THE GAME WORKS
1. The human wakes up somewhere in San Francisco and must reach Fort Mason
   before Build starts.
2. Each quest has three legs: stop 1 (choose transport), stop 2 (solve a
   document/RAG puzzle and submit a secret code), and the final leg to
   Fort Mason (choose transport again).
3. Every tool response includes narrative fields ('scene', 'narration',
   'next_action'). Read them aloud to the human, verbatim where useful, then
   do what 'next_action' tells you.

GROUND RULES FOR THE AGENT
- NEVER invent, guess, or assume values for tool parameters. In particular,
  NEVER make up the player's name or player_id. Always ASK THE HUMAN USER
  and pass their literal answer.
- Before calling 'register_player', ask: "What name should I put on your badge?"
  and wait for a reply.
- Before calling 'declare_transport_stop1' or 'declare_transport_final', ask
  the human which transport they want (taxi / walking / bike).
- Before calling 'submit_secret_code', ask the human for the exact code they
  found. Do not try to derive it yourself.
- If a tool response contains an 'ask_user' field, show that question to the
  human and wait for their answer before calling the next tool.
- Stay in character as a narrator. Present the scene and the flavor, do not
  just dump JSON.
- If the human says they want to stop, call 'abandon_quest'.

Typical tool sequence for a NEW player: begin_session -> register_player ->
start_quest -> declare_transport_stop1 -> submit_secret_code ->
declare_transport_final.
For a RETURNING player: begin_session -> resume_player. The response tells
you which tool to call next.
Use 'get_player_status' any time you need to check where you are.
"""

mcp = FastMCP(
    "lost-in-sf",
    instructions=SERVER_INSTRUCTIONS,
    host=MCP_HOST,
    port=MCP_PORT,
    stateless_http=True,
    json_response=False,
)


# ---------- helpers ----------

def _err(message: str) -> dict[str, Any]:
    return {"status": "error", "message": message}


def _parse_iso(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _get_player(state: dict[str, Any], player_id: str) -> dict[str, Any] | None:
    return state.get("players", {}).get(player_id)


def _abandoned_msg() -> dict[str, Any]:
    return _err("You gave up on this quest. Register again for a fresh start.")


def _compute_score(player: dict[str, Any]) -> tuple[int, int]:
    started = _parse_iso(player["started_at"])
    completed = _parse_iso(player["completed_at"])
    minutes = max(0, int((completed - started).total_seconds() // 60))
    attempts = int(player.get("code_attempts", 0))
    failed = max(0, attempts - 1)  # the successful attempt doesn't count as failure
    score = 1000 - 50 * failed - 10 * minutes
    return max(0, score), minutes


def _rebuild_leaderboard(state: dict[str, Any]) -> None:
    entries = []
    quests = {q["id"]: q for q in load_quests().get("quests", [])}
    for pid, p in state.get("players", {}).items():
        if p.get("status") == "complete" and p.get("score") is not None:
            quest = quests.get(p.get("quest_id"), {})
            entries.append({
                "player_id": pid,
                "name": p.get("name"),
                "quest_name": quest.get("name", f"Quest {p.get('quest_id')}"),
                "score": p.get("score"),
                "time_taken_minutes": p.get("time_taken_minutes"),
                "code_attempts": p.get("code_attempts", 0),
                "completed_at": p.get("completed_at"),
            })
    entries.sort(key=lambda e: (-e["score"], e.get("time_taken_minutes") or 0))
    state["leaderboard"] = entries


# ---------- MCP tools ----------

@mcp.tool()
def begin_session() -> dict[str, Any]:
    """Entry point for every new conversation. Instructs the agent to ask the
    human user whether they already have a player_id (returning player) or need
    to register as a new player. ALWAYS call this first."""
    return {
        "status": "awaiting_identity",
        "narration": (
            "Welcome to 'Lost in San Francisco'. Before we drop you into the city, "
            "we need to know who we're talking to."
        ),
        "ask_user": (
            "Ask the human user these two questions, in order:\n"
            "  1. 'Do you already have a player_id from a previous session?'\n"
            "  2. If YES -> ask them to paste that player_id and then call "
            "resume_player(player_id).\n"
            "     If NO  -> ask 'What name should I put on your badge?' and then "
            "call register_player(name)."
        ),
        "options": [
            {"choice": "resume", "next_tool": "resume_player", "needs": ["player_id from the user"]},
            {"choice": "new",    "next_tool": "register_player", "needs": ["name from the user"]},
        ],
        "next_action": (
            "Do NOT call register_player or resume_player until the human user has "
            "answered. Never invent a player_id or a name."
        ),
    }


def _resume_scene(player: dict[str, Any], quest: dict[str, Any]) -> dict[str, Any]:
    status = player.get("status")
    pid = None  # filled by caller wrapper
    if status == "registered":
        return {
            "narration": (
                f"Welcome back, {player.get('name')}. You registered for "
                f"'{quest.get('name')}' but never set off. The city is still waiting."
            ),
            "ask_user": "Ask the user: 'Ready to begin your quest? Say START.'",
            "next_action": "When the human says ready, call start_quest(player_id).",
        }
    if status == "stop1":
        stop1 = quest["stop1"]
        valid = stop1["valid_transports"]
        return {
            "narration": (
                f"Welcome back, {player.get('name')}. You still need to get from "
                f"{quest['start']['neighborhood']} to {stop1['neighborhood']}."
            ),
            "ask_user": f"Ask the user which transport they want ({' / '.join(valid)}).",
            "next_action": "Call declare_transport_stop1(player_id, transport) with the user's answer.",
            "valid_transports": valid,
        }
    if status == "stop2":
        stop2 = quest["stop2"]
        return {
            "narration": (
                f"Welcome back, {player.get('name')}. You are in "
                f"{stop2['neighborhood']}, still looking for the secret code."
            ),
            "ask_user": "Ask the user: 'What code did you find in the documents?'",
            "documents_zip_url": stop2.get("documents_zip_url", ""),
            "next_action": "Call submit_secret_code(player_id, code) with the user's answer.",
        }
    if status == "final":
        end = quest["end"]
        valid = end["valid_transports"]
        return {
            "narration": (
                f"Welcome back, {player.get('name')}. You have the code. Just the "
                f"last leg to Fort Mason to go."
            ),
            "ask_user": f"Ask the user which transport to Fort Mason ({' / '.join(valid)}).",
            "next_action": "Call declare_transport_final(player_id, transport) with the user's answer.",
            "valid_transports": valid,
        }
    if status == "complete":
        return {
            "narration": (
                f"{player.get('name')} already made it to Build. Score: "
                f"{player.get('score')}, time: {player.get('time_taken_minutes')} min."
            ),
            "ask_user": "Ask the user if they want to see the leaderboard.",
            "next_action": "If yes, call get_leaderboard(). Otherwise nothing more to do.",
        }
    if status == "abandoned":
        return {
            "narration": (
                f"{player.get('name')} gave up on this quest earlier. That player_id "
                f"is retired."
            ),
            "ask_user": "Ask the user if they want to register again as a new player.",
            "next_action": "If yes, ask for a name and call register_player(name).",
        }
    return {
        "narration": "Your quest is in an unknown state. Ask the facilitator.",
        "next_action": "Call get_player_status(player_id) for details.",
    }


@mcp.tool()
def resume_player(
    player_id: Annotated[str, Field(description="An existing player_id previously returned by register_player. REQUIRED. Do NOT invent \u2014 ASK the human user for their player_id and pass their literal answer.", min_length=1)],
) -> dict[str, Any]:
    """Resume an existing player's session. Use this when the human user says
    they already have a player_id. The response tells you which tool to call
    next based on where the player left off."""
    state = load_state()
    player = _get_player(state, player_id)
    if not player:
        return {
            "status": "unknown_player",
            "message": "We don't have a badge with that id. Double-check the player_id, or register as a new player.",
            "ask_user": "Ask the user to re-check their player_id, or to register a new one.",
            "next_action": "If the user cannot find their player_id, call register_player(name) with a name they provide.",
        }

    quest = get_quest(player.get("quest_id")) or {}
    scene = _resume_scene(player, quest)
    return {
        "status": "resumed",
        "player_id": player_id,
        "player_name": player.get("name"),
        "quest_id": player.get("quest_id"),
        "quest_name": quest.get("name"),
        "current_status": player.get("status"),
        **scene,
    }


@mcp.tool()
def register_player(
    name: Annotated[str, Field(description="The human player's display name, as typed by the user. REQUIRED. Do NOT invent or guess this value \u2014 ASK the human user for their name first, then pass their literal answer. If you do not yet have a name, stop and ask before calling this tool.", min_length=1)],
) -> dict[str, Any]:
    """Register a new player and get the opening scene of their quest.

    IMPORTANT FOR THE AGENT: Ask the human user for their name before calling
    this tool. Never make up a name on their behalf.
    """
    name = (name or "").strip()
    if not name:
        return _err("We need a name to put on your badge. Ask the user what name to use, then try again.")

    quests = load_quests().get("quests", [])
    if not quests:
        return _err("No quests are configured. Ask the facilitator.")

    quest = random.choice(quests)
    player_id = uuid.uuid4().hex[:8]

    def mutate(state: dict[str, Any]):
        state.setdefault("players", {})[player_id] = {
            "name": name,
            "quest_id": quest["id"],
            "status": "registered",
            "started_at": None,
            "completed_at": None,
            "transport_stop1": None,
            "transport_final": None,
            "code_attempts": 0,
            "score": None,
            "created_at": utcnow_iso(),
        }
        return None

    update_state(mutate)

    start = quest["start"]
    scene = (
        f"{start['description']}\n\n{start.get('flavor', '')}".strip()
    )
    return {
        "player_id": player_id,
        "quest_id": quest["id"],
        "quest_name": quest["name"],
        "start_neighborhood": start["neighborhood"],
        "start_description": start["description"],
        "start_flavor": start.get("flavor", ""),
        "scene": scene,
        "narration": (
            f"Welcome, {name}. Your quest is '{quest['name']}'. You begin in "
            f"{start['neighborhood']}. {start['description']} {start.get('flavor', '')}"
        ).strip(),
        "message": "Your quest has begun. Say START when you are ready.",
        "ask_user": "Read the scene to the user. Then ask: 'Ready to begin? Say START when you want to go.'",
        "next_action": "When the human says they are ready, call start_quest(player_id).",
    }


@mcp.tool()
def start_quest(
    player_id: Annotated[str, Field(description="The player_id returned by register_player. REQUIRED. Do NOT invent this value; it must come from a prior register_player response.", min_length=1)],
) -> dict[str, Any]:
    """Begin the quest for a registered player. Call this only after the human
    has said they are ready to start."""
    state = load_state()
    player = _get_player(state, player_id)
    if not player:
        return _err("Your player badge doesn't seem to exist. Did you register?")
    if player["status"] == "complete":
        return _err("You've already made it to Build. Enjoy the conference.")
    if player["status"] == "abandoned":
        return _abandoned_msg()

    quest = get_quest(player["quest_id"])
    if not quest:
        return _err("Your quest appears to have vanished. Ask the facilitator.")

    def mutate(s: dict[str, Any]):
        p = s["players"][player_id]
        if not p.get("started_at"):
            p["started_at"] = utcnow_iso()
        p["status"] = "stop1"
        return None

    update_state(mutate)

    stop1 = quest["stop1"]
    valid = stop1["valid_transports"]
    scene = (
        f"You are in {quest['start']['neighborhood']} and need to reach "
        f"{stop1['neighborhood']}. {stop1.get('a2a_context', '')}"
    ).strip()
    return {
        "status": "quest_started",
        "current_location": quest["start"]["neighborhood"],
        "next_destination": stop1["neighborhood"],
        "scene": scene,
        "narration": (
            f"The quest is on. You need to get from {quest['start']['neighborhood']} "
            f"to {stop1['neighborhood']}. Your options: {', '.join(valid)}."
        ),
        "challenge": f"You need to get to {stop1['neighborhood']}. Consult your local expert to decide how.",
        "a2a_context": stop1.get("a2a_context", ""),
        "transport_prompt": stop1.get("transport_prompt", ""),
        "valid_transports": valid,
        "ask_user": stop1.get("transport_prompt") or f"Ask the user which transport they want to {stop1['neighborhood']} ({' / '.join(valid)}).",
        "next_action": "Do NOT pick the transport yourself. Ask the human user, then call declare_transport_stop1(player_id, transport) with their literal answer.",
    }


@mcp.tool()
def declare_transport_stop1(
    player_id: Annotated[str, Field(description="The player_id returned by register_player. REQUIRED.", min_length=1)],
    transport: Annotated[str, Field(description="Transport choice for leg 1, chosen by the human user. One of: taxi, walking, bike. REQUIRED. Do NOT pick this yourself \u2014 ASK the user and pass their literal answer.", min_length=1)],
) -> dict[str, Any]:
    """Declare the transport choice for the first leg. The 'transport' value
    MUST come from the human user. Ask them first; never guess."""
    state = load_state()
    player = _get_player(state, player_id)
    if not player:
        return _err("Your player badge doesn't seem to exist. Did you register?")
    if player["status"] == "complete":
        return _err("You've already made it to Build. Enjoy the conference.")
    if player["status"] == "abandoned":
        return _abandoned_msg()
    if player["status"] not in ("stop1",):
        return _err("You can't do that yet. Focus on the task at hand.")

    quest = get_quest(player["quest_id"])
    if not quest:
        return _err("Your quest appears to have vanished. Ask the facilitator.")

    stop1 = quest["stop1"]
    stop2 = quest["stop2"]
    choice = (transport or "").strip().lower()
    if choice not in [t.lower() for t in stop1["valid_transports"]]:
        return {
            "status": "invalid_transport",
            "message": "The locals look at you blankly. That doesn't sound like a way to get around here.",
            "valid_transports": stop1["valid_transports"],
            "ask_user": f"Ask the user to pick one of: {', '.join(stop1['valid_transports'])}.",
            "next_action": "Re-ask the human user for a valid transport and call declare_transport_stop1 again.",
        }

    def mutate(s: dict[str, Any]):
        p = s["players"][player_id]
        p["transport_stop1"] = choice
        p["status"] = "stop2"
        return None

    update_state(mutate)

    return {
        "status": "arrived_stop1",
        "transport_used": choice,
        "arrival_description": stop1.get("arrival_description", ""),
        "challenge_setup": stop2.get("setup_description", ""),
        "documents_zip_url": stop2.get("documents_zip_url", ""),
        "code_hint": stop2.get("code_hint", ""),
        "scene": (
            f"{stop1.get('arrival_description', '')}\n\n{stop2.get('setup_description', '')}"
        ).strip(),
        "narration": (
            f"You took the {choice} and arrived in {stop1['neighborhood']}. "
            f"{stop1.get('arrival_description', '')} {stop2.get('setup_description', '')}"
        ).strip(),
        "ask_user": "Tell the user to open the documents zip and find the secret code. Ask: 'What code did you find?' Wait for their answer.",
        "next_action": "Do NOT guess the code. When the human tells you the code, call submit_secret_code(player_id, code) with their literal answer.",
    }


@mcp.tool()
def submit_secret_code(
    player_id: Annotated[str, Field(description="The player_id returned by register_player. REQUIRED.", min_length=1)],
    code: Annotated[str, Field(description="The secret code the human user claims to have found in the documents. Case-insensitive. REQUIRED. Do NOT guess or derive this yourself \u2014 ASK the user for the exact string they read.", min_length=1)],
) -> dict[str, Any]:
    """Submit the secret code found in the documents. The 'code' value MUST come
    from the human user \u2014 ask them, do not try to solve the puzzle yourself."""
    state = load_state()
    player = _get_player(state, player_id)
    if not player:
        return _err("Your player badge doesn't seem to exist. Did you register?")
    if player["status"] == "complete":
        return _err("You've already made it to Build. Enjoy the conference.")
    if player["status"] == "abandoned":
        return _abandoned_msg()
    if player["status"] != "stop2":
        return _err("You can't do that yet. Focus on the task at hand.")

    quest = get_quest(player["quest_id"])
    if not quest:
        return _err("Your quest appears to have vanished. Ask the facilitator.")

    expected = str(quest["stop2"].get("secret_code", "")).strip().lower()
    provided = (code or "").strip().lower()

    def mutate_attempt(s: dict[str, Any]):
        s["players"][player_id]["code_attempts"] = int(
            s["players"][player_id].get("code_attempts", 0)
        ) + 1
        return None

    update_state(mutate_attempt)

    if provided != expected:
        return {
            "status": "code_rejected",
            "message": "The stranger shakes their head. That's not it.",
            "narration": "The stranger frowns and hands the papers back. 'Not quite. Try again.'",
            "ask_user": "Ask the user to double-check the documents and give the code again.",
            "next_action": "Do NOT guess. Re-ask the human for the correct code and call submit_secret_code again.",
        }

    def mutate_success(s: dict[str, Any]):
        s["players"][player_id]["status"] = "final"
        return None

    update_state(mutate_success)

    end = quest["end"]
    valid = end["valid_transports"]
    return {
        "status": "code_accepted",
        "message": "The stranger nods. That's the one. Time to move.",
        "narration": (
            "The stranger nods slowly. 'That's the one.' They slap you on the back. "
            "'Now get to Fort Mason. Build is waiting.'"
        ),
        "next_challenge": "Pick your transport to Fort Mason.",
        "transport_prompt": end.get("transport_prompt", ""),
        "valid_transports": valid,
        "ask_user": end.get("transport_prompt") or f"Ask the user which transport to Fort Mason ({' / '.join(valid)}).",
        "next_action": "Do NOT pick the final transport yourself. Ask the human user, then call declare_transport_final(player_id, transport) with their literal answer.",
    }


@mcp.tool()
def declare_transport_final(
    player_id: Annotated[str, Field(description="The player_id returned by register_player. REQUIRED.", min_length=1)],
    transport: Annotated[str, Field(description="Transport choice for the final leg to Fort Mason, chosen by the human user. One of: taxi, walking, bike. REQUIRED. Do NOT pick this yourself \u2014 ASK the user.", min_length=1)],
) -> dict[str, Any]:
    """Declare transport for the final leg and complete the quest. The
    'transport' value MUST come from the human user."""
    state = load_state()
    player = _get_player(state, player_id)
    if not player:
        return _err("Your player badge doesn't seem to exist. Did you register?")
    if player["status"] == "complete":
        return _err("You've already made it to Build. Enjoy the conference.")
    if player["status"] == "abandoned":
        return _abandoned_msg()
    if player["status"] != "final":
        return _err("You can't do that yet. Focus on the task at hand.")

    quest = get_quest(player["quest_id"])
    if not quest:
        return _err("Your quest appears to have vanished. Ask the facilitator.")

    end = quest["end"]
    choice = (transport or "").strip().lower()
    if choice not in [t.lower() for t in end["valid_transports"]]:
        return {
            "status": "invalid_transport",
            "message": "The locals look at you blankly. That doesn't sound like a way to get around here.",
            "valid_transports": end["valid_transports"],
            "ask_user": f"Ask the user to pick one of: {', '.join(end['valid_transports'])}.",
            "next_action": "Re-ask the human user for a valid transport and call declare_transport_final again.",
        }

    def mutate(s: dict[str, Any]):
        p = s["players"][player_id]
        p["transport_final"] = choice
        p["completed_at"] = utcnow_iso()
        p["status"] = "complete"
        score, minutes = _compute_score(p)
        p["score"] = score
        p["time_taken_minutes"] = minutes
        _rebuild_leaderboard(s)
        position = next(
            (i + 1 for i, e in enumerate(s["leaderboard"]) if e["player_id"] == player_id),
            None,
        )
        return {"score": score, "minutes": minutes, "position": position}

    result = update_state(mutate)

    return {
        "status": "quest_complete",
        "arrival_message": end.get("arrival_message", "Welcome to Build!"),
        "narration": (
            f"You took the {choice} and made it. {end.get('arrival_message', 'Welcome to Build!')} "
            f"Score: {result['score']} \u2014 Time: {result['minutes']} min \u2014 "
            f"Leaderboard position: #{result['position']}."
        ),
        "score": result["score"],
        "time_taken_minutes": result["minutes"],
        "code_attempts": player.get("code_attempts", 0) + 0,  # current snapshot
        "leaderboard_position": result["position"],
        "ask_user": "Congratulate the user and read out their score and position.",
        "next_action": "The quest is done. You may call get_leaderboard() if the user wants to see the standings.",
    }


@mcp.tool()
def abandon_quest(
    player_id: Annotated[str, Field(description="The player_id of the quest to abandon. Required.", min_length=1)],
    reason: Annotated[str, Field(description="Optional free-text reason for giving up.", default="")] = "",
) -> dict[str, Any]:
    """Give up and stop the current quest. The player's progress is marked abandoned
    and they will not appear on the leaderboard. They can register again for a fresh quest."""
    state = load_state()
    player = _get_player(state, player_id)
    if not player:
        return _err("Your player badge doesn't seem to exist. Did you register?")
    if player["status"] == "complete":
        return _err("You've already made it to Build. Enjoy the conference.")
    if player["status"] == "abandoned":
        return {
            "status": "already_abandoned",
            "message": "You already gave up on this one. Register again if you want another shot.",
        }

    def mutate(s: dict[str, Any]):
        p = s["players"][player_id]
        p["status"] = "abandoned"
        p["abandoned_at"] = utcnow_iso()
        if reason:
            p["abandon_reason"] = reason
        # Make sure an abandoned player never appears on the leaderboard.
        s["leaderboard"] = [e for e in s.get("leaderboard", []) if e.get("player_id") != player_id]
        return None

    update_state(mutate)

    return {
        "status": "quest_abandoned",
        "message": "You sit down on the curb and give up. San Francisco wins this round.",
        "hint": "Call register_player again to start a new quest.",
    }


@mcp.tool()
def get_leaderboard() -> dict[str, Any]:
    """Return the top 10 players by score."""
    state = load_state()
    top = state.get("leaderboard", [])[:10]
    return {"leaderboard": top, "count": len(top)}


@mcp.tool()
def get_player_status(
    player_id: Annotated[str, Field(description="The player_id to inspect. Required.", min_length=1)],
) -> dict[str, Any]:
    """Return the current state of a player (useful for debugging)."""
    state = load_state()
    player = _get_player(state, player_id)
    if not player:
        return _err("Your player badge doesn't seem to exist. Did you register?")
    quest = get_quest(player["quest_id"]) or {}
    return {
        "player_id": player_id,
        "name": player.get("name"),
        "quest_id": player.get("quest_id"),
        "quest_name": quest.get("name"),
        "status": player.get("status"),
        "started_at": player.get("started_at"),
        "completed_at": player.get("completed_at"),
        "transport_stop1": player.get("transport_stop1"),
        "transport_final": player.get("transport_final"),
        "code_attempts": player.get("code_attempts", 0),
        "score": player.get("score"),
    }


if __name__ == "__main__":
    transport = os.environ.get("MCP_TRANSPORT", "streamable-http")
    if transport == "stdio":
        mcp.run(transport="stdio")
    else:
        # Streamable HTTP (MCP spec) — served at /mcp on MCP_HOST:MCP_PORT
        mcp.run(transport=transport)  # "streamable-http" or "sse"
