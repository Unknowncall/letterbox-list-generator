"""Shared test fixtures and configuration"""
import pytest
import logging
from unittest.mock import Mock, MagicMock
from fastapi.testclient import TestClient
from typing import Dict, Any


@pytest.fixture(autouse=True)
def setup_logging(caplog):
    """Automatically configure logging for all tests"""
    caplog.set_level(logging.INFO)


@pytest.fixture
def mock_user():
    """Create a mock User object from letterboxdpy"""
    user = Mock()
    user.username = "testuser"
    user.display_name = "Test User"
    user.bio = "Test bio"
    user.url = "https://letterboxd.com/testuser/"
    user.stats = {
        'films': 100,
        'following': 50,
        'followers': 75
    }

    # Mock watchlist data
    user.get_watchlist = Mock(return_value={
        'data': {
            'the-godfather': {
                'name': 'The Godfather',
                'year': 1972,
                'url': 'https://letterboxd.com/film/the-godfather/'
            },
            'pulp-fiction': {
                'name': 'Pulp Fiction',
                'year': 1994,
                'url': 'https://letterboxd.com/film/pulp-fiction/'
            },
            'the-dark-knight': {
                'name': 'The Dark Knight',
                'year': 2008,
                'url': 'https://letterboxd.com/film/the-dark-knight/'
            }
        }
    })

    # Mock films data (rated and liked)
    user.get_films = Mock(return_value={
        'movies': {
            'the-godfather': {
                'name': 'The Godfather',
                'year': 1972,
                'rating': 10,
                'liked': True
            },
            'pulp-fiction': {
                'name': 'Pulp Fiction',
                'year': 1994,
                'rating': 10,
                'liked': True
            },
            'the-dark-knight': {
                'name': 'The Dark Knight',
                'year': 2008,
                'rating': 9,
                'liked': True
            },
            'not-liked': {
                'name': 'Not Liked',
                'year': 2020,
                'rating': 8,
                'liked': False
            },
            'not-rated': {
                'name': 'Not Rated',
                'year': 2021,
                'rating': 0,
                'liked': True
            }
        }
    })

    return user


@pytest.fixture
def sample_films():
    """Sample film data for testing"""
    return [
        {'title': 'The Godfather', 'year': 1972, 'rating': 5.0},
        {'title': 'Pulp Fiction', 'year': 1994, 'rating': 5.0},
        {'title': 'The Dark Knight', 'year': 2008, 'rating': 4.5},
        {'title': 'Inception', 'year': 2010, 'rating': 4.5},
        {'title': 'Fight Club', 'year': 1999, 'rating': 4.0},
    ]


@pytest.fixture
def app_client():
    """Create a test client for the FastAPI app with mocked scheduler"""
    from unittest.mock import patch
    with patch('jobs.scheduler.init_scheduler'), patch('jobs.scheduler.shutdown_scheduler'):
        from index import app
        with TestClient(app) as client:
            yield client


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables for testing"""
    def _set_env(**kwargs):
        for key, value in kwargs.items():
            monkeypatch.setenv(key, value)
    return _set_env
