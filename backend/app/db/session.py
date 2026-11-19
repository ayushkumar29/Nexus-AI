"""Database session management, connection pooling, and base ORM model."""

import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import QueuePool, NullPool

from app.core.config import get_settings
from app.core.exceptions import AppException

logger = logging.getLogger("nexus_ai.database")


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy ORM models."""
    pass


def create_db_engine():
    """Create SQLAlchemy engine with appropriate connection pooling based on dialect."""
    settings = get_settings()
    db_url = settings.sync_database_url

    # Check if SQLite (local dev/test) or PostgreSQL
    if db_url.startswith("sqlite"):
        engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False},
            poolclass=NullPool,
        )
    else:
        # PostgreSQL with robust QueuePool pooling
        engine = create_engine(
            db_url,
            poolclass=QueuePool,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            pool_recycle=settings.DB_POOL_RECYCLE,
            pool_pre_ping=True,  # Test connections transparently before checkout
        )
    return engine


engine = create_db_engine()

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """Reusable FastAPI database session dependency.

    Handles transaction scope, automatic closing, and wraps SQLAlchemy operational
    failures in application-specific exceptions.
    """
    db = SessionLocal()
    try:
        yield db
    except OperationalError as exc:
        logger.error(f"Database operational connectivity failure: {exc}")
        db.rollback()
        raise AppException(
            message="Database connection error. Service temporarily unavailable.",
            status_code=503,
            details=str(exc.orig) if hasattr(exc, "orig") else str(exc),
        )
    except SQLAlchemyError as exc:
        logger.error(f"Database query failure: {exc}")
        db.rollback()
        raise AppException(
            message="Database transaction error occurred.",
            status_code=500,
        )
    finally:
        db.close()
