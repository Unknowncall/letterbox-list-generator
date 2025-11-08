"""Tests for TMDb service"""

from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest

from services.tmdb_service import TMDbService, get_tmdb_service


class TestTMDbServiceInit:
    """Tests for TMDbService initialization"""

    def test_init_with_provided_credentials(self):
        """Test initialization with provided API key and credentials"""
        with patch("services.tmdb_service.TMDbAPIs") as mock_tmdb:
            mock_instance = Mock()
            mock_tmdb.return_value = mock_instance

            service = TMDbService(api_key="test_key", v4_access_token="test_token", session_id="test_session")

            assert service.api_key == "test_key"
            assert service.v4_access_token == "test_token"
            assert service.session_id == "test_session"

    def test_init_with_env_vars(self, monkeypatch):
        """Test initialization with environment variables"""
        monkeypatch.setenv("TMDB_API_KEY", "env_key")
        monkeypatch.setenv("TMDB_V4_ACCESS_TOKEN", "env_token")
        monkeypatch.setenv("TMDB_SESSION_ID", "env_session")

        with patch("services.tmdb_service.TMDbAPIs") as mock_tmdb:
            mock_instance = Mock()
            mock_tmdb.return_value = mock_instance

            service = TMDbService()

            assert service.api_key == "env_key"
            assert service.v4_access_token == "env_token"
            assert service.session_id == "env_session"

    def test_init_without_api_key_raises_error(self, monkeypatch):
        """Test that initialization without API key raises ValueError"""
        monkeypatch.delenv("TMDB_API_KEY", raising=False)

        with pytest.raises(ValueError, match="TMDB_API_KEY is required"):
            TMDbService()

    def test_init_with_username_password_authentication(self):
        """Test initialization with username/password creates session_id"""
        with patch("services.tmdb_service.TMDbAPIs") as mock_tmdb:
            mock_instance = Mock()
            mock_instance.session_id = "auto_generated_session"
            mock_tmdb.return_value = mock_instance

            service = TMDbService(api_key="test_key", username="testuser", password="testpass")

            # Should have called authenticate
            mock_instance.authenticate.assert_called_once_with("testuser", "testpass")
            assert service.session_id == "auto_generated_session"


class TestSearchMovie:
    """Tests for search_movie method"""

    @patch("services.tmdb_service.time.sleep")  # Skip delays in tests
    def test_search_movie_with_results(self, mock_sleep):
        """Test successful movie search with results"""
        with patch("services.tmdb_service.TMDbAPIs") as mock_tmdb_class:
            mock_tmdb = Mock()
            mock_tmdb_class.return_value = mock_tmdb

            mock_movie = Mock()
            mock_movie.id = 238
            mock_movie.title = "The Godfather"
            mock_movie.release_date = datetime(1972, 3, 24)
            mock_movie.overview = "The aging patriarch..."

            mock_tmdb.movie_search.return_value = [mock_movie]

            service = TMDbService(api_key="test_key", session_id="test_session")
            result = service.search_movie("The Godfather", year=1972)

            assert result is not None
            assert result["id"] == 238
            assert result["title"] == "The Godfather"
            assert result["year"] == 1972
            assert "overview" in result

    @patch("services.tmdb_service.time.sleep")
    def test_search_movie_no_results(self, mock_sleep):
        """Test movie search with no results"""
        with patch("services.tmdb_service.TMDbAPIs") as mock_tmdb_class:
            mock_tmdb = Mock()
            mock_tmdb_class.return_value = mock_tmdb
            mock_tmdb.movie_search.return_value = []

            service = TMDbService(api_key="test_key", session_id="test_session")
            result = service.search_movie("Nonexistent Movie", year=2025)

            assert result is None

    @patch("services.tmdb_service.time.sleep")
    def test_search_movie_exception_handling(self, mock_sleep):
        """Test movie search with exception"""
        with patch("services.tmdb_service.TMDbAPIs") as mock_tmdb_class:
            mock_tmdb = Mock()
            mock_tmdb_class.return_value = mock_tmdb
            mock_tmdb.movie_search.side_effect = RuntimeError("API Error")

            service = TMDbService(api_key="test_key", session_id="test_session")
            result = service.search_movie("Test Movie")

            assert result is None


class TestGetOrCreateList:
    """Tests for get_or_create_list method"""

    def test_create_list_success(self):
        """Test successful list creation"""
        with patch("services.tmdb_service.TMDbAPIs") as mock_tmdb_class:
            mock_tmdb = Mock()
            mock_tmdb_class.return_value = mock_tmdb

            # Mock created_lists to return empty list (no existing lists)
            mock_tmdb.created_lists.return_value = []

            mock_list = Mock()
            mock_list.id = 12345
            mock_tmdb.create_list.return_value = mock_list

            service = TMDbService(api_key="test_key", session_id="test_session")
            list_id = service.get_or_create_list("My List", "Description")

            assert list_id == 12345
            mock_tmdb.create_list.assert_called_once()

    def test_create_list_without_session_id(self, monkeypatch):
        """Test list creation without session_id fails"""
        # Clear username/password env vars to prevent auto-authentication
        monkeypatch.delenv("TMDB_USERNAME", raising=False)
        monkeypatch.delenv("TMDB_PASSWORD", raising=False)

        with patch("services.tmdb_service.TMDbAPIs") as mock_tmdb_class:
            mock_tmdb = Mock()
            mock_tmdb_class.return_value = mock_tmdb

            service = TMDbService(api_key="test_key")  # No session_id
            list_id = service.get_or_create_list("My List", "Description")

            assert list_id is None


class TestAddMoviesToList:
    """Tests for add_movies_to_list method"""

    @patch("services.tmdb_service.time.sleep")
    def test_add_movies_success(self, mock_sleep):
        """Test successfully adding movies to list"""
        with patch("services.tmdb_service.TMDbAPIs") as mock_tmdb_class:
            mock_tmdb = Mock()
            mock_list = Mock()
            mock_tmdb.list.return_value = mock_list
            mock_tmdb_class.return_value = mock_tmdb

            service = TMDbService(api_key="test_key", session_id="test_session")
            result = service.add_movies_to_list(12345, [1, 2, 3])

            assert result is True
            mock_tmdb.list.assert_called_once_with(12345)
            mock_list.add_items.assert_called_once()

    def test_add_movies_without_session_id(self, monkeypatch):
        """Test adding movies without session_id fails"""
        # Clear username/password env vars to prevent auto-authentication
        monkeypatch.delenv("TMDB_USERNAME", raising=False)
        monkeypatch.delenv("TMDB_PASSWORD", raising=False)

        with patch("services.tmdb_service.TMDbAPIs") as mock_tmdb_class:
            mock_tmdb = Mock()
            mock_tmdb_class.return_value = mock_tmdb

            service = TMDbService(api_key="test_key")  # No session_id
            result = service.add_movies_to_list(12345, [1, 2, 3])

            assert result is False

    @patch("services.tmdb_service.time.sleep")
    def test_add_movies_empty_list(self, mock_sleep):
        """Test adding empty list of movies"""
        with patch("services.tmdb_service.TMDbAPIs") as mock_tmdb_class:
            mock_tmdb = Mock()
            mock_tmdb_class.return_value = mock_tmdb

            service = TMDbService(api_key="test_key", session_id="test_session")
            result = service.add_movies_to_list(12345, [])

            assert result is True  # Empty list is not an error


class TestClearList:
    """Tests for clear_list method"""

    @patch("services.tmdb_service.time.sleep")
    def test_clear_list_success(self, mock_sleep):
        """Test successfully clearing a list"""
        with patch("services.tmdb_service.TMDbAPIs") as mock_tmdb_class:
            mock_tmdb = Mock()
            mock_list = Mock()
            mock_tmdb.list.return_value = mock_list
            mock_tmdb_class.return_value = mock_tmdb

            service = TMDbService(api_key="test_key", session_id="test_session")
            result = service.clear_list(12345)

            assert result is True
            mock_tmdb.list.assert_called_once_with(12345)
            mock_list.clear.assert_called_once()

    def test_clear_list_without_session_id(self, monkeypatch):
        """Test clearing list without session_id fails"""
        # Clear username/password env vars to prevent auto-authentication
        monkeypatch.delenv("TMDB_USERNAME", raising=False)
        monkeypatch.delenv("TMDB_PASSWORD", raising=False)

        with patch("services.tmdb_service.TMDbAPIs") as mock_tmdb_class:
            mock_tmdb = Mock()
            mock_tmdb_class.return_value = mock_tmdb

            service = TMDbService(api_key="test_key")  # No session_id
            result = service.clear_list(12345)

            assert result is False

    @patch("services.tmdb_service.time.sleep")
    def test_clear_list_exception_returns_true(self, mock_sleep):
        """Test clear list exception handling (returns True to continue)"""
        with patch("services.tmdb_service.TMDbAPIs") as mock_tmdb_class:
            mock_tmdb = Mock()
            mock_tmdb.list.side_effect = RuntimeError("API Error")
            mock_tmdb_class.return_value = mock_tmdb

            service = TMDbService(api_key="test_key", session_id="test_session")
            result = service.clear_list(12345)

            # Returns True to allow continuation even if clear fails
            assert result is True


class TestDeleteList:
    """Tests for delete_list method"""

    @patch("services.tmdb_service.time.sleep")
    def test_delete_list_success(self, mock_sleep):
        """Test successfully deleting a list"""
        with patch("services.tmdb_service.TMDbAPIs") as mock_tmdb_class:
            mock_tmdb = Mock()
            mock_list = Mock()
            mock_tmdb.list.return_value = mock_list
            mock_tmdb_class.return_value = mock_tmdb

            service = TMDbService(api_key="test_key", session_id="test_session")
            result = service.delete_list(12345)

            assert result is True
            mock_list.delete.assert_called_once()


class TestUpdateListWithMovies:
    """Tests for update_list_with_movies method"""

    @patch("services.tmdb_service.time.sleep")
    def test_update_list_success(self, mock_sleep):
        """Test successful list update with movies"""
        with patch("services.tmdb_service.TMDbAPIs") as mock_tmdb_class:
            mock_tmdb = Mock()
            mock_list = Mock()
            mock_tmdb.list.return_value = mock_list
            mock_tmdb_class.return_value = mock_tmdb

            # Mock search results
            mock_movie1 = Mock()
            mock_movie1.id = 1
            mock_movie1.title = "Movie 1"
            mock_movie1.release_date = datetime(2020, 1, 1)
            mock_movie1.overview = "Overview 1"

            mock_movie2 = Mock()
            mock_movie2.id = 2
            mock_movie2.title = "Movie 2"
            mock_movie2.release_date = datetime(2021, 1, 1)
            mock_movie2.overview = "Overview 2"

            mock_tmdb.movie_search.side_effect = [[mock_movie1], [mock_movie2]]

            service = TMDbService(api_key="test_key", session_id="test_session")

            films = [{"title": "Movie 1", "year": 2020}, {"title": "Movie 2", "year": 2021}]

            result = service.update_list_with_movies(12345, films, clear_first=True)

            assert result["success"] is True
            assert result["matched"] == 2
            assert result["added"] == 2


class TestGetTMDbService:
    """Tests for get_tmdb_service helper function"""

    def test_get_tmdb_service_with_env_vars(self, monkeypatch):
        """Test getting TMDb service with valid environment variables"""
        monkeypatch.setenv("TMDB_API_KEY", "test_key")
        monkeypatch.setenv("TMDB_V4_ACCESS_TOKEN", "test_token")

        with patch("services.tmdb_service.TMDbAPIs") as mock_tmdb:
            mock_instance = Mock()
            mock_tmdb.return_value = mock_instance

            service = get_tmdb_service()

            assert service is not None
            assert isinstance(service, TMDbService)

    def test_get_tmdb_service_no_api_key(self, monkeypatch):
        """Test getting TMDb service without API key"""
        monkeypatch.delenv("TMDB_API_KEY", raising=False)

        service = get_tmdb_service()

        # Should return None if no API key
        assert service is None
