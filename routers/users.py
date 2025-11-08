"""User router handling API endpoints for Letterboxd user operations"""

from fastapi import APIRouter, HTTPException, Path, Query

from controllers import users
from models.schemas import TopRatedResponse, UserProfileResponse, WatchlistResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{username}", response_model=UserProfileResponse)
async def get_user_profile(
    username: str = Path(
        ..., min_length=1, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$", description="Letterboxd username"
    )
):
    """
    Get a Letterboxd user's profile information

    Args:
        username: Letterboxd username

    Returns:
        User profile data with stats and bio
    """
    try:
        profile = await users.get_user_profile(username)
        return profile
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") from e


@router.get("/{username}/watchlist", response_model=WatchlistResponse)
async def get_user_watchlist(
    username: str = Path(
        ..., min_length=1, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$", description="Letterboxd username"
    ),
    limit: int = Query(default=None, ge=1, le=1000, description="Optional limit on total films before pagination"),
    page: int = Query(default=1, ge=1, description="Page number (default: 1)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Number of films per page (default: 20)"),
    sort_by: str = Query(
        default="title", pattern="^(title|year)$", description="Sort by: title or year (default: title)"
    ),
    sort_order: str = Query(
        default="asc", pattern="^(asc|desc)$", description="Sort order: asc or desc (default: asc)"
    ),
):
    """
    Get a user's watchlist with pagination and sorting

    Args:
        username: Letterboxd username
        limit: Optional limit on total films before pagination (1-1000)
        page: Page number (default: 1)
        page_size: Number of films per page (1-100, default: 20)
        sort_by: Field to sort by - title or year (default: title)
        sort_order: Sort order - asc or desc (default: asc)

    Returns:
        User's watchlist films with pagination metadata
    """
    try:
        watchlist = await users.get_user_watchlist(username, limit, page, page_size, sort_by, sort_order)
        return watchlist
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") from e


@router.get("/{username}/top-rated", response_model=TopRatedResponse, response_model_exclude_none=True)
async def get_top_rated(
    username: str = Path(
        ..., min_length=1, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$", description="Letterboxd username"
    ),
    limit: int = Query(default=None, ge=1, le=1000, description="Optional limit on total films before pagination"),
    page: int = Query(default=1, ge=1, description="Page number (default: 1)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Number of films per page (default: 20)"),
    sort_by: str = Query(
        default="rating",
        pattern="^(rating|title|year)$",
        description="Sort by: rating, title, or year (default: rating)",
    ),
    sort_order: str = Query(
        default="desc", pattern="^(asc|desc)$", description="Sort order: asc or desc (default: desc)"
    ),
):
    """
    Get a user's top-rated and liked movies (all-time) with pagination and sorting

    Args:
        username: Letterboxd username
        limit: Optional limit on total films before pagination (1-1000)
        page: Page number (default: 1)
        page_size: Number of films per page (1-100, default: 20)
        sort_by: Field to sort by - rating, title, or year (default: rating)
        sort_order: Sort order - asc or desc (default: desc)

    Returns:
        Top rated and liked films with pagination metadata
    """
    try:
        top_rated = await users.get_top_rated_films(username, limit, page, page_size, sort_by, sort_order)
        return top_rated
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") from e
