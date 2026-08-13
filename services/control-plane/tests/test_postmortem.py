import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.postmortem.generator import generate_postmortem
from app.rag.store import get_rag_store
from app.services.incident_service import CreateIncidentRequest, create_incident


@pytest.mark.asyncio
async def test_postmortem_generation_and_export(db_session: AsyncSession) -> None:
    inc = await create_incident(
        db_session,
        CreateIncidentRequest(
            title="Postmortem Test Incident", severity="high", target_service="payments"
        ),
    )
    pm = await generate_postmortem(db_session, str(inc.id))

    assert pm.incident_id == inc.id
    assert pm.target_service == "payments"
    assert "Incident Postmortem" in pm.markdown_content
    assert len(pm.action_items) >= 2


@pytest.mark.asyncio
async def test_postmortem_rag_auto_ingestion(db_session: AsyncSession) -> None:
    inc = await create_incident(
        db_session,
        CreateIncidentRequest(
            title="RAG Auto Index Incident", severity="critical", target_service="orders"
        ),
    )
    pm = await generate_postmortem(db_session, str(inc.id))
    assert pm is not None

    rag_store = get_rag_store()
    results = await rag_store.search_hybrid(db_session, inc.id, top_k=5)
    assert any(chunk.metadata.get("incident_id") == inc.id for chunk, _score in results)


@pytest.mark.asyncio
async def test_postmortem_api_endpoints(async_client: AsyncClient) -> None:
    inc_res = await async_client.post(
        "/api/v1/incidents", json={"title": "Postmortem API Test", "severity": "medium"}
    )
    inc_id = inc_res.json()["id"]

    gen_res = await async_client.post("/api/v1/postmortems/generate", json={"incident_id": inc_id})
    assert gen_res.status_code == 201
    data = gen_res.json()
    assert data["incident_id"] == inc_id
    assert "markdown_content" in data

    get_res = await async_client.get(f"/api/v1/postmortems/{inc_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == f"pm_{inc_id}"
