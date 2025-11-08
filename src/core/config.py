"""Application configuration using Pydantic Settings."""

from pathlib import Path
from typing import Optional

from pydantic import Field, HttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # GigaChat API Configuration
    gigachat_auth_key: SecretStr = Field(
        ...,
        description="Authorization key (base64 encoded Client ID:Client Secret)",
    )
    gigachat_oauth_url: HttpUrl = Field(
        default="https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
        description="OAuth endpoint for getting access token",
    )
    gigachat_base_url: HttpUrl = Field(
        default="https://gigachat.devices.sberbank.ru/api/v1",
        description="GigaChat API base URL",
    )
    gigachat_scope: str = Field(
        default="GIGACHAT_API_PERS",
        description="OAuth scope for personal access",
    )
    gigachat_model: str = Field(
        default="GigaChat",
        description="GigaChat model to use (GigaChat, GigaChat-Plus, GigaChat-Pro)",
    )

    # Data Paths
    tg_fetcher_data_path: Path = Field(
        default=Path("../python-tg/data"),
        description="Path to tg_fetcher data directory",
    )
    output_path: Path = Field(
        default=Path("./output"),
        description="Path to output directory for analysis results",
    )

    # Redis Configuration (for event subscriptions)
    redis_url: str = Field(
        default="redis://localhost:6379",
        description="Redis connection URL for PubSub events",
    )
    redis_password: Optional[str] = Field(
        default=None,
        description="Redis password (if authentication is enabled)",
    )

    # Analysis Settings
    window_size: int = Field(
        default=30,
        description="Default window size for message analysis",
    )

    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )

    # Observability Stack
    loki_url: Optional[HttpUrl] = Field(
        default=None,
        description="Loki URL for centralized logging",
    )
    prometheus_pushgateway_url: Optional[HttpUrl] = Field(
        default=None,
        description="Prometheus Pushgateway URL for metrics",
    )

    # API Client Settings
    http_timeout: int = Field(
        default=60,
        description="HTTP request timeout in seconds",
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts for failed requests",
    )
    retry_delay: float = Field(
        default=1.0,
        description="Initial delay between retries in seconds (exponential backoff)",
    )


# Global settings instance
settings = Settings()
