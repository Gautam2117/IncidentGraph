import time
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from app.api.v1 import (
    audit_api,
    auth_api,
    deployments,
    evals,
    health,
    incidents,
    investigations,
    knowledge,
    mcp_api,
    model_providers,
    observability,
    postmortem_api,
    remediations,
    scenarios,
    topology,
)
from app.core.config import settings
from app.core.errors import (
    AppError,
    app_error_handler,
    generic_exception_handler,
    http_exception_handler,
)
from app.core.logger import setup_logging
from app.observability.tracer import setup_telemetry

HTTP_REQUESTS = Counter(
    "incidentgraph_http_requests_total",
    "HTTP requests handled by the control plane",
    ["method", "path", "status"],
)
HTTP_REQUEST_DURATION = Histogram(
    "incidentgraph_http_request_duration_seconds",
    "Control-plane HTTP request duration",
    ["method", "path"],
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Application startup
    setup_logging(service_name=settings.OTEL_SERVICE_NAME, log_level=settings.LOG_LEVEL)
    setup_telemetry(app, service_name=settings.OTEL_SERVICE_NAME)
    yield
    # Application shutdown cleanup


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# Request ID correlation middleware
@app.middleware("http")
async def add_request_id_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    started = time.perf_counter()
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    request.state.request_id = request_id
    response: Response = await call_next(request)
    response.headers["x-request-id"] = request_id
    route = request.scope.get("route")
    path = str(getattr(route, "path", request.url.path))
    HTTP_REQUESTS.labels(request.method, path, str(response.status_code)).inc()
    HTTP_REQUEST_DURATION.labels(request.method, path).observe(time.perf_counter() - started)
    return response


@app.get("/metrics", include_in_schema=False)
async def prometheus_metrics() -> Response:
    """Expose the process registry for Prometheus scraping."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# CORS Configuration
if settings.ALLOWED_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Exception Handlers
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(audit_api.router, prefix="/api/v1")
app.include_router(auth_api.router, prefix="/api/v1")
app.include_router(mcp_api.router, prefix="/api/v1")
app.include_router(observability.router, prefix="/api/v1")
app.include_router(evals.router, prefix="/api/v1")
app.include_router(incidents.router, prefix="/api/v1")
app.include_router(investigations.router, prefix="/api/v1")
app.include_router(knowledge.router, prefix="/api/v1")
app.include_router(remediations.router, prefix="/api/v1")
app.include_router(postmortem_api.router, prefix="/api/v1")
app.include_router(deployments.router, prefix="/api/v1")
app.include_router(model_providers.router, prefix="/api/v1")
app.include_router(scenarios.router, prefix="/api/v1")
app.include_router(topology.router, prefix="/api/v1")
# Root aliases for standard health probes
app.include_router(health.router)
