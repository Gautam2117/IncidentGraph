import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ScenarioCategory(StrEnum):
    DATABASE = "database"
    DEPLOYMENT = "deployment"
    CONFIGURATION = "configuration"
    LATENCY = "latency"
    HTTP_ERRORS = "http_errors"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    NETWORK_DEPENDENCY = "network_dependency"
    MISLEADING_SIGNAL = "misleading_signal"
    SECURITY = "security"
    EDGE_CASE = "edge_case"


class GroundTruth(BaseModel):
    """Ground truth evaluation target. Strictly isolated from agent model/tool context."""

    primary_service: str
    root_cause_category: str
    description: str
    causal_chain: list[str]
    remediation_action_type: str
    remediation_params: dict[str, Any] = Field(default_factory=dict)
    rejected_hypotheses: list[str] = Field(default_factory=list)


class ScenarioDefinition(BaseModel):
    id: str
    title: str
    category: ScenarioCategory
    summary: str
    target_service: str
    affected_services: list[str]
    tags: list[str] = Field(default_factory=list)
    ground_truth: GroundTruth

    def get_safe_metadata(self) -> dict[str, Any]:
        """Returns model-visible scenario metadata WITHOUT ground truth."""
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category.value,
            "summary": self.summary,
            "target_service": self.target_service,
            "affected_services": self.affected_services,
            "tags": self.tags,
        }


class ScenarioRunState(StrEnum):
    IDLE = "idle"
    TRIGGERED = "triggered"
    RUNNING = "running"
    CLEANED_UP = "cleaned_up"
    FAILED = "failed"


class ScenarioRun(BaseModel):
    run_id: str = Field(default_factory=lambda: f"scen_run_{uuid.uuid4().hex[:8]}")
    scenario_id: str
    state: ScenarioRunState = ScenarioRunState.IDLE
    fault_started_at: str | None = None
    fault_ended_at: str | None = None
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    error_message: str | None = None
    fault_ack: bool = False
    probe_status_code: int | None = None
    probe_latency_ms: float | None = None
