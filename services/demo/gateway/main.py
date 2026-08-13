import os
from typing import Any

from fastapi import FastAPI, Header, HTTPException, status
from opentelemetry import trace
from pydantic import BaseModel

from services.demo.common.fault_injector import FaultConfig, get_fault_injector
from services.demo.common.metrics import setup_metrics_middleware
from services.demo.common.tracing import TracedHTTPClient, setup_telemetry

SERVICE_NAME = "gateway"
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8002")
ORDERS_SERVICE_URL = os.getenv("ORDERS_SERVICE_URL", "http://localhost:8003")

setup_telemetry(SERVICE_NAME)
fault_injector = get_fault_injector(SERVICE_NAME)

app = FastAPI(title=f"Demo Service — {SERVICE_NAME}", version="0.1.0")
setup_metrics_middleware(app, SERVICE_NAME)

tracer = trace.get_tracer(SERVICE_NAME)


class CreateOrderRequest(BaseModel):
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
async def create_order(
    request: CreateOrderRequest,
    authorization: str | None = Header(default="Bearer valid-token"),
) -> dict[str, Any]:
    await fault_injector.maybe_inject("/orders")

    with tracer.start_as_current_span("gateway.create_order") as span:
        span.set_attribute("user.id", request.user_id)
        span.set_attribute("order.total", request.total_amount)

        auth_client = TracedHTTPClient(AUTH_SERVICE_URL)
        orders_client = TracedHTTPClient(ORDERS_SERVICE_URL)

        # 1. Validate Auth
        try:
            auth_res = await auth_client.post(
                "/auth/validate",
                json_data={"token": authorization},
            )
            if auth_res.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication failed at gateway",
                )
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Auth service unavailable: {str(e)}",
            ) from e

        # 2. Forward to Orders Service
        try:
            orders_res = await orders_client.post(
                "/orders",
                json_data={
                    "user_id": request.user_id,
                    "items": request.items,
                    "total_amount": request.total_amount,
                },
            )
            if orders_res.status_code != 200:
                raise HTTPException(
                    status_code=orders_res.status_code,
                    detail=f"Order processing failed: {orders_res.text}",
                )
            return orders_res.json()
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Orders service unavailable: {str(e)}",
            ) from e
