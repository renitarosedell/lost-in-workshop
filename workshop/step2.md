---
title: "Step 2: Hello Raleigh"
description: Ask a real question about Raleigh using the chat completions API with a system prompt.
---

# Step 2 - Hello Raleigh <Badge type="tip" text="~10 min" />

## The story so far

Your connection is live. Now let's make it useful. In this step you'll give the model a **persona** using a system prompt and ask it a real question about Raleigh. This teaches you the fundamental building block of every AI agent: the role-based message format.

---

## What you'll learn

- The difference between `system`, `user`, and `assistant` roles
- How system prompts shape model behaviour
- Why this raw chat completion approach is the baseline - and where it falls short

---

## How chat completions work

Every call to `client.chat.completions.create()` sends a list of **messages**, each with a `role`:

| Role | Who writes it | Purpose |
|---|---|---|
| `system` | You (the developer) | Sets the model's persona, rules, and context |
| `user` | The end user (or your code) | The actual question or instruction |
| `assistant` | The model | The model's previous replies (for multi-turn) |

The model reads all messages in order and generates the next `assistant` reply. This is the foundation that every agent framework is built on.

---

## Write the code

Create a new file `create-agent/my_step2.py` and paste in:

```python [my_step2.py]
import os

from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

client = AzureOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    api_version="2024-12-01-preview",
)

response = client.chat.completions.create(
    model=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
    messages=[
        {"role": "system", "content": "You are a helpful city guide for Raleigh, NC."},
        {"role": "user", "content": "What is Raleigh famous for?"},
    ],
    max_tokens=200,
)

print(f"Raleigh is famous for: {response.choices[0].message.content}")
```

### What the system prompt does

Without a system prompt, the model answers as a generic assistant. With `"You are a helpful city guide for Raleigh, NC."`, it:
- Focuses answers on Raleigh
- Adopts a helpful, local-guide tone
- Implicitly filters out irrelevant information

Try changing the system prompt to `"You are a grumpy tour guide who hates questions."` and run it again, and notice how the personality changes even though the question is identical.

---

## Run it

```bash
python my_step2.py
```

::: tip Expected output
```
Raleigh is famous for: Raleigh, the capital of North Carolina, is known for being
part of the Research Triangle with Durham and Chapel Hill, home to major
universities like NC State, Duke, and UNC...
```
:::

::: details Stuck? Use the fallback
`cheatsheet/step2_hello_world.py` contains the complete working solution. Run it with `python cheatsheet/step2_hello_world.py`.
:::

---

## Where this approach falls short

This code works for a single question, but notice what it can't do:
- **No tools**: it can only answer from its training data; it can't look things up
- **No memory**: each run starts fresh; it doesn't know what you said before
- **No agency**: it doesn't decide *what* to do next; you hardcode the question

The next step introduces the **Microsoft Agent Framework**, which solves all three problems.

::: info Next step
[Step 3 - Connect to the MCP Game Server](step3) →
:::
