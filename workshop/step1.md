---
title: "Step 1: Connect to Azure OpenAI"
description: Verify your Azure OpenAI credentials using the bare openai SDK — no agent framework yet.
---

# Step 1 — Connect to Azure OpenAI <Badge type="tip" text="~10 min" />

## The story so far

You've just arrived in Raleigh, NC. Before you can start navigating the city, you need to make sure your AI engine is running. Think of this step as turning the key in the ignition — if the model responds, everything else will work.

---

## What you'll learn

- How to call Azure OpenAI using the `openai` SDK directly
- What `azure_endpoint`, `api_key`, and `api_version` do
- The difference between Azure OpenAI and the public `api.openai.com`

---

## Why Azure OpenAI?

Azure OpenAI is the same GPT model family you know, but hosted inside your Azure subscription. This matters for three reasons:

1. **Data residency** — your prompts and completions stay within your Azure region
2. **Enterprise security** — API keys are managed by Azure RBAC; no shared rate limits
3. **AI Foundry integration** — you can swap models, add fine-tuning, and monitor usage all in one place

The `AzureOpenAI` client from the `openai` SDK handles the slightly different authentication flow: instead of a single API key sent to `api.openai.com`, you send your key to your own endpoint URL (`https://your-hub.openai.azure.com/`).

---

## Write the code

Open `steps/step1_foundry_test.py` and replace its contents with:

```python [steps/step1_foundry_test.py]
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
| `load_dotenv()` | Reads `.env` and sets environment variables — no hardcoded secrets |
| `AzureOpenAI(...)` | Creates a client pointed at *your* endpoint, not the shared OpenAI one |
| `api_version=` | Azure OpenAI requires a version date; use the latest stable |
| `model=os.environ[...]` | Uses your deployment name — not `gpt-4o-mini` but the name *you gave* to it in Foundry |
| `messages=[...]` | Chat completions format: a list of role/content pairs |

---

## Run it

```bash
python steps/step1_foundry_test.py
```

::: tip Expected output
```
Connected to Azure OpenAI!
Model response: Why did the tourist get lost in Raleigh? ...
```
:::

::: details Stuck? Use the fallback
The file `steps/step1_foundry_test.py` is already in the repo with the complete code. Run it as-is.
:::

---

## Key takeaway

You're talking directly to the model over HTTP. There is no agent logic, no tool-calling, no memory — just a request and a response. The next steps build on top of this foundation.

::: info Next step
[Step 2 — Hello Raleigh](step2) →
:::
