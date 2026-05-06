"""
Step 2 — Hello World with the bare AzureOpenAI client.

What this does:
  Asks "What is Raleigh famous for?" using the raw openai SDK.
  No agent framework yet — just you and the model.

  This is the baseline: if this works, Steps 3-5 will work.

Run it:
  python steps/step2_hello_world.py

Expected output:
  Raleigh is famous for: ...
"""
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
