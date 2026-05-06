"""FastAPI admin UI for the Lost in San Francisco MCP game."""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

from storage import load_quests, load_state, save_quests, update_state

app = FastAPI(title="Lost in SF — Admin")


INDEX_HTML = """<!doctype html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\" />
<title>Lost in SF — Admin</title>
<style>
 body { font-family: -apple-system, system-ui, sans-serif; margin: 2rem; color: #222; background: #fafafa; }
 h1 { margin-top: 0; }
 h2 { border-bottom: 1px solid #ccc; padding-bottom: .25rem; margin-top: 2rem; }
 table { border-collapse: collapse; width: 100%; background: #fff; }
 th, td { border: 1px solid #ddd; padding: .4rem .6rem; font-size: 14px; text-align: left; vertical-align: top; }
 th { background: #f0f0f0; }
 button { padding: .4rem .8rem; cursor: pointer; }
 .danger { background: #c33; color: #fff; border: none; border-radius: 4px; }
 .primary { background: #2a6; color: #fff; border: none; border-radius: 4px; }
 textarea { width: 100%; min-height: 340px; font-family: ui-monospace, monospace; font-size: 13px; }
 .row { display: flex; gap: 2rem; }
 .col { flex: 1; }
 .pill { display: inline-block; padding: 1px 8px; border-radius: 10px; background: #eef; font-size: 12px; }
 .muted { color: #666; font-size: 12px; }
</style>
</head>
<body>
<h1>Lost in San Francisco — Admin</h1>
<p class=\"muted\">MCP game facilitator console. Leaderboard and players refresh every 10s.</p>

<h2>Quests</h2>
<p class=\"muted\">Edit the raw JSON and save. This writes to <code>quests.json</code>.</p>
<textarea id=\"quests\"></textarea>
<div style=\"margin-top:.5rem\">
  <button class=\"primary\" onclick=\"saveQuests()\">Save quests.json</button>
  <button onclick=\"loadQuests()\">Reload</button>
  <span id=\"quests-status\" class=\"muted\"></span>
</div>

<div class=\"row\">
<div class=\"col\">
<h2>Leaderboard</h2>
<div id=\"leaderboard\"></div>
</div>
<div class=\"col\">
<h2>Players</h2>
<div id=\"players\"></div>
</div>
</div>

<h2>Danger zone</h2>
<button class=\"danger\" onclick=\"resetAll()\">Reset ALL players</button>

<script>
async function loadQuests() {
  const r = await fetch('/api/quests');
  const d = await r.json();
  document.getElementById('quests').value = JSON.stringify(d, null, 2);
  document.getElementById('quests-status').textContent = 'Loaded.';
}
async function saveQuests() {
  const text = document.getElementById('quests').value;
  let parsed;
  try { parsed = JSON.parse(text); }
  catch (e) { alert('Invalid JSON: ' + e.message); return; }
  const r = await fetch('/api/quests', { method: 'PUT', headers: {'Content-Type':'application/json'}, body: JSON.stringify(parsed) });
  const d = await r.json();
  document.getElementById('quests-status').textContent = d.ok ? 'Saved.' : ('Error: ' + d.error);
}

function fmt(x) { return x == null ? '' : x; }

async function loadLeaderboard() {
  const r = await fetch('/api/leaderboard');
  const d = await r.json();
  let html = '<table><tr><th>#</th><th>Name</th><th>Quest</th><th>Score</th><th>Minutes</th><th>Attempts</th></tr>';
  d.leaderboard.forEach((e, i) => {
    html += `<tr><td>${i+1}</td><td>${fmt(e.name)}</td><td>${fmt(e.quest_name)}</td><td>${fmt(e.score)}</td><td>${fmt(e.time_taken_minutes)}</td><td>${fmt(e.code_attempts)}</td></tr>`;
  });
  if (d.leaderboard.length === 0) html += '<tr><td colspan=\"6\" class=\"muted\">No completions yet.</td></tr>';
  html += '</table>';
  document.getElementById('leaderboard').innerHTML = html;
}

async function loadPlayers() {
  const r = await fetch('/api/players');
  const d = await r.json();
  let html = '<table><tr><th>ID</th><th>Name</th><th>Quest</th><th>Status</th><th>Attempts</th><th>Score</th><th></th></tr>';
  Object.entries(d.players).forEach(([pid, p]) => {
    html += `<tr><td><code>${pid}</code></td><td>${fmt(p.name)}</td><td>${fmt(p.quest_id)}</td><td><span class=\"pill\">${fmt(p.status)}</span></td><td>${fmt(p.code_attempts)}</td><td>${fmt(p.score)}</td><td><button onclick=\"resetPlayer('${pid}')\">Reset</button></td></tr>`;
  });
  if (Object.keys(d.players).length === 0) html += '<tr><td colspan=\"7\" class=\"muted\">No players registered.</td></tr>';
  html += '</table>';
  document.getElementById('players').innerHTML = html;
}

async function resetPlayer(pid) {
  if (!confirm('Reset player ' + pid + '?')) return;
  await fetch('/api/players/' + pid, { method: 'DELETE' });
  loadPlayers(); loadLeaderboard();
}
async function resetAll() {
  if (!confirm('This will delete ALL players and the leaderboard. Continue?')) return;
  if (!confirm('Really? This cannot be undone.')) return;
  await fetch('/api/players', { method: 'DELETE' });
  loadPlayers(); loadLeaderboard();
}

loadQuests();
loadLeaderboard();
loadPlayers();
setInterval(() => { loadLeaderboard(); loadPlayers(); }, 10000);
</script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return INDEX_HTML


@app.get("/api/quests")
def api_get_quests() -> dict[str, Any]:
    return load_quests()


@app.put("/api/quests")
def api_put_quests(payload: dict[str, Any]) -> dict[str, Any]:
    if "quests" not in payload or not isinstance(payload["quests"], list):
        raise HTTPException(status_code=400, detail="Missing 'quests' list")
    save_quests(payload)
    return {"ok": True}


@app.get("/api/leaderboard")
def api_leaderboard() -> dict[str, Any]:
    state = load_state()
    return {"leaderboard": state.get("leaderboard", [])[:10]}


@app.get("/api/players")
def api_players() -> dict[str, Any]:
    state = load_state()
    return {"players": state.get("players", {})}


@app.delete("/api/players/{player_id}")
def api_reset_player(player_id: str) -> dict[str, Any]:
    def mutate(s: dict[str, Any]):
        s.get("players", {}).pop(player_id, None)
        s["leaderboard"] = [e for e in s.get("leaderboard", []) if e.get("player_id") != player_id]
        return None

    update_state(mutate)
    return {"ok": True}


@app.delete("/api/players")
def api_reset_all() -> dict[str, Any]:
    def mutate(s: dict[str, Any]):
        s["players"] = {}
        s["leaderboard"] = []
        return None

    update_state(mutate)
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
