"""Scheduler configuration for cron jobs"""
import os
import logging
from typing import Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv
import pytz
from jobs.fetch_top_movies import run_sync_job

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: Optional[BackgroundScheduler] = None


def get_cron_config() -> dict:
    """
    Load cron configuration from environment variables
    
    Returns:
        Dictionary with cron configuration
    """
    return {
        'enabled': os.getenv('CRON_ENABLED', 'false').lower() == 'true',
        'schedule': os.getenv('CRON_SCHEDULE', '0 0 * * *'),  # Default: daily at midnight
        'timezone': os.getenv('CRON_TIMEZONE', 'UTC'),
        'target_users': [u.strip() for u in os.getenv('CRON_TARGET_USERS', '').split(',') if u.strip()]
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
    except Exception:
        return False


def init_scheduler() -> None:
    """
    Initialize and configure the APScheduler
    """
    global scheduler
    
    config = get_cron_config()
    
    if not config['enabled']:
        logger.info("Cron job is disabled (CRON_ENABLED=false)")
        return
    
    if not config['target_users']:
        logger.warning("No target users configured (CRON_TARGET_USERS is empty)")
        return
    
    if not validate_cron_expression(config['schedule']):
        logger.error(f"Invalid cron expression: {config['schedule']}")
        return
    
    try:
        # Validate timezone
        tz = pytz.timezone(config['timezone'])
        
        # Create scheduler with timezone
        scheduler = BackgroundScheduler(timezone=tz)
        
        # Parse cron expression and add job
        trigger = CronTrigger.from_crontab(config['schedule'], timezone=tz)
        
        scheduler.add_job(
            func=run_sync_job,
            trigger=trigger,
            args=[config['target_users']],
            id='fetch_top_movies',
            name='Fetch Top 15 Movies',
            replace_existing=True,
            misfire_grace_time=3600  # Allow 1 hour grace period for missed jobs
        )
        
        scheduler.start()
        
        logger.info(
            f"Scheduler started successfully:\n"
            f"  - Schedule: {config['schedule']}\n"
            f"  - Timezone: {config['timezone']}\n"
            f"  - Target users: {', '.join(config['target_users'])}\n"
            f"  - Next run: {scheduler.get_job('fetch_top_movies').next_run_time}"
        )
        
    except pytz.exceptions.UnknownTimeZoneError:
        logger.error(f"Invalid timezone: {config['timezone']}")
    except Exception as e:
        logger.error(f"Error initializing scheduler: {str(e)}")


def shutdown_scheduler() -> None:
    """
    Gracefully shutdown the scheduler
    """
    global scheduler
    
    if scheduler and scheduler.running:
        logger.info("Shutting down scheduler...")
        scheduler.shutdown()
        logger.info("Scheduler shut down successfully")


def get_scheduler() -> Optional[BackgroundScheduler]:
    """
    Get the scheduler instance
    
    Returns:
        BackgroundScheduler instance or None if not initialized
    """
    return scheduler
