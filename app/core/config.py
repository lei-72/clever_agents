"""Runtime configuration helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    """Application settings loaded from environment variables."""

    app_name: str = "Clever Agents API"
    app_version: str = "0.1.0"
    environment: str = "dev"
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"


def get_settings() -> Settings:
    """Build settings from env vars with safe defaults."""

    return Settings(
        app_name=os.getenv("APP_NAME", "Clever Agents API"),
        app_version=os.getenv("APP_VERSION", "0.1.0"),
        environment=os.getenv("APP_ENV", "dev"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        api_v1_prefix=os.getenv("API_V1_PREFIX", "/api/v1"),
    )
