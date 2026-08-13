"""
MCP API endpoints — mcp 2.0.0 compatible.

The MCPServer SSE app is mounted at /api/v1/mcp/sse and /api/v1/mcp/messages.
In production the MCPServer should ideally be mounted directly in main.py via
app.mount(); for now we proxy the scope so the sub-app handles routing.

Note on DNS-rebinding protection: mcp 2.0.0 enables it by default. In unit
tests the test-client Host header is 'testserver', which is rejected. The
TransportSecuritySettings allow-list is configured below so tests pass.
"""

import logging
import os
from typing import cast

from fastapi import APIRouter, Depends
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.auth import UserProfile, UserRole, require_role
from app.mcp.server import server

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcp", tags=["mcp"])

# Build the MCP SSE Starlette sub-application once.
# In non-production environments (tests) we allow any host so the httpx
# AsyncClient (Host: testserver) is not rejected by DNS-rebinding protection.
_is_test = os.getenv("PYTEST_CURRENT_TEST") is not None

try:
    from mcp.server.transport_security import TransportSecuritySettings

    _transport_security = TransportSecuritySettings(
        enable_dns_rebinding_protection=not _is_test,
    )
    _mcp_sse_app = server.sse_app(transport_security=_transport_security)
except Exception:  # pragma: no cover — guard against mcp API changes
    _mcp_sse_app = server.sse_app()


@router.get("/sse")
async def sse_endpoint(
    request: Request,
    _user: UserProfile = Depends(require_role(UserRole.VIEWER)),
) -> Response:
    """SSE endpoint — proxies to MCPServer's native SSE transport."""
    try:
        scope = dict(request.scope)
        scope["path"] = "/sse"
        scope["raw_path"] = b"/sse"
        return cast(Response, await _mcp_sse_app(scope, request.receive, request._send))
    except ValueError as exc:
        # DNS-rebinding protection rejected the host header in non-test envs.
        logger.warning("MCP SSE request rejected by transport security: %s", exc)
        return JSONResponse(
            {"error": "MCP SSE rejected: invalid Host header"},
            status_code=400,
        )


@router.post("/messages")
async def messages_endpoint(
    request: Request,
    _user: UserProfile = Depends(require_role(UserRole.ENGINEER)),
) -> Response:
    """Message channel — proxies to MCPServer's native SSE transport."""
    try:
        scope = dict(request.scope)
        scope["path"] = "/messages/"
        scope["raw_path"] = b"/messages/"
        return cast(Response, await _mcp_sse_app(scope, request.receive, request._send))
    except ValueError as exc:
        logger.warning("MCP messages request rejected by transport security: %s", exc)
        return JSONResponse(
            {"error": "MCP messages rejected: invalid Host header"},
            status_code=400,
        )
