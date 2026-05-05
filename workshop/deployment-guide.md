---
title: Deployment Guide
description: Deploy the game server and A2A expert to Azure Container Apps.
---

# Deployment Guide — Azure Container Apps

<Badge type="danger" text="Facilitators only" />

Deploy both services to Azure Container Apps for the workshop.
All commands use the Azure CLI (`az`). Install it from [docs.microsoft.com/cli/azure](https://docs.microsoft.com/cli/azure/) if needed.

---

## Prerequisites

- Azure CLI installed and logged in (`az login`)
- Docker installed and running
- The resource group `raleigh-workshop` exists (created in the Foundry setup guide)
- Azure Container Registry (ACR) created in that resource group (see step 1 below)

---

## 1 — Create Azure Container Registry

```bash
RESOURCE_GROUP=raleigh-workshop
LOCATION=eastus2
ACR_NAME=raleighworkshop   # must be globally unique; adjust if taken

az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $ACR_NAME \
  --sku Basic \
  --admin-enabled true
```

Get the login server:
```bash
ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --query loginServer -o tsv)
echo "ACR: $ACR_LOGIN_SERVER"
```

Log in Docker to the registry:
```bash
az acr login --name $ACR_NAME
```

---

## 2 — Build and push the game server image

From the repo root:
```bash
cd lost-in-raleigh

docker build -t $ACR_LOGIN_SERVER/lost-in-raleigh:latest .
docker push $ACR_LOGIN_SERVER/lost-in-raleigh:latest

cd ..
```

---

## 3 — Build and push the A2A expert image

```bash
cd a2a-expert

docker build -t $ACR_LOGIN_SERVER/a2a-expert:latest .
docker push $ACR_LOGIN_SERVER/a2a-expert:latest

cd ..
```

---

## 4 — Create the Container Apps environment

```bash
ENVIRONMENT=raleigh-env

az containerapp env create \
  --name $ENVIRONMENT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION
```

---

## 5 — Deploy the game server

```bash
# Replace <acr-password> with the ACR admin password from:
#   az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv

ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv)

az containerapp create \
  --name lost-in-raleigh \
  --resource-group $RESOURCE_GROUP \
  --environment $ENVIRONMENT \
  --image $ACR_LOGIN_SERVER/lost-in-raleigh:latest \
  --registry-server $ACR_LOGIN_SERVER \
  --registry-username $ACR_NAME \
  --registry-password $ACR_PASSWORD \
  --target-port 8000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 3 \
  --cpu 0.5 \
  --memory 1Gi
```

Get the public URL:
```bash
GAME_URL=$(az containerapp show \
  --name lost-in-raleigh \
  --resource-group $RESOURCE_GROUP \
  --query properties.configuration.ingress.fqdn -o tsv)
echo "Game server: https://$GAME_URL"
echo "MCP endpoint: https://$GAME_URL/mcp"
echo "Admin dashboard: https://$GAME_URL/admin"
```

**Verify**:
```bash
curl https://$GAME_URL/mcp
# Should return a 200 with the MCP capability manifest.
```

---

## 6 — Deploy the A2A expert

```bash
az containerapp create \
  --name a2a-expert \
  --resource-group $RESOURCE_GROUP \
  --environment $ENVIRONMENT \
  --image $ACR_LOGIN_SERVER/a2a-expert:latest \
  --registry-server $ACR_LOGIN_SERVER \
  --registry-username $ACR_NAME \
  --registry-password $ACR_PASSWORD \
  --target-port 8001 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 3 \
  --cpu 0.25 \
  --memory 0.5Gi \
  --env-vars \
    AZURE_OPENAI_ENDPOINT=https://your-hub.openai.azure.com/ \
    AZURE_OPENAI_API_KEY=<your-key> \
    AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini
```

Get the A2A URL:
```bash
A2A_URL=$(az containerapp show \
  --name a2a-expert \
  --resource-group $RESOURCE_GROUP \
  --query properties.configuration.ingress.fqdn -o tsv)
echo "A2A expert: https://$A2A_URL/a2a"
```

**Verify**:
```bash
curl -X POST https://$A2A_URL/a2a \
  -H "Content-Type: application/json" \
  -d '{"message": "Best way to get to Glenwood South from Moore Square?"}'
# Should return JSON with an "advice" field.
```

---

## 7 — Update city_config.yaml with live URLs

Edit `lost-in-raleigh/city_config.yaml` and replace the placeholder URLs in every quest:

```yaml
# Before:
a2a_expert_url: "https://<a2a-expert-host>/a2a"
document_bundle_url: "https://<blob-storage-host>/bundles/raleigh/glenwood_getaway.zip"

# After:
a2a_expert_url: "https://a2a-expert.<env-fqdn>/a2a"
document_bundle_url: "https://<storage-account>.blob.core.windows.net/bundles/raleigh/glenwood_getaway.zip"
```

Then rebuild and redeploy the game server image (repeat step 2 and run `az containerapp update`):

```bash
docker build -t $ACR_LOGIN_SERVER/lost-in-raleigh:latest lost-in-raleigh/
docker push $ACR_LOGIN_SERVER/lost-in-raleigh:latest

az containerapp update \
  --name lost-in-raleigh \
  --resource-group $RESOURCE_GROUP \
  --image $ACR_LOGIN_SERVER/lost-in-raleigh:latest
```

---

## 8 — Upload document bundles to Azure Blob Storage

```bash
STORAGE_ACCOUNT=raleighbundles   # must be globally unique

az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS

az storage container create \
  --account-name $STORAGE_ACCOUNT \
  --name bundles \
  --public-access blob

# Build bundles locally first:
python lost-in-raleigh/build_bundles.py

# Upload each ZIP:
for f in bundles/raleigh/*.zip; do
  az storage blob upload \
    --account-name $STORAGE_ACCOUNT \
    --container-name bundles \
    --file "$f" \
    --name "raleigh/$(basename $f)"
done

echo "Bundle base URL: https://$STORAGE_ACCOUNT.blob.core.windows.net/bundles/raleigh/"
```

---

## 9 — Share workshop URLs with attendees

Once everything is deployed, provide attendees with:

| Value | How to get it |
|-------|--------------|
| `MCP_SERVER_URL` | `https://$GAME_URL/mcp` |
| Admin dashboard | `https://$GAME_URL/admin` |

Paste these into the workshop Slack/Teams channel before the session starts.

---

## Tear down (after the workshop)

```bash
az group delete --name $RESOURCE_GROUP --yes --no-wait
```

This removes all resources — Container Apps, ACR, storage account, and networking.
