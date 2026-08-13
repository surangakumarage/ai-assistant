from mcp import types
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client

from app.core.config import get_settings


def _mcp_endpoint() -> str:
    settings = get_settings()
    return f"{settings.mcp_server_url.rstrip('/')}/mcp"


async def call_mcp_tool(tool_name: str, arguments: dict) -> list[dict] | str:
    async with streamable_http_client(_mcp_endpoint()) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)

    if not isinstance(result, types.CallToolResult):
        return str(result)
    if result.structured_content is not None:
        content = result.structured_content
        # MCP wraps non-object return types (e.g. list[dict]) as {"result": [...]}
        # since structuredContent must be a JSON object at the top level.
        if isinstance(content, dict) and content.keys() == {"result"}:
            return content["result"]
        return content
    return "\n".join(block.text for block in result.content if isinstance(block, types.TextContent))
