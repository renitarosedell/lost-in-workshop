# Quickstart: Lost in [City] Workshop — Developer Setup

**For**: Contributors building or maintaining workshop materials.
**Not for**: Workshop attendees (see `workshop/workshop.md` instead).

---

## Prerequisites

- Python 3.11 or higher
- Git
- Docker (for server components)
- Azure CLI (`az`) with an active subscription (for deployment tasks)

---

## 1. Clone and Branch

```bash
git clone https://github.com/<org>/lost-in-workshop-v2.git
cd lost-in-workshop-v2
git checkout lost-in-raleigh   # attendee branch (sample-agent + city-guide + workshop docs)
# OR
git checkout admin             # organiser branch (server + A2A expert)
```

---

## 2. Attendee Materials (lost-in-raleigh branch)

### Set up the sample agent

```bash
cd sample-agent
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Azure OpenAI values
```

### Test Azure connectivity (Step 1 fallback)

```bash
python steps/step1_foundry_test.py
# Expected: a short model response printed to stdout
```

### Run through workshop steps

```bash
python steps/step2_hello_world.py   # Hello World agent
python steps/step3_mcp_connect.py   # MCP + register_player (needs running server)
python steps/step4_memory.py        # Add player memory
python steps/step5_quest.py         # Full autonomous quest loop
```

The full reference agent (all steps combined):

```bash
python agent.py
```

---

## 3. Game Server (admin branch)

### Run locally

```bash
git checkout admin
cd lost-in-raleigh
python -m venv .venv
source .venv/bin/activate      # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

# Ensure city_config.yaml is present (copy the template if needed)
python server.py
# Server starts on http://localhost:8000
# MCP endpoint: http://localhost:8000/mcp
# Admin dashboard: http://localhost:8000/
```

### Run with Docker

```bash
cd lost-in-raleigh
docker build -t lost-in-raleigh .
docker run -p 8000:8000 -v $(pwd)/city_config.yaml:/app/city_config.yaml lost-in-raleigh
```

### Run the A2A expert

```bash
cd a2a-expert
pip install -r requirements.txt
python expert.py
# A2A endpoint: http://localhost:8001/a2a
```

---

## 4. Environment Variables

### Sample agent (`.env`)

```
AZURE_OPENAI_ENDPOINT=https://<your-hub>.openai.azure.com/
AZURE_OPENAI_API_KEY=<your-key>
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini
MCP_SERVER_URL=http://localhost:8000/mcp
```

`MCP_SERVER_URL` is pre-filled with the live Raleigh server URL before each event (T6.3).

### Game server

No `.env` required. The server reads `city_config.yaml` from its working directory.
Set `HOST` and `PORT` environment variables to override defaults (default: `0.0.0.0:8000`).

---

## 5. Adding a New City

1. Create `city-guide/<city>/` with ≥20 Markdown chapters.
2. Copy `lost-in-raleigh/city_config.yaml` → `lost-in-<city>/city_config.yaml` and edit
   all city-specific fields (city name, final destination, quest definitions, transport
   options, secret codes).
3. Assemble three document bundle ZIPs from `city-guide/<city>/`, embedding each quest's
   secret code in natural prose in one document.
4. Host the ZIPs and update `document_bundle_url` values in `city_config.yaml`.
5. Deploy a new server instance (or update the existing one) with the new config.

No code changes are required. See Constitution §4 (City-Agnostic Architecture).

---

## 6. Verifying the Full Quest (smoke test)

Run the step 5 fallback against the live server to confirm end-to-end functionality:

```bash
cd sample-agent
python steps/step5_quest.py
```

Expected output:
1. Player registered; `player_id` printed.
2. Stop 1: A2A expert consulted; transport declared.
3. Stop 2: document bundle downloaded; secret code found and submitted.
4. Final leg: transport declared; score and completion message printed.
5. Score appears on the admin dashboard leaderboard within 5 seconds.

This is the T4.3 validation run. Fix any failures before event day.

---

## 7. Key Files Reference

| File | Purpose |
|------|---------|
| `spec/specification.md` | What the workshop is (requirements) |
| `spec/plan.md` | How it is built (technical design) |
| `spec/data-model.md` | Entity definitions and state schema |
| `spec/contracts/mcp-tools.md` | MCP tool contracts |
| `spec/contracts/a2a-protocol.md` | A2A expert HTTP contract |
| `spec/tasks.md` | Implementation task list |
| `lost-in-raleigh/city_config.yaml` | Raleigh city + quest configuration |
| `lost-in-raleigh/server.py` | FastMCP game server |
| `lost-in-raleigh/admin.py` | Admin dashboard |
| `sample-agent/steps/` | Progressive step fallback code |
| `workshop/workshop.md` | Attendee step-by-step guide |
| `workshop/azure-foundry-setup.md` | Azure setup guide (Step 1) |
| `workshop/bonus-exercises.md` | Bonus A–D instructions |
