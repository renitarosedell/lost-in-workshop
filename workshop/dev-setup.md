---
title: Developer Environment Setup
description: Install Python, clone the repo, configure your .env file, and verify your setup before the workshop.
---

# Developer Environment Setup

<Badge type="warning" text="Complete before writing any code" />

This page walks you through everything you need on your laptop before the first coding step.

---

## What you need

| Requirement | Version | Check with |
|---|---|---|
| Python | 3.11 or later | `python --version` |
| Git | any recent | `git --version` |
| A code editor | VS Code recommended | - |
| A terminal | PowerShell, bash, zsh | - |

::: tip VS Code users
Install the **Python** extension and the **Pylance** language server for the best experience.
:::

---

## 1. Clone the repository

```bash
git clone https://github.com/RoelantD/lost-in-workshop.git
cd lost-in-workshop
```

---

## 2. Create a virtual environment

::: code-group
```bash [macOS / Linux]
cd sample-agent
python -m venv .venv
source .venv/bin/activate
```
```powershell [Windows]
cd sample-agent
python -m venv .venv
.venv\Scripts\Activate.ps1
```
:::

::: tip Your prompt changes
Once the virtual environment is active, your terminal prompt shows `(.venv)`. All packages you install go into this isolated environment, so they won't affect other Python projects on your machine.
:::

---

## 3. Log in to Azure

Before you can call Azure OpenAI from your terminal, the Azure CLI needs to know who you are.

Run this command and follow the on-screen instructions:

```bash
az login --use-device-code
```

You will see output like:

```
To sign in, use a web browser to open the page https://microsoft.com/devicelogin
and enter the code XXXXXXXX to authenticate.
```

1. Open that URL in your browser
2. Enter the code shown in the terminal
3. Sign in with the **same Microsoft account** that has your Azure subscription
4. Return to the terminal, it will confirm you are logged in

::: tip Expected output
```json
[
  {
    "name": "Your Subscription Name",
    "state": "Enabled",
    ...
  }
]
```
If you see a subscription listed, you're logged in.
:::

::: details Behind the scenes
`az login` stores a token in your local credential cache. Tools like `DefaultAzureCredential` (used by many Azure SDKs) pick this up automatically. For this workshop we use API keys in `.env` instead, but being logged in makes the portal and CLI work correctly.
:::

---

## 4. Install the dependencies

```bash
pip install -r requirements.txt
```

The `requirements.txt` includes:
- `agent-framework`: Microsoft Agent Framework
- `openai`: Azure OpenAI SDK
- `python-dotenv`: loads `.env` files
- `httpx`: async HTTP client (used for A2A calls)

::: details What is installed?
Run `pip list` after the install to see the full list. The key packages are `agent-framework`, `openai`, and `httpx`.
:::

---

## 5. Create your `.env` file

The agent reads credentials from a `.env` file that is **never committed to Git**.

::: code-group
```bash [macOS / Linux]
cp .env.example .env
```
```powershell [Windows]
copy .env.example .env
```
:::

Open `.env` in your editor. You will see placeholders for every variable:

```ini [.env]
# ──────────────────────────────────────────────────
#  Azure OpenAI - from your AI Foundry project
# ──────────────────────────────────────────────────

# The endpoint URL of your Azure OpenAI resource.
# Looks like: https://your-hub-name.openai.azure.com/
AZURE_OPENAI_ENDPOINT=

# Your API key - copy Key 1 from AI Foundry → Settings → Keys and endpoints.
AZURE_OPENAI_API_KEY=

# The deployment name you chose when you deployed gpt-4o-mini.
# Default: gpt-4o-mini
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini

# ──────────────────────────────────────────────────
#  Game server - provided by your facilitator
# ──────────────────────────────────────────────────

# The URL of the Lost in Raleigh MCP game server.
# Your facilitator will share this at the start of the workshop.
MCP_SERVER_URL=

# ──────────────────────────────────────────────────
#  A2A agents - provided by your facilitator
# ──────────────────────────────────────────────────

# URL of the transport expert A2A agent (used in Step 5).
A2A_SERVER_URL=

# URL of the city guide A2A agent (used in Step 7).
CITY_GUIDE_URL=
```

### Where to find each value

| Variable | Where to find it |
|---|---|
| `AZURE_OPENAI_ENDPOINT` | AI Foundry → your project → **Settings → Keys and endpoints** → Target URI |
| `AZURE_OPENAI_API_KEY` | Same page → **Key 1** |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | The name you gave your deployment in AI Foundry (default: `gpt-4o-mini`) |
| `MCP_SERVER_URL` | See [Event Resources](event-resources) |
| `A2A_SERVER_URL` | See [Event Resources](event-resources) - provided at Step 5 |
| `CITY_GUIDE_URL` | See [Event Resources](event-resources) - provided at Step 7 |

::: danger Keep your .env private
`.env` is already in `.gitignore`. Never paste your API key into a file that gets committed, posted in chat, or shared on screen.
:::

---

## 6. Set up Azure AI Foundry

If you haven't yet created your Azure OpenAI deployment, follow the [Azure Foundry Setup](azure-foundry-setup) guide. Come back here once you have your endpoint, key, and deployment name.

---

## 7. Verify your setup

Run the connectivity test from inside `sample-agent/`:

```bash
python steps/step1_foundry_test.py
```

::: tip Expected output
```
Connected to Azure OpenAI!
Model response: ...
```
If you see this, you are ready to start the workshop.
:::

::: details Troubleshooting

**`KeyError: 'AZURE_OPENAI_ENDPOINT'`**  
Your `.env` file is missing or the variable is empty. Open `.env` and fill in the value.

**`AuthenticationError`**  
Your API key is wrong. Double-check Key 1 in AI Foundry.

**`DeploymentNotFound`**  
Your `AZURE_OPENAI_DEPLOYMENT_NAME` doesn't match what you created in AI Foundry. Common mistake: the default is `gpt-4o-mini` but you named your deployment something else.

**`Connection refused` / timeout**  
Your `AZURE_OPENAI_ENDPOINT` URL is wrong, or you are behind a corporate proxy. Try copying the URL again from AI Foundry.
:::
