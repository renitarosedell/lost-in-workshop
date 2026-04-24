"""Hello world agent using Microsoft Agent Framework with Azure AI Foundry (key auth)."""

import asyncio
import os

from agent_framework import Agent, MCPStreamableHTTPTool
from agent_framework.openai import OpenAIChatClient 
from agent_framework_foundry import FoundryChatClient
from agent_framework import ContextProvider, SessionContext
from dotenv import load_dotenv
from azure.identity import AzureCliCredential
from openai import azure_endpoint


load_dotenv()


async def main() -> None:

    #client = FoundryChatClient(
    #    model=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
    #    credential=AzureCliCredential(),
    #    project_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"]      
    #)

    client = OpenAIChatClient(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        model=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
    )

    game_mcp = MCPStreamableHTTPTool(
        name="Gaming MCP Server",
        url="http://localhost:8000/mcp",
        description="",
    )    
    await game_mcp.connect()

    user_id = "user123"
    store = {}

    class PlayerMemory(ContextProvider):
        def __init__(self, user_id: str, store: dict):
            super().__init__("player-memory")
            self._user_id = user_id
            self._store = store  # any key-value store: dict, Redis, Cosmos, etc.

        async def before_run(self, *, context: SessionContext, **_) -> None:
            player_id = self._store.get(self._user_id)
            if player_id:
                context.extend_instructions(self.source_id, f"The player_id is {player_id}.")

        async def after_run(self, *, context: SessionContext, **_) -> None:
            # Only runs in the registration session, once
            if not self._store.get(self._user_id):
                for msg in context.input_messages:
                    text = getattr(msg, "text", "") or ""
                    if "player_id" in text.lower():
                        # extract and persist it
                        player_id = extract_player_id(text)  # your parsing logic
                        self._store[self._user_id] = player_id
                        break

    def extract_player_id(text: str) -> str:
        # replace with your actual parsing logic
        for word in text.split():
            if word.startswith("PLR"):
                return word
        return text.strip()


    agent = Agent(
        client=client,
        name="HelloAgent",
        instructions="You are HelloAgent, a helpful assistant that can chat with users and use tools to learn about the world.",
        tools=[game_mcp],
        context_providers=[PlayerMemory(user_id=user_id, store=store)],
    )

    print("Chat with HelloAgent (type 'exit' or 'quit' to stop, Ctrl+C to abort)\n")
    session = agent.create_session()
    response = await agent.run("start the game", session=session)
    print(f"Agent: {response.text}\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            break

        response = await agent.run(user_input, session=session)
        print(f"Agent: {response.text}\n")
    

    await game_mcp.close()
    print(store)

if __name__ == "__main__":
    asyncio.run(main())
