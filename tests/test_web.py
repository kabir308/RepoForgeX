"""Tests for the web API endpoints."""

import json
from unittest.mock import MagicMock, patch

import pytest

from repoforgex.web import app


@pytest.fixture
def client():
    """Create test client for the Flask app."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestBasicEndpoints:
    """Tests for basic web API endpoints."""

    def test_index(self, client):
        """Test the index endpoint."""
        response = client.get("/")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["name"] == "RepoForgeX"
        assert data["version"] == "0.4.0"
        assert data["status"] == "running"
        assert "features" in data
        assert "NEOPlayer Integration" in data["features"]

    def test_health(self, client):
        """Test the health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["status"] == "healthy"


class TestHealthCheckAPI:
    """Tests for health check API endpoint."""

    def test_health_check_missing_files(self, client):
        """Test health check with missing files in request."""
        response = client.post("/api/v1/health-check", json={})
        assert response.status_code == 400

        data = json.loads(response.data)
        assert "error" in data
        assert "files" in data["error"]

    def test_health_check_success(self, client):
        """Test health check with valid files."""
        response = client.post(
            "/api/v1/health-check",
            json={
                "files": ["README.md", "LICENSE", ".gitignore"],
                "repository": "test-repo",
                "developer": "alice",
            },
        )
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "score" in data
        assert "percentage" in data
        assert "rating" in data
        assert "recommendations" in data

    def test_health_check_excellent_score(self, client):
        """Test health check with excellent score."""
        excellent_files = [
            "README.md",
            "LICENSE",
            ".gitignore",
            "CONTRIBUTING.md",
            "CODE_OF_CONDUCT.md",
            "SECURITY.md",
            ".github/workflows/ci.yml",
            "tests/test_main.py",
        ]

        response = client.post(
            "/api/v1/health-check",
            json={
                "files": excellent_files,
                "repository": "excellent-repo",
                "developer": "bob",
            },
        )
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["score"] == 100
        assert data["percentage"] == 100.0
        assert data["rating"] == "Excellent"


class TestAnalyticsAPI:
    """Tests for analytics API endpoint."""

    def test_analytics_endpoint(self, client):
        """Test the analytics endpoint."""
        response = client.get("/api/v1/analytics")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "summary" in data
        assert "recommendations" in data


class TestEventsAPI:
    """Tests for events API endpoints."""

    def test_get_events(self, client):
        """Test getting all events."""
        response = client.get("/api/v1/events")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "summary" in data
        assert "events" in data
        assert "total_events" in data["summary"]

    def test_get_developer_events(self, client):
        """Test getting events for a specific developer."""
        response = client.get("/api/v1/events/developer/alice")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["developer"] == "alice"
        assert "total_xp" in data
        assert "event_count" in data
        assert "events" in data


class TestTemplateGenerationAPI:
    """Tests for template generation API endpoint."""

    def test_generate_all_templates(self, client):
        """Test generating all templates."""
        response = client.post(
            "/api/v1/templates/generate", json={"type": "all", "repo_type": "api"}
        )
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "issue_template" in data
        assert "pr_template" in data
        assert "security_policy" in data
        assert "code_of_conduct" in data

    def test_generate_issue_template(self, client):
        """Test generating only issue template."""
        response = client.post(
            "/api/v1/templates/generate", json={"type": "issue", "repo_type": "api"}
        )
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "issue_template" in data
        assert "pr_template" not in data

    def test_generate_pr_template(self, client):
        """Test generating only PR template."""
        response = client.post(
            "/api/v1/templates/generate", json={"type": "pr"}
        )
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "pr_template" in data
        assert "issue_template" not in data

    def test_generate_security_policy(self, client):
        """Test generating only security policy."""
        response = client.post(
            "/api/v1/templates/generate", json={"type": "security"}
        )
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "security_policy" in data

    def test_generate_code_of_conduct(self, client):
        """Test generating only code of conduct."""
        response = client.post(
            "/api/v1/templates/generate", json={"type": "conduct"}
        )
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "code_of_conduct" in data


class TestCICDWebhook:
    """Tests for CI/CD webhook endpoint."""

    def test_cicd_webhook_push_event(self, client):
        """Test CI/CD webhook with push event."""
        webhook_payload = {
            "ref": "refs/heads/main",
            "repository": {"name": "test-repo"},
            "pusher": {"name": "alice"},
        }

        response = client.post(
            "/api/v1/cicd/webhook",
            json=webhook_payload,
            headers={"X-GitHub-Event": "push"},
        )
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["status"] == "processed"
        assert data["event"] == "push"

    def test_cicd_webhook_repository_created(self, client):
        """Test CI/CD webhook with repository creation."""
        webhook_payload = {
            "action": "created",
            "repository": {"name": "new-repo"},
            "sender": {"login": "bob"},
        }

        response = client.post(
            "/api/v1/cicd/webhook",
            json=webhook_payload,
            headers={"X-GitHub-Event": "repository"},
        )
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["status"] == "processed"
        assert data["event"] == "repository"

    def test_cicd_webhook_unknown_event(self, client):
        """Test CI/CD webhook with unknown event type."""
        response = client.post(
            "/api/v1/cicd/webhook",
            json={"test": "data"},
            headers={"X-GitHub-Event": "issues"},
        )
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["status"] == "processed"
        assert data["event"] == "issues"
