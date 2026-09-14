from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    app_env: str
    database_url: str
    log_level: str
    cors_origins: tuple[str, ...]


def load_settings() -> Settings:
    origins = tuple(
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    )

    return Settings(
        app_env=os.getenv("APP_ENV", "development"),
        database_url=os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://hirein:hirein@localhost:5432/hirein",
        ),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        cors_origins=origins,
    )
