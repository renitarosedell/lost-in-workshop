"""
Step 7 — RAG: Search the document bundle and submit the secret code.

What this adds:
  - Downloads the ZIP bundle from Azure Blob Storage (httpx).
  - Feeds the Markdown documents to an Agent as context (Retrieval-Augmented Generation).
  - The Agent reads the documents, finds the secret code, and calls submit_secret_code.

Run it:
  python steps/step7_rag.py

Expected output:
  Player: PLR-XXXXXXXX
  Downloading bundle: https://...
  Bundle downloaded (42 KB)
  Code accepted! Attempts: 1
"""
from __future__ import annotations

import asyncio
import io
import os
import zipfile

import httpx
from agent_framework import Agent, MCPStreamableHTTPTool
from agent_framework.openai import OpenAIChatClient
from dotenv import load_dotenv

from shared import FileContextProvider

load_dotenv()

MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8000/mcp")


def download_bundle(bundle_url: str) -> str:
    """Download the quest ZIP and return all Markdown content as one string."""
    with httpx.Client(timeout=60, follow_redirects=True) as client:
        r = client.get(bundle_url)
        r.raise_for_status()
        zip_bytes = r.content

    print(f"Bundle downloaded ({len(zip_bytes) // 1024} KB)")

    parts: list[str] = []
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        for name in sorted(zf.namelist()):
            if name.endswith(".md"):
                text = zf.read(name).decode("utf-8", errors="replace")
                parts.append(f"### {name}\n\n{text}")

    return "\n\n---\n\n".join(parts)


async def main() -> None:
    memory = FileContextProvider()
    saved = memory._load()

    player_id = saved.get("player_id")
    bundle_url = saved.get("bundle_url")

    if not player_id:
        print("No player_id found. Run step4_memory.py first.")
        return
    if not bundle_url:
        print("No bundle_url found. Run step6_transport.py first.")
        return

    print(f"Player: {player_id}")
    print(f"Downloading bundle: {bundle_url}")

    # 1. Download and extract the document bundle
    documents = download_bundle(bundle_url)

    # 2. Use an Agent to find the secret code and submit it (RAG pattern)
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

    agent = Agent(
        client=client,
        name="RaleighAgent",
        instructions=(
            f"You are helping player_id='{player_id}' complete the Lost in Raleigh quest. "
            "The user will provide quest documents. Read them carefully to find the secret "
            "code hidden in the text, then call submit_secret_code(player_id, code). "
            "The secret code is a short uppercase alphanumeric string. "
            "Print whether the submission was accepted."
        ),
        tools=[game_mcp],
    )
    session = agent.create_session()
    response = await agent.run(
        f"Here are the quest documents. Find and submit the secret code:\n\n{documents}",
        session=session,
    )
    print(f"\n{response.text}")

    await game_mcp.close()


if __name__ == "__main__":
    asyncio.run(main())
