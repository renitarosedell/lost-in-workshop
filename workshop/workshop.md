---
title: Workshop Guide
description: Build a Python AI agent that navigates a quest through Raleigh, NC using MCP, A2A, and multi-agent orchestration.
---

# Lost in Raleigh — Workshop Guide

::: info The workshop is split into individual step pages
Use the sidebar on the left to jump to any step, or start from [Step 1](step1).
:::

<Badge type="tip" text="~90 minutes" /> <Badge type="info" text="Beginner–Intermediate Python" />

## Workshop Steps

| Step | Topic | Time |
|------|-------|------|
| [Step 1](step1) | Connect to Azure OpenAI | ~10 min |
| [Step 2](step2) | Hello Raleigh | ~10 min |
| [Step 3](step3) | MCP Game Server | ~15 min |
| [Step 4](step4) | Memory | ~10 min |
| [Step 5](step5) | A2A Transport Expert | ~15 min |
| [Step 6](step6) | Multi-turn Conversations | ~10 min |
| [Step 7](step7) | Orchestration | ~20 min |
| [Step 8](step8) | Complete the Quest | ~5 min |

In this workshop you will build a Python AI agent that navigates a quest through Raleigh, NC.
Your agent will use **Microsoft Agent Framework**, **Azure OpenAI**, an **MCP game server**,
memory persistence, **A2A expert agents**, and multi-agent orchestration.

## Before you start

::: warning Prerequisites
- Claim your Azure subscription → [Get Azure](get-azure)
- Set up your dev environment → [Developer Environment Setup](dev-setup)
- Create your Azure OpenAI deployment → [Azure AI Foundry Setup](azure-foundry-setup)
- Get the shared event URLs → [Event Resources](event-resources)

All step files are in `sample-agent/steps/`. Run each from inside the `sample-agent/` folder:

```bash
python steps/step1_foundry_test.py
```
:::

[Start Step 1 →](step1)
