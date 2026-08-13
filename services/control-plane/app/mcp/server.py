"""
IncidentGraph MCP Server — mcp>=2.0.0 compatible.

Uses the high-level MCPServer API with decorator-based resource/tool/prompt
registration. Exposes:
  Resources  : incidents://active, topology://graph, scenarios://metadata
  Tools      : query_metrics, search_logs, get_traces
  Prompts    : incident_triage, rca_synthesis
"""

import json
import logging

from mcp.server import MCPServer
from mcp.types import (
    GetPromptResult,
    PromptMessage,
    TextContent,
    TextResourceContents,
)

from app.db.session import AsyncSessionLocal
from app.scenarios.registry import list_scenarios
from app.services.incident_service import list_incidents
from app.tools.tool_registry import execute_tool

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Server instance
# ---------------------------------------------------------------------------
server = MCPServer(
    name="IncidentGraph MCP Server",
    version="0.2.0",
    description=(
        "Model Context Protocol server for the IncidentGraph AI incident-investigation "
        "platform. Exposes live incident state, microservice topology, and SRE runbook "
        "knowledge as MCP resources, plus diagnostic tools for telemetry querying."
    ),
)


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------


@server.resource(
    uri="incidents://active",
    name="Active Incidents",
    description="List of currently active incidents in the control plane",
    mime_type="application/json",
)
async def active_incidents_resource() -> TextResourceContents:
    """Return all active incidents serialised as JSON."""
    async with AsyncSessionLocal() as session:
        incidents = await list_incidents(session, status="open")
    content = json.dumps([inc.model_dump() for inc in incidents])
    return TextResourceContents(
        uri="incidents://active",
        text=content,
        mime_type="application/json",
    )


@server.resource(
    uri="topology://graph",
    name="System Topology Graph",
    description="Microservice architecture dependency topology graph",
    mime_type="application/json",
)
async def topology_graph_resource() -> TextResourceContents:
    """Return the six-service microservice topology."""
    content = json.dumps(
        {
            "services": [
                "gateway",
                "auth",
                "orders",
                "payments",
                "inventory",
                "notifications",
            ]
        }
    )
    return TextResourceContents(
        uri="topology://graph",
        text=content,
        mime_type="application/json",
    )


@server.resource(
    uri="scenarios://metadata",
    name="Chaos Scenarios Metadata",
    description="Registered chaos scenarios — public fields only (ground truth excluded)",
    mime_type="application/json",
)
async def scenarios_metadata_resource() -> TextResourceContents:
    """Return public scenario metadata. Ground truth is never exposed here."""
    scenarios = list_scenarios()
    public = [{"id": s.id, "title": s.title, "service": s.target_service} for s in scenarios]
    return TextResourceContents(
        uri="scenarios://metadata",
        text=json.dumps(public),
        mime_type="application/json",
    )


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@server.tool(
    name="query_metrics",
    description="Query Prometheus metrics for a target microservice",
)
async def tool_query_metrics(service: str) -> list[TextContent]:
    """Execute a Prometheus metrics query via the tool registry."""
    res = await execute_tool("metrics.query", {"service": service})
    return [TextContent(type="text", text=json.dumps(res.data))]


@server.tool(
    name="search_logs",
    description="Search Loki error/warning logs for a target microservice",
)
async def tool_search_logs(service: str, severity: str = "ERROR") -> list[TextContent]:
    """Execute a Loki log search via the tool registry."""
    res = await execute_tool("logs.search", {"service": service, "severity": severity})
    return [TextContent(type="text", text=json.dumps(res.data))]


@server.tool(
    name="get_traces",
    description="Retrieve Tempo distributed traces for a target microservice",
)
async def tool_get_traces(service: str) -> list[TextContent]:
    """Fetch distributed traces via the tool registry."""
    res = await execute_tool("traces.search", {"service": service})
    return [TextContent(type="text", text=json.dumps(res.data))]


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------


@server.prompt(
    name="incident_triage",
    description="Initial triage prompt for scoping incident severity and primary service",
)
async def prompt_incident_triage() -> GetPromptResult:
    return GetPromptResult(
        description="Initial triage prompt for scoping incident severity and primary service",
        messages=[
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=(
                        "Analyze the incoming alert webhook payload, assess severity, "
                        "and identify the primary impacted service."
                    ),
                ),
            )
        ],
    )


@server.prompt(
    name="rca_synthesis",
    description="Root cause analysis synthesis prompt combining telemetry evidence and runbooks",
)
async def prompt_rca_synthesis() -> GetPromptResult:
    return GetPromptResult(
        description="Root cause analysis synthesis prompt combining telemetry evidence and runbooks",
        messages=[
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=(
                        "Synthesize a verified root cause analysis report using empirical "
                        "metric/log evidence, distributed traces, and historical runbooks."
                    ),
                ),
            )
        ],
    )
