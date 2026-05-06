---
title: Event Resources
description: URLs and access information for all shared services running during the Lost in Raleigh workshop.
---

# Event Resources

This page lists all the URLs and shared endpoints you will need during the workshop. Your facilitator will fill these in before the event, so bookmark this page.

::: info These values go in your `.env` file
Copy each URL into the matching variable in `create-agent/.env`. See [Developer Environment Setup](dev-setup) for the full setup guide.
:::

---

## Game Server (MCP)

The **Lost in Raleigh** game server manages player registration, quest state, and scoring.

| | URL |
|---|---|
| **MCP endpoint** (for your `.env`) | _provided by facilitator_ |
| **Leaderboard / Player dashboard** | _provided by facilitator_ |
| **Admin dashboard** (facilitators only) | _provided by facilitator_ |

```ini [.env]
MCP_SERVER_URL=https://lost-in-raleigh.<your-event>.azurecontainerapps.io/mcp
```

::: tip Deriving the admin URL
The admin dashboard is always available at the same base URL with `/admin` instead of `/mcp`:
- MCP endpoint: `https://lost-in-raleigh.xxx.azurecontainerapps.io/mcp`
- Admin dashboard: `https://lost-in-raleigh.xxx.azurecontainerapps.io/admin`
:::

---

## A2A Transport Expert

The transport expert is a remote agent you consult in **Step 5** to get route advice. It knows Raleigh's bus routes, bike lanes, and rideshare options.

| | URL |
|---|---|
| **A2A base URL** (for your `.env`) | _provided by facilitator_ |
| **AgentCard** | `<A2A_SERVER_URL>/agent.json` |

```ini [.env]
A2A_SERVER_URL=https://a2a-expert.<your-event>.azurecontainerapps.io
```

::: details Verify it's running
Open `<A2A_SERVER_URL>/agent.json` in your browser. You should see a JSON object with `"name": "Raleigh Transport Expert"`.
:::

---

## City Guide Agent

The city guide is a remote agent you consult in **Step 7** to learn about Raleigh neighbourhoods and retrieve the quest reference code.

| | URL |
|---|---|
| **City Guide base URL** (for your `.env`) | _provided by facilitator_ |
| **AgentCard** | `<CITY_GUIDE_URL>/agent.json` |

```ini [.env]
CITY_GUIDE_URL=https://a2a-expert.<your-event>.azurecontainerapps.io/city-guide
```

::: tip Same server as the transport expert
`CITY_GUIDE_URL` is the city guide path on the same container as `A2A_SERVER_URL`. It will always be `<A2A_SERVER_URL>/city-guide`.
:::

---

## Your Azure OpenAI Deployment

You create this yourself during the [Azure AI Foundry Setup](azure-foundry-setup). Find your values at [ai.azure.com](https://ai.azure.com) → your project → **Settings → Keys and endpoints**.

| Variable | What it looks like |
|---|---|
| `AZURE_OPENAI_ENDPOINT` | `https://your-hub-name.openai.azure.com/` |
| `AZURE_OPENAI_API_KEY` | 32-character hex string |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | `gpt-4o-mini` (or whatever you named it) |

---

## Complete `.env` Example

Once you have all the values from your facilitator, your `.env` file should look like this:

```ini [create-agent/.env]
# Azure OpenAI (your own - from AI Foundry)
AZURE_OPENAI_ENDPOINT=https://your-hub.openai.azure.com/
AZURE_OPENAI_API_KEY=your-key-here
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini

# Shared game server (from your facilitator)
MCP_SERVER_URL=https://lost-in-raleigh.<your-event>.azurecontainerapps.io/mcp

# Shared A2A agents (from your facilitator)
A2A_SERVER_URL=https://a2a-expert.<your-event>.azurecontainerapps.io
CITY_GUIDE_URL=https://a2a-expert.<your-event>.azurecontainerapps.io/city-guide
```

::: danger Never commit this file
`.env` is in `.gitignore`. Keep it local. Never paste your API key into a chat, email, or any file that gets committed.
:::

---

## Useful Azure Portal Links

| Resource | Link |
|---|---|
| Azure Portal | [portal.azure.com](https://portal.azure.com) |
| Azure AI Foundry | [ai.azure.com](https://ai.azure.com) |
| Switch directory (tenant) | [portal.azure.com/#settings/directory](https://portal.azure.com/#settings/directory) |
| Subscription filter | [portal.azure.com/#view/Microsoft_Azure_Billing/SubscriptionsBladeV2](https://portal.azure.com/#view/Microsoft_Azure_Billing/SubscriptionsBladeV2) |
