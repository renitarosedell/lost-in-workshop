"""A2A Expert: Raleigh transport adviser — exposed via the A2A protocol."""
from __future__ import annotations

import os

import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from agent_framework import Agent
from agent_framework.a2a import A2AExecutor
from agent_framework.openai import OpenAIChatClient

# ---------------------------------------------------------------------------
# System prompt — Raleigh transport knowledge
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are a local Raleigh, NC transport expert helping workshop attendees navigate
the city during the 'Lost in Raleigh' game.

RALEIGH TRANSPORT KNOWLEDGE

GoRaleigh (city bus):
- Route 11: Moore Square Transit Center → Glenwood South (every 30 min, ~18 min, $1.25)
- Route 16: City Market area → Bicentennial Plaza / Museum District (every 30 min, ~10 min)
- All routes originate from Moore Square Transit Center at Blount & Martin streets.

GoTriangle (regional bus):
- Route 100 Express: Downtown Raleigh ↔ Research Triangle Park / NC Biotech Center
  (~35 min, departs top of hour and half-hour, $2.25)

Capital Bikeshare stations (relevant docks):
- Moore Square: corner of Blount & Hargett (~20 bikes typical)
- Nash Square: Dawson & Morgan (~12 bikes)
- Glenwood South: 505 Glenwood Ave (~10 bikes)
- Warehouse District: South Blount & Davie (~8 bikes)

Rideshare (Uber/Lyft) typical wait times by area:
- Downtown core (Moore Square, Nash Square, City Market): 3–5 min
- Glenwood South: 4–8 min
- Museum District / Bicentennial Plaza: 4–7 min
- Warehouse District / CAM Raleigh: 5–9 min
- Boylan Heights: 6–12 min (residential, fewer drivers)

Walking distances between key quest locations:
- Moore Square → Glenwood South: ~1.1 miles, 15 min on foot
- City Market → NC Museum of Natural Sciences: ~0.5 miles, 8 min on foot
- Nash Square → Warehouse District: ~0.7 miles, 10 min on foot
- Warehouse District → Boylan Heights: ~0.5 miles, 8 min on foot (uphill)
- Downtown Raleigh → NC Biotech Center (RTP): ~13 miles — do not walk; use rideshare or GoTriangle

ADVICE STYLE
- Always recommend one primary option and one alternative.
- Include a rough time estimate for each.
- Be concise — two or three sentences per option is enough.
- If the attendee mentions time pressure, favour rideshare.
- If they mention cost, favour GoRaleigh bus or walking where feasible.
"""

# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Agent card — describes this agent to any A2A client
# ---------------------------------------------------------------------------

_transport_skill = AgentSkill(
    id="raleigh_transport_advice",
    name="Raleigh Transport Advice",
    description="Gives transport advice for navigating Raleigh during the Lost in Raleigh quest.",
    tags=["transport", "raleigh", "navigation"],
    examples=["What is the fastest way to get to Glenwood South?"],
)

_BASE_URL = os.environ.get("A2A_BASE_URL", "http://localhost:8001")

agent_card = AgentCard(
    name="Raleigh Transport Expert",
    description="A local Raleigh, NC transport expert for the Lost in Raleigh workshop quest.",
    url=_BASE_URL,
    version="1.0.0",
    defaultInputModes=["text"],
    defaultOutputModes=["text"],
    capabilities=AgentCapabilities(streaming=False),
    skills=[_transport_skill],
)

# ---------------------------------------------------------------------------
# Agent (backed by Azure OpenAI)
# ---------------------------------------------------------------------------

_client = OpenAIChatClient(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    model=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
)

_agent = Agent(
    client=_client,
    name="Raleigh Transport Expert",
    instructions=SYSTEM_PROMPT,
)

# ---------------------------------------------------------------------------
# A2A server
# ---------------------------------------------------------------------------

server = A2AStarletteApplication(
    agent_card=agent_card,
    http_handler=DefaultRequestHandler(
        agent_executor=A2AExecutor(_agent),
        task_store=InMemoryTaskStore(),
    ),
).build()

if __name__ == "__main__":
    uvicorn.run(server, host="0.0.0.0", port=int(os.environ.get("PORT", 8001)))
