from typing import Any

from fastapi import FastAPI, HTTPException, status
from opentelemetry import trace
from pydantic import BaseModel

from services.demo.common.fault_injector import FaultConfig, get_fault_injector
from services.demo.common.metrics import setup_metrics_middleware
from services.demo.common.tracing import setup_telemetry

SERVICE_NAME = "auth"

setup_telemetry(SERVICE_NAME)
fault_injector = get_fault_injector(SERVICE_NAME)

app = FastAPI(title=f"Demo Service — {SERVICE_NAME}", version="0.1.0")
setup_metrics_middleware(app, SERVICE_NAME)

tracer = trace.get_tracer(SERVICE_NAME)


class ValidateTokenRequest(BaseModel):
    token: str | None = None


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


@app.post("/auth/validate")
async def validate_token(request: ValidateTokenRequest) -> dict[str, Any]:
    await fault_injector.maybe_inject("/auth/validate")

    with tracer.start_as_current_span("auth.validate_token") as span:
        if not request.token or "invalid" in request.token.lower():
            span.set_attribute("auth.success", False)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )
        span.set_attribute("auth.success", True)
        return {
            "valid": True,
            "user_id": "usr_demo_12345",
            "roles": ["customer"],
        }
