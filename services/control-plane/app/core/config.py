from typing import Any

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        validate_default=True,
    )

    # Project metadata
    PROJECT_NAME: str = "IncidentGraph Control Plane"
    VERSION: str = "0.1.0"
    GIT_SHA: str = Field(default="unknown")
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=True)
    LOG_LEVEL: str = Field(default="INFO")

    # API Server
    API_HOST: str = Field(default="0.0.0.0")  # nosec B104
    API_PORT: int = Field(default=8000)
    SECRET_KEY: str = Field(default="", min_length=32)
    ALLOWED_ORIGINS: list[str] | str = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"]
    )

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            v_str = v.strip()
            if v_str.startswith("[") and v_str.endswith("]"):
                import json

                try:
                    parsed = json.loads(v_str)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed if str(item).strip()]
                except Exception:
                    pass
            return [origin.strip() for origin in v_str.split(",") if origin.strip()]
        if isinstance(v, list):
            return [str(origin).strip() for origin in v if str(origin).strip()]
        return ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Database
    POSTGRES_SERVER: str = Field(default="localhost")
    POSTGRES_PORT: int = Field(default=5432)
    POSTGRES_USER: str = Field(default="incidentgraph")
    POSTGRES_PASSWORD: str = Field(default="incidentgraph_secret")
    POSTGRES_DB: str = Field(default="incidentgraph_db")
    DATABASE_URL: str | None = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str | None, info: Any) -> str:
        if isinstance(v, str) and v:
            return v
        data = info.data
        return str(
            PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=data.get("POSTGRES_USER", "incidentgraph"),
                password=data.get("POSTGRES_PASSWORD", "incidentgraph_secret"),
                host=data.get("POSTGRES_SERVER", "localhost"),
                port=data.get("POSTGRES_PORT", 5432),
                path=data.get("POSTGRES_DB", "incidentgraph_db"),
            )
        )

    # Redis
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_PASSWORD: str | None = Field(default=None)
    REDIS_URL: str = Field(default="redis://localhost:6379/0")

    # Breakable demo application. Docker overrides these with service DNS names.
    DEMO_GATEWAY_URL: str = Field(default="http://localhost:8001")
    DEMO_AUTH_URL: str = Field(default="http://localhost:8002")
    DEMO_ORDERS_URL: str = Field(default="http://localhost:8003")
    DEMO_PAYMENTS_URL: str = Field(default="http://localhost:8004")
    DEMO_INVENTORY_URL: str = Field(default="http://localhost:8005")
    DEMO_NOTIFICATIONS_URL: str = Field(default="http://localhost:8006")
    WEBHOOK_SIGNING_SECRET: str | None = Field(default=None, min_length=16)

    # AI Provider Config
    PRIMARY_LLM_PROVIDER: str = Field(default="openai")
    OPENAI_API_KEY: str | None = Field(default=None)
    OPENAI_MODEL: str = Field(default="gpt-4o")
    GEMINI_API_KEY: str | None = Field(default=None)
    GEMINI_MODEL: str = Field(default="gemini-2.0-flash")
    OLLAMA_URL: str = Field(default="http://localhost:11434")
    OLLAMA_MODEL: str = Field(default="llama3.2")
    LLM_FALLBACK_PROVIDER: str = Field(default="none")
    LLM_INPUT_COST_PER_MILLION_USD: float = Field(default=0.0, ge=0.0)
    LLM_OUTPUT_COST_PER_MILLION_USD: float = Field(default=0.0, ge=0.0)
    ENABLE_OFFLINE_MODEL_ADAPTER: bool = Field(default=False)
    EMBEDDING_PROVIDER: str = Field(default="openai")
    EMBEDDING_MODEL: str = Field(default="text-embedding-3-small")

    # OpenTelemetry
    OTEL_EXPORTER_OTLP_ENDPOINT: str = Field(default="http://localhost:4317")
    OTEL_SERVICE_NAME: str = Field(default="control-plane")
    PROMETHEUS_URL: str = Field(default="http://localhost:9090")
    LOKI_URL: str = Field(default="http://localhost:3100")
    TEMPO_URL: str = Field(default="http://localhost:3200")


settings = Settings()
