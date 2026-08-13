import asyncio
import json
import logging
import random

from fastapi import HTTPException, status
from pydantic import BaseModel

from services.demo.common.metrics import (
    FAULT_INJECTIONS_TOTAL,
    SCENARIO_FAULT_ACTIVE,
)

logger = logging.getLogger(__name__)


class FaultConfig(BaseModel):
    enabled: bool = False
    latency_ms: float = 0.0
    error_rate: float = 0.0
    error_status_code: int = 500
    error_message: str = "Simulated fault injection error"
    pool_exhaustion: bool = False
    timeout: bool = False
    scenario_id: str = "manual"
    fault_kind: str = "generic"


class FaultInjector:
    def __init__(self, service_name: str) -> None:
        self.service_name = service_name
        self._faults: dict[str, FaultConfig] = {}

    def set_fault(self, endpoint: str, config: FaultConfig) -> None:
        previous = self._faults.get(endpoint)
        if previous:
            SCENARIO_FAULT_ACTIVE.labels(
                service=self.service_name,
                scenario_id=previous.scenario_id,
                fault_kind=previous.fault_kind,
            ).set(0)
        self._faults[endpoint] = config
        SCENARIO_FAULT_ACTIVE.labels(
            service=self.service_name,
            scenario_id=config.scenario_id,
            fault_kind=config.fault_kind,
        ).set(1 if config.enabled else 0)
        logger.warning(
            json.dumps(
                {
                    "event": "scenario_fault_configured",
                    "service": self.service_name,
                    "endpoint": endpoint,
                    "scenario_id": config.scenario_id,
                    "fault_kind": config.fault_kind,
                    "enabled": config.enabled,
                }
            )
        )

    def clear_fault(self, endpoint: str | None = None) -> None:
        if endpoint:
            previous = self._faults.pop(endpoint, None)
            if previous:
                SCENARIO_FAULT_ACTIVE.labels(
                    service=self.service_name,
                    scenario_id=previous.scenario_id,
                    fault_kind=previous.fault_kind,
                ).set(0)
        else:
            for previous in self._faults.values():
                SCENARIO_FAULT_ACTIVE.labels(
                    service=self.service_name,
                    scenario_id=previous.scenario_id,
                    fault_kind=previous.fault_kind,
                ).set(0)
            self._faults.clear()

    def get_fault(self, endpoint: str) -> FaultConfig | None:
        return self._faults.get(endpoint)

    async def maybe_inject(self, endpoint: str) -> None:
        fault = self._faults.get(endpoint)
        if not fault or not fault.enabled:
            return

        FAULT_INJECTIONS_TOTAL.labels(
            service=self.service_name,
            scenario_id=fault.scenario_id,
            fault_kind=fault.fault_kind,
        ).inc()
        logger.warning(
            json.dumps(
                {
                    "event": "scenario_fault_injected",
                    "service": self.service_name,
                    "endpoint": endpoint,
                    "scenario_id": fault.scenario_id,
                    "fault_kind": fault.fault_kind,
                }
            )
        )

        # Latency injection
        if fault.latency_ms > 0:
            await asyncio.sleep(fault.latency_ms / 1000.0)

        # Timeout simulation
        if fault.timeout:
            await asyncio.sleep(10.0)
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=f"[{self.service_name}] Simulated upstream request timeout",
            )

        # Error rate injection
        if fault.error_rate > 0 and random.random() < fault.error_rate:
            raise HTTPException(
                status_code=fault.error_status_code,
                detail=f"[{self.service_name}] {fault.error_message}",
            )


# Global registry of fault injectors per service
fault_injectors: dict[str, FaultInjector] = {}


def get_fault_injector(service_name: str) -> FaultInjector:
    if service_name not in fault_injectors:
        fault_injectors[service_name] = FaultInjector(service_name)
    return fault_injectors[service_name]
