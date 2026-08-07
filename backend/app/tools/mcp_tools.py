from langchain_core.tools import tool

from app.guardrails.input_validation import truncate
from app.tools.mcp_client import call_mcp_tool

MAX_QUERY_LENGTH = 200


@tool
async def search_employee_directory(query: str = "", department: str | None = None) -> list[dict] | str:
    """Search the enterprise employee directory (via MCP) by name, title, or email substring, optionally filtered by department."""
    return await call_mcp_tool("search_employee_directory", {"query": truncate(query, MAX_QUERY_LENGTH), "department": department})


@tool
async def search_service_catalog(query: str = "", department: str | None = None) -> list[dict] | str:
    """Search the enterprise service catalog (via MCP) by service name or owner, optionally filtered by department."""
    return await call_mcp_tool("search_service_catalog", {"query": truncate(query, MAX_QUERY_LENGTH), "department": department})


@tool
async def search_incident_records(query: str = "", department: str | None = None) -> list[dict] | str:
    """Search enterprise incident records (via MCP) by title or incident id, optionally filtered by department."""
    return await call_mcp_tool("search_incident_records", {"query": truncate(query, MAX_QUERY_LENGTH), "department": department})
