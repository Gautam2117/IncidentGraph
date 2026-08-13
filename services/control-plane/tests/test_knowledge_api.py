import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_knowledge_version_reindex_and_archive(async_client: AsyncClient) -> None:
    source = f"test://runbook/{uuid.uuid4()}"
    create = await async_client.post(
        "/api/v1/knowledge",
        json={
            "source_uri": source,
            "title": "Connection Pool Runbook",
            "content": f"Inspect connection pool saturation and timeout metrics before remediation. Source {source}.",
            "category": "runbook",
        },
    )
    assert create.status_code == 201
    first = create.json()
    assert first["version"] == 1
    assert first["chunk_count"] == 1

    updated = await async_client.post(
        "/api/v1/knowledge",
        json={
            "source_uri": source,
            "title": "Connection Pool Runbook",
            "content": f"Inspect pool saturation, active connections, and acquisition timeout metrics. Source {source}.",
            "category": "runbook",
        },
    )
    assert updated.status_code == 201
    second = updated.json()
    assert second["version"] == 2

    detail = await async_client.get(f"/api/v1/knowledge/{second['id']}")
    assert detail.status_code == 200
    assert detail.json()["source_uri"] == source

    listing = await async_client.get("/api/v1/knowledge")
    assert listing.status_code == 200
    assert any(item["id"] == second["id"] for item in listing.json())

    search = await async_client.post(
        "/api/v1/knowledge/search",
        json={"query": "pool saturation timeout", "mode": "hybrid", "top_k": 5},
    )
    assert search.status_code == 200
    assert any(item["document_id"] == source for item in search.json())

    reindex = await async_client.post(f"/api/v1/knowledge/{second['id']}/reindex")
    assert reindex.status_code == 200
    archive = await async_client.delete(f"/api/v1/knowledge/{second['id']}")
    assert archive.status_code == 200
    assert archive.json()["status"] == "archived"

    missing = await async_client.get(f"/api/v1/knowledge/{uuid.uuid4()}")
    assert missing.status_code == 404
