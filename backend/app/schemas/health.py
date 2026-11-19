"""Pydantic schemas for health check and system status."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class HealthStatusEnum(str, Enum):
    """Health status enumeration."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class HealthCheckResponse(BaseModel):
    """Schema for health check response."""

    application_name: str = Field(
        ...,
        description="Name of the application",
        examples=["Nexus AI"],
    )
    api_status: HealthStatusEnum = Field(
        default=HealthStatusEnum.HEALTHY,
        description="Operational status of the API",
        examples=["healthy"],
    )
    application_version: str = Field(
        ...,
        description="Semantic version of the application",
        examples=["0.1.0"],
    )
    environment: str = Field(
        ...,
        description="Current runtime environment",
        examples=["development"],
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of the health check in UTC ISO format",
    )
    details: Optional[str] = Field(
        default=None,
        description="Optional diagnostic information or message",
    )
