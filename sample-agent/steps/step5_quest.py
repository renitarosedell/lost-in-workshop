"""
Step 5 — Full quest loop: A2A call, stop 1, RAG document search, final transport.

What this adds:
  - A2A call: asks the Raleigh transport expert for the best route via httpx.post.
  - declare_transport_stop1: records your leg-1 transport choice.
  - Document download: fetches the quest ZIP from Azure Blob Storage, extracts
    Markdown files, and searches for the secret code in the text.
  - submit_secret_code: submits the code.
  - declare_transport_final: completes the quest and prints your final score.

Run it:
  python steps/step5_quest.py

Expected output:
  A2A advice: Rideshare is fastest at around 8 minutes...
  Transport: rideshare
  Bundle downloaded: glenwood_getaway.zip
  Secret code found: GLENWOOD42
  Code accepted!
  Quest complete! Final score: 920
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
MEMORY_FILE = Path(__file__).parent.parent / "memory.json"


# ─── Memory provider (same as step 4) ──────────────────────────────────────

class FileContextProvider(ContextProvider):
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
                f"Your player_id is {player_id}. Use it for all tool calls.",
            )

    async def after_run(self, *, context: SessionContext, **_) -> None:
        pass  # player_id is saved from main() after agent.run() returns


# ─── A2A helper ─────────────────────────────────────────────────────────────

def ask_a2a_expert(a2a_url: str, question: str) -> str:
    """Call the A2A transport expert and return its advice."""
    with httpx.Client(timeout=30) as client:
        response = client.post(a2a_url, json={"message": question})
        response.raise_for_status()
        return response.json()["advice"]


# ─── RAG helper ─────────────────────────────────────────────────────────────

def find_secret_code(bundle_url: str) -> str | None:
    """Download the quest ZIP, extract Markdown files, and search for the code."""
    with httpx.Client(timeout=60, follow_redirects=True) as client:
        r = client.get(bundle_url)
        r.raise_for_status()
        zip_bytes = r.content

    print(f"Bundle downloaded ({len(zip_bytes) // 1024} KB)")

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        for name in zf.namelist():
            if not name.endswith(".md"):
                continue
            text = zf.read(name).decode("utf-8", errors="replace")
            # Look for uppercase words that appear to be codes (ALL_CAPS or ALL_CAPS+digits)
            candidates = re.findall(r"\b[A-Z]{3,}[A-Z0-9]*\b", text)
            for word in candidates:
                # Heuristic: codes are 5-12 chars, all upper, may contain digits
                if 5 <= len(word) <= 15 and word.isalnum():
                    print(f"Code candidate in {name}: {word}")
                    return word
    return None


# ─── Main quest loop ─────────────────────────────────────────────────────────

async def main() -> None:
    client = OpenAIChatClient(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        model=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
    )

    game_mcp = MCPStreamableHTTPTool(
        name="Lost in Raleigh Game Server",
        url=MCP_SERVER_URL,
        description="MCP game server for the Lost in Raleigh workshop.",
    )
    await game_mcp.connect()

    memory = FileContextProvider()

    # Check if already registered from a previous step
    saved = memory._load()
    saved_player_id = saved.get("player_id")

    if saved_player_id and saved.get("a2a_expert_url"):
        # Resume from memory — no need to call register_player again
        player_id = saved_player_id
        a2a_url = saved["a2a_expert_url"]
        stop1_location = saved.get("stop1_location", "stop 1")
        print(f"Resuming with saved player_id: {player_id}")
    else:
        # Step 1: Register as a new player
        register_agent = Agent(
            client=client,
            name="RaleighAgent",
            instructions=(
                "Register as a new player with the name 'Workshop Attendee' using "
                "register_player. Return a JSON object with: player_id, a2a_expert_url, "
                "stop1_location, and transport_options. Return ONLY valid JSON."
            ),
            tools=[game_mcp],
            context_providers=[memory],
        )
        session = register_agent.create_session()
        reg_response = await register_agent.run(
            "Register me and return the quest details as JSON.", session=session
        )

        # Parse the registration JSON from the response
        reg_text = reg_response.text or ""
        json_match = re.search(r"\{.*\}", reg_text, re.DOTALL)
        if not json_match:
            print("Registration response:", reg_text)
            raise RuntimeError("Could not parse registration response as JSON.")
        reg_data = json.loads(json_match.group(0))

        player_id = reg_data["player_id"]
        a2a_url = reg_data["a2a_expert_url"]
        stop1_location = reg_data.get("stop1_location", "stop 1")
        print(f"\nRegistered! player_id = {player_id}")

        # Save all quest data to memory for future steps
        memory._save({
            "player_id": player_id,
            "a2a_expert_url": a2a_url,
            "stop1_location": stop1_location,
        })

    # Step 2: Ask A2A expert for transport advice
    question = f"What is the best way to get to {stop1_location} for the quest?"
    advice = ask_a2a_expert(a2a_url, question)
    print(f"\nA2A advice: {advice}")

    # Pick the first transport option mentioned (simplified heuristic)
    transport_stop1 = "rideshare"
    for keyword in ["rideshare", "bus", "bike", "walk", "GoRaleigh"]:
        if keyword.lower() in advice.lower():
            transport_stop1 = keyword.lower().replace("goraleigh", "goRaleigh_bus")
            break
    print(f"Transport chosen: {transport_stop1}")

    # Step 3: Declare transport to stop 1 and get bundle URL
    declare_agent = Agent(
        client=client,
        name="RaleighAgent",
        instructions=(
            f"Call declare_transport_stop1 with player_id='{player_id}' and "
            f"transport='{transport_stop1}'. Return a JSON object with: "
            "document_bundle_url. Return ONLY valid JSON."
        ),
        tools=[game_mcp],
    )
    declare_session = declare_agent.create_session()
    declare_response = await declare_agent.run("Declare transport to stop 1.", session=declare_session)
    declare_text = declare_response.text or ""
    json_match2 = re.search(r"\{.*\}", declare_text, re.DOTALL)
    if not json_match2:
        print("Declare response:", declare_text)
        raise RuntimeError("Could not parse declare_transport_stop1 response.")
    declare_data = json.loads(json_match2.group(0))
    bundle_url: str = declare_data["document_bundle_url"]
    print(f"\nBundle URL: {bundle_url}")

    # Step 4: Download bundle and find secret code
    code = find_secret_code(bundle_url)
    if not code:
        raise RuntimeError("Could not find secret code in the document bundle.")
    print(f"Secret code found: {code}")

    # Step 5: Submit secret code
    submit_agent = Agent(
        client=client,
        name="RaleighAgent",
        instructions=(
            f"Call submit_secret_code with player_id='{player_id}' and "
            f"code='{code}'. Print whether the code was accepted."
        ),
        tools=[game_mcp],
    )
    submit_session = submit_agent.create_session()
    submit_response = await submit_agent.run("Submit the secret code.", session=submit_session)
    print(f"\n{submit_response.text}")

    # Step 6: Declare final transport and complete quest
    transport_final = "rideshare"
    final_agent = Agent(
        client=client,
        name="RaleighAgent",
        instructions=(
            f"Call declare_transport_final with player_id='{player_id}' and "
            f"transport='{transport_final}'. Print the final score."
        ),
        tools=[game_mcp],
    )
    final_session = final_agent.create_session()
    final_response = await final_agent.run("Complete the quest.", session=final_session)
    print(f"\n{final_response.text}")

    await game_mcp.close()


if __name__ == "__main__":
    asyncio.run(main())
