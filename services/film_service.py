"""Film data service for extracting and normalizing Letterboxd film data"""

from typing import List

from letterboxdpy.user import User


def get_rated_and_liked_films(user: User) -> List[dict]:
    """
    Extract all rated and liked films from user's film collection

    Args:
        user: User object

    Returns:
        List of normalized film dictionaries (only liked films with ratings)
    """
    films_data = user.get_films()
    films = []

    if "movies" in films_data:
        for slug, film in films_data["movies"].items():
            rating = film.get("rating")
            liked = film.get("liked", False)

            # Only include films that are both rated and liked
            if rating and rating > 0 and liked:
                films.append(
                    {
                        "title": film.get("name"),
                        "slug": slug,
                        "url": f"https://letterboxd.com/film/{slug}/",
                        "rating": rating / 2.0,  # Convert from 10-point to 5-star scale
                        "year": film.get("year"),
                    }
                )

    return films


def normalize_watchlist_film(_slug: str, film: dict) -> dict:
    """
    Normalize a watchlist film entry to a standard format

    Args:
        _slug: Film slug identifier (unused, kept for API compatibility)
        film: Raw film data from letterboxdpy

    Returns:
        Normalized film dictionary
    """
    return {"title": film.get("name"), "year": film.get("year"), "url": film.get("url")}
