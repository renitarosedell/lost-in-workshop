"""
Lost in Raleigh — Reference Agent (all five steps combined).

This is the gold-standard fallback for Step 5. It combines every capability
from steps 1–5 into a single autonomous agent that completes the full quest
without any manual intervention.

It satisfies all constitution compliance gates:
  - Python 3.11+, Microsoft Agent Framework
  - Azure OpenAI via AI Foundry (no api.openai.com)
  - MCPStreamableHTTPTool for game server
  - FileContextProvider for player_id persistence
  - httpx.post for A2A expert calls
  - zipfile + re for RAG document parsing
  - Full quest loop: register → A2A → stop1 → bundle → code → final transport

Run it:
  python agent.py

On first run: registers you and runs the full quest.
On subsequent runs: resumes from memory.json if not already complete.
"""
from __future__ import annotations

import asyncio
import io
import json
import os
import re
import zipfile
from pathlib import Path

import httpx
from agent_framework import Agent, MCPStreamableHTTPTool, ContextProvider, SessionContext
from agent_framework.openai import OpenAIChatClient
from dotenv import load_dotenv

load_dotenv()


MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8000/mcp")
MEMORY_FILE = Path(__file__).parent / "memory.json"


# ─── FileContextProvider ────────────────────────────────────────────────────

class FileContextProvider(ContextProvider):
    """Persists player_id to memory.json between runs."""

    def __init__(self) -> None:
        super().__init__("player-memory")

    def _load(self) -> dict:
        if MEMORY_FILE.exists():
            return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
        return {}

    def _save(self, data: dict) -> None:
        MEMORY_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

    async def before_run(self, *, context: SessionContext, **_) -> None:
        data = self._load()
        player_id = data.get("player_id")
        if player_id:
            context.extend_instructions(
                self.source_id,
                f"Your player_id is {player_id}. Use it for all tool calls. "
                "Do not call register_player again.",
            )

    async def after_run(self, *, context: SessionContext, **_) -> None:
        data = self._load()
        if data.get("player_id"):
            return
        for msg in context.output_messages:
            text = getattr(msg, "text", "") or ""
            match = re.search(r"PLR-[A-Z0-9]{8}", text)
            if match:
                data["player_id"] = match.group(0)
                self._save(data)
                break


# ─── A2A helper ─────────────────────────────────────────────────────────────

def ask_a2a_expert(a2a_url: str, question: str) -> str:
    with httpx.Client(timeout=30) as client:
        r = client.post(a2a_url, json={"message": question})
        r.raise_for_status()
        return r.json()["advice"]


# ─── RAG helper ─────────────────────────────────────────────────────────────

def find_secret_code(bundle_url: str) -> str:
    """Download the quest ZIP and search Markdown files for the secret code."""
    with httpx.Client(timeout=60, follow_redirects=True) as client:
        r = client.get(bundle_url)
        r.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
        for name in zf.namelist():
            if not name.endswith(".md"):
                continue
            text = zf.read(name).decode("utf-8", errors="replace")
            candidates = re.findall(r"\b[A-Z]{3,}[A-Z0-9]*\b", text)
            for word in candidates:
                if 5 <= len(word) <= 15 and word.isalnum():
                    return word
    raise RuntimeError("Secret code not found in document bundle.")


# ─── Agent helpers ───────────────────────────────────────────────────────────

def _make_client() -> OpenAIChatClient:
    return OpenAIChatClient(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        model=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
    )


def _parse_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise RuntimeError(f"Could not parse JSON from: {text[:200]}")
    return json.loads(match.group(0))


# ─── Main ────────────────────────────────────────────────────────────────────

async def main() -> None:
    game_mcp = MCPStreamableHTTPTool(
        name="Lost in Raleigh Game Server",
        url=MCP_SERVER_URL,
        description="MCP game server for the Lost in Raleigh workshop.",
    )
    await game_mcp.connect()

    memory = FileContextProvider()

    # ── Phase 1: Register ──
    print("=== Phase 1: Register ===")
    reg_agent = Agent(
        client=_make_client(),
        name="RaleighAgent",
        instructions=(
            "Register as a new player called 'Workshop Attendee' using register_player. "
            "Return a JSON object containing: player_id, a2a_expert_url, "
            "stop1_location, transport_options. Return ONLY valid JSON."
        ),
        tools=[game_mcp],
        context_providers=[memory],
    )
    reg_session = reg_agent.create_session()
    reg_text = (await reg_agent.run("Register me.", session=reg_session)).text or ""
    reg = _parse_json(reg_text)
    player_id: str = reg["player_id"]
    a2a_url: str = reg["a2a_expert_url"]
    print(f"player_id = {player_id}")

    # ── Phase 2: A2A transport advice ──
    print("\n=== Phase 2: A2A Transport Advice ===")
    stop1_location = reg.get("stop1_location", "stop 1")
    advice = ask_a2a_expert(a2a_url, f"Best way to get to {stop1_location}?")
    print(f"A2A advice: {advice}")
    transport_stop1 = "rideshare"
    for kw in ["rideshare", "bus", "bike", "walk"]:
        if kw in advice.lower():
            transport_stop1 = kw
            break

    # ── Phase 3: Declare transport to stop 1 ──
    print("\n=== Phase 3: Declare Transport → Stop 1 ===")
    dec1_agent = Agent(
        client=_make_client(),
        name="RaleighAgent",
        instructions=(
            f"Call declare_transport_stop1 with player_id='{player_id}' and "
            f"transport='{transport_stop1}'. Return JSON with document_bundle_url."
        ),
        tools=[game_mcp],
    )
    dec1_text = (await dec1_agent.run("Declare transport.", session=dec1_agent.create_session())).text or ""
    dec1 = _parse_json(dec1_text)
    bundle_url: str = dec1["document_bundle_url"]
    print(f"Bundle URL: {bundle_url}")

    # ── Phase 4: RAG — find secret code ──
    print("\n=== Phase 4: Document Bundle & Secret Code ===")
    code = find_secret_code(bundle_url)
    print(f"Secret code: {code}")

    # ── Phase 5: Submit code ──
    print("\n=== Phase 5: Submit Code ===")
    sub_agent = Agent(
        client=_make_client(),
        name="RaleighAgent",
        instructions=(
            f"Call submit_secret_code with player_id='{player_id}' and code='{code}'. "
            "Print whether the code was accepted."
        ),
        tools=[game_mcp],
    )
    print((await sub_agent.run("Submit the code.", session=sub_agent.create_session())).text)

    # ── Phase 6: Final transport ──
    print("\n=== Phase 6: Final Transport → NC Biotech Center ===")
    fin_agent = Agent(
        client=_make_client(),
        name="RaleighAgent",
        instructions=(
            f"Call declare_transport_final with player_id='{player_id}' and "
            "transport='rideshare'. Print the final score."
        ),
        tools=[game_mcp],
    )
    print((await fin_agent.run("Complete the quest.", session=fin_agent.create_session())).text)

    await game_mcp.close()


if __name__ == "__main__":
    asyncio.run(main())
