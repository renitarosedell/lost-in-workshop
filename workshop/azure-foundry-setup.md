---
title: Azure AI Foundry Setup
description: Create your Azure OpenAI deployment in Azure AI Foundry. Complete this as part of the Developer Environment Setup.
---

# Azure AI Foundry Setup

<Badge type="warning" text="~15 minutes" /> <Badge type="info" text="Complete before Step 1" />

::: tip Before you start
Make sure you have an Azure subscription. If you don't have one yet, see [Get Azure Subscription](get-azure) first.
:::

This guide walks you through creating an Azure OpenAI deployment in Azure AI Foundry, the service your agent uses to call GPT-4o-mini.


---

## 1. Redeem your Azure subscription

1. Open your browser and go to the URL printed on your subscription card
   (something like `https://azure.microsoft.com/en-us/free/...`).
2. Sign in with a **personal Microsoft account** (Outlook.com, Hotmail.com, Live.com).
   If you do not have one, click "Create one" and follow the prompts, it takes two minutes.
3. Enter the promotional code from your card when prompted.
4. Complete the sign-up form. You do not need to enter a credit card for a free
   trial subscription, so click "I agree" when asked about the free offer terms.

::: tip Expected result
You are redirected to the Azure portal (`portal.azure.com`) and you can see "Microsoft Azure"
in the top-left corner.
:::

::: details Troubleshooting
- **Code already redeemed**: ask your facilitator for a fresh one.
- **Credit card prompt you can't dismiss**: you may be signed in to an existing paid account
  - sign out and sign back in with a fresh Microsoft account.
:::

::: info Already have Azure?
If you have an existing Azure account with an active subscription, skip ahead to step 2.
:::

---

## 2. Sign in to Azure AI Foundry

1. Open a new tab and go to **[ai.azure.com](https://ai.azure.com)**.
2. Click "Sign in" and use the same Microsoft account you used in step 1.

::: tip Expected result
You see the Azure AI Foundry home page with a "Create project" button and a left-hand
navigation panel.
:::

::: details Troubleshooting
If you land on a "You don't have access" page, confirm you are signed in with the same
account that redeemed the subscription code.
:::

---

## 3. Create a Resource Group

1. In the Azure portal (`portal.azure.com`), type "Resource groups" in the top search bar
   and click the result.
2. Click **+ Create**.
3. Fill in the form:
   - **Subscription**: choose the subscription you just activated.
   - **Resource group name**: `raleigh-workshop`
   - **Region**: `East US 2`
4. Click **Review + Create**, then **Create**.

::: tip Expected result
After a few seconds you see "Your deployment is complete." The resource group
`raleigh-workshop` now exists.
:::

---

## 4. Create a Foundry Hub

1. Return to **[ai.azure.com](https://ai.azure.com)**.
2. Click **+ New hub** (or "Create hub" if visible on the home page).
3. Fill in the form:
   - **Hub name**: `raleigh-hub` (or any name you like)
   - **Subscription**: the subscription from step 1
   - **Resource group**: `raleigh-workshop` (select the one you just created)
   - **Location**: `East US 2`
4. Leave all other fields at their defaults.
5. Click **Next**, then **Create**.

::: tip Expected result
The hub is created in about 60–90 seconds. You see it listed in the Foundry home page
under "Hubs."
:::

::: details Troubleshooting
If you get a **quota** error, try a different region, West US 2 or East US are good alternatives.
:::

---

## 5. Create a Project

1. Inside your new hub, click **+ New project**.
2. Fill in:
   - **Project name**: `raleigh-workshop`
   - **Hub**: leave as your new hub
3. Click **Create**.

::: tip Expected result
The project is created in under 30 seconds. You land on the project overview page.
:::

---

## 6. Deploy the gpt-4o-mini model

1. In the left navigation of your project, click **Models + endpoints**.
2. Click **+ Deploy model**, then **Deploy base model**.
3. Search for `gpt-4o-mini` and select it.
4. Click **Confirm**.
5. In the deployment configuration:
   - **Deployment name**: `gpt-4o-mini` (keep the default, this becomes your
     `AZURE_OPENAI_DEPLOYMENT_NAME`)
   - **Tokens per minute**: leave at the default (usually 10K TPM for free tier)
6. Click **Deploy**.

::: tip Expected result
After 30–60 seconds the deployment status shows "Succeeded."
:::

::: details Troubleshooting
If you see **"Quota exceeded"**, try `East US` instead of `East US 2`.
:::

---

## 7. Copy your endpoint, key, and deployment name

1. Click on your `gpt-4o-mini` deployment to open its details.
2. Find the **Target URI** (endpoint). It looks like:
   `https://your-hub.openai.azure.com/`, copy it.
3. Click **Keys and Endpoints** (or look for \"API key\" on the same page).
   Copy **Key 1**.
4. Note your deployment name: `gpt-4o-mini` (or whatever you named it in step 6).

::: info Where to find these values later
The endpoint and key are also visible on the project overview page at
[ai.azure.com](https://ai.azure.com) under **Settings → Keys and endpoints**.
:::

---

## 8. Create your .env file

1. In your terminal, change directory to `create-agent/`:

::: code-group
```bash [macOS / Linux]
cd create-agent
cp .env.example .env
```
```powershell [Windows]
cd create-agent
copy .env.example .env
```
:::

2. Open `.env` in a text editor and fill in your three values:

```ini [.env]
AZURE_OPENAI_ENDPOINT=https://your-hub.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini
MCP_SERVER_URL=https://...   # provided by your facilitator
```

3. Save the file.

::: danger Never commit your .env file
`.env` is already listed in `.gitignore`. Do not remove it from there or paste your key
into any other file that gets committed.
:::

---

## 9. Verify your connection

1. Install the requirements (if you haven't already):

```bash
pip install -r requirements.txt
```

2. Run the connectivity test:

```bash
python steps/step1_foundry_test.py
```

::: tip Expected output
```
Connected to Azure OpenAI!
Model response: Hello! I am ready to help you navigate Raleigh.
```
:::

::: details Troubleshooting
- **`AuthenticationError`**: check that `AZURE_OPENAI_API_KEY` is correct and has no trailing spaces.
- **`ResourceNotFoundError`**: check that `AZURE_OPENAI_ENDPOINT` ends with a `/` and matches
  the endpoint shown in Foundry.
- **`DeploymentNotFound`**: check that `AZURE_OPENAI_DEPLOYMENT_NAME` matches the name you gave
  the deployment in step 6 exactly, and it is case-sensitive.
:::

---

You are ready. Move on to the [Workshop Guide](workshop), Step 2.
