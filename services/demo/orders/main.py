import os
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException
from opentelemetry import trace
from pydantic import BaseModel

from services.demo.common.fault_injector import FaultConfig, get_fault_injector
from services.demo.common.metrics import setup_metrics_middleware
from services.demo.common.tracing import TracedHTTPClient, setup_telemetry

SERVICE_NAME = "orders"
INVENTORY_SERVICE_URL = os.getenv("INVENTORY_SERVICE_URL", "http://localhost:8005")
PAYMENTS_SERVICE_URL = os.getenv("PAYMENTS_SERVICE_URL", "http://localhost:8004")
NOTIFICATIONS_SERVICE_URL = os.getenv("NOTIFICATIONS_SERVICE_URL", "http://localhost:8006")

setup_telemetry(SERVICE_NAME)
fault_injector = get_fault_injector(SERVICE_NAME)

app = FastAPI(title=f"Demo Service — {SERVICE_NAME}", version="0.1.0")
setup_metrics_middleware(app, SERVICE_NAME)

tracer = trace.get_tracer(SERVICE_NAME)


class ProcessOrderRequest(BaseModel):
    user_id: str
    items: list[dict[str, Any]]
    total_amount: float


@app.get("/health/live")
async def health_live() -> dict[str, str]:
    return {"status": "ok", "service": SERVICE_NAME}


@app.get("/health/ready")
async def health_ready() -> dict[str, str]:
    return {"status": "ready", "service": SERVICE_NAME}


@app.get("/version")
async def version() -> dict[str, str]:
    return {"service": SERVICE_NAME, "version": "0.1.0"}


@app.post("/faults")
async def set_fault(endpoint: str, config: FaultConfig) -> dict[str, str]:
    fault_injector.set_fault(endpoint, config)
    return {"message": f"Fault set for {endpoint}"}


@app.post("/orders")
async def process_order(request: ProcessOrderRequest) -> dict[str, Any]:
    await fault_injector.maybe_inject("/orders")

    with tracer.start_as_current_span("orders.process") as span:
        order_id = f"ord_{uuid.uuid4().hex[:8]}"
        span.set_attribute("order.id", order_id)
        span.set_attribute("order.user_id", request.user_id)

        inventory_client = TracedHTTPClient(INVENTORY_SERVICE_URL)
        payments_client = TracedHTTPClient(PAYMENTS_SERVICE_URL)
        notifications_client = TracedHTTPClient(NOTIFICATIONS_SERVICE_URL)

        # 1. Reserve Inventory
        inv_res = await inventory_client.post(
            "/inventory/reserve",
            json_data={"order_id": order_id, "items": request.items},
        )
        if inv_res.status_code != 200:
            raise HTTPException(
                status_code=inv_res.status_code,
                detail=f"Inventory reservation failed: {inv_res.text}",
            )

        # 2. Charge Payment
        pay_res = await payments_client.post(
            "/payments/charge",
            json_data={
                "order_id": order_id,
                "amount": request.total_amount,
                "user_id": request.user_id,
            },
        )
        if pay_res.status_code != 200:
            raise HTTPException(
                status_code=pay_res.status_code,
                detail=f"Payment processing failed: {pay_res.text}",
            )

        # 3. Notify Customer
        await notifications_client.post(
            "/notifications/send",
            json_data={
                "order_id": order_id,
                "user_id": request.user_id,
                "channel": "email",
            },
        )

        return {
            "order_id": order_id,
            "status": "CONFIRMED",
            "user_id": request.user_id,
            "total_amount": request.total_amount,
            "items": request.items,
        }
