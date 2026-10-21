from core.groq import GroqService
from mcp_client import MCPClient
from core.tools import ToolManager


class Chat:
    def __init__(self, groq_service: GroqService, clients: dict[str, MCPClient]):
        self.groq_service: GroqService = groq_service
        self.clients: dict[str, MCPClient] = clients
        self.messages: list[dict] = []

    async def _process_query(self, query: str):
        self.messages.append({"role": "user", "content": query})

    async def run(
        self,
        query: str,
    ) -> str:
        final_text_response = ""

        await self._process_query(query)

        while True:
            response = self.groq_service.chat(
                messages=self.messages,
                tools=await ToolManager.get_all_tools(self.clients),
            )
            message = response.choices[0].message

            self.groq_service.add_assistant_message(self.messages, message)

            if response.choices[0].finish_reason == "tool_calls":
                print(self.groq_service.text_from_message(message))
                tool_result_parts = await ToolManager.execute_tool_requests(
                    self.clients, message
                )

                self.messages.extend(tool_result_parts)
            else:
                final_text_response = self.groq_service.text_from_message(message)
                break

        return final_text_response
