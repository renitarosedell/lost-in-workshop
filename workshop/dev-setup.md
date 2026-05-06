---
title: Developer Environment Setup
description: Fork the repo, open a GitHub Codespace, configure your .env file, and verify your setup before the workshop.
---

# Developer Environment Setup

<Badge type="warning" text="Complete before writing any code" />

The recommended way to do this workshop is with **GitHub Codespaces** — a cloud development environment that runs in your browser. No local installs required.

::: tip Why Codespaces?
- Python 3.11 and all dependencies are pre-installed
- GitHub Copilot is enabled out of the box
- Works on any machine — no Python, Git, or VS Code setup needed
- Identical environment for every attendee
:::

---

## 1. Fork the repository

1. Go to **[https://github.com/RoelantD/lost-in-workshop](https://github.com/RoelantD/lost-in-workshop)**
2. Click **Fork** in the top-right corner
3. Select your GitHub account as the destination

This creates your own copy of the repo that you can write to.

---

## 2. Start a Codespace

1. In your forked repository, click the green **Code** button
2. Select the **Codespaces** tab
3. Click **Create codespace on main**

GitHub will build a container with Python 3.11 and install all dependencies automatically. This takes **2–3 minutes** the first time.

::: tip Expected result
When the Codespace opens, you will see VS Code in your browser with a terminal at the bottom. Your prompt will look like:
```
(.venv) /workspaces/lost-in-workshop $
```
:::

---

## 3. Set up your `.env` file

The agent reads credentials from a `.env` file that is **never committed to Git**.

In the Codespace terminal, run:

```bash
cd create-agent
cp .env.example .env
```

Then open `.env` (click it in the file explorer on the left) and fill in your values:

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
| `A2A_SERVER_URL` | See [Event Resources](event-resources) — provided at Step 5 |
| `CITY_GUIDE_URL` | See [Event Resources](event-resources) — provided at Step 7 |

::: danger Keep your .env private
`.env` is already in `.gitignore`. Never paste your API key into a file that gets committed, posted in chat, or shared on screen.
:::

---

## 4. Set up Azure AI Foundry

If you haven't yet created your Azure OpenAI deployment, follow the [Azure Foundry Setup](azure-foundry-setup) guide. Come back here once you have your endpoint, key, and deployment name.

---

## 5. Verify your setup

Run the connectivity test from inside `create-agent/`:

```bash
python cheatsheet/step1_foundry_test.py
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

---

## Local setup (alternative)

::: details Click to expand — only needed if you prefer to work locally instead of in a Codespace

**What you need**

| Requirement | Version | Check with |
|---|---|---|
| Python | 3.11 or later | `python --version` |
| Git | any recent | `git --version` |
| A code editor | VS Code recommended | — |

**1. Clone the repository**

```bash
git clone https://github.com/RoelantD/lost-in-workshop.git
cd lost-in-workshop
```

**2. Create a virtual environment**

::: code-group
```bash [macOS / Linux]
cd create-agent
python -m venv .venv
source .venv/bin/activate
```
```powershell [Windows]
cd create-agent
python -m venv .venv
.venv\Scripts\Activate.ps1
```
:::

Once active, your terminal prompt shows `(.venv)`.

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Create your `.env` file**

::: code-group
```bash [macOS / Linux]
cp .env.example .env
```
```powershell [Windows]
copy .env.example .env
```
:::

Then fill in the values as described in step 3 above.

**5. Log in to Azure CLI** *(optional but recommended)*

```bash
az login --use-device-code
```

Follow the on-screen instructions to sign in with the account that has your Azure subscription.

**6. Verify your setup**

```bash
python cheatsheet/step1_foundry_test.py
```

Expected: `Connected to Azure OpenAI!`

:::

