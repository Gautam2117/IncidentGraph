import asyncio

import pytest

from app.tools.audit import get_tool_audit_logs
from app.tools.tool_base import BaseTool
from app.tools.tool_registry import execute_tool, list_registered_tools


class SlowMockTool(BaseTool):  # type: ignore[misc]
    name = "mock.slow"
    description = "Mock slow tool for timeout testing"
    timeout_seconds = 0.1

    async def execute(self, **kwargs: str) -> str:
        await asyncio.sleep(0.5)
        return "done"


class LargeOutputMockTool(BaseTool):  # type: ignore[misc]
    name = "mock.large"
    description = "Mock tool producing large list output"
    max_output_items = 5

    async def execute(self, **kwargs: str) -> list[int]:
        return list(range(100))


@pytest.mark.asyncio
async def test_tool_registry_list() -> None:
    tools = list_registered_tools()
    assert len(tools) == 10
    names = {t["name"] for t in tools}
    assert "metrics.query" in names
    assert "logs.search" in names
    assert "traces.get" in names


@pytest.mark.asyncio
async def test_metrics_query_tool_execution() -> None:
    res = await execute_tool(
        "metrics.query", {"service": "inventory", "metric_type": "http_requests_total"}
    )
    assert res.success is True
    assert res.data["service"] == "inventory"
    assert "audit_id" in res.model_dump()


@pytest.mark.asyncio
async def test_tool_timeout() -> None:
    tool = SlowMockTool()
    res = await tool.run()
    assert res.success is False
    assert "timed out" in res.error


@pytest.mark.asyncio
async def test_output_bounding_truncation() -> None:
    tool = LargeOutputMockTool()
    res = await tool.run()
    assert res.success is True
    assert res.truncated is True
    assert len(res.data) == 5


@pytest.mark.asyncio
async def test_duplicate_query_suppression() -> None:
    res1 = await execute_tool("deployments.list", {"service": "orders"})
    res2 = await execute_tool("deployments.list", {"service": "orders"})
    assert res1.data == res2.data
    assert res1.audit_id == res2.audit_id


@pytest.mark.asyncio
async def test_tool_audit_logging() -> None:
    await execute_tool("topology.get", {})
    logs = await get_tool_audit_logs("topology.get")
    assert len(logs) >= 1
    assert logs[-1]["tool_name"] == "topology.get"
