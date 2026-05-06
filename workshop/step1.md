---
title: "Step 1: Connect to Azure OpenAI"
description: Verify your Azure OpenAI credentials using the bare openai SDK, with no agent framework yet.
---

# Step 1 - Connect to Azure OpenAI <Badge type="tip" text="~10 min" />

::: warning Before you start
Complete all three Getting Started steps first:
1. [Get Azure Subscription](get-azure) - claim your event subscription or free trial
2. [Developer Environment Setup](dev-setup) - create your virtual environment and `.env` file
3. [Azure AI Foundry Setup](azure-foundry-setup) - deploy `gpt-4o-mini` and copy your endpoint and key

**Do not skip these.** Step 1 will fail without a working `.env` file.
:::

## The story so far

You've just arrived in Raleigh, NC. Before you can start navigating the city, you need to make sure your AI engine is running. Think of this step as turning the key in the ignition, and if the model responds, everything else will work.

---

## What you'll learn

- How to call Azure OpenAI using the `openai` SDK directly
- What `azure_endpoint`, `api_key`, and `api_version` do
- The difference between Azure OpenAI and the public `api.openai.com`

---

## Why Azure OpenAI?

Azure OpenAI is the same GPT model family you know, but hosted inside your Azure subscription. This matters for three reasons:

1. **Data residency**: your prompts and completions stay within your Azure region
2. **Enterprise security**: API keys are managed by Azure RBAC; no shared rate limits
3. **AI Foundry integration**: you can swap models, add fine-tuning, and monitor usage all in one place

The `AzureOpenAI` client from the `openai` SDK handles the slightly different authentication flow: instead of a single API key sent to `api.openai.com`, you send your key to your own endpoint URL (`https://your-hub.openai.azure.com/`).

---

## Write the code

::: tip How the cheatsheet works
The `create-agent/cheatsheet/` folder contains a working reference copy of every step. You write your own code in `create-agent/` (or any file you like in the Codespace), and if you get stuck or run out of time, you can always run the cheatsheet version directly to see the expected output.
:::

::: warning Always work from the `create-agent/` directory
Your `.env` file lives in `create-agent/`. The `load_dotenv()` call looks for it in the **current working directory**, so all your scripts must be run from there:

```bash
cd create-agent
python my_step1.py
```

If you run from the repo root, the `.env` will not be found and you will get `KeyError` on every environment variable.
:::

Create a new file `my_step1.py` inside `create-agent/` (or any name you like) and paste in:

```python [my_step1.py]
import os

from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()  # reads your .env file

client = AzureOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    api_version="2024-12-01-preview",
)

response = client.chat.completions.create(
    model=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
    messages=[
        {"role": "user", "content": "Tell a joke about navigating Raleigh."},
    ],
    max_tokens=50,
)

print("Connected to Azure OpenAI!")
print(f"Model response: {response.choices[0].message.content}")
```

### Why each line matters

| Line | Purpose |
|---|---|
| `load_dotenv()` | Reads `.env` and sets environment variables - no hardcoded secrets |
| `AzureOpenAI(...)` | Creates a client pointed at *your* endpoint, not the shared OpenAI one |
| `api_version=` | Azure OpenAI requires a version date; use the latest stable |
| `model=os.environ[...]` | Uses your deployment name - not `gpt-4o-mini` but the name *you gave* to it in Foundry |
| `messages=[...]` | Chat completions format: a list of role/content pairs |

---

## Run it

Make sure you are in the `create-agent/` directory, then run:

```bash
python my_step1.py
```

::: tip Expected output
```
Connected to Azure OpenAI!
Model response: Why did the tourist get lost in Raleigh? ...
```
:::

::: details Stuck? Use the cheatsheet
The file `cheatsheet/step1_foundry_test.py` contains the complete working solution. Run it directly:

```bash
python cheatsheet/step1_foundry_test.py
```
:::

---

## Key takeaway

You're talking directly to the model over HTTP. There is no agent logic, no tool-calling, no memory, just a request and a response. The next steps build on top of this foundation.

::: info Next step
[Step 2 - Hello Raleigh](step2) →
:::
