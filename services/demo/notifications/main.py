from typing import Any

from fastapi import FastAPI
from opentelemetry import trace
from pydantic import BaseModel

from services.demo.common.fault_injector import FaultConfig, get_fault_injector
from services.demo.common.metrics import QUEUE_DEPTH, setup_metrics_middleware
from services.demo.common.tracing import setup_telemetry

SERVICE_NAME = "notifications"

setup_telemetry(SERVICE_NAME)
fault_injector = get_fault_injector(SERVICE_NAME)

app = FastAPI(title=f"Demo Service — {SERVICE_NAME}", version="0.1.0")
setup_metrics_middleware(app, SERVICE_NAME)

tracer = trace.get_tracer(SERVICE_NAME)

QUEUE_DEPTH.labels(service=SERVICE_NAME, queue_name="email_queue").set(0)


class SendNotificationRequest(BaseModel):
    order_id: str
    user_id: str
    channel: str = "email"


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


@app.post("/notifications/send")
async def send_notification(request: SendNotificationRequest) -> dict[str, Any]:
    await fault_injector.maybe_inject("/notifications/send")

    with tracer.start_as_current_span("notifications.send") as span:
        span.set_attribute("notification.order_id", request.order_id)
        span.set_attribute("notification.channel", request.channel)

        return {
            "notification_id": f"notif_{request.order_id}",
            "order_id": request.order_id,
            "status": "SENT",
            "channel": request.channel,
        }
