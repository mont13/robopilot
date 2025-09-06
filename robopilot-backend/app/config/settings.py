from enum import Enum
from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings


class Environment(str, Enum):
    localdev = "localdev"
    dev = "dev"
    staging = "staging"
    prod = "prod"


class DatabaseSettings(BaseSettings):
    name: str = "fastapi_db"
    user: str = "postgres"
    password: str = "postgres"
    host: str = "localhost"
    port: int = 5432

    model_config = {"env_prefix": "POSTGRES_DB_"}

    @property
    def url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

    @property
    def async_url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class Settings(BaseSettings):
    environment: str = "localdev"
    service: str = "fast-api-docker-poetry"
    port: int = int("8009")
    host: str = "0.0.0.0"
    log_level: str = "debug"
    app_reload: bool = False
    db_retry_window_seconds: int = 60
    otel_service_name: str | None = None
    otel_exporter_otlp_endpoint: str | None = None

    model_config = {"env_prefix": ""}  # No prefix for environment variables

    ALLOWED_CORS_ORIGINS: set = ["*"]

    @property
    def code_branch(self) -> str:
        if self.environment == "prod":
            return "main"
        else:
            return "dev"

    @model_validator(mode="after")
    def adjust_db_retry_for_localdev(self) -> "Settings":
        if self.environment == "localdev" and self.db_retry_window_seconds == 60:
            self.db_retry_window_seconds = 1
        return self

    @property
    def is_local_dev(self) -> bool:
        return self.environment == "localdev"


@lru_cache(maxsize=1)
def get_settings():
    return Settings()


@lru_cache
def get_database_settings() -> DatabaseSettings:
    return DatabaseSettings()
