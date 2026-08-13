import pytest
from httpx import AsyncClient

from app.services.incident_service import verify_webhook_signature


@pytest.mark.asyncio
async def test_manual_incident_creation(async_client: AsyncClient) -> None:
    payload = {
        "title": "High Latency on Orders Service",
        "severity": "high",
        "target_service": "orders",
        "summary": "Manual incident opened by test runner",
    }
    response = await async_client.post("/api/v1/incidents", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert len(data["id"]) > 10
    assert data["title"] == payload["title"]
    assert data["severity"] == "high"
    assert data["status"] == "open"


@pytest.mark.asyncio
async def test_incident_list_and_detail(async_client: AsyncClient) -> None:
    # Create incident first
    create_res = await async_client.post(
        "/api/v1/incidents",
        json={
            "title": "DB Pool Exhaustion Alert",
            "severity": "critical",
            "target_service": "inventory",
        },
    )
    inc_id = create_res.json()["id"]

    # List incidents
    list_res = await async_client.get("/api/v1/incidents")
    assert list_res.status_code == 200
    incidents = list_res.json()
    assert len(incidents) >= 1

    # Detail view
    detail_res = await async_client.get(f"/api/v1/incidents/{inc_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["id"] == inc_id
    assert detail["title"] == "DB Pool Exhaustion Alert"


@pytest.mark.asyncio
async def test_incident_timeline(async_client: AsyncClient) -> None:
    create_res = await async_client.post(
        "/api/v1/incidents",
        json={"title": "Payment 5xx Failure", "severity": "high", "target_service": "payments"},
    )
    inc_id = create_res.json()["id"]

    timeline_res = await async_client.get(f"/api/v1/incidents/{inc_id}/timeline")
    assert timeline_res.status_code == 200
    timeline = timeline_res.json()
    assert len(timeline) >= 1
    assert timeline[0]["event_type"] == "system"


@pytest.mark.asyncio
async def test_webhook_ingestion(
    async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    import hashlib
    import hmac
    import json
    import time
    import uuid

    from app.core.config import settings

    secret = "test-webhook-signing-secret"
    monkeypatch.setattr(settings, "WEBHOOK_SIGNING_SECRET", secret)
    alert_payload = {
        "title": "Prometheus Alert: Payment 5xx Error Rate > 10%",
        "severity": "critical",
        "service": "payments",
        "summary": "High 5xx error rate detected on payments endpoint",
    }
    canonical = json.dumps(alert_payload, sort_keys=True).encode("utf-8")
    timestamp = str(int(time.time()))
    signed_payload = f"{timestamp}.".encode() + canonical
    signature = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    delivery_id = f"test-{uuid.uuid4()}"
    headers = {
        "X-Signature": signature,
        "X-Webhook-ID": delivery_id,
        "X-Webhook-Timestamp": timestamp,
    }
    response = await async_client.post(
        "/api/v1/incidents/webhooks/ingest",
        json=alert_payload,
        headers=headers,
    )
    assert response.status_code in [200, 201]
    data = response.json()
    assert "id" in data
    assert data["severity"] == "critical"

    replay = await async_client.post(
        "/api/v1/incidents/webhooks/ingest",
        json=alert_payload,
        headers=headers,
    )
    assert replay.status_code == 400
    assert "already been processed" in replay.json()["message"]


def test_webhook_hmac_signature() -> None:
    payload = b'{"alert":"cpu_high"}'
    secret = "secret123"
    import hashlib
    import hmac

    sig = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()

    assert verify_webhook_signature(payload, secret, sig) is True
    assert verify_webhook_signature(payload, secret, "invalid_sig") is False
