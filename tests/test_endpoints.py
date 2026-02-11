"""
Tests for the Meeting Minutes API endpoints.

Run with: pytest tests/ -v
"""
from fastapi.testclient import TestClient
from src.main import app

# TestClient lets you test FastAPI endpoints without starting a server
client = TestClient(app)


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_returns_200(self):
        """Health check should always return 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_healthy_status(self):
        """Health response should contain status: healthy."""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_contains_version(self):
        """Health response should include the API version."""
        response = client.get("/health")
        data = response.json()
        assert "version" in data


class TestGenerateMinutesEndpoint:
    """Tests for the /generate-minutes endpoint."""

    def test_rejects_empty_notes(self):
        """Should return 422 for empty input."""
        response = client.post(
            "/generate-minutes",
            json={"raw_notes": ""}
        )
        assert response.status_code == 422

    def test_rejects_too_short_notes(self):
        """Should reject notes shorter than 50 characters."""
        response = client.post(
            "/generate-minutes",
            json={"raw_notes": "Short text"}
        )
        assert response.status_code == 422

    def test_rejects_missing_field(self):
        """Should reject requests without raw_notes field."""
        response = client.post(
            "/generate-minutes",
            json={}
        )
        assert response.status_code == 422
