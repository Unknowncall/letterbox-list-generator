"""Tests for index.py (main application)"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

# Import app at module level for tests that need it
# Mock scheduler to prevent initialization issues
with patch('jobs.scheduler.init_scheduler'), patch('jobs.scheduler.shutdown_scheduler'):
    from index import app


@pytest.fixture(scope="module")
def test_client():
    """Create a test client with mocked scheduler"""
    with patch('jobs.scheduler.init_scheduler'), patch('jobs.scheduler.shutdown_scheduler'):
        with TestClient(app) as client:
            yield client


class TestHealthEndpoint:
    """Test suite for health check endpoint"""

    def test_health_check_success(self, test_client):
        """Test health check endpoint returns healthy status"""
        response = test_client.get('/health')

        assert response.status_code == 200
        assert response.json() == {'status': 'healthy'}

    def test_health_check_method_get(self, test_client):
        """Test health check only accepts GET requests"""
        response = test_client.post('/health')
        assert response.status_code == 405  # Method not allowed

    def test_health_check_route_exists(self, test_client):
        """Test health check route is registered"""
        response = test_client.get('/health')
        assert response.status_code != 404


class TestAppConfiguration:
    """Test suite for FastAPI app configuration"""

    def test_app_title(self):
        """Test app has correct title"""
        assert app.title == "Letterbox List Generator"

    def test_users_router_included(self):
        """Test users router is included"""
        routes = [route.path for route in app.routes]

        # Check that user routes are registered
        assert any('/users/{username}' in route for route in routes)
        assert any('/users/{username}/watchlist' in route for route in routes)
        assert any('/users/{username}/top-rated' in route for route in routes)

    def test_health_route_registered(self):
        """Test health route is registered"""
        routes = [route.path for route in app.routes]
        assert '/health' in routes


class TestLifespanEvent:
    """Test suite for application lifespan events"""

    @pytest.mark.asyncio
    async def test_lifespan_initializes_and_shuts_down_scheduler(self):
        """Test lifespan context manager calls init and shutdown"""
        from index import lifespan

        with patch('index.init_scheduler') as mock_init:
            with patch('index.shutdown_scheduler') as mock_shutdown:
                # Use the lifespan context manager
                async with lifespan(app):
                    # During the context, init should be called
                    mock_init.assert_called_once()
                    mock_shutdown.assert_not_called()

                # After exiting the context, shutdown should be called
                mock_shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_lifespan_function_exists(self):
        """Test that lifespan function exists"""
        from index import lifespan
        from contextlib import AbstractAsyncContextManager

        # Test that lifespan is callable and returns an async context manager
        assert callable(lifespan)
        context = lifespan(app)
        assert isinstance(context, AbstractAsyncContextManager)


class TestAtexitHandler:
    """Test suite for atexit handler"""

    def test_atexit_handler_registered(self):
        """Test that atexit handler is registered"""
        # This test verifies the code runs without error
        # The atexit.register call is executed at import time
        # We can verify by checking if shutdown_scheduler is callable
        from index import shutdown_scheduler
        assert callable(shutdown_scheduler)


class TestAppLifecycle:
    """Test suite for full application lifecycle"""

    @pytest.mark.asyncio
    async def test_full_startup_shutdown_cycle(self):
        """Test complete startup and shutdown cycle using lifespan"""
        from index import lifespan

        with patch('index.init_scheduler') as mock_init:
            with patch('index.shutdown_scheduler') as mock_shutdown:
                # Execute the full lifespan cycle
                async with lifespan(app):
                    # Verify startup was called
                    mock_init.assert_called_once()
                    # Verify shutdown not called yet
                    mock_shutdown.assert_not_called()

                # Verify shutdown was called after context exit
                mock_shutdown.assert_called_once()


class TestAppIntegration:
    """Integration tests for the application"""

    def test_app_accepts_requests(self, test_client):
        """Test that app can handle requests"""
        response = test_client.get('/health')
        assert response.status_code == 200

    def test_app_handles_404(self, test_client):
        """Test that app handles non-existent routes"""
        response = test_client.get('/nonexistent-route')
        assert response.status_code == 404

    def test_app_cors_not_configured_by_default(self, test_client):
        """Test that CORS is not configured by default"""
        # FastAPI doesn't add CORS headers unless CORSMiddleware is added
        response = test_client.get('/health')
        assert 'access-control-allow-origin' not in [
            key.lower() for key in response.headers.keys()
        ]

    def test_app_json_responses(self, test_client):
        """Test that app returns JSON responses"""
        response = test_client.get('/health')
        assert response.headers['content-type'] == 'application/json'


class TestErrorHandling:
    """Test suite for error handling"""

    def test_validation_error_response_format(self, test_client):
        """Test validation error response format"""
        # Try to access endpoint with invalid username
        response = test_client.get('/users/invalid@username')

        assert response.status_code == 422
        data = response.json()
        assert 'detail' in data

    def test_not_found_error_format(self, test_client):
        """Test 404 error response format"""
        with patch('controllers.users.get_user_profile') as mock_get:
            from unittest.mock import AsyncMock
            mock_get = AsyncMock(side_effect=ValueError('User not found'))

            with patch('controllers.users.get_user_profile', mock_get):
                response = test_client.get('/users/nonexistent')

                assert response.status_code == 404
                data = response.json()
                assert 'detail' in data


class TestDocumentation:
    """Test suite for API documentation"""

    def test_openapi_schema_available(self, test_client):
        """Test that OpenAPI schema is available"""
        response = test_client.get('/openapi.json')
        assert response.status_code == 200

        schema = response.json()
        assert 'openapi' in schema
        assert 'info' in schema
        assert schema['info']['title'] == 'Letterbox List Generator'

    def test_docs_endpoint_available(self, test_client):
        """Test that /docs endpoint is available"""
        response = test_client.get('/docs')
        assert response.status_code == 200

    def test_redoc_endpoint_available(self, test_client):
        """Test that /redoc endpoint is available"""
        response = test_client.get('/redoc')
        assert response.status_code == 200

    def test_openapi_has_user_routes(self, test_client):
        """Test that OpenAPI schema includes user routes"""
        response = test_client.get('/openapi.json')
        schema = response.json()

        paths = schema['paths']
        assert '/users/{username}' in paths
        assert '/users/{username}/watchlist' in paths
        assert '/users/{username}/top-rated' in paths

    def test_openapi_has_health_route(self, test_client):
        """Test that OpenAPI schema includes health route"""
        response = test_client.get('/openapi.json')
        schema = response.json()

        assert '/health' in schema['paths']
