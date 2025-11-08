"""Job to sync top-rated movies to TMDb list (one list per user)"""

import asyncio
import os
from datetime import datetime
from typing import Dict, List

from dotenv import load_dotenv

from controllers.users import get_top_rated_films
from logger import logger
from services.tmdb_service import TMDbService

# Load environment variables
load_dotenv()


def get_tmdb_config() -> dict:
    """
    Load TMDb configuration from environment variables

    Returns:
        Dictionary with TMDb configuration
    """
    return {
        "enabled": os.getenv("TMDB_SYNC_ENABLED", "false").lower() == "true",
        "api_key": os.getenv("TMDB_API_KEY", ""),
        "v4_access_token": os.getenv("TMDB_V4_ACCESS_TOKEN", ""),
        "limit": int(os.getenv("TMDB_SYNC_LIMIT", "100")),
        "page_size": int(os.getenv("TMDB_SYNC_LIMIT", "100")),
        "sort_by": os.getenv("TMDB_SYNC_SORT_BY", "rating"),
        "sort_order": os.getenv("TMDB_SYNC_SORT_ORDER", "desc"),
    }


def _log_sync_results(username: str, list_id: int, sync_result: Dict) -> None:
    """Log the results of a sync operation"""
    logger.info(
        "Successfully synced %s's list (ID: %s):\n"
        "  - Total films: %d\n"
        "  - Matched on TMDb: %d\n"
        "  - Added to list: %d\n"
        "  - Not matched: %d",
        username,
        list_id,
        sync_result["total_films"],
        sync_result["matched"],
        sync_result["added"],
        len(sync_result["not_matched"]),
    )

    if sync_result["not_matched"]:
        unmatched_preview = ", ".join(sync_result["not_matched"][:5])
        logger.info("Films not found on TMDb: %s", unmatched_preview)
        if len(sync_result["not_matched"]) > 5:
            logger.info("  ... and %d more", len(sync_result["not_matched"]) - 5)


async def _process_user(username: str, config: Dict, tmdb_service: TMDbService) -> None:
    """Process a single user's sync to TMDb"""
    logger.info("\n%s", "=" * 60)
    logger.info("Processing user: %s", username)
    logger.info("%s", "=" * 60)

    # Get or create list for this user
    list_name = f"{username}'s Top Rated Movies"
    list_description = f"Top-rated and liked movies from Letterboxd user {username}, automatically synced"

    list_id = tmdb_service.get_or_create_list(list_name=list_name, description=list_description)

    if not list_id:
        logger.error("Failed to get or create TMDb list for %s", username)
        return

    # Fetch top-rated films for this user
    logger.info("Fetching top movies for %s...", username)

    result = await get_top_rated_films(
        username=username,
        limit=config["limit"],
        page=1,
        page_size=config["page_size"],
        sort_by=config["sort_by"],
        sort_order=config["sort_order"],
    )

    films = result.get("films", [])
    films_count = len(films)

    if films_count == 0:
        logger.warning("No top-rated films found for %s", username)
        return

    logger.info("Found %d top-rated films for %s", films_count, username)

    # Sync to this user's TMDb list
    sync_result = tmdb_service.update_list_with_movies(list_id=list_id, films=films, clear_first=True)

    # Log results
    if sync_result["success"]:
        _log_sync_results(username, list_id, sync_result)
    else:
        logger.error("Failed to sync films to TMDb for %s", username)


async def sync_to_tmdb_job(usernames: List[str]) -> None:
    """
    Fetch top-rated movies for users and sync each user to their own TMDb list

    Creates one list per user. If a list doesn't exist, it's created.
    If it exists, it's overwritten with the latest top-rated movies.

    Args:
        usernames: List of Letterboxd usernames to process
    """
    config = get_tmdb_config()

    if not config["enabled"]:
        logger.info("TMDb sync is disabled (TMDB_SYNC_ENABLED=false)")
        return

    if not config["api_key"]:
        logger.error("TMDb API key not configured (TMDB_API_KEY)")
        return

    if not config["v4_access_token"]:
        logger.error("TMDb v4 access token not configured (TMDB_V4_ACCESS_TOKEN)")
        return

    if not usernames:
        logger.warning("No usernames provided for TMDb sync")
        return

    logger.info("[%s] Starting TMDb sync job for %d user(s) (one list per user)", datetime.now(), len(usernames))

    # Debug: Log config (masked)
    logger.info(
        "TMDb config - API key set: %s, V4 token set: %s",
        bool(config["api_key"]),
        bool(config["v4_access_token"]),
    )
    logger.info("TMDb API key length: %d", len(config["api_key"]) if config["api_key"] else 0)
    logger.info("TMDb V4 token length: %d", len(config["v4_access_token"]) if config["v4_access_token"] else 0)

    try:
        # Initialize TMDb service
        tmdb_service = TMDbService(api_key=config["api_key"], v4_access_token=config["v4_access_token"])

        # Process each user separately
        for username in usernames:
            try:
                await _process_user(username, config, tmdb_service)
            except (ValueError, ConnectionError, TimeoutError, KeyError, AttributeError, RuntimeError) as e:
                logger.error("Error processing %s: %s", username, str(e))
                # Continue with other users

    except (ValueError, ConnectionError, TimeoutError, RuntimeError) as e:
        logger.error("Error in TMDb sync job: %s", str(e))

    logger.info("\n[%s] Completed TMDb sync job", datetime.now())


def run_sync_job(usernames: List[str]) -> None:
    """
    Synchronous wrapper for the async job (required by APScheduler)

    Args:
        usernames: List of Letterboxd usernames to process
    """
    try:
        # Run the async function in a new event loop
        asyncio.run(sync_to_tmdb_job(usernames))
    except (RuntimeError, ValueError) as e:
        logger.error("Error running sync job wrapper: %s", str(e))
