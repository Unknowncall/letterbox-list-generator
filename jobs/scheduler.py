"""Scheduler configuration for cron jobs"""

import os
from typing import Optional

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

from jobs.sync_to_tmdb import run_sync_job
from utils.logger import logger

# Load environment variables
load_dotenv()


class SchedulerManager:
    """Singleton manager for the background scheduler"""

    _instance: Optional["SchedulerManager"] = None
    _scheduler: Optional[BackgroundScheduler] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def scheduler(self) -> Optional[BackgroundScheduler]:
        """Get the scheduler instance"""
        return self._scheduler

    @scheduler.setter
    def scheduler(self, value: Optional[BackgroundScheduler]) -> None:
        """Set the scheduler instance"""
        self._scheduler = value

    @scheduler.deleter
    def scheduler(self) -> None:
        """Delete the scheduler instance"""
        self._scheduler = None


# Singleton instance
_scheduler_manager = SchedulerManager()


def get_cron_config() -> dict:
    """
    Load cron configuration from environment variables

    Returns:
        Dictionary with cron configuration
    """
    return {
        "enabled": os.getenv("CRON_ENABLED", "false").lower() == "true",
        "schedule": os.getenv("CRON_SCHEDULE", "0 0 * * *"),  # Default: daily at midnight
        "timezone": os.getenv("CRON_TIMEZONE", "UTC"),
        "target_users": [u.strip() for u in os.getenv("CRON_TARGET_USERS", "").split(",") if u.strip()],
    }


def validate_cron_expression(cron_expr: str) -> bool:
    """
    Validate a cron expression

    Args:
        cron_expr: Cron expression to validate

    Returns:
        True if valid, False otherwise
    """
    try:
        # Try to parse the cron expression
        parts = cron_expr.split()
        if len(parts) != 5:
            return False
        # CronTrigger will validate the expression
        CronTrigger.from_crontab(cron_expr)
        return True
    except (ValueError, TypeError, AttributeError):
        return False


def init_scheduler() -> None:
    """
    Initialize and configure the APScheduler
    """
    config = get_cron_config()

    if not config["enabled"]:
        logger.info("Cron job is disabled (CRON_ENABLED=false)")
        return

    if not config["target_users"]:
        logger.warning("No target users configured (CRON_TARGET_USERS is empty)")
        return

    if not validate_cron_expression(config["schedule"]):
        logger.error("Invalid cron expression: %s", config["schedule"])
        return

    try:
        # Validate timezone
        tz = pytz.timezone(config["timezone"])

        # Create scheduler with timezone
        _scheduler_manager.scheduler = BackgroundScheduler(timezone=tz)

        # Parse cron expression and add job
        trigger = CronTrigger.from_crontab(config["schedule"], timezone=tz)

        _scheduler_manager.scheduler.add_job(
            func=run_sync_job,
            trigger=trigger,
            args=[config["target_users"]],
            id="sync_to_tmdb",
            name="Sync Top Rated Movies to TMDb",
            replace_existing=True,
            misfire_grace_time=3600,  # Allow 1 hour grace period for missed jobs
        )

        _scheduler_manager.scheduler.start()

        logger.info(
            "Scheduler started successfully:\n"
            "  - Schedule: %s\n"
            "  - Timezone: %s\n"
            "  - Target users: %s\n"
            "  - Next run: %s",
            config["schedule"],
            config["timezone"],
            ", ".join(config["target_users"]),
            _scheduler_manager.scheduler.get_job("sync_to_tmdb").next_run_time,
        )

    except pytz.exceptions.UnknownTimeZoneError:
        logger.error("Invalid timezone: %s", config["timezone"])
    except (ValueError, RuntimeError, OSError) as e:
        logger.error("Error initializing scheduler: %s", str(e))


def shutdown_scheduler() -> None:
    """
    Gracefully shutdown the scheduler
    """
    if _scheduler_manager.scheduler and _scheduler_manager.scheduler.running:
        logger.info("Shutting down scheduler...")
        _scheduler_manager.scheduler.shutdown()
        logger.info("Scheduler shut down successfully")


def get_scheduler() -> Optional[BackgroundScheduler]:
    """
    Get the scheduler instance

    Returns:
        BackgroundScheduler instance or None if not initialized
    """
    return _scheduler_manager.scheduler
