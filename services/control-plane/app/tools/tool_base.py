import asyncio
import logging
import time
import uuid
from datetime import UTC, datetime
from typing import Any, TypeVar

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ToolResult[T](BaseModel):
    success: bool = True
    data: T | None = None
    error: str | None = None
    duration_ms: float = 0.0
    truncated: bool = False
    audit_id: str = Field(default_factory=lambda: f"audit_{uuid.uuid4().hex[:10]}")
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class BaseTool:
    name: str = "base_tool"
    description: str = "Base tool description"
    timeout_seconds: float = 5.0
    max_output_items: int = 100

    async def run(self, **kwargs: Any) -> ToolResult[Any]:
        start_time = time.perf_counter()
        audit_id = f"audit_{uuid.uuid4().hex[:10]}"

        try:
            # Enforce execution timeout
            result_data = await asyncio.wait_for(
                self.execute(**kwargs), timeout=self.timeout_seconds
            )
            duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

            # Enforce output-size bounding
            truncated = False
            if isinstance(result_data, list) and len(result_data) > self.max_output_items:
                result_data = result_data[: self.max_output_items]
                truncated = True

            return ToolResult(
                success=True,
                data=result_data,
                duration_ms=duration_ms,
                truncated=truncated,
                audit_id=audit_id,
            )
        except TimeoutError:
            duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            return ToolResult(
                success=False,
                error=f"Tool '{self.name}' timed out after {self.timeout_seconds}s",
                duration_ms=duration_ms,
                audit_id=audit_id,
            )
        except Exception as e:
            duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            logger.error(f"Tool '{self.name}' execution failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                duration_ms=duration_ms,
                audit_id=audit_id,
            )

    async def execute(self, **kwargs: Any) -> Any:
        raise NotImplementedError
