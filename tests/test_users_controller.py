"""Tests for controllers/users.py"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from controllers.users import get_user_profile, get_user_watchlist, get_top_rated_films


class TestGetUserProfile:
    """Test suite for get_user_profile function"""

    @pytest.mark.asyncio
    async def test_get_user_profile_success(self, mock_user):
        """Test successfully getting a user profile"""
        with patch('controllers.users.User', return_value=mock_user):
            result = await get_user_profile('testuser')

            assert result['username'] == 'testuser'
            assert result['display_name'] == 'Test User'
            assert result['bio'] == 'Test bio'
            assert result['stats']['films_watched'] == 100
            assert result['stats']['following'] == 50
            assert result['stats']['followers'] == 75
            assert result['stats']['lists'] == 0
            assert result['url'] == 'https://letterboxd.com/testuser/'

    @pytest.mark.asyncio
    async def test_get_user_profile_without_bio(self):
        """Test getting a user profile when bio is None"""
        user = Mock()
        user.username = 'testuser'
        user.display_name = 'Test User'
        user.bio = None
        user.url = 'https://letterboxd.com/testuser/'
        user.stats = {
            'films': 50,
            'following': 25,
            'followers': 30
        }

        with patch('controllers.users.User', return_value=user):
            result = await get_user_profile('testuser')

            assert result['bio'] is None

    @pytest.mark.asyncio
    async def test_get_user_profile_missing_stats(self):
        """Test getting a user profile with missing stats"""
        user = Mock()
        user.username = 'testuser'
        user.display_name = 'Test User'
        user.bio = 'Bio'
        user.url = 'https://letterboxd.com/testuser/'
        user.stats = {}

        with patch('controllers.users.User', return_value=user):
            result = await get_user_profile('testuser')

            assert result['stats']['films_watched'] == 0
            assert result['stats']['following'] == 0
            assert result['stats']['followers'] == 0

    @pytest.mark.asyncio
    async def test_get_user_profile_error(self):
        """Test error handling when user fetch fails"""
        with patch('controllers.users.User', side_effect=Exception('User not found')):
            with pytest.raises(ValueError) as exc_info:
                await get_user_profile('invaliduser')

            assert 'Error fetching user profile' in str(exc_info.value)
            assert 'User not found' in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_user_profile_with_different_username(self, mock_user):
        """Test that username parameter is used in response"""
        with patch('controllers.users.User', return_value=mock_user):
            result = await get_user_profile('anotheruser')

            assert result['username'] == 'anotheruser'


class TestGetUserWatchlist:
    """Test suite for get_user_watchlist function"""

    @pytest.mark.asyncio
    async def test_get_watchlist_default_params(self, mock_user):
        """Test getting watchlist with default parameters"""
        with patch('controllers.users.User', return_value=mock_user):
            result = await get_user_watchlist('testuser')

            assert result['username'] == 'testuser'
            assert result['total_watchlist'] == 3
            assert result['page'] == 1
            assert result['page_size'] == 20
            assert len(result['films']) == 3

    @pytest.mark.asyncio
    async def test_get_watchlist_with_pagination(self, mock_user):
        """Test getting watchlist with pagination"""
        with patch('controllers.users.User', return_value=mock_user):
            result = await get_user_watchlist('testuser', page=1, page_size=2)

            assert result['page'] == 1
            assert result['page_size'] == 2
            assert result['films_count'] == 2
            assert result['has_next'] is True

    @pytest.mark.asyncio
    async def test_get_watchlist_sort_by_title_asc(self, mock_user):
        """Test watchlist sorted by title ascending"""
        with patch('controllers.users.User', return_value=mock_user):
            result = await get_user_watchlist(
                'testuser',
                sort_by='title',
                sort_order='asc'
            )

            films = result['films']
            # Should be sorted alphabetically: Pulp Fiction, The Dark Knight, The Godfather
            assert films[0]['title'] == 'Pulp Fiction'
            assert films[1]['title'] == 'The Dark Knight'
            assert films[2]['title'] == 'The Godfather'

    @pytest.mark.asyncio
    async def test_get_watchlist_sort_by_title_desc(self, mock_user):
        """Test watchlist sorted by title descending"""
        with patch('controllers.users.User', return_value=mock_user):
            result = await get_user_watchlist(
                'testuser',
                sort_by='title',
                sort_order='desc'
            )

            films = result['films']
            # Should be sorted reverse alphabetically: The Godfather, The Dark Knight, Pulp Fiction
            assert films[0]['title'] == 'The Godfather'
            assert films[1]['title'] == 'The Dark Knight'
            assert films[2]['title'] == 'Pulp Fiction'

    @pytest.mark.asyncio
    async def test_get_watchlist_sort_by_year_asc(self, mock_user):
        """Test watchlist sorted by year ascending"""
        with patch('controllers.users.User', return_value=mock_user):
            result = await get_user_watchlist(
                'testuser',
                sort_by='year',
                sort_order='asc'
            )

            films = result['films']
            # Should be sorted: 1972, 1994, 2008
            assert films[0]['year'] == 1972
            assert films[1]['year'] == 1994
            assert films[2]['year'] == 2008

    @pytest.mark.asyncio
    async def test_get_watchlist_sort_by_year_desc(self, mock_user):
        """Test watchlist sorted by year descending"""
        with patch('controllers.users.User', return_value=mock_user):
            result = await get_user_watchlist(
                'testuser',
                sort_by='year',
                sort_order='desc'
            )

            films = result['films']
            # Should be sorted: 2008, 1994, 1972
            assert films[0]['year'] == 2008
            assert films[1]['year'] == 1994
            assert films[2]['year'] == 1972

    @pytest.mark.asyncio
    async def test_get_watchlist_with_limit(self, mock_user):
        """Test watchlist with limit parameter"""
        with patch('controllers.users.User', return_value=mock_user):
            result = await get_user_watchlist('testuser', limit=2)

            assert result['total_watchlist'] == 3  # Original count
            assert result['films_count'] == 2  # Limited count
            assert len(result['films']) == 2

    @pytest.mark.asyncio
    async def test_get_watchlist_empty(self):
        """Test getting an empty watchlist"""
        user = Mock()
        user.get_watchlist = Mock(return_value={'data': {}})

        with patch('controllers.users.User', return_value=user):
            result = await get_user_watchlist('testuser')

            assert result['total_watchlist'] == 0
            assert result['films_count'] == 0
            assert result['films'] == []

    @pytest.mark.asyncio
    async def test_get_watchlist_no_data_key(self):
        """Test getting watchlist when 'data' key is missing"""
        user = Mock()
        user.get_watchlist = Mock(return_value={})

        with patch('controllers.users.User', return_value=user):
            result = await get_user_watchlist('testuser')

            assert result['total_watchlist'] == 0
            assert result['films'] == []

    @pytest.mark.asyncio
    async def test_get_watchlist_error(self):
        """Test error handling when watchlist fetch fails"""
        with patch('controllers.users.User', side_effect=Exception('API error')):
            with pytest.raises(ValueError) as exc_info:
                await get_user_watchlist('testuser')

            assert 'Error fetching watchlist' in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_watchlist_pagination_metadata(self, mock_user):
        """Test that pagination metadata is correct"""
        with patch('controllers.users.User', return_value=mock_user):
            result = await get_user_watchlist('testuser', page=1, page_size=2)

            assert result['total_pages'] == 2
            assert result['has_next'] is True
            assert result['has_previous'] is False


class TestGetTopRatedFilms:
    """Test suite for get_top_rated_films function"""

    @pytest.mark.asyncio
    async def test_get_top_rated_default_params(self, mock_user):
        """Test getting top rated films with default parameters"""
        with patch('controllers.users.User', return_value=mock_user):
            result = await get_top_rated_films('testuser')

            assert result['username'] == 'testuser'
            assert result['total_rated'] == 3
            assert result['page'] == 1
            assert result['page_size'] == 20

    @pytest.mark.asyncio
    async def test_get_top_rated_sort_by_rating_desc(self, mock_user):
        """Test top rated films sorted by rating descending (default)"""
        with patch('controllers.users.User', return_value=mock_user):
            result = await get_top_rated_films(
                'testuser',
                sort_by='rating',
                sort_order='desc'
            )

            films = result['films']
            # Should be sorted: 5.0, 5.0, 4.5
            assert films[0]['rating'] >= films[1]['rating']
            assert films[1]['rating'] >= films[2]['rating']

    @pytest.mark.asyncio
    async def test_get_top_rated_sort_by_rating_asc(self, mock_user):
        """Test top rated films sorted by rating ascending"""
        with patch('controllers.users.User', return_value=mock_user):
            result = await get_top_rated_films(
                'testuser',
                sort_by='rating',
                sort_order='asc'
            )

            films = result['films']
            # Should be sorted: 4.5, 5.0, 5.0
            assert films[0]['rating'] <= films[1]['rating']
            assert films[1]['rating'] <= films[2]['rating']

    @pytest.mark.asyncio
    async def test_get_top_rated_sort_by_title(self, mock_user):
        """Test top rated films sorted by title"""
        with patch('controllers.users.User', return_value=mock_user):
            result = await get_top_rated_films(
                'testuser',
                sort_by='title',
                sort_order='asc'
            )

            films = result['films']
            titles = [f['title'] for f in films]
            assert titles == sorted(titles, key=lambda x: x.lower())

    @pytest.mark.asyncio
    async def test_get_top_rated_sort_by_year(self, mock_user):
        """Test top rated films sorted by year"""
        with patch('controllers.users.User', return_value=mock_user):
            result = await get_top_rated_films(
                'testuser',
                sort_by='year',
                sort_order='asc'
            )

            films = result['films']
            years = [f['year'] for f in films]
            assert years == sorted(years)

    @pytest.mark.asyncio
    async def test_get_top_rated_with_limit(self, mock_user):
        """Test top rated films with limit"""
        with patch('controllers.users.User', return_value=mock_user):
            result = await get_top_rated_films('testuser', limit=2)

            assert result['total_rated'] == 3  # Original count
            assert result['films_count'] == 2  # Limited count
            assert len(result['films']) == 2

    @pytest.mark.asyncio
    async def test_get_top_rated_with_pagination(self, mock_user):
        """Test top rated films with pagination"""
        with patch('controllers.users.User', return_value=mock_user):
            result = await get_top_rated_films('testuser', page=1, page_size=2)

            assert result['page'] == 1
            assert result['page_size'] == 2
            assert result['films_count'] == 2
            assert result['total_pages'] == 2

    @pytest.mark.asyncio
    async def test_get_top_rated_empty(self):
        """Test getting top rated films when user has none"""
        user = Mock()
        user.get_films = Mock(return_value={'movies': {}})

        with patch('controllers.users.User', return_value=user):
            result = await get_top_rated_films('testuser')

            assert result['total_rated'] == 0
            assert result['films_count'] == 0
            assert result['films'] == []

    @pytest.mark.asyncio
    async def test_get_top_rated_error(self):
        """Test error handling when fetching top rated films fails"""
        with patch('controllers.users.User', side_effect=Exception('API error')):
            with pytest.raises(ValueError) as exc_info:
                await get_top_rated_films('testuser')

            assert 'Error fetching top rated films' in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_top_rated_pagination_metadata(self, mock_user):
        """Test pagination metadata for top rated films"""
        with patch('controllers.users.User', return_value=mock_user):
            result = await get_top_rated_films('testuser', page=1, page_size=2)

            assert result['has_next'] is True
            assert result['has_previous'] is False
            assert result['total_pages'] == 2

    @pytest.mark.asyncio
    async def test_get_top_rated_only_liked_and_rated(self):
        """Test that only liked and rated films are returned"""
        user = Mock()
        user.get_films = Mock(return_value={
            'movies': {
                'film-1': {'name': 'Film 1', 'rating': 10, 'liked': True},
                'film-2': {'name': 'Film 2', 'rating': 8, 'liked': False},
                'film-3': {'name': 'Film 3', 'rating': 0, 'liked': True},
            }
        })

        with patch('controllers.users.User', return_value=user):
            result = await get_top_rated_films('testuser')

            # Only film-1 should be returned
            assert result['total_rated'] == 1
            assert result['films'][0]['title'] == 'Film 1'

    @pytest.mark.asyncio
    async def test_get_top_rated_complex_sorting_and_pagination(self, mock_user):
        """Test complex scenario with sorting, limit, and pagination"""
        with patch('controllers.users.User', return_value=mock_user):
            result = await get_top_rated_films(
                'testuser',
                limit=3,
                page=1,
                page_size=2,
                sort_by='rating',
                sort_order='desc'
            )

            assert result['films_count'] == 2
            assert result['total_pages'] == 2
            # First page should have the top 2 rated films
            assert all('rating' in film for film in result['films'])
