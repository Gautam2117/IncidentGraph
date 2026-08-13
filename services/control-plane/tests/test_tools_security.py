import pytest

from app.tools.tool_registry import execute_tool


@pytest.mark.asyncio
async def test_denial_arbitrary_sql() -> None:
    """IG-419: Verifies that arbitrary SQL tool execution is strictly denied."""
    res = await execute_tool("system.sql", {"query": "SELECT * FROM users;"})
    assert res.success is False
    assert "Permission Denied" in res.error


@pytest.mark.asyncio
async def test_denial_arbitrary_shell() -> None:
    """IG-420: Verifies that arbitrary shell command execution is strictly denied."""
    res = await execute_tool("system.shell", {"command": "cat /etc/passwd"})
    assert res.success is False
    assert "Permission Denied" in res.error


@pytest.mark.asyncio
async def test_denial_arbitrary_url_fetch() -> None:
    """IG-421: Verifies that arbitrary URL fetching is strictly denied."""
    res = await execute_tool("system.curl", {"url": "http://169.254.169.254/latest/meta-data"})
    assert res.success is False
    assert "Permission Denied" in res.error


@pytest.mark.asyncio
async def test_denial_filesystem_escape() -> None:
    """IG-422: Verifies that arbitrary filesystem access is strictly denied."""
    res = await execute_tool("system.read_file", {"path": "../../../../etc/shadow"})
    assert res.success is False
    assert "Permission Denied" in res.error
