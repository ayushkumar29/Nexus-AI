"""Health service encapsulating system diagnostics and health status."""

import logging
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import Settings
from app.schemas.health import HealthCheckResponse, HealthStatusEnum

logger = logging.getLogger("nexus_ai.health")


class HealthService:
    """Service for assessing system health and runtime metadata."""

    def __init__(self, settings: Settings, db: Session | None = None) -> None:
        self.settings = settings
        self.db = db

    def get_system_health(self) -> HealthCheckResponse:
        """Evaluate system health, test database connectivity, and assemble status payload."""
        api_status = HealthStatusEnum.HEALTHY
        details = "All services operational"

        if self.db is not None:
            try:
                self.db.execute(text("SELECT 1"))
            except SQLAlchemyError as exc:
                logger.warning(f"Health check detected database connectivity issue: {exc}")
                api_status = HealthStatusEnum.DEGRADED
                details = "Database connection unavailable"

        return HealthCheckResponse(
            application_name=self.settings.APP_NAME,
            api_status=api_status,
            application_version=self.settings.APP_VERSION,
            environment=self.settings.APP_ENV,
            details=details,
        )
