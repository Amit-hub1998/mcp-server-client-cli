import asyncio
import sys
import os
from dotenv import load_dotenv
from contextlib import AsyncExitStack

from mcp_client import MCPClient
from core.groq import GroqService

from core.cli_chat import CliChat
from core.cli import CliApp

load_dotenv()

groq_model = os.getenv("GROQ_MODEL", "")
groq_api_key = os.getenv("GROQ_API_KEY", "")


assert groq_model, "Error: GROQ_MODEL cannot be empty. Update .env"
assert groq_api_key, "Error: GROQ_API_KEY cannot be empty. Update .env"


async def main():
    groq_service = GroqService(model=groq_model, api_key=groq_api_key)

    server_scripts = sys.argv[1:]
    clients = {}

    use_uv = os.getenv("USE_UV", "0") == "1"
    command = "uv" if use_uv else sys.executable
    server_args = ["run", "mcp_server.py"] if use_uv else ["mcp_server.py"]

    async with AsyncExitStack() as stack:
        doc_client = await stack.enter_async_context(
            MCPClient(command=command, args=server_args)
        )
        clients["doc_client"] = doc_client

        for i, server_script in enumerate(server_scripts):
            client_id = f"client_{i}_{server_script}"
            args = ["run", server_script] if use_uv else [server_script]
            client = await stack.enter_async_context(
                MCPClient(command=command, args=args)
            )
            clients[client_id] = client

        chat = CliChat(
            doc_client=doc_client,
            clients=clients,
            groq_service=groq_service,
        )

        cli = CliApp(chat)
        await cli.initialize()
        await cli.run()


if __name__ == "__main__":
    asyncio.run(main())
