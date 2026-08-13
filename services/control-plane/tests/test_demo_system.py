import pytest
from httpx import AsyncClient

from app.services.topology_extractor import extract_system_topology
from services.demo.common.fault_injector import get_fault_injector
from services.demo.common.tracing import get_current_trace_context


@pytest.mark.asyncio
async def test_topology_api(async_client: AsyncClient) -> None:
    response = await async_client.get("/api/v1/topology")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) >= 6
    assert len(data["edges"]) >= 5

    service_ids = {node["id"] for node in data["nodes"]}
    assert "gateway" in service_ids
    assert "auth" in service_ids
    assert "orders" in service_ids
    assert "payments" in service_ids
    assert "inventory" in service_ids
    assert "notifications" in service_ids


def test_topology_extractor() -> None:
    topology = extract_system_topology()
    assert len(topology.nodes) >= 6
    assert len(topology.edges) >= 5


def test_trace_context_generation() -> None:
    context = get_current_trace_context()
    assert isinstance(context, dict)


def test_fault_injector_registration() -> None:
    injector = get_fault_injector("payments")
    assert injector.service_name == "payments"
