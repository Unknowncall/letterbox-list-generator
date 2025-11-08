"""Tests for routers/users.py"""
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from index import app

client = TestClient(app)


class TestGetUserProfileEndpoint:
    """Test suite for GET /users/{username} endpoint"""

    def test_get_user_profile_success(self):
        """Test successful user profile retrieval"""
        mock_profile = {
            'username': 'testuser',
            'display_name': 'Test User',
            'bio': 'Test bio',
            'stats': {
                'films_watched': 100,
                'lists': 5,
                'following': 50,
                'followers': 75
            },
            'url': 'https://letterboxd.com/testuser/'
        }

        with patch('controllers.users.get_user_profile', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_profile
            response = client.get('/users/testuser')

            assert response.status_code == 200
            data = response.json()
            assert data['username'] == 'testuser'
            assert data['display_name'] == 'Test User'
            assert data['stats']['films_watched'] == 100

    def test_get_user_profile_not_found(self):
        """Test 404 error when user not found"""
        with patch('controllers.users.get_user_profile', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = ValueError('User not found')
            response = client.get('/users/nonexistentuser')

            assert response.status_code == 404
            assert 'User not found' in response.json()['detail']

    def test_get_user_profile_invalid_username_special_chars(self):
        """Test validation error with special characters in username"""
        response = client.get('/users/test@user')

        assert response.status_code == 422

    def test_get_user_profile_invalid_username_spaces(self):
        """Test validation error with spaces in username"""
        response = client.get('/users/test user')

        assert response.status_code == 422

    def test_get_user_profile_invalid_username_empty(self):
        """Test validation error with empty username"""
        response = client.get('/users/')

        assert response.status_code in [404, 422]  # Could be 404 (not found route) or 422

    def test_get_user_profile_server_error(self):
        """Test 500 error on server exception"""
        with patch('controllers.users.get_user_profile', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = Exception('Database error')
            response = client.get('/users/testuser')

            assert response.status_code == 500
            assert 'Internal server error' in response.json()['detail']

    def test_get_user_profile_valid_username_formats(self):
        """Test various valid username formats"""
        valid_usernames = ['user123', 'test_user', 'test-user', 'User-123_test']

        mock_profile = {
            'username': 'testuser',
            'display_name': 'Test',
            'stats': {'films_watched': 0, 'lists': 0, 'following': 0, 'followers': 0},
            'url': 'https://letterboxd.com/testuser/'
        }

        for username in valid_usernames:
            with patch('controllers.users.get_user_profile', new_callable=AsyncMock) as mock_get:
                mock_get.return_value = mock_profile
                response = client.get(f'/users/{username}')

                assert response.status_code == 200


class TestGetUserWatchlistEndpoint:
    """Test suite for GET /users/{username}/watchlist endpoint"""

    def test_get_watchlist_success_default_params(self):
        """Test successful watchlist retrieval with default parameters"""
        mock_watchlist = {
            'username': 'testuser',
            'total_watchlist': 50,
            'films_count': 20,
            'page': 1,
            'page_size': 20,
            'total_pages': 3,
            'has_next': True,
            'has_previous': False,
            'films': []
        }

        with patch('controllers.users.get_user_watchlist', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_watchlist
            response = client.get('/users/testuser/watchlist')

            assert response.status_code == 200
            data = response.json()
            assert data['username'] == 'testuser'
            assert data['page'] == 1
            assert data['page_size'] == 20

    def test_get_watchlist_with_pagination(self):
        """Test watchlist with pagination parameters"""
        mock_watchlist = {
            'username': 'testuser',
            'total_watchlist': 100,
            'films_count': 10,
            'page': 2,
            'page_size': 10,
            'total_pages': 10,
            'has_next': True,
            'has_previous': True,
            'films': []
        }

        with patch('controllers.users.get_user_watchlist', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_watchlist
            response = client.get('/users/testuser/watchlist?page=2&page_size=10')

            assert response.status_code == 200
            mock_get.assert_called_once()

    def test_get_watchlist_with_limit(self):
        """Test watchlist with limit parameter"""
        mock_watchlist = {
            'username': 'testuser',
            'total_watchlist': 100,
            'films_count': 50,
            'page': 1,
            'page_size': 50,
            'total_pages': 1,
            'has_next': False,
            'has_previous': False,
            'films': []
        }

        with patch('controllers.users.get_user_watchlist', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_watchlist
            response = client.get('/users/testuser/watchlist?limit=50')

            assert response.status_code == 200

    def test_get_watchlist_sort_by_title(self):
        """Test watchlist sorted by title"""
        mock_watchlist = {
            'username': 'testuser',
            'total_watchlist': 10,
            'films_count': 10,
            'page': 1,
            'page_size': 20,
            'total_pages': 1,
            'has_next': False,
            'has_previous': False,
            'films': []
        }

        with patch('controllers.users.get_user_watchlist', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_watchlist
            response = client.get('/users/testuser/watchlist?sort_by=title&sort_order=asc')

            assert response.status_code == 200

    def test_get_watchlist_sort_by_year(self):
        """Test watchlist sorted by year"""
        mock_watchlist = {
            'username': 'testuser',
            'total_watchlist': 10,
            'films_count': 10,
            'page': 1,
            'page_size': 20,
            'total_pages': 1,
            'has_next': False,
            'has_previous': False,
            'films': []
        }

        with patch('controllers.users.get_user_watchlist', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_watchlist
            response = client.get('/users/testuser/watchlist?sort_by=year&sort_order=desc')

            assert response.status_code == 200

    def test_get_watchlist_invalid_sort_by(self):
        """Test validation error with invalid sort_by parameter"""
        response = client.get('/users/testuser/watchlist?sort_by=rating')

        assert response.status_code == 422

    def test_get_watchlist_invalid_sort_order(self):
        """Test validation error with invalid sort_order parameter"""
        response = client.get('/users/testuser/watchlist?sort_order=random')

        assert response.status_code == 422

    def test_get_watchlist_invalid_page_zero(self):
        """Test validation error with page=0"""
        response = client.get('/users/testuser/watchlist?page=0')

        assert response.status_code == 422

    def test_get_watchlist_invalid_page_negative(self):
        """Test validation error with negative page"""
        response = client.get('/users/testuser/watchlist?page=-1')

        assert response.status_code == 422

    def test_get_watchlist_invalid_page_size_zero(self):
        """Test validation error with page_size=0"""
        response = client.get('/users/testuser/watchlist?page_size=0')

        assert response.status_code == 422

    def test_get_watchlist_invalid_page_size_too_large(self):
        """Test validation error with page_size > 100"""
        response = client.get('/users/testuser/watchlist?page_size=101')

        assert response.status_code == 422

    def test_get_watchlist_invalid_limit_zero(self):
        """Test validation error with limit=0"""
        response = client.get('/users/testuser/watchlist?limit=0')

        assert response.status_code == 422

    def test_get_watchlist_invalid_limit_too_large(self):
        """Test validation error with limit > 1000"""
        response = client.get('/users/testuser/watchlist?limit=1001')

        assert response.status_code == 422

    def test_get_watchlist_not_found(self):
        """Test 404 error when user not found"""
        with patch('controllers.users.get_user_watchlist', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = ValueError('User not found')
            response = client.get('/users/nonexistentuser/watchlist')

            assert response.status_code == 404

    def test_get_watchlist_server_error(self):
        """Test 500 error on server exception"""
        with patch('controllers.users.get_user_watchlist', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = Exception('Database error')
            response = client.get('/users/testuser/watchlist')

            assert response.status_code == 500


class TestGetTopRatedEndpoint:
    """Test suite for GET /users/{username}/top-rated endpoint"""

    def test_get_top_rated_success_default_params(self):
        """Test successful top rated retrieval with default parameters"""
        mock_top_rated = {
            'username': 'testuser',
            'total_rated': 100,
            'films_count': 20,
            'page': 1,
            'page_size': 20,
            'total_pages': 5,
            'has_next': True,
            'has_previous': False,
            'films': []
        }

        with patch('controllers.users.get_top_rated_films', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_top_rated
            response = client.get('/users/testuser/top-rated')

            assert response.status_code == 200
            data = response.json()
            assert data['username'] == 'testuser'
            assert data['total_rated'] == 100

    def test_get_top_rated_with_pagination(self):
        """Test top rated with pagination parameters"""
        mock_top_rated = {
            'username': 'testuser',
            'total_rated': 50,
            'films_count': 10,
            'page': 3,
            'page_size': 10,
            'total_pages': 5,
            'has_next': True,
            'has_previous': True,
            'films': []
        }

        with patch('controllers.users.get_top_rated_films', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_top_rated
            response = client.get('/users/testuser/top-rated?page=3&page_size=10')

            assert response.status_code == 200

    def test_get_top_rated_sort_by_rating(self):
        """Test top rated sorted by rating (default)"""
        mock_top_rated = {
            'username': 'testuser',
            'total_rated': 20,
            'films_count': 20,
            'page': 1,
            'page_size': 20,
            'total_pages': 1,
            'has_next': False,
            'has_previous': False,
            'films': []
        }

        with patch('controllers.users.get_top_rated_films', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_top_rated
            response = client.get('/users/testuser/top-rated?sort_by=rating&sort_order=desc')

            assert response.status_code == 200

    def test_get_top_rated_sort_by_title(self):
        """Test top rated sorted by title"""
        mock_top_rated = {
            'username': 'testuser',
            'total_rated': 20,
            'films_count': 20,
            'page': 1,
            'page_size': 20,
            'total_pages': 1,
            'has_next': False,
            'has_previous': False,
            'films': []
        }

        with patch('controllers.users.get_top_rated_films', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_top_rated
            response = client.get('/users/testuser/top-rated?sort_by=title&sort_order=asc')

            assert response.status_code == 200

    def test_get_top_rated_sort_by_year(self):
        """Test top rated sorted by year"""
        mock_top_rated = {
            'username': 'testuser',
            'total_rated': 20,
            'films_count': 20,
            'page': 1,
            'page_size': 20,
            'total_pages': 1,
            'has_next': False,
            'has_previous': False,
            'films': []
        }

        with patch('controllers.users.get_top_rated_films', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_top_rated
            response = client.get('/users/testuser/top-rated?sort_by=year&sort_order=desc')

            assert response.status_code == 200

    def test_get_top_rated_invalid_sort_by(self):
        """Test validation error with invalid sort_by parameter"""
        response = client.get('/users/testuser/top-rated?sort_by=director')

        assert response.status_code == 422

    def test_get_top_rated_invalid_sort_order(self):
        """Test validation error with invalid sort_order parameter"""
        response = client.get('/users/testuser/top-rated?sort_order=invalid')

        assert response.status_code == 422

    def test_get_top_rated_with_limit(self):
        """Test top rated with limit parameter"""
        mock_top_rated = {
            'username': 'testuser',
            'total_rated': 100,
            'films_count': 15,
            'page': 1,
            'page_size': 15,
            'total_pages': 1,
            'has_next': False,
            'has_previous': False,
            'films': []
        }

        with patch('controllers.users.get_top_rated_films', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_top_rated
            response = client.get('/users/testuser/top-rated?limit=15')

            assert response.status_code == 200

    def test_get_top_rated_invalid_page_zero(self):
        """Test validation error with page=0"""
        response = client.get('/users/testuser/top-rated?page=0')

        assert response.status_code == 422

    def test_get_top_rated_invalid_page_size_too_large(self):
        """Test validation error with page_size > 100"""
        response = client.get('/users/testuser/top-rated?page_size=101')

        assert response.status_code == 422

    def test_get_top_rated_invalid_limit_too_large(self):
        """Test validation error with limit > 1000"""
        response = client.get('/users/testuser/top-rated?limit=1001')

        assert response.status_code == 422

    def test_get_top_rated_not_found(self):
        """Test 404 error when user not found"""
        with patch('controllers.users.get_top_rated_films', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = ValueError('User not found')
            response = client.get('/users/nonexistentuser/top-rated')

            assert response.status_code == 404

    def test_get_top_rated_server_error(self):
        """Test 500 error on server exception"""
        with patch('controllers.users.get_top_rated_films', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = Exception('Database error')
            response = client.get('/users/testuser/top-rated')

            assert response.status_code == 500

    def test_get_top_rated_all_parameters_combined(self):
        """Test top rated with all parameters combined"""
        mock_top_rated = {
            'username': 'testuser',
            'total_rated': 500,
            'films_count': 5,
            'page': 2,
            'page_size': 5,
            'total_pages': 10,
            'has_next': True,
            'has_previous': True,
            'films': []
        }

        with patch('controllers.users.get_top_rated_films', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_top_rated
            response = client.get(
                '/users/testuser/top-rated?limit=50&page=2&page_size=5&sort_by=rating&sort_order=desc'
            )

            assert response.status_code == 200
            # Verify the controller was called with correct parameters
            mock_get.assert_called_once_with('testuser', 50, 2, 5, 'rating', 'desc')
