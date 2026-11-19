"""Health router exposing operational health endpoints."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.schemas.health import HealthCheckResponse
from app.services.health_service import HealthService

router = APIRouter(prefix="", tags=["Health"])


def get_health_service(
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
) -> HealthService:
    """Dependency provider for HealthService with DB session injection."""
    return HealthService(settings=settings, db=db)


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="API Health Status",
    description="Returns current status, application name, version, environment, and DB health.",
)
async def check_health(
    health_service: HealthService = Depends(get_health_service),
) -> HealthCheckResponse:
    """Check and return health status of the API."""
    return health_service.get_system_health()
