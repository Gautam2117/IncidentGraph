from typing import Any

from app.services.topology_extractor import extract_system_topology
from app.tools.tool_base import BaseTool


class TopologyGetTool(BaseTool):  # type: ignore[misc]
    name = "topology.get"
    description = "Retrieves current service dependency graph nodes and edges."

    async def execute(self) -> dict[str, Any]:
        topology = extract_system_topology()
        return dict(topology.model_dump())
