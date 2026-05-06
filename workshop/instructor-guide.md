---
title: Instructor Guide
description: End-to-end setup guide for workshop instructors, covering dependencies, deployment, and day-of operations.
---

# Instructor Guide

<Badge type="danger" text="Facilitators only" />

This guide walks you through everything needed to run a Lost in Workshop event from scratch, from provisioning Azure infrastructure to handing attendees their subscription codes.

::: info Page not linked in nav
Share this URL directly with co-facilitators. It does not appear in the site navigation.
:::

::: tip One-command deployment
All steps below are automated in `scripts/deploy.ps1`. Set up a config file once and then run the script with no arguments:

```powershell
# First time only - copy the example and fill in your values
Copy-Item scripts\deploy.config.json.example scripts\deploy.config.json
notepad scripts\deploy.config.json

# Deploy everything
.\scripts\deploy.ps1
```

The config file (`scripts/deploy.config.json`) is gitignored, so your API key will never be committed. The manual steps below explain what each phase does if you need to run them individually or troubleshoot.
:::

---

## Overview of what you are deploying

| Component | What it is | Where it runs |
|---|---|---|
| **Game server** (`lost-in-raleigh`) | FastMCP + FastAPI - manages players, quests, leaderboard | Azure Container App |
| **A2A expert** (`a2a-expert`) | GPT-4o-mini powered transport advisor | Azure Container App |
| **Document bundles** | ZIP files of city-guide chapters (one per quest) | Azure Blob Storage |
| **Attendee agent** (`sample-agent`) | Python agent skeleton attendees build on | Attendee laptop |

---

## Prerequisites

- Azure CLI installed and logged in (`az login`)  
- Docker installed and running  
- Python 3.11+  
- A resource group already created (the Foundry setup guide creates `raleigh-workshop`)  
- Azure OpenAI deployment of `gpt-4o-mini` in that subscription

---

## Step 1 - Build the document bundles

The document bundles are ZIP files of city-guide chapters. Each bundle contains one chapter with a hidden secret code that attendees must find.

From the repo root:

```bash
cd lost-in-raleigh
python build_bundles.py
```

::: tip Expected output
```
bundles/raleigh/glenwood_getaway.zip
bundles/raleigh/museum_mile.zip
bundles/raleigh/warehouse_run.zip
```
:::

The secret codes embedded in the bundles are:

| Quest | Secret code |
|---|---|
| The Glenwood Getaway | `GLENWOOD42` |
| The Museum Mile | `MUSEUMRUN88` |
| The Warehouse Run | `TOBACCO55` |

::: warning Keep these private
Do not share secret codes with attendees before or during the workshop. Codes are embedded in the prose of one chapter per bundle, and finding them is part of the exercise.
:::

---

## Step 2 - Upload bundles to Azure Blob Storage

```bash
RESOURCE_GROUP=raleigh-workshop
STORAGE_ACCOUNT=raleighworkshop   # must be globally unique; adjust if taken
LOCATION=eastus2

# Create storage account
az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS

# Create public-read container
az storage container create \
  --name bundles \
  --account-name $STORAGE_ACCOUNT \
  --public-access blob

# Upload all three bundles
az storage blob upload-batch \
  --account-name $STORAGE_ACCOUNT \
  --destination bundles \
  --source bundles/raleigh \
  --pattern "*.zip"
```

Get the base URL:
```bash
echo "https://$STORAGE_ACCOUNT.blob.core.windows.net/bundles/"
```

::: tip Verify each bundle is reachable
```bash
curl -I "https://$STORAGE_ACCOUNT.blob.core.windows.net/bundles/glenwood_getaway.zip"
# Expected: HTTP/2 200
```
:::

---

## Step 3 - Deploy to Azure Container Apps

See the full [Deployment Guide](deployment-guide) for detailed `az containerapp` commands.

Quick summary:

```bash
# 1. Create ACR and Container Apps environment
az acr create --name $ACR_NAME --resource-group $RESOURCE_GROUP --sku Basic --admin-enabled true
az containerapp env create --name raleigh-env --resource-group $RESOURCE_GROUP --location $LOCATION

# 2. Build and push both images
docker build -t $ACR_LOGIN_SERVER/lost-in-raleigh:latest lost-in-raleigh/
docker build -t $ACR_LOGIN_SERVER/a2a-expert:latest a2a-expert/
docker push $ACR_LOGIN_SERVER/lost-in-raleigh:latest
docker push $ACR_LOGIN_SERVER/a2a-expert:latest

# 3. Deploy both container apps (see deployment-guide for full flags)
```

After deploying, note these two URLs:
- `GAME_URL` - the game server FQDN (e.g. `lost-in-raleigh.<env>.eastus2.azurecontainerapps.io`)
- `A2A_URL` - the A2A expert FQDN

---

## Step 4 - Update city_config.yaml with live URLs

Edit `lost-in-raleigh/city_config.yaml` and replace every placeholder with your deployed URLs:

```yaml
# Replace:
a2a_expert_url: "https://<a2a-expert-host>/a2a"
document_bundle_url: "https://<blob-storage-host>/bundles/raleigh/glenwood_getaway.zip"

# With (example):
a2a_expert_url: "https://a2a-expert.raleigh-env.eastus2.azurecontainerapps.io/a2a"
document_bundle_url: "https://raleighworkshop.blob.core.windows.net/bundles/glenwood_getaway.zip"
```

Then rebuild and redeploy the game server:

```bash
docker build -t $ACR_LOGIN_SERVER/lost-in-raleigh:latest lost-in-raleigh/
docker push $ACR_LOGIN_SERVER/lost-in-raleigh:latest
az containerapp update \
  --name lost-in-raleigh \
  --resource-group $RESOURCE_GROUP \
  --image $ACR_LOGIN_SERVER/lost-in-raleigh:latest
```

---

## Step 5 - Set attendee environment variables

Attendees need two values in their `.env` file:

| Variable | Value | Where to find it |
|---|---|---|
| `AZURE_OPENAI_ENDPOINT` | their personal Foundry hub endpoint | Azure AI Foundry → project → settings |
| `AZURE_OPENAI_API_KEY` | their personal API key | same location |
| `MCP_SERVER_URL` | `https://<GAME_URL>/mcp` | your deployed game server |

Post `MCP_SERVER_URL` to the workshop Slack/Teams channel and on the room screen before attendees arrive. The [Azure Foundry Setup guide](azure-foundry-setup) directs them to fill in the first two values themselves.

---

## Step 6 - Install attendee Python dependencies (local check)

Attendees run this themselves during [Azure Foundry Setup](azure-foundry-setup) step 8. But if you want to pre-verify the environment works:

```bash
cd sample-agent
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

`requirements.txt` installs:
- `agent-framework`: the scaffolding used in workshop steps
- `openai`: Azure OpenAI client
- `python-dotenv`: `.env` file loading
- `httpx` + `requests`: HTTP clients for MCP and A2A calls

::: tip Smoke test
```bash
python steps/step1_foundry_test.py
# Expected: "Connected to Azure OpenAI!"
```
:::

---

## Step 7 - Pre-event checks (day of)

See the [Pre-Event Checklist](pre-event-checklist) for the full day-of checklist. Key items:

- [ ] Game server returns 200 at `https://<GAME_URL>/mcp`
- [ ] A2A expert returns 200 at `https://<A2A_URL>/a2a`
- [ ] Bundles are publicly accessible in Blob Storage
- [ ] Admin dashboard (`https://<GAME_URL>/admin`) shows 0 players
- [ ] `MCP_SERVER_URL` posted to attendee channel

---

## Teardown after the workshop

```bash
# Delete the entire resource group (removes all resources)
az group delete --name $RESOURCE_GROUP --yes --no-wait
```

::: warning This is irreversible
All container apps, the ACR, and the storage account will be permanently deleted.
Only run this after the event is fully complete.
:::
