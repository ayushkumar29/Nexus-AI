"""Pydantic schemas for authentication and user profiles."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """Base schema for user attributes."""

    email: EmailStr = Field(..., description="Unique email address", examples=["user@example.com"])
    full_name: str = Field(..., min_length=1, max_length=255, description="User's full name", examples=["Jane Doe"])


class UserRegisterRequest(UserBase):
    """Payload schema for user registration."""

    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="User password (min 8 characters)",
        examples=["SecurePassw0rd!"],
    )


class UserLoginRequest(BaseModel):
    """Payload schema for user authentication."""

    email: EmailStr = Field(..., description="User's registered email", examples=["user@example.com"])
    password: str = Field(..., description="User password", examples=["SecurePassw0rd!"])


class UserResponse(UserBase):
    """Public user profile schema returned to clients."""

    id: int = Field(..., description="Unique user identifier", examples=[1])
    is_active: bool = Field(..., description="Whether user account is active", examples=[True])
    created_at: datetime = Field(..., description="Account creation timestamp in UTC")
    updated_at: datetime = Field(..., description="Account last update timestamp in UTC")

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Schema for OAuth2 token responses."""

    access_token: str = Field(..., description="Signed JWT bearer access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token lifespan in seconds", examples=[3600])
