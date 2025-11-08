"""Tests for TMDb service"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from services.tmdb_service import TMDbService, get_tmdb_service


class TestTMDbServiceInit:
    """Tests for TMDbService initialization"""

    def test_init_with_provided_credentials(self):
        """Test initialization with provided API key and token"""
        with patch('services.tmdb_service.TMDbAPIs') as mock_tmdb:
            service = TMDbService(api_key='test_key', v4_access_token='test_token')

            assert service.api_key == 'test_key'
            assert service.v4_access_token == 'test_token'
            mock_tmdb.assert_called_once_with('test_key', v4_access_token='test_token')

    def test_init_with_env_vars(self, monkeypatch):
        """Test initialization with environment variables"""
        monkeypatch.setenv('TMDB_API_KEY', 'env_key')
        monkeypatch.setenv('TMDB_V4_ACCESS_TOKEN', 'env_token')

        with patch('services.tmdb_service.TMDbAPIs') as mock_tmdb:
            service = TMDbService()

            assert service.api_key == 'env_key'
            assert service.v4_access_token == 'env_token'
            mock_tmdb.assert_called_once_with('env_key', v4_access_token='env_token')

    def test_init_without_api_key_raises_error(self):
        """Test that initialization without API key raises ValueError"""
        with pytest.raises(ValueError, match="TMDB_API_KEY is required"):
            TMDbService()


class TestSearchMovie:
    """Tests for search_movie method"""

    def test_search_movie_with_results(self):
        """Test successful movie search with results"""
        with patch('services.tmdb_service.TMDbAPIs') as mock_tmdb_class:
            # Setup mock
            mock_tmdb = Mock()
            mock_tmdb_class.return_value = mock_tmdb

            mock_movie = Mock()
            mock_movie.id = 238
            mock_movie.title = "The Godfather"
            mock_movie.release_date = "1972-03-24"
            mock_movie.overview = "The aging patriarch of an organized crime dynasty..."

            mock_tmdb.search_movie.return_value = [mock_movie]

            # Test
            service = TMDbService(api_key='test_key')
            result = service.search_movie("The Godfather", year=1972)

            # Assertions
            assert result is not None
            assert result['id'] == 238
            assert result['title'] == "The Godfather"
            assert result['year'] == 1972
            assert 'overview' in result
            mock_tmdb.search_movie.assert_called_once_with("The Godfather", year=1972)

    def test_search_movie_without_year(self):
        """Test movie search without year"""
        with patch('services.tmdb_service.TMDbAPIs') as mock_tmdb_class:
            mock_tmdb = Mock()
            mock_tmdb_class.return_value = mock_tmdb

            mock_movie = Mock()
            mock_movie.id = 680
            mock_movie.title = "Pulp Fiction"
            mock_movie.release_date = "1994-10-14"
            mock_movie.overview = "A burger-loving hit man..."

            mock_tmdb.search_movie.return_value = [mock_movie]

            service = TMDbService(api_key='test_key')
            result = service.search_movie("Pulp Fiction")

            assert result is not None
            assert result['id'] == 680
            mock_tmdb.search_movie.assert_called_once_with("Pulp Fiction", year=None)

    def test_search_movie_no_results(self):
        """Test movie search with no results"""
        with patch('services.tmdb_service.TMDbAPIs') as mock_tmdb_class:
            mock_tmdb = Mock()
            mock_tmdb_class.return_value = mock_tmdb
            mock_tmdb.search_movie.return_value = []

            service = TMDbService(api_key='test_key')
            result = service.search_movie("Nonexistent Movie", year=2025)

            assert result is None

    def test_search_movie_without_release_date(self):
        """Test movie search when movie has no release date"""
        with patch('services.tmdb_service.TMDbAPIs') as mock_tmdb_class:
            mock_tmdb = Mock()
            mock_tmdb_class.return_value = mock_tmdb

            mock_movie = Mock()
            mock_movie.id = 999
            mock_movie.title = "Unknown Release"
            mock_movie.release_date = None
            mock_movie.overview = "A mysterious film..."

            mock_tmdb.search_movie.return_value = [mock_movie]

            service = TMDbService(api_key='test_key')
            result = service.search_movie("Unknown Release")

            assert result is not None
            assert result['year'] is None

    def test_search_movie_exception_handling(self):
        """Test movie search handles exceptions gracefully"""
        with patch('services.tmdb_service.TMDbAPIs') as mock_tmdb_class:
            mock_tmdb = Mock()
            mock_tmdb_class.return_value = mock_tmdb
            mock_tmdb.search_movie.side_effect = Exception("API Error")

            service = TMDbService(api_key='test_key')
            result = service.search_movie("Error Movie")

            assert result is None


class TestGetOrCreateList:
    """Tests for get_or_create_list method"""

    def test_create_list_success(self):
        """Test successful list creation"""
        with patch('services.tmdb_service.TMDbAPIs') as mock_tmdb_class:
            mock_tmdb = Mock()
            mock_tmdb_class.return_value = mock_tmdb
            mock_tmdb.create_list.return_value = {'id': 12345, 'success': True}

            service = TMDbService(api_key='test_key', v4_access_token='test_token')
            result = service.get_or_create_list("My List", "Description")

            assert result == 12345
            mock_tmdb.create_list.assert_called_once()

    def test_create_list_without_v4_token(self):
        """Test list creation without v4 access token"""
        with patch('services.tmdb_service.TMDbAPIs'):
            service = TMDbService(api_key='test_key')
            result = service.get_or_create_list("My List")

            assert result is None

    def test_create_list_failure(self):
        """Test list creation failure"""
        with patch('services.tmdb_service.TMDbAPIs') as mock_tmdb_class:
            mock_tmdb = Mock()
            mock_tmdb_class.return_value = mock_tmdb
            mock_tmdb.create_list.return_value = {'success': False}

            service = TMDbService(api_key='test_key', v4_access_token='test_token')
            result = service.get_or_create_list("My List")

            assert result is None

    def test_create_list_exception_handling(self):
        """Test list creation handles exceptions"""
        with patch('services.tmdb_service.TMDbAPIs') as mock_tmdb_class:
            mock_tmdb = Mock()
            mock_tmdb_class.return_value = mock_tmdb
            mock_tmdb.create_list.side_effect = Exception("API Error")

            service = TMDbService(api_key='test_key', v4_access_token='test_token')
            result = service.get_or_create_list("My List")

            assert result is None


class TestAddMoviesToList:
    """Tests for add_movies_to_list method"""

    def test_add_movies_success(self):
        """Test successfully adding movies to list"""
        with patch('services.tmdb_service.TMDbAPIs') as mock_tmdb_class:
            mock_tmdb = Mock()
            mock_tmdb_class.return_value = mock_tmdb
            mock_tmdb.add_items_to_list.return_value = {'success': True}

            service = TMDbService(api_key='test_key', v4_access_token='test_token')
            result = service.add_movies_to_list(12345, [238, 680, 155])

            assert result is True
            mock_tmdb.add_items_to_list.assert_called_once()
            call_args = mock_tmdb.add_items_to_list.call_args
            assert call_args[0][0] == 12345
            assert len(call_args[0][1]) == 3

    def test_add_movies_without_v4_token(self):
        """Test adding movies without v4 token"""
        with patch('services.tmdb_service.TMDbAPIs'):
            service = TMDbService(api_key='test_key')
            result = service.add_movies_to_list(12345, [238])

            assert result is False

    def test_add_movies_empty_list(self):
        """Test adding empty list of movies"""
        with patch('services.tmdb_service.TMDbAPIs') as mock_tmdb_class:
            mock_tmdb = Mock()
            mock_tmdb_class.return_value = mock_tmdb

            service = TMDbService(api_key='test_key', v4_access_token='test_token')
            result = service.add_movies_to_list(12345, [])

            assert result is True  # Not an error
            mock_tmdb.add_items_to_list.assert_not_called()

    def test_add_movies_failure(self):
        """Test adding movies failure"""
        with patch('services.tmdb_service.TMDbAPIs') as mock_tmdb_class:
            mock_tmdb = Mock()
            mock_tmdb_class.return_value = mock_tmdb
            mock_tmdb.add_items_to_list.return_value = {'success': False}

            service = TMDbService(api_key='test_key', v4_access_token='test_token')
            result = service.add_movies_to_list(12345, [238])

            assert result is False

    def test_add_movies_exception_handling(self):
        """Test adding movies handles exceptions"""
        with patch('services.tmdb_service.TMDbAPIs') as mock_tmdb_class:
            mock_tmdb = Mock()
            mock_tmdb_class.return_value = mock_tmdb
            mock_tmdb.add_items_to_list.side_effect = Exception("API Error")

            service = TMDbService(api_key='test_key', v4_access_token='test_token')
            result = service.add_movies_to_list(12345, [238])

            assert result is False


class TestClearList:
    """Tests for clear_list method"""

    def test_clear_list_success(self):
        """Test successfully clearing a list"""
        with patch('services.tmdb_service.TMDbAPIs') as mock_tmdb_class:
            mock_tmdb = Mock()
            mock_tmdb_class.return_value = mock_tmdb
            mock_tmdb.clear_list.return_value = {'success': True}

            service = TMDbService(api_key='test_key', v4_access_token='test_token')
            result = service.clear_list(12345)

            assert result is True
            mock_tmdb.clear_list.assert_called_once_with(12345)

    def test_clear_list_without_v4_token(self):
        """Test clearing list without v4 token"""
        with patch('services.tmdb_service.TMDbAPIs'):
            service = TMDbService(api_key='test_key')
            result = service.clear_list(12345)

            assert result is False

    def test_clear_list_failure(self):
        """Test clearing list failure"""
        with patch('services.tmdb_service.TMDbAPIs') as mock_tmdb_class:
            mock_tmdb = Mock()
            mock_tmdb_class.return_value = mock_tmdb
            mock_tmdb.clear_list.return_value = {'success': False}

            service = TMDbService(api_key='test_key', v4_access_token='test_token')
            result = service.clear_list(12345)

            assert result is False

    def test_clear_list_exception_handling(self):
        """Test clearing list handles exceptions"""
        with patch('services.tmdb_service.TMDbAPIs') as mock_tmdb_class:
            mock_tmdb = Mock()
            mock_tmdb_class.return_value = mock_tmdb
            mock_tmdb.clear_list.side_effect = Exception("API Error")

            service = TMDbService(api_key='test_key', v4_access_token='test_token')
            result = service.clear_list(12345)

            assert result is False


class TestUpdateListWithMovies:
    """Tests for update_list_with_movies method"""

    def test_update_list_success(self):
        """Test successfully updating list with movies"""
        with patch('services.tmdb_service.TMDbAPIs') as mock_tmdb_class:
            mock_tmdb = Mock()
            mock_tmdb_class.return_value = mock_tmdb

            # Setup mocks
            mock_tmdb.clear_list.return_value = {'success': True}
            mock_tmdb.add_items_to_list.return_value = {'success': True}

            mock_movie1 = Mock()
            mock_movie1.id = 238
            mock_movie1.title = "The Godfather"
            mock_movie1.release_date = "1972-03-24"
            mock_movie1.overview = "..."

            mock_movie2 = Mock()
            mock_movie2.id = 680
            mock_movie2.title = "Pulp Fiction"
            mock_movie2.release_date = "1994-10-14"
            mock_movie2.overview = "..."

            mock_tmdb.search_movie.side_effect = [
                [mock_movie1],
                [mock_movie2]
            ]

            # Test
            service = TMDbService(api_key='test_key', v4_access_token='test_token')
            films = [
                {'title': 'The Godfather', 'year': 1972, 'rating': 5.0},
                {'title': 'Pulp Fiction', 'year': 1994, 'rating': 5.0}
            ]

            result = service.update_list_with_movies(12345, films, clear_first=True)

            # Assertions
            assert result['success'] is True
            assert result['total_films'] == 2
            assert result['matched'] == 2
            assert result['added'] == 2
            assert len(result['not_matched']) == 0

    def test_update_list_without_clearing(self):
        """Test updating list without clearing first"""
        with patch('services.tmdb_service.TMDbAPIs') as mock_tmdb_class:
            mock_tmdb = Mock()
            mock_tmdb_class.return_value = mock_tmdb
            mock_tmdb.add_items_to_list.return_value = {'success': True}

            mock_movie = Mock()
            mock_movie.id = 238
            mock_movie.title = "The Godfather"
            mock_movie.release_date = "1972-03-24"
            mock_movie.overview = "..."

            mock_tmdb.search_movie.return_value = [mock_movie]

            service = TMDbService(api_key='test_key', v4_access_token='test_token')
            films = [{'title': 'The Godfather', 'year': 1972}]

            result = service.update_list_with_movies(12345, films, clear_first=False)

            assert result['success'] is True
            mock_tmdb.clear_list.assert_not_called()

    def test_update_list_with_unmatched_films(self):
        """Test updating list with some films not found on TMDb"""
        with patch('services.tmdb_service.TMDbAPIs') as mock_tmdb_class:
            mock_tmdb = Mock()
            mock_tmdb_class.return_value = mock_tmdb
            mock_tmdb.clear_list.return_value = {'success': True}
            mock_tmdb.add_items_to_list.return_value = {'success': True}

            mock_movie = Mock()
            mock_movie.id = 238
            mock_movie.title = "The Godfather"
            mock_movie.release_date = "1972-03-24"
            mock_movie.overview = "..."

            # First search succeeds, second fails
            mock_tmdb.search_movie.side_effect = [
                [mock_movie],
                []  # No results for second movie
            ]

            service = TMDbService(api_key='test_key', v4_access_token='test_token')
            films = [
                {'title': 'The Godfather', 'year': 1972},
                {'title': 'Unknown Movie', 'year': 2025}
            ]

            result = service.update_list_with_movies(12345, films)

            assert result['success'] is True
            assert result['matched'] == 1
            assert result['added'] == 1
            assert len(result['not_matched']) == 1
            assert 'Unknown Movie (2025)' in result['not_matched']

    def test_update_list_empty_films(self):
        """Test updating list with empty films list"""
        with patch('services.tmdb_service.TMDbAPIs') as mock_tmdb_class:
            mock_tmdb = Mock()
            mock_tmdb_class.return_value = mock_tmdb

            service = TMDbService(api_key='test_key', v4_access_token='test_token')
            result = service.update_list_with_movies(12345, [])

            assert result['success'] is True
            assert result['total_films'] == 0
            mock_tmdb.clear_list.assert_not_called()

    def test_update_list_clear_failure(self):
        """Test updating list when clear operation fails"""
        with patch('services.tmdb_service.TMDbAPIs') as mock_tmdb_class:
            mock_tmdb = Mock()
            mock_tmdb_class.return_value = mock_tmdb
            mock_tmdb.clear_list.return_value = {'success': False}

            service = TMDbService(api_key='test_key', v4_access_token='test_token')
            films = [{'title': 'The Godfather', 'year': 1972}]

            result = service.update_list_with_movies(12345, films, clear_first=True)

            assert result['success'] is False

    def test_update_list_add_failure(self):
        """Test updating list when add operation fails"""
        with patch('services.tmdb_service.TMDbAPIs') as mock_tmdb_class:
            mock_tmdb = Mock()
            mock_tmdb_class.return_value = mock_tmdb
            mock_tmdb.clear_list.return_value = {'success': True}
            mock_tmdb.add_items_to_list.return_value = {'success': False}

            mock_movie = Mock()
            mock_movie.id = 238
            mock_movie.title = "The Godfather"
            mock_movie.release_date = "1972-03-24"
            mock_movie.overview = "..."

            mock_tmdb.search_movie.return_value = [mock_movie]

            service = TMDbService(api_key='test_key', v4_access_token='test_token')
            films = [{'title': 'The Godfather', 'year': 1972}]

            result = service.update_list_with_movies(12345, films)

            assert result['success'] is False
            assert result['matched'] == 1
            assert result['added'] == 0

    def test_update_list_no_matches(self):
        """Test updating list when no films match on TMDb"""
        with patch('services.tmdb_service.TMDbAPIs') as mock_tmdb_class:
            mock_tmdb = Mock()
            mock_tmdb_class.return_value = mock_tmdb
            mock_tmdb.clear_list.return_value = {'success': True}
            mock_tmdb.search_movie.return_value = []

            service = TMDbService(api_key='test_key', v4_access_token='test_token')
            films = [{'title': 'Unknown Movie', 'year': 2025}]

            result = service.update_list_with_movies(12345, films)

            assert result['success'] is True  # Not an error
            assert result['matched'] == 0
            assert result['added'] == 0
            mock_tmdb.add_items_to_list.assert_not_called()

    def test_update_list_film_without_title(self):
        """Test updating list with film missing title"""
        with patch('services.tmdb_service.TMDbAPIs') as mock_tmdb_class:
            mock_tmdb = Mock()
            mock_tmdb_class.return_value = mock_tmdb
            mock_tmdb.clear_list.return_value = {'success': True}

            service = TMDbService(api_key='test_key', v4_access_token='test_token')
            films = [
                {'year': 1972},  # Missing title
                {'title': None, 'year': 1994}  # Null title
            ]

            result = service.update_list_with_movies(12345, films)

            # Should skip films without titles
            assert result['success'] is True
            assert result['matched'] == 0
            mock_tmdb.search_movie.assert_not_called()


class TestGetTMDbService:
    """Tests for get_tmdb_service factory function"""

    def test_get_tmdb_service_success(self, monkeypatch):
        """Test successful service creation"""
        monkeypatch.setenv('TMDB_API_KEY', 'test_key')

        with patch('services.tmdb_service.TMDbAPIs'):
            service = get_tmdb_service()
            assert service is not None
            assert isinstance(service, TMDbService)

    def test_get_tmdb_service_no_api_key(self):
        """Test service creation without API key"""
        service = get_tmdb_service()
        assert service is None
