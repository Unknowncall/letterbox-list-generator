"""Tests for jobs/fetch_top_movies.py"""
import pytest
import logging
from unittest.mock import patch, AsyncMock, MagicMock
from jobs.fetch_top_movies import fetch_top_movies_job, run_sync_job


class TestFetchTopMoviesJob:
    """Test suite for fetch_top_movies_job function"""

    @pytest.mark.asyncio
    async def test_fetch_top_movies_single_user_success(self, caplog):
        """Test fetching top movies for a single user successfully"""
        caplog.set_level(logging.INFO)
        mock_result = {
            'films_count': 3,
            'films': [
                {'title': 'The Godfather', 'year': 1972, 'rating': 5.0},
                {'title': 'Pulp Fiction', 'year': 1994, 'rating': 5.0},
                {'title': 'The Dark Knight', 'year': 2008, 'rating': 4.5},
            ]
        }

        with patch('jobs.fetch_top_movies.get_top_rated_films', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_result

            await fetch_top_movies_job(['testuser'])

            # Verify controller was called with correct parameters
            mock_get.assert_called_once_with(
                username='testuser',
                limit=15,
                page=1,
                page_size=15,
                sort_by='rating',
                sort_order='desc'
            )

            # Verify logs
            assert 'Starting top movies fetch job for 1 user(s)' in caplog.text
            assert 'Fetching top 15 movies for user: testuser' in caplog.text
            assert 'Successfully fetched 3 top movies for testuser' in caplog.text
            assert 'The Godfather (1972) - Rating: 5.0/5.0' in caplog.text
            assert 'Completed top movies fetch job' in caplog.text

    @pytest.mark.asyncio
    async def test_fetch_top_movies_multiple_users_success(self, caplog):
        """Test fetching top movies for multiple users"""
        mock_result = {
            'films_count': 2,
            'films': [
                {'title': 'Film 1', 'year': 2000, 'rating': 5.0},
                {'title': 'Film 2', 'year': 2010, 'rating': 4.5},
            ]
        }

        with patch('jobs.fetch_top_movies.get_top_rated_films', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_result

            await fetch_top_movies_job(['user1', 'user2', 'user3'])

            # Verify controller was called for each user
            assert mock_get.call_count == 3

            # Verify logs for all users
            assert 'Starting top movies fetch job for 3 user(s)' in caplog.text
            assert 'Fetching top 15 movies for user: user1' in caplog.text
            assert 'Fetching top 15 movies for user: user2' in caplog.text
            assert 'Fetching top 15 movies for user: user3' in caplog.text

    @pytest.mark.asyncio
    async def test_fetch_top_movies_empty_results(self, caplog):
        """Test fetching top movies when user has no films"""
        mock_result = {
            'films_count': 0,
            'films': []
        }

        with patch('jobs.fetch_top_movies.get_top_rated_films', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_result

            await fetch_top_movies_job(['testuser'])

            assert 'Successfully fetched 0 top movies for testuser' in caplog.text

    @pytest.mark.asyncio
    async def test_fetch_top_movies_user_error_continues(self, caplog):
        """Test that job continues when one user fails"""
        mock_result = {
            'films_count': 1,
            'films': [
                {'title': 'Film 1', 'year': 2000, 'rating': 5.0},
            ]
        }

        with patch('jobs.fetch_top_movies.get_top_rated_films', new_callable=AsyncMock) as mock_get:
            # First call fails, second succeeds
            mock_get.side_effect = [
                Exception('User not found'),
                mock_result
            ]

            await fetch_top_movies_job(['baduser', 'gooduser'])

            # Verify error was logged but job continued
            assert 'Error fetching top movies for baduser: User not found' in caplog.text
            assert 'Successfully fetched 1 top movies for gooduser' in caplog.text
            assert 'Completed top movies fetch job' in caplog.text

    @pytest.mark.asyncio
    async def test_fetch_top_movies_all_users_fail(self, caplog):
        """Test job when all users fail"""
        with patch('jobs.fetch_top_movies.get_top_rated_films', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = Exception('API error')

            await fetch_top_movies_job(['user1', 'user2'])

            # Verify errors were logged for both users
            assert 'Error fetching top movies for user1: API error' in caplog.text
            assert 'Error fetching top movies for user2: API error' in caplog.text
            assert 'Completed top movies fetch job' in caplog.text

    @pytest.mark.asyncio
    async def test_fetch_top_movies_film_logging_format(self, caplog):
        """Test that films are logged in the correct format"""
        mock_result = {
            'films_count': 2,
            'films': [
                {'title': 'Film A', 'year': 2020, 'rating': 5.0},
                {'title': 'Film B', 'year': None, 'rating': 4.5},
            ]
        }

        with patch('jobs.fetch_top_movies.get_top_rated_films', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_result

            await fetch_top_movies_job(['testuser'])

            # Verify film logging format
            assert '1. Film A (2020) - Rating: 5.0/5.0' in caplog.text
            assert '2. Film B (None) - Rating: 4.5/5.0' in caplog.text

    @pytest.mark.asyncio
    async def test_fetch_top_movies_empty_username_list(self, caplog):
        """Test job with empty username list"""
        await fetch_top_movies_job([])

        assert 'Starting top movies fetch job for 0 user(s)' in caplog.text
        assert 'Completed top movies fetch job' in caplog.text

    @pytest.mark.asyncio
    async def test_fetch_top_movies_logs_timestamp(self, caplog):
        """Test that job logs timestamps"""
        mock_result = {
            'films_count': 0,
            'films': []
        }

        with patch('jobs.fetch_top_movies.get_top_rated_films', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_result

            await fetch_top_movies_job(['testuser'])

            # Check for timestamp pattern in logs (brackets with datetime)
            assert '[' in caplog.text
            assert ']' in caplog.text

    @pytest.mark.asyncio
    async def test_fetch_top_movies_exact_parameters(self):
        """Test that exact parameters are passed to controller"""
        mock_result = {
            'films_count': 0,
            'films': []
        }

        with patch('jobs.fetch_top_movies.get_top_rated_films', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_result

            await fetch_top_movies_job(['testuser'])

            # Verify exact parameters
            call_kwargs = mock_get.call_args[1]
            assert call_kwargs['username'] == 'testuser'
            assert call_kwargs['limit'] == 15
            assert call_kwargs['page'] == 1
            assert call_kwargs['page_size'] == 15
            assert call_kwargs['sort_by'] == 'rating'
            assert call_kwargs['sort_order'] == 'desc'

    @pytest.mark.asyncio
    async def test_fetch_top_movies_handles_missing_year(self, caplog):
        """Test handling of films without year field"""
        mock_result = {
            'films_count': 1,
            'films': [
                {'title': 'No Year Film', 'rating': 5.0},
            ]
        }

        with patch('jobs.fetch_top_movies.get_top_rated_films', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_result

            await fetch_top_movies_job(['testuser'])

            # Should not crash, year should be None
            assert 'Successfully fetched 1 top movies for testuser' in caplog.text


class TestRunSyncJob:
    """Test suite for run_sync_job function"""

    def test_run_sync_job_success(self, caplog):
        """Test synchronous wrapper runs async job successfully"""
        import asyncio as asyncio_module

        def mock_asyncio_run(coro):
            # Close the coroutine to prevent warnings
            coro.close()

        with patch.object(asyncio_module, 'run', side_effect=mock_asyncio_run):
            run_sync_job(['testuser'])

    def test_run_sync_job_with_multiple_users(self):
        """Test synchronous wrapper with multiple users"""
        import asyncio as asyncio_module

        def mock_asyncio_run(coro):
            # Close the coroutine to prevent warnings
            coro.close()

        with patch.object(asyncio_module, 'run', side_effect=mock_asyncio_run):
            run_sync_job(['user1', 'user2', 'user3'])

    def test_run_sync_job_error_handling(self, caplog):
        """Test error handling in synchronous wrapper"""
        import asyncio as asyncio_module

        def mock_asyncio_run(coro):
            # Close the coroutine and raise the error
            coro.close()
            raise Exception('Async job error')

        with patch.object(asyncio_module, 'run', side_effect=mock_asyncio_run):
            run_sync_job(['testuser'])

            # Verify error was logged
            assert 'Error running sync job wrapper: Async job error' in caplog.text

    def test_run_sync_job_empty_list(self):
        """Test synchronous wrapper with empty user list"""
        import asyncio as asyncio_module

        def mock_asyncio_run(coro):
            # Close the coroutine to prevent warnings
            coro.close()

        with patch.object(asyncio_module, 'run', side_effect=mock_asyncio_run):
            run_sync_job([])

    def test_run_sync_job_creates_event_loop(self):
        """Test that synchronous wrapper uses asyncio.run"""
        import asyncio as asyncio_module

        # Create a mock that properly handles the coroutine to avoid warnings
        def mock_asyncio_run(coro):
            # Close the coroutine to prevent "never awaited" warning
            coro.close()

        with patch.object(asyncio_module, 'run', side_effect=mock_asyncio_run) as mock_run:
            run_sync_job(['testuser'])

            # Verify asyncio.run was called
            mock_run.assert_called_once()
