import json
from typing import Optional, List
from mcp.types import CallToolResult, Tool, TextContent
from mcp_client import MCPClient
from google.genai import types


class ToolManager:
    @classmethod
    async def get_all_tools(cls, clients: dict[str, MCPClient]) -> list[dict]:
        """Gets all tools from the provided clients, in dict format for claude.py to convert."""
        tools = []
        for client in clients.values():
            tool_models = await client.list_tools()
            tools += [
                {
                    "name": t.name,
                    "description": t.description,
                    "input_schema": t.inputSchema,
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
        cls, clients: dict[str, MCPClient], response
    ) -> list[types.Part]:
        """Exécute les appels de fonctions demandés par Gemini et retourne les Parts de résultats."""
        function_calls = response.function_calls
        if not function_calls:
            return []

        result_parts: list[types.Part] = []

        for fc in function_calls:
            tool_name = fc.name
            tool_input = dict(fc.args) if fc.args else {}

            client = await cls._find_client_with_tool(
                list(clients.values()), tool_name
            )

            if not client:
                result_part = types.Part.from_function_response(
                    name=tool_name,
                    response={"error": "Could not find that tool"},
                )
                result_parts.append(result_part)
                continue

            tool_output = None
            try:
                tool_output: CallToolResult | None = await client.call_tool(
                    tool_name, tool_input
                )
                items = []
                if tool_output:
                    items = tool_output.content
                content_list = [
                    item.text for item in items if isinstance(item, TextContent)
                ]
                content_json = json.dumps(content_list)

                result_part = types.Part.from_function_response(
                    name=tool_name,
                    response={"result": content_json},
                )

            except Exception as e:
                error_message = f"Error executing tool '{tool_name}': {e}"
                print(error_message)
                result_part = types.Part.from_function_response(
                    name=tool_name,
                    response={"error": error_message},
                )

            result_parts.append(result_part)

        return result_parts
