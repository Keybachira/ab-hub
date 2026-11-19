"""Application core engine — orchestration helpers."""

from __future__ import annotations

from ab_hub.core.config import Settings, get_settings
from ab_hub.core.logger import get_logger

logger = get_logger(__name__)


class ApplicationEngine:
    """Lightweight application context holder."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.settings.ensure_data_dir()

    def ready(self) -> bool:
        """Basic readiness check."""
        return self.settings.db_path.parent.exists()
