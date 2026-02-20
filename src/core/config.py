"""
Application configuration using Pydantic Settings.

All configuration is loaded from environment variables with sensible defaults
for development. Production deployments should set all values explicitly.
"""

from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Attributes are grouped by concern for easier navigation.
    All secrets and sensitive values MUST be provided via environment.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # -------------------------------------------------------------------------
    # Application Settings
    # -------------------------------------------------------------------------
    app_name: str = "FastAPI REST API Starter"
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8080"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # -------------------------------------------------------------------------
    # Server Settings
    # -------------------------------------------------------------------------
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1

    # -------------------------------------------------------------------------
    # Database Settings
    # -------------------------------------------------------------------------
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/fastapi_starter"
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_echo: bool = False

    # -------------------------------------------------------------------------
    # Redis Settings
    # -------------------------------------------------------------------------
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl: int = 300  # 5 minutes

    # -------------------------------------------------------------------------
    # JWT Settings
    # -------------------------------------------------------------------------
    jwt_secret_key: str = "your-super-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # -------------------------------------------------------------------------
    # Google APIs
    # -------------------------------------------------------------------------
    google_maps_api_key: str

    # -------------------------------------------------------------------------
    # Rate Limiting Settings
    # -------------------------------------------------------------------------
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60
    auth_rate_limit_per_minute: int = 10

    # -------------------------------------------------------------------------
    # Security Settings
    # -------------------------------------------------------------------------
    bcrypt_rounds: int = 12

    # -------------------------------------------------------------------------
    # Logging Settings
    # -------------------------------------------------------------------------
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_format: Literal["json", "text"] = "text"

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings.

    Uses lru_cache to ensure settings are only loaded once.
    """
    return Settings()


# Global settings instance
settings = get_settings()
