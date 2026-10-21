import json
from typing import Any, Optional
from mcp.types import CallToolResult, TextContent
from mcp_client import MCPClient
from groq.types.chat import ChatCompletionMessage


class ToolManager:
    @classmethod
    async def get_all_tools(cls, clients: dict[str, MCPClient]) -> list[dict]:
        """Gets all tools from the provided clients."""
        tools = []
        for client in clients.values():
            tool_models = await client.list_tools()
            tools += [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description or "",
                        "parameters": t.inputSchema,
                    },
                }
                for t in tool_models
            ]
        return tools

    @classmethod
    async def _find_client_with_tool(
        cls, clients: list[MCPClient], tool_name: str
    ) -> Optional[MCPClient]:
        """Finds the first client that has the specified tool."""
        for client in clients:
            tools = await client.list_tools()
            tool = next((t for t in tools if t.name == tool_name), None)
            if tool:
                return client
        return None

    @classmethod
    async def execute_tool_requests(
        cls, clients: dict[str, MCPClient], message: ChatCompletionMessage
    ) -> list[dict[str, Any]]:
        """Executes a list of tool requests against the provided clients."""
        tool_result_messages = []
        for tool_call in message.tool_calls or []:
            tool_name = tool_call.function.name

            client = await cls._find_client_with_tool(
                list(clients.values()), tool_name
            )

            if not client:
                tool_result_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(
                            {"error": "Could not find that tool"}
                        ),
                    }
                )
                continue

            try:
                tool_input = json.loads(tool_call.function.arguments)
                tool_output: CallToolResult | None = await client.call_tool(
                    tool_name, tool_input
                )
                items = tool_output.content if tool_output else []
                content_list = [
                    item.text for item in items if isinstance(item, TextContent)
                ]
                content = json.dumps(content_list)
                if tool_output and tool_output.isError:
                    content = json.dumps({"error": content_list})
            except Exception as e:
                error_message = f"Error executing tool '{tool_name}': {e}"
                print(error_message)
                content = json.dumps({"error": error_message})

            tool_result_messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": content,
                }
            )
        return tool_result_messages
