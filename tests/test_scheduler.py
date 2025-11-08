"""Tests for jobs/scheduler.py"""
import pytest
import logging
from unittest.mock import patch, Mock, MagicMock
import pytz
from jobs.scheduler import (
    get_cron_config,
    validate_cron_expression,
    init_scheduler,
    shutdown_scheduler,
    get_scheduler
)


class TestGetCronConfig:
    """Test suite for get_cron_config function"""

    def test_get_cron_config_defaults(self, monkeypatch):
        """Test get_cron_config with default values"""
        # Clear environment variables
        monkeypatch.delenv('CRON_ENABLED', raising=False)
        monkeypatch.delenv('CRON_SCHEDULE', raising=False)
        monkeypatch.delenv('CRON_TIMEZONE', raising=False)
        monkeypatch.delenv('CRON_TARGET_USERS', raising=False)

        config = get_cron_config()

        assert config['enabled'] is False
        assert config['schedule'] == '0 0 * * *'
        assert config['timezone'] == 'UTC'
        assert config['target_users'] == []

    def test_get_cron_config_enabled_true(self, monkeypatch):
        """Test get_cron_config when cron is enabled"""
        monkeypatch.setenv('CRON_ENABLED', 'true')

        config = get_cron_config()

        assert config['enabled'] is True

    def test_get_cron_config_enabled_false(self, monkeypatch):
        """Test get_cron_config when explicitly disabled"""
        monkeypatch.setenv('CRON_ENABLED', 'false')

        config = get_cron_config()

        assert config['enabled'] is False

    def test_get_cron_config_enabled_case_insensitive(self, monkeypatch):
        """Test that enabled check is case insensitive"""
        monkeypatch.setenv('CRON_ENABLED', 'TRUE')
        config = get_cron_config()
        assert config['enabled'] is True

        monkeypatch.setenv('CRON_ENABLED', 'False')
        config = get_cron_config()
        assert config['enabled'] is False

    def test_get_cron_config_custom_schedule(self, monkeypatch):
        """Test get_cron_config with custom schedule"""
        monkeypatch.setenv('CRON_SCHEDULE', '0 2 * * *')

        config = get_cron_config()

        assert config['schedule'] == '0 2 * * *'

    def test_get_cron_config_custom_timezone(self, monkeypatch):
        """Test get_cron_config with custom timezone"""
        monkeypatch.setenv('CRON_TIMEZONE', 'America/New_York')

        config = get_cron_config()

        assert config['timezone'] == 'America/New_York'

    def test_get_cron_config_single_user(self, monkeypatch):
        """Test get_cron_config with single target user"""
        monkeypatch.setenv('CRON_TARGET_USERS', 'testuser')

        config = get_cron_config()

        assert config['target_users'] == ['testuser']

    def test_get_cron_config_multiple_users(self, monkeypatch):
        """Test get_cron_config with multiple target users"""
        monkeypatch.setenv('CRON_TARGET_USERS', 'user1,user2,user3')

        config = get_cron_config()

        assert config['target_users'] == ['user1', 'user2', 'user3']

    def test_get_cron_config_users_with_spaces(self, monkeypatch):
        """Test get_cron_config trims spaces from usernames"""
        monkeypatch.setenv('CRON_TARGET_USERS', 'user1, user2 , user3')

        config = get_cron_config()

        assert config['target_users'] == ['user1', 'user2', 'user3']

    def test_get_cron_config_empty_users(self, monkeypatch):
        """Test get_cron_config with empty users string"""
        monkeypatch.setenv('CRON_TARGET_USERS', '')

        config = get_cron_config()

        assert config['target_users'] == []

    def test_get_cron_config_users_with_empty_values(self, monkeypatch):
        """Test get_cron_config filters out empty values"""
        monkeypatch.setenv('CRON_TARGET_USERS', 'user1,,user2, ,user3')

        config = get_cron_config()

        assert config['target_users'] == ['user1', 'user2', 'user3']


class TestValidateCronExpression:
    """Test suite for validate_cron_expression function"""

    def test_valid_cron_expression_standard(self):
        """Test validation of standard cron expressions"""
        valid_expressions = [
            '0 0 * * *',     # Daily at midnight
            '0 */6 * * *',   # Every 6 hours
            '0 9 * * 1',     # Every Monday at 9 AM
            '30 2 * * *',    # Daily at 2:30 AM
            '0 0 1 * *',     # First day of month
            '*/5 * * * *',   # Every 5 minutes
            '0 0 * * 0',     # Every Sunday
        ]

        for expr in valid_expressions:
            assert validate_cron_expression(expr) is True

    def test_invalid_cron_expression_too_few_fields(self):
        """Test validation fails with too few fields"""
        assert validate_cron_expression('0 0 * *') is False

    def test_invalid_cron_expression_too_many_fields(self):
        """Test validation fails with too many fields"""
        assert validate_cron_expression('0 0 * * * *') is False

    def test_invalid_cron_expression_bad_syntax(self):
        """Test validation fails with bad syntax"""
        assert validate_cron_expression('invalid cron expression') is False

    def test_invalid_cron_expression_out_of_range(self):
        """Test validation fails with out of range values"""
        # Hour > 23
        assert validate_cron_expression('0 25 * * *') is False

    def test_invalid_cron_expression_empty(self):
        """Test validation fails with empty string"""
        assert validate_cron_expression('') is False

    def test_valid_cron_expression_with_ranges(self):
        """Test validation of cron expressions with ranges"""
        assert validate_cron_expression('0 9-17 * * *') is True

    def test_valid_cron_expression_with_lists(self):
        """Test validation of cron expressions with lists"""
        assert validate_cron_expression('0 0 * * 1,3,5') is True

    def test_valid_cron_expression_complex(self):
        """Test validation of complex cron expressions"""
        assert validate_cron_expression('*/15 9-17 * * 1-5') is True


class TestInitScheduler:
    """Test suite for init_scheduler function"""

    def test_init_scheduler_disabled(self, monkeypatch, caplog):
        """Test that scheduler is not initialized when disabled"""
        monkeypatch.setenv('CRON_ENABLED', 'false')

        init_scheduler()

        assert 'Cron job is disabled' in caplog.text

    def test_init_scheduler_no_target_users(self, monkeypatch, caplog):
        """Test that scheduler warns when no target users configured"""
        monkeypatch.setenv('CRON_ENABLED', 'true')
        monkeypatch.setenv('CRON_TARGET_USERS', '')

        init_scheduler()

        assert 'No target users configured' in caplog.text

    def test_init_scheduler_invalid_cron_expression(self, monkeypatch, caplog):
        """Test that scheduler logs error with invalid cron expression"""
        monkeypatch.setenv('CRON_ENABLED', 'true')
        monkeypatch.setenv('CRON_TARGET_USERS', 'testuser')
        monkeypatch.setenv('CRON_SCHEDULE', 'invalid')

        init_scheduler()

        assert 'Invalid cron expression' in caplog.text

    def test_init_scheduler_invalid_timezone(self, monkeypatch, caplog):
        """Test that scheduler logs error with invalid timezone"""
        monkeypatch.setenv('CRON_ENABLED', 'true')
        monkeypatch.setenv('CRON_TARGET_USERS', 'testuser')
        monkeypatch.setenv('CRON_SCHEDULE', '0 0 * * *')
        monkeypatch.setenv('CRON_TIMEZONE', 'Invalid/Timezone')

        init_scheduler()

        assert 'Invalid timezone' in caplog.text

    def test_init_scheduler_success(self, monkeypatch, caplog):
        """Test successful scheduler initialization"""
        monkeypatch.setenv('CRON_ENABLED', 'true')
        monkeypatch.setenv('CRON_TARGET_USERS', 'testuser')
        monkeypatch.setenv('CRON_SCHEDULE', '0 0 * * *')
        monkeypatch.setenv('CRON_TIMEZONE', 'UTC')

        with patch('jobs.scheduler.BackgroundScheduler') as mock_scheduler_class:
            mock_scheduler = MagicMock()
            mock_scheduler_class.return_value = mock_scheduler
            mock_job = MagicMock()
            mock_job.next_run_time = '2025-01-01 00:00:00'
            mock_scheduler.get_job.return_value = mock_job

            init_scheduler()

            # Verify scheduler was created
            mock_scheduler_class.assert_called_once()
            # Verify job was added
            mock_scheduler.add_job.assert_called_once()
            # Verify scheduler was started
            mock_scheduler.start.assert_called_once()
            # Verify success log
            assert 'Scheduler started successfully' in caplog.text

    def test_init_scheduler_sets_timezone(self, monkeypatch):
        """Test that scheduler is created with correct timezone"""
        monkeypatch.setenv('CRON_ENABLED', 'true')
        monkeypatch.setenv('CRON_TARGET_USERS', 'testuser')
        monkeypatch.setenv('CRON_TIMEZONE', 'America/Los_Angeles')

        with patch('jobs.scheduler.BackgroundScheduler') as mock_scheduler_class:
            mock_scheduler = MagicMock()
            mock_scheduler_class.return_value = mock_scheduler
            mock_job = MagicMock()
            mock_job.next_run_time = '2025-01-01 00:00:00'
            mock_scheduler.get_job.return_value = mock_job

            init_scheduler()

            # Verify timezone was passed to scheduler
            call_kwargs = mock_scheduler_class.call_args[1]
            assert 'timezone' in call_kwargs
            assert call_kwargs['timezone'] == pytz.timezone('America/Los_Angeles')

    def test_init_scheduler_job_configuration(self, monkeypatch):
        """Test that job is configured correctly"""
        monkeypatch.setenv('CRON_ENABLED', 'true')
        monkeypatch.setenv('CRON_TARGET_USERS', 'user1,user2')
        monkeypatch.setenv('CRON_SCHEDULE', '0 2 * * *')

        with patch('jobs.scheduler.BackgroundScheduler') as mock_scheduler_class:
            mock_scheduler = MagicMock()
            mock_scheduler_class.return_value = mock_scheduler
            mock_job = MagicMock()
            mock_job.next_run_time = '2025-01-01 00:00:00'
            mock_scheduler.get_job.return_value = mock_job

            init_scheduler()

            # Verify job configuration
            call_kwargs = mock_scheduler.add_job.call_args[1]
            assert call_kwargs['id'] == 'fetch_top_movies'
            assert call_kwargs['name'] == 'Fetch Top 15 Movies'
            assert call_kwargs['replace_existing'] is True
            assert call_kwargs['misfire_grace_time'] == 3600
            assert call_kwargs['args'] == [['user1', 'user2']]


class TestShutdownScheduler:
    """Test suite for shutdown_scheduler function"""

    def test_shutdown_scheduler_when_running(self, caplog):
        """Test shutting down a running scheduler"""
        mock_scheduler = MagicMock()
        mock_scheduler.running = True

        with patch('jobs.scheduler.scheduler', mock_scheduler):
            shutdown_scheduler()

            mock_scheduler.shutdown.assert_called_once()
            assert 'Shutting down scheduler' in caplog.text
            assert 'Scheduler shut down successfully' in caplog.text

    def test_shutdown_scheduler_when_not_running(self):
        """Test shutting down when scheduler is not running"""
        mock_scheduler = MagicMock()
        mock_scheduler.running = False

        with patch('jobs.scheduler.scheduler', mock_scheduler):
            shutdown_scheduler()

            # Should not call shutdown
            mock_scheduler.shutdown.assert_not_called()

    def test_shutdown_scheduler_when_none(self):
        """Test shutting down when scheduler is None"""
        with patch('jobs.scheduler.scheduler', None):
            # Should not raise an error
            shutdown_scheduler()


class TestGetScheduler:
    """Test suite for get_scheduler function"""

    def test_get_scheduler_when_initialized(self):
        """Test getting scheduler when it's initialized"""
        mock_scheduler = MagicMock()

        with patch('jobs.scheduler.scheduler', mock_scheduler):
            result = get_scheduler()

            assert result is mock_scheduler

    def test_get_scheduler_when_none(self):
        """Test getting scheduler when it's None"""
        with patch('jobs.scheduler.scheduler', None):
            result = get_scheduler()

            assert result is None
