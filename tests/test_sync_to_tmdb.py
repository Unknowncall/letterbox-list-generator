"""Tests for sync_to_tmdb job (one list per user)"""
import pytest
import json
from unittest.mock import patch, AsyncMock, Mock, mock_open, MagicMock
from pathlib import Path
from jobs.sync_to_tmdb import (
    get_tmdb_config,
    load_list_mappings,
    save_list_mappings,
    sync_to_tmdb_job,
    run_sync_job,
    LIST_MAPPINGS_FILE
)


class TestGetTMDbConfig:
    """Tests for get_tmdb_config function"""

    def test_get_config_with_env_vars(self, monkeypatch):
        """Test loading configuration from environment variables"""
        monkeypatch.setenv('TMDB_SYNC_ENABLED', 'true')
        monkeypatch.setenv('TMDB_API_KEY', 'test_api_key')
        monkeypatch.setenv('TMDB_V4_ACCESS_TOKEN', 'test_token')

        config = get_tmdb_config()

        assert config['enabled'] is True
        assert config['api_key'] == 'test_api_key'
        assert config['v4_access_token'] == 'test_token'

    def test_get_config_with_defaults(self):
        """Test configuration with default values"""
        config = get_tmdb_config()

        assert config['enabled'] is False
        assert config['api_key'] == ''
        assert config['v4_access_token'] == ''

    def test_get_config_disabled(self, monkeypatch):
        """Test configuration when sync is disabled"""
        monkeypatch.setenv('TMDB_SYNC_ENABLED', 'false')

        config = get_tmdb_config()

        assert config['enabled'] is False

    def test_get_config_enabled_variations(self, monkeypatch):
        """Test various TRUE values for enabled flag"""
        test_cases = ['true', 'True', 'TRUE', 'TrUe']

        for value in test_cases:
            monkeypatch.setenv('TMDB_SYNC_ENABLED', value)
            config = get_tmdb_config()
            assert config['enabled'] is True


class TestListMappings:
    """Tests for list mapping functions"""

    def test_load_list_mappings_file_exists(self):
        """Test loading mappings from existing file"""
        test_mappings = {"user1": 12345, "user2": 67890}
        m = mock_open(read_data=json.dumps(test_mappings))

        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', m):
            mappings = load_list_mappings()

            assert mappings == test_mappings

    def test_load_list_mappings_file_not_exists(self):
        """Test loading mappings when file doesn't exist"""
        with patch('pathlib.Path.exists', return_value=False):
            mappings = load_list_mappings()

            assert mappings == {}

    def test_load_list_mappings_json_error(self, caplog):
        """Test loading mappings with JSON decode error"""
        m = mock_open(read_data="invalid json")

        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', m):
            mappings = load_list_mappings()

            assert mappings == {}
            assert "Error loading list mappings" in caplog.text

    def test_save_list_mappings_success(self, caplog):
        """Test saving mappings successfully"""
        test_mappings = {"user1": 12345, "user2": 67890}
        m = mock_open()

        with patch('builtins.open', m):
            save_list_mappings(test_mappings)

            m.assert_called_once()
            handle = m()
            # Check that json.dump was called with the right data
            written_data = ''.join(call[0][0] for call in handle.write.call_args_list)
            assert "user1" in written_data
            assert "12345" in written_data

    def test_save_list_mappings_error(self, caplog):
        """Test saving mappings with error"""
        test_mappings = {"user1": 12345}

        with patch('builtins.open', side_effect=IOError("Write error")):
            save_list_mappings(test_mappings)

            assert "Error saving list mappings" in caplog.text


class TestSyncToTMDbJob:
    """Tests for sync_to_tmdb_job function (per-user lists)"""

    @pytest.mark.asyncio
    async def test_sync_disabled(self, monkeypatch, caplog):
        """Test job when sync is disabled"""
        monkeypatch.setenv('TMDB_SYNC_ENABLED', 'false')

        await sync_to_tmdb_job(['testuser'])

        assert "TMDb sync is disabled" in caplog.text

    @pytest.mark.asyncio
    async def test_sync_no_api_key(self, monkeypatch, caplog):
        """Test job when API key is missing"""
        monkeypatch.setenv('TMDB_SYNC_ENABLED', 'true')
        monkeypatch.setenv('TMDB_API_KEY', '')

        await sync_to_tmdb_job(['testuser'])

        assert "TMDb API key not configured" in caplog.text

    @pytest.mark.asyncio
    async def test_sync_no_access_token(self, monkeypatch, caplog):
        """Test job when v4 access token is missing"""
        monkeypatch.setenv('TMDB_SYNC_ENABLED', 'true')
        monkeypatch.setenv('TMDB_API_KEY', 'test_key')
        monkeypatch.setenv('TMDB_V4_ACCESS_TOKEN', '')

        await sync_to_tmdb_job(['testuser'])

        assert "TMDb v4 access token not configured" in caplog.text

    @pytest.mark.asyncio
    async def test_sync_no_usernames(self, monkeypatch, caplog):
        """Test job with empty usernames list"""
        monkeypatch.setenv('TMDB_SYNC_ENABLED', 'true')
        monkeypatch.setenv('TMDB_API_KEY', 'test_key')
        monkeypatch.setenv('TMDB_V4_ACCESS_TOKEN', 'test_token')

        await sync_to_tmdb_job([])

        assert "No usernames provided" in caplog.text

    @pytest.mark.asyncio
    async def test_sync_with_existing_list_mapping(self, monkeypatch, caplog):
        """Test job using existing list mapping for user"""
        monkeypatch.setenv('TMDB_SYNC_ENABLED', 'true')
        monkeypatch.setenv('TMDB_API_KEY', 'test_key')
        monkeypatch.setenv('TMDB_V4_ACCESS_TOKEN', 'test_token')

        mock_films = [
            {'title': 'The Godfather', 'year': 1972, 'rating': 5.0}
        ]

        existing_mappings = {"testuser": 12345}

        with patch('jobs.sync_to_tmdb.load_list_mappings', return_value=existing_mappings), \
             patch('jobs.sync_to_tmdb.save_list_mappings') as mock_save, \
             patch('jobs.sync_to_tmdb.get_top_rated_films', new_callable=AsyncMock) as mock_get_films, \
             patch('jobs.sync_to_tmdb.TMDbService') as mock_service_class:

            mock_get_films.return_value = {'films': mock_films, 'films_count': 1}

            mock_service = Mock()
            mock_service.update_list_with_movies.return_value = {
                'success': True,
                'total_films': 1,
                'matched': 1,
                'added': 1,
                'not_matched': []
            }
            mock_service_class.return_value = mock_service

            await sync_to_tmdb_job(['testuser'])

            assert "Using existing TMDb list ID 12345 for testuser" in caplog.text
            mock_service.update_list_with_movies.assert_called_once()
            # Shouldn't save mappings if nothing changed
            mock_save.assert_not_called()

    @pytest.mark.asyncio
    async def test_sync_create_new_list_for_user(self, monkeypatch, caplog):
        """Test job creating a new list for user"""
        monkeypatch.setenv('TMDB_SYNC_ENABLED', 'true')
        monkeypatch.setenv('TMDB_API_KEY', 'test_key')
        monkeypatch.setenv('TMDB_V4_ACCESS_TOKEN', 'test_token')

        mock_films = [
            {'title': 'Pulp Fiction', 'year': 1994, 'rating': 5.0}
        ]

        with patch('jobs.sync_to_tmdb.load_list_mappings', return_value={}), \
             patch('jobs.sync_to_tmdb.save_list_mappings') as mock_save, \
             patch('jobs.sync_to_tmdb.get_top_rated_films', new_callable=AsyncMock) as mock_get_films, \
             patch('jobs.sync_to_tmdb.TMDbService') as mock_service_class:

            mock_get_films.return_value = {'films': mock_films, 'films_count': 1}

            mock_service = Mock()
            mock_service.get_or_create_list.return_value = 67890
            mock_service.update_list_with_movies.return_value = {
                'success': True,
                'total_films': 1,
                'matched': 1,
                'added': 1,
                'not_matched': []
            }
            mock_service_class.return_value = mock_service

            await sync_to_tmdb_job(['testuser'])

            assert "Created new TMDb list for testuser" in caplog.text
            assert "testuser's Top Rated Movies" in caplog.text
            mock_service.get_or_create_list.assert_called_once()
            mock_save.assert_called_once_with({"testuser": 67890})

    @pytest.mark.asyncio
    async def test_sync_list_creation_failure(self, monkeypatch, caplog):
        """Test job when list creation fails"""
        monkeypatch.setenv('TMDB_SYNC_ENABLED', 'true')
        monkeypatch.setenv('TMDB_API_KEY', 'test_key')
        monkeypatch.setenv('TMDB_V4_ACCESS_TOKEN', 'test_token')

        with patch('jobs.sync_to_tmdb.load_list_mappings', return_value={}), \
             patch('jobs.sync_to_tmdb.save_list_mappings'), \
             patch('jobs.sync_to_tmdb.TMDbService') as mock_service_class:

            mock_service = Mock()
            mock_service.get_or_create_list.return_value = None
            mock_service_class.return_value = mock_service

            await sync_to_tmdb_job(['testuser'])

            assert "Failed to create TMDb list for testuser" in caplog.text

    @pytest.mark.asyncio
    async def test_sync_multiple_users(self, monkeypatch, caplog):
        """Test job with multiple users (each gets their own list)"""
        monkeypatch.setenv('TMDB_SYNC_ENABLED', 'true')
        monkeypatch.setenv('TMDB_API_KEY', 'test_key')
        monkeypatch.setenv('TMDB_V4_ACCESS_TOKEN', 'test_token')

        mock_films_user1 = [
            {'title': 'The Godfather', 'year': 1972, 'rating': 5.0}
        ]
        mock_films_user2 = [
            {'title': 'Pulp Fiction', 'year': 1994, 'rating': 5.0}
        ]

        with patch('jobs.sync_to_tmdb.load_list_mappings', return_value={}), \
             patch('jobs.sync_to_tmdb.save_list_mappings') as mock_save, \
             patch('jobs.sync_to_tmdb.get_top_rated_films', new_callable=AsyncMock) as mock_get_films, \
             patch('jobs.sync_to_tmdb.TMDbService') as mock_service_class:

            mock_get_films.side_effect = [
                {'films': mock_films_user1, 'films_count': 1},
                {'films': mock_films_user2, 'films_count': 1}
            ]

            mock_service = Mock()
            mock_service.get_or_create_list.side_effect = [11111, 22222]
            mock_service.update_list_with_movies.return_value = {
                'success': True,
                'total_films': 1,
                'matched': 1,
                'added': 1,
                'not_matched': []
            }
            mock_service_class.return_value = mock_service

            await sync_to_tmdb_job(['user1', 'user2'])

            assert "Starting TMDb sync job for 2 user(s) (one list per user)" in caplog.text
            assert "Processing user: user1" in caplog.text
            assert "Processing user: user2" in caplog.text
            assert mock_get_films.call_count == 2
            assert mock_service.get_or_create_list.call_count == 2
            mock_save.assert_called_once_with({"user1": 11111, "user2": 22222})

    @pytest.mark.asyncio
    async def test_sync_user_fetch_error(self, monkeypatch, caplog):
        """Test job continues when one user fetch fails"""
        monkeypatch.setenv('TMDB_SYNC_ENABLED', 'true')
        monkeypatch.setenv('TMDB_API_KEY', 'test_key')
        monkeypatch.setenv('TMDB_V4_ACCESS_TOKEN', 'test_token')

        mock_films = [
            {'title': 'Pulp Fiction', 'year': 1994, 'rating': 5.0}
        ]

        with patch('jobs.sync_to_tmdb.load_list_mappings', return_value={}), \
             patch('jobs.sync_to_tmdb.save_list_mappings') as mock_save, \
             patch('jobs.sync_to_tmdb.get_top_rated_films', new_callable=AsyncMock) as mock_get_films, \
             patch('jobs.sync_to_tmdb.TMDbService') as mock_service_class:

            # First user fails, second succeeds
            mock_get_films.side_effect = [
                Exception("User not found"),
                {'films': mock_films, 'films_count': 1}
            ]

            mock_service = Mock()
            mock_service.get_or_create_list.return_value = 67890
            mock_service.update_list_with_movies.return_value = {
                'success': True,
                'total_films': 1,
                'matched': 1,
                'added': 1,
                'not_matched': []
            }
            mock_service_class.return_value = mock_service

            await sync_to_tmdb_job(['baduser', 'gooduser'])

            assert "Error processing baduser" in caplog.text
            assert "Successfully synced gooduser's list" in caplog.text

    @pytest.mark.asyncio
    async def test_sync_no_films_found(self, monkeypatch, caplog):
        """Test job when user has no films"""
        monkeypatch.setenv('TMDB_SYNC_ENABLED', 'true')
        monkeypatch.setenv('TMDB_API_KEY', 'test_key')
        monkeypatch.setenv('TMDB_V4_ACCESS_TOKEN', 'test_token')

        with patch('jobs.sync_to_tmdb.load_list_mappings', return_value={}), \
             patch('jobs.sync_to_tmdb.save_list_mappings'), \
             patch('jobs.sync_to_tmdb.get_top_rated_films', new_callable=AsyncMock) as mock_get_films, \
             patch('jobs.sync_to_tmdb.TMDbService') as mock_service_class:

            mock_get_films.return_value = {'films': [], 'films_count': 0}

            mock_service = Mock()
            mock_service.get_or_create_list.return_value = 12345
            mock_service_class.return_value = mock_service

            await sync_to_tmdb_job(['testuser'])

            assert "No top-rated films found for testuser" in caplog.text
            # Should not try to sync if no films
            mock_service.update_list_with_movies.assert_not_called()

    @pytest.mark.asyncio
    async def test_sync_with_unmatched_films(self, monkeypatch, caplog):
        """Test job logs unmatched films"""
        monkeypatch.setenv('TMDB_SYNC_ENABLED', 'true')
        monkeypatch.setenv('TMDB_API_KEY', 'test_key')
        monkeypatch.setenv('TMDB_V4_ACCESS_TOKEN', 'test_token')

        mock_films = [
            {'title': 'The Godfather', 'year': 1972, 'rating': 5.0},
            {'title': 'Unknown Movie', 'year': 2025, 'rating': 4.0}
        ]

        with patch('jobs.sync_to_tmdb.load_list_mappings', return_value={"testuser": 12345}), \
             patch('jobs.sync_to_tmdb.save_list_mappings'), \
             patch('jobs.sync_to_tmdb.get_top_rated_films', new_callable=AsyncMock) as mock_get_films, \
             patch('jobs.sync_to_tmdb.TMDbService') as mock_service_class:

            mock_get_films.return_value = {'films': mock_films, 'films_count': 2}

            mock_service = Mock()
            mock_service.update_list_with_movies.return_value = {
                'success': True,
                'total_films': 2,
                'matched': 1,
                'added': 1,
                'not_matched': ['Unknown Movie (2025)']
            }
            mock_service_class.return_value = mock_service

            await sync_to_tmdb_job(['testuser'])

            assert "Films not found on TMDb" in caplog.text

    @pytest.mark.asyncio
    async def test_sync_exception_handling(self, monkeypatch, caplog):
        """Test job handles unexpected exceptions"""
        monkeypatch.setenv('TMDB_SYNC_ENABLED', 'true')
        monkeypatch.setenv('TMDB_API_KEY', 'test_key')
        monkeypatch.setenv('TMDB_V4_ACCESS_TOKEN', 'test_token')

        with patch('jobs.sync_to_tmdb.load_list_mappings', side_effect=Exception("Unexpected error")):
            await sync_to_tmdb_job(['testuser'])

            assert "Error in TMDb sync job" in caplog.text


class TestRunSyncJob:
    """Tests for run_sync_job wrapper function"""

    def test_run_sync_job_success(self, monkeypatch):
        """Test successful execution of sync job wrapper"""
        monkeypatch.setenv('TMDB_SYNC_ENABLED', 'false')  # Disabled so it exits early

        # Should not raise any exceptions
        run_sync_job(['testuser'])

    def test_run_sync_job_exception_handling(self, caplog, monkeypatch):
        """Test sync job wrapper handles exceptions"""
        monkeypatch.setenv('TMDB_SYNC_ENABLED', 'false')  # Disable to avoid actual API calls

        with patch('jobs.sync_to_tmdb.sync_to_tmdb_job', new_callable=AsyncMock, side_effect=Exception("Async error")):
            run_sync_job(['testuser'])

            assert "Error running sync job wrapper" in caplog.text
