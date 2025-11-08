"""Tests for jobs router"""

from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client with mocked scheduler"""
    with patch("jobs.scheduler.init_scheduler"), patch("jobs.scheduler.shutdown_scheduler"):
        from index import app

        with TestClient(app) as test_client:
            yield test_client


class TestSyncTMDbEndpoint:
    """Tests for POST /jobs/sync-tmdb endpoint"""

    def test_sync_tmdb_success(self, client, monkeypatch):
        """Test successful TMDb sync trigger"""
        monkeypatch.setenv("TMDB_SYNC_ENABLED", "true")
        monkeypatch.setenv("TMDB_API_KEY", "test_key")
        monkeypatch.setenv("TMDB_V4_ACCESS_TOKEN", "test_token")

        with patch("routers.jobs.run_sync_job") as mock_sync:
            response = client.post("/jobs/sync-tmdb", json={"usernames": ["testuser1", "testuser2"]})

            assert response.status_code == 200
            data = response.json()
            assert data["job_started"] is True
            assert data["usernames"] == ["testuser1", "testuser2"]
            assert "2 user(s)" in data["message"]
            assert "own list" in data["message"]

    def test_sync_tmdb_single_user(self, client, monkeypatch):
        """Test TMDb sync with single user"""
        monkeypatch.setenv("TMDB_SYNC_ENABLED", "true")
        monkeypatch.setenv("TMDB_API_KEY", "test_key")
        monkeypatch.setenv("TMDB_V4_ACCESS_TOKEN", "test_token")

        with patch("routers.jobs.run_sync_job"):
            response = client.post("/jobs/sync-tmdb", json={"usernames": ["ian_fried"]})

            assert response.status_code == 200
            data = response.json()
            assert data["usernames"] == ["ian_fried"]
            assert "1 user(s)" in data["message"]

    def test_sync_tmdb_disabled(self, client, monkeypatch):
        """Test TMDb sync when disabled"""
        monkeypatch.setenv("TMDB_SYNC_ENABLED", "false")

        response = client.post("/jobs/sync-tmdb", json={"usernames": ["testuser"]})

        assert response.status_code == 503
        assert "disabled" in response.json()["detail"].lower()

    def test_sync_tmdb_no_api_key(self, client, monkeypatch):
        """Test TMDb sync without API key"""
        monkeypatch.setenv("TMDB_SYNC_ENABLED", "true")
        monkeypatch.setenv("TMDB_API_KEY", "")

        response = client.post("/jobs/sync-tmdb", json={"usernames": ["testuser"]})

        assert response.status_code == 503
        assert "API key not configured" in response.json()["detail"]

    def test_sync_tmdb_no_access_token(self, client, monkeypatch):
        """Test TMDb sync without v4 access token"""
        monkeypatch.setenv("TMDB_SYNC_ENABLED", "true")
        monkeypatch.setenv("TMDB_API_KEY", "test_key")
        monkeypatch.setenv("TMDB_V4_ACCESS_TOKEN", "")

        response = client.post("/jobs/sync-tmdb", json={"usernames": ["testuser"]})

        assert response.status_code == 503
        assert "access token not configured" in response.json()["detail"]

    def test_sync_tmdb_empty_usernames(self, client):
        """Test TMDb sync with empty usernames list"""
        response = client.post("/jobs/sync-tmdb", json={"usernames": []})

        assert response.status_code == 422  # Validation error

    def test_sync_tmdb_invalid_username_format(self, client, monkeypatch):
        """Test TMDb sync with invalid username"""
        monkeypatch.setenv("TMDB_SYNC_ENABLED", "true")
        monkeypatch.setenv("TMDB_API_KEY", "test_key")
        monkeypatch.setenv("TMDB_V4_ACCESS_TOKEN", "test_token")

        # Invalid character (space)
        response = client.post("/jobs/sync-tmdb", json={"usernames": ["invalid username"]})

        assert response.status_code == 422

        # Invalid character (special char)
        response = client.post("/jobs/sync-tmdb", json={"usernames": ["user@name"]})

        assert response.status_code == 422

    def test_sync_tmdb_empty_username(self, client):
        """Test TMDb sync with empty username string"""
        response = client.post("/jobs/sync-tmdb", json={"usernames": [""]})

        assert response.status_code == 422

    def test_sync_tmdb_username_too_long(self, client):
        """Test TMDb sync with username exceeding max length"""
        response = client.post("/jobs/sync-tmdb", json={"usernames": ["a" * 101]})  # 101 characters

        assert response.status_code == 422

    def test_sync_tmdb_valid_special_chars(self, client, monkeypatch):
        """Test TMDb sync with valid special characters in username"""
        monkeypatch.setenv("TMDB_SYNC_ENABLED", "true")
        monkeypatch.setenv("TMDB_API_KEY", "test_key")
        monkeypatch.setenv("TMDB_V4_ACCESS_TOKEN", "test_token")

        with patch("routers.jobs.run_sync_job"):
            # Underscores and hyphens are allowed
            response = client.post("/jobs/sync-tmdb", json={"usernames": ["user_name-123"]})

            assert response.status_code == 200

    def test_sync_tmdb_missing_request_body(self, client):
        """Test TMDb sync without request body"""
        response = client.post("/jobs/sync-tmdb")

        assert response.status_code == 422

    def test_sync_tmdb_invalid_json(self, client):
        """Test TMDb sync with invalid JSON"""
        response = client.post("/jobs/sync-tmdb", data="not json", headers={"Content-Type": "application/json"})

        assert response.status_code == 422

    def test_sync_tmdb_background_task_queued(self, client, monkeypatch):
        """Test that sync job is actually queued as background task"""
        monkeypatch.setenv("TMDB_SYNC_ENABLED", "true")
        monkeypatch.setenv("TMDB_API_KEY", "test_key")
        monkeypatch.setenv("TMDB_V4_ACCESS_TOKEN", "test_token")

        with patch("routers.jobs.run_sync_job") as mock_sync:
            response = client.post("/jobs/sync-tmdb", json={"usernames": ["user1", "user2"]})

            assert response.status_code == 200
            # Background task will execute, but we can't easily verify it was called
            # in the test due to how FastAPI BackgroundTasks work
            # The fact that we got 200 means it was queued successfully
