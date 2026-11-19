"""Unit and integration tests for /api/v1/health endpoint and error handling."""

from fastapi import status
from fastapi.testclient import TestClient


def test_health_check_success(client: TestClient) -> None:
    """Verify GET /api/v1/health returns 200 and expected schema keys."""
    response = client.get("/api/v1/health")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["application_name"] == "Nexus AI Test"
    assert data["api_status"] == "healthy"
    assert data["application_version"] == "0.1.0-test"
    assert data["environment"] == "testing"
    assert "timestamp" in data
    assert data["details"] == "All services operational"


def test_cors_headers(client: TestClient) -> None:
    """Verify CORS headers are returned for allowed origin."""
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_404_centralized_error_handling(client: TestClient) -> None:
    """Verify centralized exception handler formats 404 responses appropriately."""
    response = client.get("/api/v1/nonexistent-route")
    assert response.status_code == status.HTTP_404_NOT_FOUND

    data = response.json()
    assert data["success"] is False
    assert "error" in data
    assert data["error"]["status_code"] == 404
    assert "Not Found" in data["error"]["message"]
