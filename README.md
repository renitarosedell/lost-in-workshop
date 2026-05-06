# Lost in Raleigh — AI Agent Workshop 🚀

[View the published workshop](https://roelantd.github.io/lost-in-workshop/)

## Workshop Overview

In this hands-on 90-minute session you will build a Python AI agent that navigates a quest through Raleigh, NC. Starting from a simple Azure OpenAI connection, you'll progressively add capabilities until your agent can autonomously complete a multi-leg city quest.

By the end of the workshop you will have built an agent that:

- Connects to **Azure AI Foundry** and holds a conversation
- Discovers and calls live tools via the **Model Context Protocol (MCP)**
- Persists context across turns using **memory**
- Delegates to a specialist via the **Agent-to-Agent (A2A) protocol**
- Coordinates multiple expert agents through **multi-agent orchestration**

## Agenda

| Step | Topic | Time |
| --- | --- | --- |
| Step 1 | Connect to Azure OpenAI | ~10 min |
| Step 2 | Hello Raleigh | ~10 min |
| Step 3 | MCP Game Server | ~15 min |
| Step 4 | Memory | ~10 min |
| Step 5 | A2A Transport Expert | ~15 min |
| Step 6 | Multi-turn Conversations | ~10 min |
| Step 7 | Orchestration | ~20 min |
| Step 8 | Complete the Quest | ~5 min |

## What You'll Need

- A browser and access to the [Azure Portal](https://portal.azure.com/)
- An [Azure subscription](https://roelantd.github.io/lost-in-workshop/workshop/get-azure) — provided at the event or sign up for a free trial
- A [development environment](https://roelantd.github.io/lost-in-workshop/workshop/dev-setup) with Python 3.11+ installed
- Familiarity with Python basics (no deep AI background required)

## What's in this repo

| Folder | Purpose |
| --- | --- |
| [workshop/](workshop/) | Step-by-step workshop guide and facilitator notes. |
| [sample-agent/](sample-agent/) | Reference Python agent (Microsoft Agent Framework) used throughout the workshop. |
| [lost-in-raleigh/](lost-in-raleigh/) | MCP game server + FastAPI admin UI that powers the quest. |
| [a2a-expert/](a2a-expert/) | A2A transport expert agent consulted in Step 5. |
| [city-guide/](city-guide/) | 20-chapter Raleigh city guide used as source material for the quest. |
| [bundles/](bundles/) | Pre-built document bundles served to agents during the quest. |
| [instructions/](instructions/) | MCP server prompt that defines the game behaviour. |

## Workshop Goal

By the end of this session you'll know how to:

1. Create and configure an agent with Azure AI Foundry
2. Connect it to external tools via MCP
3. Persist state across conversation turns
4. Delegate tasks to specialist agents using A2A
5. Orchestrate multiple agents to solve a complex, multi-leg problem

You'll walk away with a working agent that can autonomously navigate Raleigh and complete the quest.
