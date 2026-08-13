from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class Hypothesis(BaseModel):
    id: str
    target_service: str
    root_cause_category: str
    description: str
    confidence: float
    supporting_evidence: list[str] = Field(default_factory=list)
    status: str = "proposed"  # proposed, verified, rejected


class RCAReport(BaseModel):
    summary: str
    primary_service: str
    root_cause_category: str
    causal_chain: list[str]
    confidence_score: float
    is_conclusive: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class RemediationStep(BaseModel):
    step_number: int
    action_type: str
    description: str
    target_service: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    is_safe: bool = True


class RemediationPlan(BaseModel):
    plan_id: str
    incident_id: str
    steps: list[RemediationStep]
    risk_level: str = "low"  # low, medium, high
    requires_human_approval: bool = False
    approved: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class InvestigationState(BaseModel):
    incident_id: str
    status: str = "open"  # includes terminal resolved/failed/cancelled outcomes
    target_service: str | None = None
    triage_summary: str | None = None
    telemetry_evidence: list[dict[str, Any]] = Field(default_factory=list)
    knowledge_docs: list[dict[str, Any]] = Field(default_factory=list)
    knowledge_search_completed: bool = False
    hypotheses: list[Hypothesis] = Field(default_factory=list)
    skeptic_feedback: list[str] = Field(default_factory=list)
    rca_report: RCAReport | None = None
    remediation_plan: RemediationPlan | None = None
    remediation_execution: dict[str, Any] | None = None
    # Explicitly enables deterministic telemetry adapters for offline evaluation.
    # Production investigations must leave this disabled.
    use_test_adapters: bool = False
    step_count: int = 0
    history: list[str] = Field(default_factory=list)
