"""User controller handling Letterboxd user operations"""

from typing import Optional

from letterboxdpy.user import User

from services.film_service import get_rated_and_liked_films, normalize_watchlist_film
from utils.pagination import paginate_data


async def get_user_profile(username: str) -> dict:
    """
    Get a user's profile information from Letterboxd

    Args:
        username: Letterboxd username

    Returns:
        Dictionary containing user profile data and statistics

    Raises:
        ValueError: If there's an error fetching the profile
    """
    try:
        user = User(username)
        stats = user.stats

        return {
            "username": username,
            "display_name": user.display_name,
            "bio": user.bio,
            "stats": {
                "films_watched": stats.get("films", 0),
                "lists": 0,  # Not available in letterboxdpy stats
                "following": stats.get("following", 0),
                "followers": stats.get("followers", 0),
            },
            "url": user.url,
        }
    except Exception as e:
        raise ValueError(f"Error fetching user profile: {str(e)}") from e


async def get_user_watchlist(
    username: str,
    limit: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "title",
    sort_order: str = "asc",
) -> dict:
    """
    Get a user's watchlist with pagination and sorting

    Args:
        username: Letterboxd username
        limit: Optional limit to apply before pagination
        page: Page number (1-indexed)
        page_size: Number of items per page
        sort_by: Field to sort by ('title' or 'year')
        sort_order: Sort order ('asc' or 'desc')

    Returns:
        Dictionary containing watchlist data with pagination metadata

    Raises:
        ValueError: If there's an error fetching the watchlist
    """
    try:
        user = User(username)
        watchlist_data = user.get_watchlist()

        films = []
        if "data" in watchlist_data:
            for slug, film in watchlist_data["data"].items():
                films.append(normalize_watchlist_film(slug, film))

        # Define sort key based on sort_by parameter
        def sort_by_title(x):
            return (x.get("title") or "").lower()

        def sort_by_year(x):
            return x.get("year") or 0

        sort_key = None
        if sort_by == "title":
            sort_key = sort_by_title
        elif sort_by == "year":
            sort_key = sort_by_year

        # Apply pagination with sorting
        pagination_result = paginate_data(
            films, limit, page, page_size, sort_key=sort_key, reverse=(sort_order == "desc")
        )

        return {
            "username": username,
            "total_watchlist": pagination_result["total_count"],
            "films_count": pagination_result["items_count"],
            "page": pagination_result["page"],
            "page_size": pagination_result["page_size"],
            "total_pages": pagination_result["total_pages"],
            "has_next": pagination_result["has_next"],
            "has_previous": pagination_result["has_previous"],
            "films": pagination_result["paginated_data"],
        }
    except Exception as e:
        raise ValueError(f"Error fetching watchlist: {str(e)}") from e


async def get_top_rated_films(
    username: str,
    limit: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "rating",
    sort_order: str = "desc",
) -> dict:
    """
    Get a user's top-rated movies (all-time) with pagination and sorting

    Args:
        username: Letterboxd username
        limit: Optional limit to apply before pagination
        page: Page number (1-indexed)
        page_size: Number of items per page
        sort_by: Field to sort by ('rating', 'title', or 'year')
        sort_order: Sort order ('asc' or 'desc')

    Returns:
        Dictionary containing top-rated films with pagination metadata

    Raises:
        ValueError: If there's an error fetching the ratings
    """
    try:
        user = User(username)
        films = get_rated_and_liked_films(user)

        # Define sort key based on sort_by parameter
        def sort_by_rating(x):
            return x.get("rating", 0)

        def sort_by_title_top(x):
            return (x.get("title") or "").lower()

        def sort_by_year_top(x):
            return x.get("year") or 0

        sort_key = None
        if sort_by == "rating":
            sort_key = sort_by_rating
        elif sort_by == "title":
            sort_key = sort_by_title_top
        elif sort_by == "year":
            sort_key = sort_by_year_top

        # Apply pagination with sorting
        pagination_result = paginate_data(
            films, limit, page, page_size, sort_key=sort_key, reverse=(sort_order == "desc")
        )

        return {
            "username": username,
            "total_rated": pagination_result["total_count"],
            "films_count": pagination_result["items_count"],
            "page": pagination_result["page"],
            "page_size": pagination_result["page_size"],
            "total_pages": pagination_result["total_pages"],
            "has_next": pagination_result["has_next"],
            "has_previous": pagination_result["has_previous"],
            "films": pagination_result["paginated_data"],
        }
    except Exception as e:
        raise ValueError(f"Error fetching top rated films: {str(e)}") from e
