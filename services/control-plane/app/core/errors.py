from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    loc: list[str] | None = None
    msg: str
    type: str | None = None


class ErrorResponseContract(BaseModel):
    code: str = Field(description="Machine-readable error code")
    message: str = Field(description="Human-readable description of error")
    details: list[Any] | dict[str, Any] | None = Field(
        default=None, description="Additional context or validation errors"
    )
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    request_id: str | None = Field(default=None, description="Unique trace/request correlation ID")


class AppError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Any = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    error_payload = ErrorResponseContract(
        code=exc.code,
        message=exc.message,
        details=exc.details,
        request_id=request_id,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload.model_dump(),
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    code = f"HTTP_{exc.status_code}"
    message = str(exc.detail) if exc.detail else "HTTP Exception"
    error_payload = ErrorResponseContract(
        code=code,
        message=message,
        request_id=request_id,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload.model_dump(),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    error_payload = ErrorResponseContract(
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected server error occurred.",
        details={"error_type": type(exc).__name__},
        request_id=request_id,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_payload.model_dump(),
    )
