"""Cron job to fetch top 15 movies for users"""
import logging
from datetime import datetime
from typing import List
from controllers.users import get_top_rated_films

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def fetch_top_movies_job(usernames: List[str]) -> None:
    """
    Fetch the top 15 movies for each specified user
    
    Args:
        usernames: List of Letterboxd usernames to process
    """
    logger.info(f"[{datetime.now()}] Starting top movies fetch job for {len(usernames)} user(s)")
    
    for username in usernames:
        try:
            logger.info(f"Fetching top 15 movies for user: {username}")
            
            # Fetch top 15 movies (sorted by rating, descending)
            result = await get_top_rated_films(
                username=username,
                limit=15,
                page=1,
                page_size=15,
                sort_by="rating",
                sort_order="desc"
            )
            
            films_count = result.get('films_count', 0)
            logger.info(f"Successfully fetched {films_count} top movies for {username}")
            
            # Log the top movies (you can modify this to save to DB, send notification, etc.)
            for idx, film in enumerate(result.get('films', []), 1):
                logger.info(
                    f"  {idx}. {film.get('title')} ({film.get('year')}) - "
                    f"Rating: {film.get('rating')}/5.0"
                )
            
        except Exception as e:
            logger.error(f"Error fetching top movies for {username}: {str(e)}")
    
    logger.info(f"[{datetime.now()}] Completed top movies fetch job")


def run_sync_job(usernames: List[str]) -> None:
    """
    Synchronous wrapper for the async job (required by APScheduler)
    
    Args:
        usernames: List of Letterboxd usernames to process
    """
    import asyncio
    
    try:
        # Run the async function in a new event loop
        asyncio.run(fetch_top_movies_job(usernames))
    except Exception as e:
        logger.error(f"Error running sync job wrapper: {str(e)}")
