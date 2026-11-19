"""Pytest configuration and shared fixtures for Nexus AI backend tests."""

import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings, get_settings
from app.db.session import Base, get_db
from app.main import create_application

# Use in-memory SQLite with StaticPool for fast, isolated, clean tests
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db() -> Generator[None, None, None]:
    """Create all database tables before test session and drop them after."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provide a transactional database session per test, rolling back on teardown."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def test_settings() -> Settings:
    """Fixture providing isolated test settings without production secrets."""
    return Settings(
        APP_NAME="Nexus AI Test",
        APP_ENV="testing",
        APP_VERSION="0.1.0-test",
        DEBUG=True,
        CORS_ORIGINS=["http://localhost:3000"],
        SECRET_KEY="test-insecure-secret-key-for-testing-purposes-only",
        ALGORITHM="HS256",
        ACCESS_TOKEN_EXPIRE_MINUTES=15,
        DATABASE_URL=TEST_DATABASE_URL,
    )


@pytest.fixture
def client(test_settings: Settings, db_session: Session) -> Generator[TestClient, None, None]:
    """Fixture providing a FastAPI TestClient with test settings and DB session overridden."""
    app = create_application(settings=test_settings)

    # Override get_settings and get_db dependencies
    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_db] = lambda: db_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
