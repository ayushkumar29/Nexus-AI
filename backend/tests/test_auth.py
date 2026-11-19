"""Automated test suite for M2.1 Authentication & User Management.

Covers:
- Successful registration
- Duplicate email registration
- Invalid email format
- Successful login
- Incorrect password
- Protected endpoint access (/api/v1/auth/me)
- Expired JWT token handling
- Invalid / malformed JWT token handling
"""

from datetime import timedelta
from fastapi import status
from fastapi.testclient import TestClient

from app.core.security import create_access_token


def test_successful_registration(client: TestClient) -> None:
    """Test user registration returns 201 Created and user profile."""
    payload = {
        "full_name": "Alice Smith",
        "email": "alice@example.com",
        "password": "SecurePassword123!",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()
    assert data["email"] == "alice@example.com"
    assert data["full_name"] == "Alice Smith"
    assert data["is_active"] is True
    assert "id" in data
    assert "hashed_password" not in data
    assert "password" not in data


def test_duplicate_email_registration(client: TestClient) -> None:
    """Test registering with an existing email returns 409 Conflict."""
    payload = {
        "full_name": "Bob Jones",
        "email": "bob@example.com",
        "password": "SecurePassword123!",
    }
    # First registration
    res1 = client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == status.HTTP_201_CREATED

    # Second registration with same email (even with mixed case)
    payload_dup = {
        "full_name": "Bob Jones Duplicate",
        "email": "BOB@example.com",
        "password": "AnotherPassword456!",
    }
    res2 = client.post("/api/v1/auth/register", json=payload_dup)
    assert res2.status_code == status.HTTP_409_CONFLICT
    data = res2.json()
    assert data["success"] is False
    assert "already exists" in data["error"]["message"]


def test_invalid_email_registration(client: TestClient) -> None:
    """Test registration with malformed email triggers validation error (422)."""
    payload = {
        "full_name": "Invalid Email User",
        "email": "not-an-email",
        "password": "SecurePassword123!",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()
    assert data["success"] is False
    assert data["error"]["status_code"] == 422


def test_successful_login(client: TestClient) -> None:
    """Test successful login returns JWT access token."""
    # Register user first
    reg_payload = {
        "full_name": "Charlie Brown",
        "email": "charlie@example.com",
        "password": "Password789!",
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    # Login
    login_payload = {
        "email": "charlie@example.com",
        "password": "Password789!",
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0


def test_incorrect_password_login(client: TestClient) -> None:
    """Test login with wrong password returns 401 Unauthorized."""
    reg_payload = {
        "full_name": "Dave Miller",
        "email": "dave@example.com",
        "password": "CorrectPassword123!",
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    login_payload = {
        "email": "dave@example.com",
        "password": "WrongPassword!",
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert data["success"] is False
    assert "Invalid email or password" in data["error"]["message"]


def test_protected_endpoint_access_success(client: TestClient) -> None:
    """Test accessing /api/v1/auth/me with valid Bearer token succeeds."""
    # Register and login
    reg_payload = {
        "full_name": "Eve Adams",
        "email": "eve@example.com",
        "password": "EveSecurePassword1!",
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "eve@example.com", "password": "EveSecurePassword1!"},
    )
    token = login_res.json()["access_token"]

    # Access /api/v1/auth/me
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == "eve@example.com"
    assert data["full_name"] == "Eve Adams"
    assert "id" in data


def test_protected_endpoint_without_token(client: TestClient) -> None:
    """Test accessing /api/v1/auth/me without token returns 401 Unauthorized."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert data["success"] is False


def test_protected_endpoint_invalid_jwt(client: TestClient) -> None:
    """Test accessing /api/v1/auth/me with corrupted/invalid token returns 401."""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not-a-valid-token-string"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert data["success"] is False
    assert "Could not validate credentials" in data["error"]["message"]


def test_protected_endpoint_expired_jwt(client: TestClient) -> None:
    """Test accessing /api/v1/auth/me with an expired JWT returns 401 with expiration detail."""
    # Register user
    reg_payload = {
        "full_name": "Frank Castle",
        "email": "frank@example.com",
        "password": "FrankPassword1!",
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    user_id = reg_res.json()["id"]

    # Create expired token (-10 minutes)
    expired_token = create_access_token(
        subject=user_id,
        expires_delta=timedelta(minutes=-10),
    )

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert data["success"] is False
    assert "Token has expired" in data["error"]["message"]
