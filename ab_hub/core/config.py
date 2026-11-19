"""Application configuration using pydantic-settings."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """AB-hub runtime settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="AB_HUB_",
        extra="ignore",
    )

    # GitHub
    github_token: str | None = Field(default=None, alias="GITHUB_TOKEN")
    github_api_base: str = "https://api.github.com"
    github_api_version: str = "2022-11-28"

    # Database
    db_path: Path = Field(default=Path("./data/ab_hub.db"))

    # Runtime
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    max_concurrency: int = Field(default=5, ge=1, le=20)
    request_timeout: float = 30.0
    max_retries: int = 3
    per_page: int = 100

    # Paths
    data_dir: Path = Field(default=Path("./data"))

    def ensure_data_dir(self) -> None:
        """Create data directory if it does not exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)


def get_settings() -> Settings:
    """Return a cached settings instance."""
    return Settings()
