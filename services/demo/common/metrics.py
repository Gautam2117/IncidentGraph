import time
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

# Metrics definitions
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP request count",
    ["service", "method", "endpoint", "status_code"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["service", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

DEPENDENCY_REQUEST_DURATION_SECONDS = Histogram(
    "dependency_request_duration_seconds",
    "Outbound dependency HTTP request duration in seconds",
    ["service", "target_service", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

DB_POOL_ACTIVE_CONNECTIONS = Gauge(
    "db_pool_active_connections",
    "Number of active database connections in pool",
    ["service"],
)

DB_POOL_MAX_CONNECTIONS = Gauge(
    "db_pool_max_connections",
    "Maximum allowed database connections in pool",
    ["service"],
)

QUEUE_DEPTH = Gauge(
    "queue_depth_messages",
    "Current queue depth / backlog count",
    ["service", "queue_name"],
)

SCENARIO_FAULT_ACTIVE = Gauge(
    "scenario_fault_active",
    "Whether a named sandbox scenario fault is currently active",
    ["service", "scenario_id", "fault_kind"],
)

FAULT_INJECTIONS_TOTAL = Counter(
    "scenario_fault_injections_total",
    "Number of business requests affected by an injected scenario fault",
    ["service", "scenario_id", "fault_kind"],
)


def setup_metrics_middleware(app: FastAPI, service_name: str) -> None:
    @app.middleware("http")
    async def metrics_middleware(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        start_time = time.perf_counter()
        endpoint = request.url.path

        # Don't record internal metrics endpoint calls
        if endpoint == "/metrics":
            return await call_next(request)

        try:
            response = await call_next(request)
            duration = time.perf_counter() - start_time
            HTTP_REQUESTS_TOTAL.labels(
                service=service_name,
                method=request.method,
                endpoint=endpoint,
                status_code=str(response.status_code),
            ).inc()
            HTTP_REQUEST_DURATION_SECONDS.labels(
                service=service_name,
                endpoint=endpoint,
            ).observe(duration)
            return response
        except Exception as e:
            duration = time.perf_counter() - start_time
            HTTP_REQUESTS_TOTAL.labels(
                service=service_name,
                method=request.method,
                endpoint=endpoint,
                status_code="500",
            ).inc()
            HTTP_REQUEST_DURATION_SECONDS.labels(
                service=service_name,
                endpoint=endpoint,
            ).observe(duration)
            raise e

    @app.get("/metrics")
    async def metrics_endpoint() -> Response:
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
