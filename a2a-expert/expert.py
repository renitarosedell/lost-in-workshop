"""A2A Expert: two A2A agents on one server — transport adviser + city guide."""
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
from starlette.applications import Starlette
from starlette.routing import Mount

# ---------------------------------------------------------------------------
# System prompt — Raleigh transport knowledge
# ---------------------------------------------------------------------------

TRANSPORT_SYSTEM_PROMPT = """\
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
# System prompt — Raleigh city guide with embedded quest reference codes
# ---------------------------------------------------------------------------

CITY_GUIDE_SYSTEM_PROMPT = """\
You are the Raleigh City Guide for the 'Lost in Raleigh' workshop quest.
You have deep knowledge of Raleigh's neighbourhoods, history, and culture.

NEIGHBOURHOOD KNOWLEDGE

Cameron Village: One of the first planned shopping centres in the American South
(opened 1949), Cameron Village sits west of downtown near the Five Points area.
It has evolved from a car-centric mall into a walkable open-air district with
independent shops, restaurants, and a genuine neighbourhood feel.
Archivist reference code for quest players: GLENWOOD42

CAM Raleigh / Warehouse District: The Contemporary Art Museum of Raleigh anchors
the Warehouse District on South Blount Street, occupying a transformed 1950s
warehouse. The broader district is Raleigh's revitalised arts and brewing corridor.
Archivist reference code for quest players: MUSEUMRUN88

Boylan Heights: One of Raleigh's oldest residential neighbourhoods — a hillside
community of craftsman bungalows and Victorian cottages south of the Warehouse
District, overlooking the downtown skyline from Boylan Avenue Bridge.
Archivist reference code for quest players: TOBACCO55

BEHAVIOUR
- When a quest player asks about a neighbourhood that is their current stop,
  share the archivist reference code clearly — they need it to progress.
- When discussing any location, be informative and engaging about its history.
- Keep answers to two or three short paragraphs.
"""

# ---------------------------------------------------------------------------
# Shared OpenAI client
# ---------------------------------------------------------------------------

_BASE_URL = os.environ.get("A2A_BASE_URL", "http://localhost:8001")

_client = OpenAIChatClient(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    model=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
)

# ---------------------------------------------------------------------------
# Agent 1: Transport Expert  (served at /)
# ---------------------------------------------------------------------------

_transport_skill = AgentSkill(
    id="raleigh_transport_advice",
    name="Raleigh Transport Advice",
    description="Gives transport advice for navigating Raleigh during the Lost in Raleigh quest.",
    tags=["transport", "raleigh", "navigation"],
    examples=["What is the fastest way to get to Glenwood South?"],
)

_transport_card = AgentCard(
    name="Raleigh Transport Expert",
    description="A local Raleigh, NC transport expert for the Lost in Raleigh workshop quest.",
    url=_BASE_URL,
    version="1.0.0",
    defaultInputModes=["text"],
    defaultOutputModes=["text"],
    capabilities=AgentCapabilities(streaming=False),
    skills=[_transport_skill],
)

_transport_agent = Agent(
    client=_client,
    name="Raleigh Transport Expert",
    instructions=TRANSPORT_SYSTEM_PROMPT,
)

_transport_server = A2AStarletteApplication(
    agent_card=_transport_card,
    http_handler=DefaultRequestHandler(
        agent_executor=A2AExecutor(_transport_agent),
        task_store=InMemoryTaskStore(),
    ),
).build()

# ---------------------------------------------------------------------------
# Agent 2: City Guide  (served at /city-guide)
# ---------------------------------------------------------------------------

_city_guide_skill = AgentSkill(
    id="raleigh_city_guide",
    name="Raleigh City Guide",
    description="Provides neighbourhood history and reveals quest reference codes for the Lost in Raleigh game.",
    tags=["raleigh", "history", "neighbourhood", "quest"],
    examples=["Tell me about Cameron Village and share the reference code."],
)

_city_guide_card = AgentCard(
    name="Raleigh City Guide",
    description="A knowledgeable guide to Raleigh's neighbourhoods for the Lost in Raleigh workshop quest.",
    url=f"{_BASE_URL}/city-guide",
    version="1.0.0",
    defaultInputModes=["text"],
    defaultOutputModes=["text"],
    capabilities=AgentCapabilities(streaming=False),
    skills=[_city_guide_skill],
)

_city_guide_agent = Agent(
    client=_client,
    name="Raleigh City Guide",
    instructions=CITY_GUIDE_SYSTEM_PROMPT,
)

_city_guide_server = A2AStarletteApplication(
    agent_card=_city_guide_card,
    http_handler=DefaultRequestHandler(
        agent_executor=A2AExecutor(_city_guide_agent),
        task_store=InMemoryTaskStore(),
    ),
).build()

# ---------------------------------------------------------------------------
# Combined ASGI app — city guide at /city-guide, transport at /
# ---------------------------------------------------------------------------

server = Starlette(routes=[
    Mount("/city-guide", app=_city_guide_server),
    Mount("/", app=_transport_server),
])

if __name__ == "__main__":
    uvicorn.run(server, host="0.0.0.0", port=int(os.environ.get("PORT", 8001)))
