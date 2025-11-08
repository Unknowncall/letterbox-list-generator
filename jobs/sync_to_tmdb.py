"""Job to sync top-rated movies to TMDb list (one list per user)"""
import os
import json
import logging
from datetime import datetime
from typing import List, Dict
from pathlib import Path
from dotenv import load_dotenv
from controllers.users import get_top_rated_films
from services.tmdb_service import TMDbService

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Path to store list mappings
LIST_MAPPINGS_FILE = Path(__file__).parent.parent / 'tmdb_list_mappings.json'


def load_list_mappings() -> Dict[str, int]:
    """
    Load username -> list_id mappings from JSON file

    Returns:
        Dictionary mapping usernames to TMDb list IDs
    """
    if LIST_MAPPINGS_FILE.exists():
        try:
            with open(LIST_MAPPINGS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading list mappings: {str(e)}")
            return {}
    return {}


def save_list_mappings(mappings: Dict[str, int]) -> None:
    """
    Save username -> list_id mappings to JSON file

    Args:
        mappings: Dictionary mapping usernames to TMDb list IDs
    """
    try:
        with open(LIST_MAPPINGS_FILE, 'w') as f:
            json.dump(mappings, f, indent=2)
        logger.info(f"Saved list mappings to {LIST_MAPPINGS_FILE}")
    except Exception as e:
        logger.error(f"Error saving list mappings: {str(e)}")


def get_tmdb_config() -> dict:
    """
    Load TMDb configuration from environment variables

    Returns:
        Dictionary with TMDb configuration
    """
    return {
        'enabled': os.getenv('TMDB_SYNC_ENABLED', 'false').lower() == 'true',
        'api_key': os.getenv('TMDB_API_KEY', ''),
        'v4_access_token': os.getenv('TMDB_V4_ACCESS_TOKEN', ''),
        'limit': int(os.getenv('TMDB_SYNC_LIMIT', '100')),
        'page_size': int(os.getenv('TMDB_SYNC_LIMIT', '100')),
        'sort_by': os.getenv('TMDB_SYNC_SORT_BY', 'rating'),
        'sort_order': os.getenv('TMDB_SYNC_SORT_ORDER', 'desc'),
    }


async def sync_to_tmdb_job(usernames: List[str]) -> None:
    """
    Fetch top-rated movies for users and sync each user to their own TMDb list

    Creates one list per user. If a list doesn't exist, it's created.
    If it exists, it's overwritten with the latest top-rated movies.

    Args:
        usernames: List of Letterboxd usernames to process
    """
    config = get_tmdb_config()

    if not config['enabled']:
        logger.info("TMDb sync is disabled (TMDB_SYNC_ENABLED=false)")
        return

    if not config['api_key']:
        logger.error("TMDb API key not configured (TMDB_API_KEY)")
        return

    if not config['v4_access_token']:
        logger.error("TMDb v4 access token not configured (TMDB_V4_ACCESS_TOKEN)")
        return

    if not usernames:
        logger.warning("No usernames provided for TMDb sync")
        return

    logger.info(f"[{datetime.now()}] Starting TMDb sync job for {len(usernames)} user(s) (one list per user)")

    # Debug: Log config (masked)
    logger.info(f"TMDb config - API key set: {bool(config['api_key'])}, V4 token set: {bool(config['v4_access_token'])}")
    logger.info(f"TMDb API key length: {len(config['api_key']) if config['api_key'] else 0}")
    logger.info(f"TMDb V4 token length: {len(config['v4_access_token']) if config['v4_access_token'] else 0}")

    try:
        # Load existing list mappings
        list_mappings = load_list_mappings()
        mappings_updated = False
        # Initialize TMDb service
        tmdb_service = TMDbService(
            api_key=config['api_key'],
            v4_access_token=config['v4_access_token']
        )

        # Process each user separately
        for username in usernames:
            try:
                logger.info(f"\n{'='*60}")
                logger.info(f"Processing user: {username}")
                logger.info(f"{'='*60}")

                # Get or create list for this user
                list_id = list_mappings.get(username)

                if list_id:
                    logger.info(f"Using existing TMDb list ID {list_id} for {username}")
                else:
                    # Create a new list for this user
                    list_name = f"{username}'s Top Rated Movies"
                    list_description = f"Top-rated and liked movies from Letterboxd user {username}, automatically synced"

                    list_id = tmdb_service.get_or_create_list(
                        list_name=list_name,
                        description=list_description
                    )

                    if not list_id:
                        logger.error(f"Failed to create TMDb list for {username}")
                        continue

                    # Save the mapping
                    list_mappings[username] = list_id
                    mappings_updated = True

                    logger.info(
                        f"Created new TMDb list for {username}:\n"
                        f"  - Name: {list_name}\n"
                        f"  - ID: {list_id}"
                    )

                # Fetch top-rated films for this user
                logger.info(f"Fetching top movies for {username}...")

                result = await get_top_rated_films(
                    username=username,
                    limit=config['limit'],
                    page=1,
                    page_size=config['page_size'],
                    sort_by=config['sort_by'],
                    sort_order=config['sort_order']
                )

                films = result.get('films', [])
                films_count = len(films)

                if films_count == 0:
                    logger.warning(f"No top-rated films found for {username}")
                    continue

                logger.info(f"Found {films_count} top-rated films for {username}")

                # Sync to this user's TMDb list
                sync_result = tmdb_service.update_list_with_movies(
                    list_id=list_id,
                    films=films,
                    clear_first=True
                )

                # Log results
                if sync_result['success']:
                    logger.info(
                        f"Successfully synced {username}'s list (ID: {list_id}):\n"
                        f"  - Total films: {sync_result['total_films']}\n"
                        f"  - Matched on TMDb: {sync_result['matched']}\n"
                        f"  - Added to list: {sync_result['added']}\n"
                        f"  - Not matched: {len(sync_result['not_matched'])}"
                    )

                    if sync_result['not_matched']:
                        unmatched_preview = ', '.join(sync_result['not_matched'][:5])
                        logger.info(f"Films not found on TMDb: {unmatched_preview}")
                        if len(sync_result['not_matched']) > 5:
                            logger.info(f"  ... and {len(sync_result['not_matched']) - 5} more")
                else:
                    logger.error(f"Failed to sync films to TMDb for {username}")

            except Exception as e:
                logger.error(f"Error processing {username}: {str(e)}")
                # Continue with other users

        # Save updated mappings if any were created
        if mappings_updated:
            save_list_mappings(list_mappings)
            logger.info(f"\nList mappings saved: {len(list_mappings)} users")

    except Exception as e:
        logger.error(f"Error in TMDb sync job: {str(e)}")

    logger.info(f"\n[{datetime.now()}] Completed TMDb sync job")


def run_sync_job(usernames: List[str]) -> None:
    """
    Synchronous wrapper for the async job (required by APScheduler)

    Args:
        usernames: List of Letterboxd usernames to process
    """
    import asyncio

    try:
        # Run the async function in a new event loop
        asyncio.run(sync_to_tmdb_job(usernames))
    except Exception as e:
        logger.error(f"Error running sync job wrapper: {str(e)}")
