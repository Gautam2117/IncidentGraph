from typing import Any

from fastapi import FastAPI, HTTPException, status
from opentelemetry import trace
from pydantic import BaseModel

from services.demo.common.fault_injector import FaultConfig, get_fault_injector
from services.demo.common.metrics import (
    DB_POOL_ACTIVE_CONNECTIONS,
    DB_POOL_MAX_CONNECTIONS,
    setup_metrics_middleware,
)
from services.demo.common.tracing import setup_telemetry

SERVICE_NAME = "inventory"

setup_telemetry(SERVICE_NAME)
fault_injector = get_fault_injector(SERVICE_NAME)

app = FastAPI(title=f"Demo Service — {SERVICE_NAME}", version="0.1.0")
setup_metrics_middleware(app, SERVICE_NAME)

tracer = trace.get_tracer(SERVICE_NAME)

# Set DB pool metrics baseline
DB_POOL_MAX_CONNECTIONS.labels(service=SERVICE_NAME).set(20)
DB_POOL_ACTIVE_CONNECTIONS.labels(service=SERVICE_NAME).set(3)


class ReserveInventoryRequest(BaseModel):
    order_id: str
    items: list[dict[str, Any]]


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
    if config.pool_exhaustion:
        DB_POOL_ACTIVE_CONNECTIONS.labels(service=SERVICE_NAME).set(20)
    else:
        DB_POOL_ACTIVE_CONNECTIONS.labels(service=SERVICE_NAME).set(3)
    return {"message": f"Fault set for {endpoint}"}


@app.post("/inventory/reserve")
async def reserve_inventory(request: ReserveInventoryRequest) -> dict[str, Any]:
    await fault_injector.maybe_inject("/inventory/reserve")

    with tracer.start_as_current_span("inventory.reserve") as span:
        span.set_attribute("inventory.order_id", request.order_id)
        span.set_attribute("inventory.item_count", len(request.items))

        fault = fault_injector.get_fault("/inventory/reserve")
        if fault and fault.pool_exhaustion:
            DB_POOL_ACTIVE_CONNECTIONS.labels(service=SERVICE_NAME).set(20)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection pool exhausted: timeout waiting for connection from pool",
            )

        return {
            "order_id": request.order_id,
            "status": "RESERVED",
            "reservation_id": f"res_{request.order_id}",
        }
