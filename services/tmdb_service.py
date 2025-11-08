"""TMDb service for managing movie lists"""

import os
import time
from typing import Dict, List, Optional

from tmdbapis import TMDbAPIs

from logger import logger


class TMDbService:
    """Service for interacting with TMDb API"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        v4_access_token: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        """
        Initialize TMDb service

        Args:
            api_key: TMDb API v3 key (optional, will use env var if not provided)
            v4_access_token: TMDb v4 access token for read operations (optional)
            username: TMDb username for v3 authentication (optional)
            password: TMDb password for v3 authentication (optional)
            session_id: Pre-existing session_id for authenticated operations (optional)
        """
        self.api_key = api_key or os.getenv("TMDB_API_KEY")
        self.v4_access_token = v4_access_token or os.getenv("TMDB_V4_ACCESS_TOKEN")
        self.username = username or os.getenv("TMDB_USERNAME")
        self.password = password or os.getenv("TMDB_PASSWORD")
        self.session_id = session_id or os.getenv("TMDB_SESSION_ID")

        if not self.api_key:
            raise ValueError("TMDB_API_KEY is required")

        # Initialize TMDb API
        self.tmdb = TMDbAPIs(self.api_key, v4_access_token=self.v4_access_token, session_id=self.session_id)

        # If username and password provided, authenticate to get session_id
        if self.username and self.password and not self.session_id:
            try:
                logger.info("Authenticating with TMDb using username/password...")
                self.tmdb.authenticate(self.username, self.password)
                self.session_id = self.tmdb.session_id
                logger.info("Successfully authenticated. Session ID obtained.")
            except Exception as e:
                logger.error("Authentication failed: %s", str(e))
                raise

    def search_movie(self, title: str, year: Optional[int] = None) -> Optional[Dict]:
        """
        Search for a movie on TMDb by title and optionally year

        Args:
            title: Movie title
            year: Release year (optional, helps with accuracy)

        Returns:
            Movie data dict with id, title, year, etc. or None if not found
        """
        try:
            # Rate limiting: TMDb allows ~40 requests per 10 seconds
            # Adding 250ms delay = ~4 requests/second to stay well under limit
            time.sleep(0.25)

            # Use the movie_search method from tmdbapis
            search_results = self.tmdb.movie_search(title, year=year)

            if search_results and len(search_results) > 0:
                # Return the first (best) match
                movie = search_results[0]

                # Handle release_date which can be a datetime object or string
                year = None
                if hasattr(movie, "release_date") and movie.release_date:
                    if hasattr(movie.release_date, "year"):
                        # It's a datetime object
                        year = movie.release_date.year
                    elif isinstance(movie.release_date, str):
                        # It's a string like "2019-11-27"
                        year = int(movie.release_date.split("-")[0])

                return {
                    "id": movie.id,
                    "title": movie.title,
                    "year": year,
                    "overview": movie.overview if hasattr(movie, "overview") else "",
                }

            logger.warning("No TMDb match found for: %s (%s)", title, year)
            return None

        except (ConnectionError, TimeoutError, ValueError, KeyError, AttributeError, RuntimeError) as e:
            logger.error("Error searching for movie %s: %s", title, str(e))
            return None

    def get_or_create_list(self, list_name: str, description: str = "") -> Optional[int]:
        """
        Get existing list by name or create a new one

        Args:
            list_name: Name of the list
            description: Description for the list (used when creating)

        Returns:
            List ID or None if operation failed
        """
        if not self.session_id:
            logger.error("Authentication required for list operations. Please provide username/password or session_id.")
            return None

        try:
            # First, try to find an existing list with this name
            logger.info("Checking for existing list: %s", list_name)
            try:
                # Get user's created lists
                user_lists = self.tmdb.created_lists()
                list_count = len(user_lists) if user_lists and hasattr(user_lists, "__len__") else 0
                logger.info("Retrieved %d lists from TMDb", list_count)

                # Log all list names for debugging
                if user_lists:
                    for idx, user_list in enumerate(user_lists):
                        if hasattr(user_list, "name"):
                            list_id_display = user_list.id if hasattr(user_list, "id") else "unknown"
                            logger.info("  List %d: '%s' (ID: %s)", idx + 1, user_list.name, list_id_display)

                # Search for a list with matching name
                for user_list in user_lists:
                    if hasattr(user_list, "name") and user_list.name == list_name:
                        list_id = user_list.id
                        logger.info("Found existing TMDb list: %s (ID: %s)", list_name, list_id)
                        return list_id

                logger.info("No existing list found with name: %s", list_name)
            except (ConnectionError, TimeoutError, ValueError, KeyError, AttributeError) as e:
                logger.error("Error fetching user lists: %s", str(e))
                logger.warning("Could not fetch user lists, will attempt to create new list")
                # Continue to create a new list if we can't fetch existing ones

            # No existing list found, create a new one
            logger.info("Creating new TMDb list: %s", list_name)
            result = self.tmdb.create_list(
                name=list_name, description=description, iso_639_1="en", iso_3166_1="US", public=True
            )

            # Access the id attribute from the TMDbList object
            list_id = result.id if hasattr(result, "id") else None

            if list_id:
                logger.info("Created TMDb list: %s (ID: %s)", list_name, list_id)
                return list_id

            logger.error("Failed to create list: %s", list_name)
            return None

        except (ConnectionError, TimeoutError, ValueError, KeyError, AttributeError, RuntimeError) as e:
            logger.error("Error in get_or_create_list: %s", str(e))
            return None

    def add_movies_to_list(self, list_id: int, movie_ids: List[int]) -> bool:
        """
        Add multiple movies to a TMDb list

        Args:
            list_id: TMDb list ID
            movie_ids: List of TMDb movie IDs

        Returns:
            True if successful, False otherwise
        """
        if not self.session_id:
            logger.error("Authentication required for list operations")
            return False

        if not movie_ids:
            logger.warning("No movie IDs provided to add to list")
            return True  # Nothing to do, but not an error

        try:
            # Get the list object
            list_obj = self.tmdb.list(list_id)

            # Prepare items as tuples: (movie_id, 'movie')
            items = [(mid, "movie") for mid in movie_ids]

            # Add all items at once (with rate limiting before the call)
            time.sleep(0.25)
            list_obj.add_items(items)

            logger.info("Added %d movies to list %s", len(movie_ids), list_id)
            return True

        except (ConnectionError, TimeoutError, ValueError, KeyError, AttributeError, RuntimeError) as e:
            logger.error("Error adding movies to list %s: %s", list_id, str(e))
            return False

    def clear_list(self, list_id: int) -> bool:
        """
        Clear all items from a TMDb list

        Args:
            list_id: TMDb list ID

        Returns:
            True if successful, False otherwise
        """
        if not self.session_id:
            logger.error("Authentication required for list operations")
            return False

        try:
            # Get the list object and use its clear() method
            list_obj = self.tmdb.list(list_id)

            # Add rate limiting before the clear operation
            time.sleep(0.25)
            list_obj.clear()

            logger.info("Cleared list %s", list_id)
            return True

        except (ConnectionError, TimeoutError, ValueError, KeyError, AttributeError, RuntimeError) as e:
            logger.error("Error clearing list %s: %s", list_id, str(e))
            # If clearing fails, just continue - we'll add the new movies anyway
            logger.warning("Skipping clear operation for list %s, will add movies directly", list_id)
            return True  # Return True to continue with adding movies

    def delete_list(self, list_id: int) -> bool:
        """
        Delete a TMDb list

        Args:
            list_id: TMDb list ID

        Returns:
            True if successful, False otherwise
        """
        if not self.session_id:
            logger.error("Authentication required for list operations")
            return False

        try:
            # Get the list object and use its delete() method
            list_obj = self.tmdb.list(list_id)

            # Add rate limiting before the delete operation
            time.sleep(0.25)
            list_obj.delete()

            logger.info("Deleted list %s", list_id)
            return True

        except (ConnectionError, TimeoutError, ValueError, KeyError, AttributeError, RuntimeError) as e:
            logger.error("Error deleting list %s: %s", list_id, str(e))
            return False

    def update_list_with_movies(self, list_id: int, films: List[Dict], clear_first: bool = True) -> Dict[str, any]:
        """
        Update a TMDb list with movies from Letterboxd films

        Args:
            list_id: TMDb list ID
            films: List of film dicts with 'title', 'year', etc.
            clear_first: Whether to clear the list before adding new items

        Returns:
            Dict with results: {
                'success': bool,
                'total_films': int,
                'matched': int,
                'not_matched': List[str],
                'added': int
            }
        """
        result = {"success": False, "total_films": len(films), "matched": 0, "not_matched": [], "added": 0}

        if not films:
            logger.warning("No films provided to add to list")
            result["success"] = True
            return result

        # Clear list if requested
        if clear_first:
            if not self.clear_list(list_id):
                logger.error("Failed to clear list before updating")
                return result

        # Search for each film on TMDb
        movie_ids = []
        for film in films:
            title = film.get("title")
            year = film.get("year")

            if not title:
                logger.warning("Film missing title, skipping: %s", film)
                continue

            tmdb_movie = self.search_movie(title, year)

            if tmdb_movie:
                movie_ids.append(tmdb_movie["id"])
                result["matched"] += 1
                logger.info("Matched: %s (%s) -> TMDb ID %s", title, year, tmdb_movie["id"])
            else:
                result["not_matched"].append(f"{title} ({year})")

        # Add all matched movies to the list
        if movie_ids:
            if self.add_movies_to_list(list_id, movie_ids):
                result["added"] = len(movie_ids)
                result["success"] = True
                logger.info(
                    "Successfully updated list %s: %d/%d films matched and added",
                    list_id,
                    result["matched"],
                    result["total_films"],
                )
            else:
                logger.error("Failed to add movies to list")
        else:
            logger.warning("No movies matched on TMDb")
            result["success"] = True  # Not an error, just no matches

        return result


def get_tmdb_service() -> Optional[TMDbService]:
    """
    Factory function to create TMDbService instance

    Returns:
        TMDbService instance or None if configuration is missing
    """
    try:
        return TMDbService()
    except ValueError as e:
        logger.error("Failed to initialize TMDb service: %s", str(e))
        return None
