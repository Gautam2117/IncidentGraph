from typing import Any

from app.scenarios.registry import get_scenario
from app.tools.tool_base import BaseTool


class ScenariosGetSafeMetadataTool(BaseTool):  # type: ignore[misc]
    name = "scenarios.get_safe_metadata"
    description = "Retrieves sanitized scenario metadata (Ground Truth strictly omitted)."

    async def execute(self, scenario_id: str) -> dict[str, Any]:
        scenario = get_scenario(scenario_id)
        if not scenario:
            raise ValueError(f"Scenario '{scenario_id}' not found")
        return dict(scenario.get_safe_metadata())
