from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.scenarios.schema import ScenarioCategory, ScenarioDefinition

SERVICE_URLS: dict[str, str] = {
    "gateway": settings.DEMO_GATEWAY_URL,
    "auth": settings.DEMO_AUTH_URL,
    "orders": settings.DEMO_ORDERS_URL,
    "payments": settings.DEMO_PAYMENTS_URL,
    "inventory": settings.DEMO_INVENTORY_URL,
    "notifications": settings.DEMO_NOTIFICATIONS_URL,
}

BUSINESS_ENDPOINTS: dict[str, str] = {
    "gateway": "/orders",
    "auth": "/auth/validate",
    "orders": "/orders",
    "payments": "/payments/charge",
    "inventory": "/inventory/reserve",
    "notifications": "/notifications/send",
}


def get_service_url(service: str) -> str:
    try:
        return SERVICE_URLS[service].rstrip("/")
    except KeyError as exc:
        raise ValueError(f"Unknown demo service '{service}'") from exc


def get_business_endpoint(service: str) -> str:
    try:
        return BUSINESS_ENDPOINTS[service]
    except KeyError as exc:
        raise ValueError(f"Unknown demo service '{service}'") from exc


def build_fault_config(scenario: ScenarioDefinition) -> dict[str, Any]:
    """Translate safe scenario metadata into a deterministic sandbox fault.

    Hidden evaluation labels are deliberately not read here. The resulting
    signature is observable through service logs and Prometheus metrics.
    """
    scenario_id = scenario.id
    tags = {tag.lower() for tag in scenario.tags}
    config: dict[str, Any] = {
        "enabled": True,
        "scenario_id": scenario_id,
        "fault_kind": scenario.category.value,
        "latency_ms": 0.0,
        "error_rate": 0.0,
        "error_status_code": 500,
        "error_message": f"Scenario {scenario_id} injected on {scenario.target_service}",
        "pool_exhaustion": False,
        "timeout": False,
    }

    if scenario_id == "db_pool_exhaustion":
        config["pool_exhaustion"] = True
    elif scenario_id == "harmless_deployment":
        config["fault_kind"] = "marker_only"
    elif scenario_id == "recovered_before_investigation":
        config["error_rate"] = 1.0
        config["error_status_code"] = 503
        config["fault_kind"] = "transient_recovered"
    elif scenario_id == "insufficient_evidence":
        config["error_rate"] = 1.0
        config["error_message"] = "Transient unexplained service failure"
    elif (
        scenario.category == ScenarioCategory.LATENCY
        or "latency" in tags
        or "slow" in tags
        or "timeout" in tags
    ):
        config["latency_ms"] = 1500.0
    elif "timeout" in scenario_id or scenario_id in {
        "dns_network_simulation",
        "cascading_failure",
    }:
        config["timeout"] = True
    else:
        config["error_rate"] = 1.0
        if "rate" in tags or "throttling" in scenario_id:
            config["error_status_code"] = 429
        elif "unavailable" in scenario_id or "exhaustion" in scenario_id:
            config["error_status_code"] = 503

    return config


def build_probe_request(service: str) -> dict[str, Any]:
    payloads: dict[str, dict[str, Any]] = {
        "gateway": {
            "user_id": "scenario-probe",
            "items": [{"sku": "probe", "quantity": 1}],
            "total_amount": 1.0,
        },
        "auth": {"token": "Bearer valid-token"},
        "orders": {
            "user_id": "scenario-probe",
            "items": [{"sku": "probe", "quantity": 1}],
            "total_amount": 1.0,
        },
        "payments": {
            "order_id": "scenario-probe",
            "amount": 1.0,
            "user_id": "scenario-probe",
        },
        "inventory": {
            "order_id": "scenario-probe",
            "items": [{"sku": "probe", "quantity": 1}],
        },
        "notifications": {
            "order_id": "scenario-probe",
            "user_id": "scenario-probe",
            "channel": "email",
        },
    }
    try:
        return payloads[service]
    except KeyError as exc:
        raise ValueError(f"Unknown demo service '{service}'") from exc
