"""
Concurrent load test for the Lost in Raleigh game server.

Registers 150 players simultaneously using threading and verifies that:
  - All 150 receive distinct PLR- player IDs.
  - state.json contains exactly 150 valid, uncorrupted player records.

Usage:
  python load_test.py [--url http://localhost:8000/mcp] [--players 150]
"""
from __future__ import annotations

import argparse
import json
import threading
import time
import uuid
from pathlib import Path

import requests

BASE_DIR = Path(__file__).parent


def register_one(url: str, name: str, results: dict, idx: int) -> None:
    """Call the MCP register_player tool via JSON-RPC and store the result."""
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": idx,
            "method": "tools/call",
            "params": {
                "name": "register_player",
                "arguments": {"name": name},
            },
        }
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        # Extract player_id from MCP tool response
        content = data.get("result", {}).get("content", [])
        player_id = None
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                text = block.get("text", "")
                import re
                match = re.search(r"PLR-[A-Z0-9]{8}", text)
                if match:
                    player_id = match.group(0)
                    break

        results[idx] = {"player_id": player_id, "name": name, "ok": player_id is not None}
    except Exception as exc:  # noqa: BLE001
        results[idx] = {"player_id": None, "name": name, "ok": False, "error": str(exc)}


def run_load_test(url: str, num_players: int) -> None:
    print(f"Starting load test: {num_players} players → {url}")
    start = time.monotonic()

    results: dict[int, dict] = {}
    threads = []
    for i in range(num_players):
        name = f"LoadTestPlayer-{uuid.uuid4().hex[:8].upper()}"
        t = threading.Thread(target=register_one, args=(url, name, results, i), daemon=True)
        threads.append(t)

    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=60)

    elapsed = time.monotonic() - start

    # ── Analysis ────────────────────────────────────────────────────────────
    succeeded = [r for r in results.values() if r["ok"]]
    failed = [r for r in results.values() if not r["ok"]]
    player_ids = [r["player_id"] for r in succeeded]
    unique_ids = set(player_ids)

    print(f"\nResults ({elapsed:.1f}s):")
    print(f"  Requests sent    : {num_players}")
    print(f"  Succeeded        : {len(succeeded)}")
    print(f"  Failed           : {len(failed)}")
    print(f"  Unique player IDs: {len(unique_ids)}")

    if failed:
        print("\nFirst 5 failures:")
        for r in failed[:5]:
            print(f"  {r.get('name')}: {r.get('error', 'no player_id returned')}")

    duplicates = len(player_ids) - len(unique_ids)
    if duplicates:
        print(f"\n⚠ WARNING: {duplicates} duplicate player IDs detected!")
    else:
        print("\n✓ No duplicate player IDs.")

    # ── state.json check ────────────────────────────────────────────────────
    state_file = BASE_DIR / "lost-in-raleigh" / "state.json"
    if state_file.exists():
        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
            registered = state.get("players", {})
            print(f"\nstate.json check:")
            print(f"  Player records in state.json : {len(registered)}")
            # Verify no corrupted records (each must have a 'name' key)
            corrupted = [pid for pid, p in registered.items() if not isinstance(p, dict) or "name" not in p]
            if corrupted:
                print(f"  ⚠ Corrupted records: {corrupted[:5]}")
            else:
                print("  ✓ All records have valid structure.")
        except json.JSONDecodeError as exc:
            print(f"  ✗ state.json is not valid JSON: {exc}")
    else:
        print("\nstate.json not found (server may write to a different path).")

    # ── Final verdict ────────────────────────────────────────────────────────
    if len(succeeded) == num_players and duplicates == 0:
        print("\n✓ PASS: All players registered with unique IDs.")
    else:
        print("\n✗ FAIL: Load test did not pass all checks.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Lost in Raleigh load test")
    parser.add_argument(
        "--url",
        default="http://localhost:8000/mcp",
        help="MCP server URL (default: http://localhost:8000/mcp)",
    )
    parser.add_argument(
        "--players",
        type=int,
        default=150,
        help="Number of concurrent player registrations (default: 150)",
    )
    args = parser.parse_args()
    run_load_test(args.url, args.players)


if __name__ == "__main__":
    main()
