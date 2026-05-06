"""
Step 1 — Azure AI Foundry connectivity test.

What this does:
  Sends a single chat message to your Azure OpenAI deployment using the bare
  openai SDK (no agent framework). If it prints a response, your .env is
  correct and your Foundry deployment is reachable.

Run it:
  python cheatsheet/step1_foundry_test.py

Expected output (something like):
  Connected to Azure OpenAI!
  Model response: Hello! I'm ready to help you navigate Raleigh.
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
        {"role": "user", "content": "Tell a joke about navigating Raleigh.'"},
    ],
    max_tokens=50,
)

print("Connected to Azure OpenAI!")
print(f"Model response: {response.choices[0].message.content}")
