"""
MCP Server tests — validates mcp>=2.0.0 MCPServer API.
"""

import pytest
from httpx import AsyncClient

from app.mcp.server import server


@pytest.mark.asyncio
async def test_mcp_server_name() -> None:
    """Server name must match the registered value."""
    assert server.name == "IncidentGraph MCP Server"


@pytest.mark.asyncio
async def test_mcp_tools_registered() -> None:
    """All three diagnostic tools must be registered with the MCPServer."""
    # MCPServer 2.0.0 exposes tools via list_tools() (sync or async)
    tools = await server.list_tools()
    tool_names = {t.name for t in tools}
    assert "query_metrics" in tool_names, f"query_metrics missing from {tool_names}"
    assert "search_logs" in tool_names, f"search_logs missing from {tool_names}"
    assert "get_traces" in tool_names, f"get_traces missing from {tool_names}"


@pytest.mark.asyncio
async def test_mcp_prompts_registered() -> None:
    """Both SRE prompts must be registered."""
    prompts = await server.list_prompts()
    prompt_names = {p.name for p in prompts}
    assert "incident_triage" in prompt_names
    assert "rca_synthesis" in prompt_names


@pytest.mark.asyncio
async def test_mcp_resources_registered() -> None:
    """All three resources must be registered."""
    resources = await server.list_resources()
    uris = {r.uri for r in resources}
    assert "incidents://active" in uris
    assert "topology://graph" in uris
    assert "scenarios://metadata" in uris


@pytest.mark.asyncio
async def test_mcp_api_endpoint(async_client: AsyncClient) -> None:
    """GET /api/v1/mcp/sse must be reachable — not 404 or 500.

    In test mode DNS-rebinding protection is disabled so any host is allowed.
    The test client may receive 200 (streaming) or a handled error; both are
    acceptable.  404 = route missing, 500 = unhandled crash.
    """
    res = await async_client.get("/api/v1/mcp/sse")
    assert res.status_code not in (404, 500), (
        f"SSE endpoint returned unexpected status {res.status_code}"
    )
