import json
import logging
import sys
from datetime import UTC, datetime


class JSONFormatter(logging.Formatter):
    """Structured JSON log formatter including timestamp, service, level, message, and trace context."""

    def __init__(self, service_name: str = "control-plane") -> None:
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        log_obj: dict[str, str | int | float | None] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "service": self.service_name,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if hasattr(record, "trace_id"):
            log_obj["trace_id"] = str(record.trace_id)
        if hasattr(record, "span_id"):
            log_obj["span_id"] = str(record.span_id)

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)


def setup_logging(service_name: str = "control-plane", log_level: str = "INFO") -> None:
    root_logger = logging.getLogger()
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger.setLevel(numeric_level)

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONFormatter(service_name=service_name))
    root_logger.addHandler(console_handler)
