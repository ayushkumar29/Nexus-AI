"""Application configuration loaded from environment variables."""

import os
from functools import lru_cache
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings schema."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = Field(default="Nexus AI", description="Name of the application")
    APP_ENV: str = Field(default="development", description="Current runtime environment")
    APP_VERSION: str = Field(default="0.1.0", description="Application semantic version")
    DEBUG: bool = Field(default=False, description="Debug mode flag")

    HOST: str = Field(default="127.0.0.1", description="Backend host address")
    PORT: int = Field(default=8000, description="Backend port number")

    # Raw CORS origins from env, supports comma-separated string or list
    CORS_ORIGINS: Union[str, List[str]] = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        description="Allowed CORS origins",
    )

    # Database Configuration
    POSTGRES_SERVER: str = Field(default="localhost", description="PostgreSQL host server")
    POSTGRES_PORT: int = Field(default=5432, description="PostgreSQL port")
    POSTGRES_USER: str = Field(default="postgres", description="PostgreSQL username")
    POSTGRES_PASSWORD: str = Field(default="postgres", description="PostgreSQL password")
    POSTGRES_DB: str = Field(default="nexus_ai", description="PostgreSQL database name")
    DATABASE_URL: str | None = Field(
        default=None,
        description="Complete database connection string (if provided, overrides POSTGRES_* properties)",
    )

    # Database Pooling Configuration
    DB_POOL_SIZE: int = Field(default=10, description="SQLAlchemy connection pool size")
    DB_MAX_OVERFLOW: int = Field(default=20, description="SQLAlchemy connection pool max overflow")
    DB_POOL_TIMEOUT: int = Field(default=30, description="SQLAlchemy pool timeout in seconds")
    DB_POOL_RECYCLE: int = Field(default=1800, description="SQLAlchemy pool recycle in seconds")

    # Authentication & Security
    SECRET_KEY: str = Field(
        default="dev-insecure-nexus-ai-super-secret-key-change-in-production-min32chars",
        description="Secret key for JWT generation and verification",
    )
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, description="Access token expiration in minutes")

    # Document Processing & Storage (M3.1)
    STORAGE_DIR: str = Field(default="./storage/documents", description="Directory to store ingested documents")
    MAX_UPLOAD_SIZE_BYTES: int = Field(default=20 * 1024 * 1024, description="Max upload size (20 MB)")
    CHUNK_SIZE_TOKENS: int = Field(default=700, description="Target token count per chunk")
    CHUNK_OVERLAP_TOKENS: int = Field(default=100, description="Target overlap token count between chunks")

    @property
    def sync_database_url(self) -> str:
        """Resolve synchronous database connection URL."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @field_validator("CORS_ORIGINS", mode="after")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v


@lru_cache()
def get_settings() -> Settings:
    """Singleton getter for application settings."""
    return Settings()
