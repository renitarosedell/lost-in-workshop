"""FastAPI admin UI for the Lost in Raleigh MCP game."""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

from storage import load_state, update_state

app = FastAPI(title="Lost in Raleigh — Admin")


INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>Lost in Raleigh — Admin</title>
<style>
 body { font-family: -apple-system, system-ui, sans-serif; margin: 2rem; color: #222; background: #fafafa; }
 h1 { margin-top: 0; }
 h2 { border-bottom: 1px solid #ccc; padding-bottom: .25rem; margin-top: 2rem; }
 table { border-collapse: collapse; width: 100%; background: #fff; }
 th, td { border: 1px solid #ddd; padding: .4rem .6rem; font-size: 14px; text-align: left; vertical-align: top; }
 th { background: #f0f0f0; }
 button { padding: .4rem .8rem; cursor: pointer; border-radius: 4px; }
 .danger { background: #c33; color: #fff; border: none; }
 .primary { background: #2a6; color: #fff; border: none; }
 .pill { display: inline-block; padding: 1px 8px; border-radius: 10px; font-size: 12px; }
 .pill-reg { background: #ddf; }
 .pill-stop1 { background: #ffd; }
 .pill-stop2 { background: #dfd; }
 .pill-done { background: #cfc; font-weight: bold; }
 .muted { color: #666; font-size: 12px; }
 .row { display: flex; gap: 2rem; }
 .col { flex: 1; }
 #summary-bar { display: flex; gap: 1rem; margin-bottom: 1rem; }
 .summary-cell { flex: 1; background: #fff; border: 1px solid #ddd; padding: .75rem 1rem; border-radius: 4px; text-align: center; }
 .summary-cell .num { font-size: 2rem; font-weight: bold; }
 .summary-cell .label { font-size: 12px; color: #666; }
</style>
</head>
<body>
<h1>Lost in Raleigh — Admin</h1>
<p class="muted">Facilitator console. Players and leaderboard refresh every 5 seconds.</p>

<div id="summary-bar">
  <div class="summary-cell"><div class="num" id="cnt-reg">—</div><div class="label">Registered</div></div>
  <div class="summary-cell"><div class="num" id="cnt-stop1">—</div><div class="label">At Stop 1</div></div>
  <div class="summary-cell"><div class="num" id="cnt-stop2">—</div><div class="label">At Stop 2</div></div>
  <div class="summary-cell"><div class="num" id="cnt-done">—</div><div class="label">Finished</div></div>
</div>

<div class="row">
<div class="col">
<h2>Leaderboard</h2>
<div id="leaderboard"></div>
</div>
<div class="col">
<h2>Players</h2>
<div id="players"></div>
</div>
</div>

<h2>Danger zone</h2>
<button class="danger" onclick="resetAll()">Reset ALL players</button>

<script>
function fmt(x) { return x == null ? '—' : x; }

function milestone_stage(p) {
  const m = p.milestones || {};
  if (m.finished_at) return ['done', 'Finished'];
  if (m.stop2_at)    return ['stop2', 'At Stop 2'];
  if (m.stop1_at)    return ['stop1', 'At Stop 1'];
  return ['reg', 'Registered'];
}

async function loadAll() {
  const [lb, pl] = await Promise.all([
    fetch('/admin/api/leaderboard').then(r => r.json()),
    fetch('/admin/api/players').then(r => r.json()),
  ]);

  // Summary bar
  const players = Object.values(pl.players);
  let reg = 0, stop1 = 0, stop2 = 0, done = 0;
  players.forEach(p => {
    const [stage] = milestone_stage(p);
    if (stage === 'reg')   reg++;
    if (stage === 'stop1') stop1++;
    if (stage === 'stop2') stop2++;
    if (stage === 'done')  done++;
  });
  document.getElementById('cnt-reg').textContent   = reg + stop1 + stop2 + done;
  document.getElementById('cnt-stop1').textContent = stop1;
  document.getElementById('cnt-stop2').textContent = stop2;
  document.getElementById('cnt-done').textContent  = done;

  // Leaderboard
  let html = '<table><tr><th>#</th><th>Name</th><th>Quest</th><th>Score</th><th>Minutes</th><th>Attempts</th></tr>';
  lb.leaderboard.forEach((e, i) => {
    html += `<tr><td>${i+1}</td><td>${fmt(e.name)}</td><td>${fmt(e.quest_name)}</td><td>${fmt(e.score)}</td><td>${fmt(e.time_taken_minutes)}</td><td>${fmt(e.code_attempts)}</td></tr>`;
  });
  if (lb.leaderboard.length === 0) html += '<tr><td colspan="6" class="muted">No completions yet.</td></tr>';
  html += '</table>';
  document.getElementById('leaderboard').innerHTML = html;

  // Players (sorted: done first, then stop2, stop1, reg)
  const order = { done: 0, stop2: 1, stop1: 2, reg: 3 };
  const sorted = Object.entries(pl.players).sort((a, b) => {
    return order[milestone_stage(a[1])[0]] - order[milestone_stage(b[1])[0]];
  });
  html = '<table><tr><th>ID</th><th>Name</th><th>Quest</th><th>Stage</th><th>Attempts</th><th>Score</th><th></th></tr>';
  sorted.forEach(([pid, p]) => {
    const [stage, label] = milestone_stage(p);
    html += `<tr>
      <td><code>${pid}</code></td>
      <td>${fmt(p.name)}</td>
      <td>${fmt(p.quest_id)}</td>
      <td><span class="pill pill-${stage}">${label}</span></td>
      <td>${fmt(p.code_attempts)}</td>
      <td>${p.score != null ? p.score : '—'}</td>
      <td><button class="danger" onclick="resetPlayer('${pid}')">Reset</button></td>
    </tr>`;
  });
  if (sorted.length === 0) html += '<tr><td colspan="7" class="muted">No players registered.</td></tr>';
  html += '</table>';
  document.getElementById('players').innerHTML = html;
}

async function resetPlayer(pid) {
  if (!confirm('Reset player ' + pid + '? This removes them from the leaderboard.')) return;
  await fetch('/admin/api/players/' + pid, { method: 'DELETE' });
  loadAll();
}

async function resetAll() {
  if (!confirm('Delete ALL players and the leaderboard?')) return;
  if (!confirm('Really? This cannot be undone.')) return;
  await fetch('/admin/api/players', { method: 'DELETE' });
  loadAll();
}

loadAll();
setInterval(loadAll, 5000);
</script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return INDEX_HTML


@app.get("/api/leaderboard")
def api_leaderboard() -> dict[str, Any]:
    state = load_state()
    return {"leaderboard": state.get("leaderboard", [])[:20]}


@app.get("/api/players")
def api_players() -> dict[str, Any]:
    state = load_state()
    return {"players": state.get("players", {})}


@app.delete("/api/players/{player_id}")
def api_reset_player(player_id: str) -> dict[str, Any]:
    def mutate(s: dict[str, Any]) -> None:
        s.get("players", {}).pop(player_id, None)
        s["leaderboard"] = [
            e for e in s.get("leaderboard", []) if e.get("player_id") != player_id
        ]

    update_state(mutate)
    return {"ok": True}


@app.delete("/api/players")
def api_reset_all() -> dict[str, Any]:
    def mutate(s: dict[str, Any]) -> None:
        s["players"] = {}
        s["leaderboard"] = []

    update_state(mutate)
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
