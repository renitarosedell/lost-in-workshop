---
title: Event Resources
description: URLs and access information for all shared services running during the Lost in Raleigh workshop.
---

# Event Resources

All shared endpoints for this event are listed below. Copy the values into your `create-agent/.env` file.

::: info These values go in your `.env` file
See [Developer Environment Setup](dev-setup) if you haven't set up your `.env` yet.
:::

---

## Game Server (MCP)

The **Lost in Raleigh** game server manages player registration, quest state, and scoring.

| | URL |
|---|---|
| **MCP endpoint** | `https://lost-in-raleigh.redriver-3b1b0600.eastus2.azurecontainerapps.io/mcp` |
| **Leaderboard** | [lost-in-raleigh.redriver-3b1b0600.eastus2.azurecontainerapps.io](https://lost-in-raleigh.redriver-3b1b0600.eastus2.azurecontainerapps.io) |

```ini [.env]
MCP_SERVER_URL=https://lost-in-raleigh.redriver-3b1b0600.eastus2.azurecontainerapps.io/mcp
```

---

## A2A Transport Expert

The transport expert is a remote agent you consult in **Step 5** to get route advice. It knows Raleigh's bus routes, bike lanes, and rideshare options.

| | URL |
|---|---|
| **A2A base URL** | `https://a2a-expert.redriver-3b1b0600.eastus2.azurecontainerapps.io` |
| **AgentCard** | [/agent.json](https://a2a-expert.redriver-3b1b0600.eastus2.azurecontainerapps.io/agent.json) |

```ini [.env]
A2A_SERVER_URL=https://a2a-expert.redriver-3b1b0600.eastus2.azurecontainerapps.io
```

---

## City Guide Agent

The city guide is a remote agent you consult in **Step 7** to learn about Raleigh neighbourhoods and retrieve the quest reference code.

| | URL |
|---|---|
| **City Guide URL** | `https://a2a-expert.redriver-3b1b0600.eastus2.azurecontainerapps.io/city-guide` |
| **AgentCard** | [/city-guide/agent.json](https://a2a-expert.redriver-3b1b0600.eastus2.azurecontainerapps.io/city-guide/agent.json) |

```ini [.env]
CITY_GUIDE_URL=https://a2a-expert.redriver-3b1b0600.eastus2.azurecontainerapps.io/city-guide
```

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

```ini [create-agent/.env]
# Azure OpenAI (your own - from AI Foundry)
AZURE_OPENAI_ENDPOINT=https://your-hub.openai.azure.com/
AZURE_OPENAI_API_KEY=your-key-here
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini

# Shared game server
MCP_SERVER_URL=https://lost-in-raleigh.redriver-3b1b0600.eastus2.azurecontainerapps.io/mcp

# Shared A2A agents
A2A_SERVER_URL=https://a2a-expert.redriver-3b1b0600.eastus2.azurecontainerapps.io
CITY_GUIDE_URL=https://a2a-expert.redriver-3b1b0600.eastus2.azurecontainerapps.io/city-guide
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
