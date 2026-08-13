import uuid
from typing import Any

from fastapi import FastAPI, HTTPException, status
from opentelemetry import trace
from pydantic import BaseModel

from services.demo.common.fault_injector import FaultConfig, get_fault_injector
from services.demo.common.metrics import setup_metrics_middleware
from services.demo.common.tracing import setup_telemetry

SERVICE_NAME = "payments"

setup_telemetry(SERVICE_NAME)
fault_injector = get_fault_injector(SERVICE_NAME)

app = FastAPI(title=f"Demo Service — {SERVICE_NAME}", version="0.1.0")
setup_metrics_middleware(app, SERVICE_NAME)

tracer = trace.get_tracer(SERVICE_NAME)


class ChargeRequest(BaseModel):
    order_id: str
    amount: float
    user_id: str


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


@app.post("/payments/charge")
async def charge_payment(request: ChargeRequest) -> dict[str, Any]:
    await fault_injector.maybe_inject("/payments/charge")

    with tracer.start_as_current_span("payments.charge") as span:
        txn_id = f"txn_{uuid.uuid4().hex[:10]}"
        span.set_attribute("payment.transaction_id", txn_id)
        span.set_attribute("payment.amount", request.amount)

        if request.amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment amount must be greater than zero",
            )

        return {
            "transaction_id": txn_id,
            "order_id": request.order_id,
            "status": "SUCCESS",
            "amount": request.amount,
        }
