"""A2A Expert: Raleigh transport adviser — FastAPI + Microsoft Agent Framework."""
from __future__ import annotations

import os

import httpx
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI(title="Raleigh A2A Transport Expert")

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

class A2ARequest(BaseModel):
    message: str


class A2AResponse(BaseModel):
    advice: str


# ---------------------------------------------------------------------------
# Azure OpenAI client (bare openai SDK — no agent framework needed here)
# ---------------------------------------------------------------------------

def _get_advice(question: str) -> str:
    """Call Azure OpenAI directly to answer a transport question."""
    import openai

    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(),
        "https://cognitiveservices.azure.com/.default",
    )
    client = openai.AzureOpenAI(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        azure_ad_token_provider=token_provider,
        api_version="2024-12-01-preview",
    )
    response = client.chat.completions.create(
        model=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
        max_tokens=300,
        temperature=0.3,
    )
    return response.choices[0].message.content or "No advice available."


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@app.post("/a2a", response_model=A2AResponse)
async def a2a(request: A2ARequest) -> JSONResponse:
    """Receive a natural-language transport question; return transport advice."""
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="message field must not be empty.")
    advice = _get_advice(request.message.strip())
    return JSONResponse({"advice": advice})


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
