"""Tests for services/film_service.py"""

from unittest.mock import Mock

import pytest

from services.film_service import get_rated_and_liked_films, normalize_watchlist_film


class TestGetRatedAndLikedFilms:
    """Test suite for get_rated_and_liked_films function"""

    def test_get_films_rated_and_liked(self, mock_user):
        """Test getting films that are both rated and liked"""
        films = get_rated_and_liked_films(mock_user)

        # Should return 3 films (The Godfather, Pulp Fiction, The Dark Knight)
        # Excludes: not-liked (not liked), not-rated (rating is 0)
        assert len(films) == 3

        # Verify film data structure
        for film in films:
            assert "title" in film
            assert "slug" in film
            assert "url" in film
            assert "rating" in film
            assert "year" in film

    def test_films_have_correct_ratings(self, mock_user):
        """Test that ratings are correctly converted from 10-point to 5-star scale"""
        films = get_rated_and_liked_films(mock_user)

        # Find specific films and check their ratings
        godfather = next(f for f in films if f["slug"] == "the-godfather")
        assert godfather["rating"] == 5.0  # 10 / 2.0

        dark_knight = next(f for f in films if f["slug"] == "the-dark-knight")
        assert dark_knight["rating"] == 4.5  # 9 / 2.0

    def test_films_have_correct_structure(self, mock_user):
        """Test that each film has the correct structure"""
        films = get_rated_and_liked_films(mock_user)

        godfather = next(f for f in films if f["slug"] == "the-godfather")
        assert godfather["title"] == "The Godfather"
        assert godfather["slug"] == "the-godfather"
        assert godfather["url"] == "https://letterboxd.com/film/the-godfather/"
        assert godfather["rating"] == 5.0
        assert godfather["year"] == 1972

    def test_excludes_not_liked_films(self):
        """Test that films without 'liked' flag are excluded"""
        user = Mock()
        user.get_films = Mock(
            return_value={
                "movies": {
                    "film-1": {"name": "Film 1", "year": 2020, "rating": 8, "liked": False},
                    "film-2": {"name": "Film 2", "year": 2021, "rating": 10, "liked": True},
                }
            }
        )

        films = get_rated_and_liked_films(user)
        assert len(films) == 1
        assert films[0]["title"] == "Film 2"

    def test_excludes_zero_rated_films(self):
        """Test that films with 0 rating are excluded"""
        user = Mock()
        user.get_films = Mock(
            return_value={
                "movies": {
                    "film-1": {"name": "Film 1", "year": 2020, "rating": 0, "liked": True},
                    "film-2": {"name": "Film 2", "year": 2021, "rating": 8, "liked": True},
                }
            }
        )

        films = get_rated_and_liked_films(user)
        assert len(films) == 1
        assert films[0]["title"] == "Film 2"

    def test_excludes_unrated_films(self):
        """Test that films without rating field are excluded"""
        user = Mock()
        user.get_films = Mock(
            return_value={
                "movies": {
                    "film-1": {"name": "Film 1", "year": 2020, "liked": True},
                    "film-2": {"name": "Film 2", "year": 2021, "rating": 8, "liked": True},
                }
            }
        )

        films = get_rated_and_liked_films(user)
        assert len(films) == 1
        assert films[0]["title"] == "Film 2"

    def test_empty_movies_dict(self):
        """Test handling of empty movies dictionary"""
        user = Mock()
        user.get_films = Mock(return_value={"movies": {}})

        films = get_rated_and_liked_films(user)
        assert films == []

    def test_no_movies_key(self):
        """Test handling when 'movies' key is missing"""
        user = Mock()
        user.get_films = Mock(return_value={})

        films = get_rated_and_liked_films(user)
        assert films == []

    def test_film_without_year(self):
        """Test handling films without year field"""
        user = Mock()
        user.get_films = Mock(return_value={"movies": {"film-1": {"name": "Film 1", "rating": 8, "liked": True}}})

        films = get_rated_and_liked_films(user)
        assert len(films) == 1
        assert films[0]["year"] is None

    def test_rating_conversion_various_values(self):
        """Test rating conversion for various values"""
        user = Mock()
        user.get_films = Mock(
            return_value={
                "movies": {
                    "film-1": {"name": "Film 1", "rating": 10, "liked": True},
                    "film-2": {"name": "Film 2", "rating": 9, "liked": True},
                    "film-3": {"name": "Film 3", "rating": 5, "liked": True},
                    "film-4": {"name": "Film 4", "rating": 1, "liked": True},
                }
            }
        )

        films = get_rated_and_liked_films(user)
        ratings = {f["title"]: f["rating"] for f in films}

        assert ratings["Film 1"] == 5.0  # 10 / 2.0
        assert ratings["Film 2"] == 4.5  # 9 / 2.0
        assert ratings["Film 3"] == 2.5  # 5 / 2.0
        assert ratings["Film 4"] == 0.5  # 1 / 2.0

    def test_url_format(self):
        """Test that URLs are correctly formatted"""
        user = Mock()
        user.get_films = Mock(
            return_value={"movies": {"test-slug-123": {"name": "Test Film", "rating": 8, "liked": True}}}
        )

        films = get_rated_and_liked_films(user)
        assert films[0]["url"] == "https://letterboxd.com/film/test-slug-123/"

    def test_preserves_slug_key(self):
        """Test that slug is correctly extracted from dictionary key"""
        user = Mock()
        user.get_films = Mock(
            return_value={
                "movies": {
                    "the-shawshank-redemption": {"name": "The Shawshank Redemption", "rating": 10, "liked": True}
                }
            }
        )

        films = get_rated_and_liked_films(user)
        assert films[0]["slug"] == "the-shawshank-redemption"

    def test_multiple_films_all_valid(self):
        """Test with multiple films all meeting criteria"""
        user = Mock()
        user.get_films = Mock(
            return_value={
                "movies": {
                    f"film-{i}": {"name": f"Film {i}", "year": 2000 + i, "rating": 8 + i % 3, "liked": True}
                    for i in range(10)
                }
            }
        )

        films = get_rated_and_liked_films(user)
        assert len(films) == 10


class TestNormalizeWatchlistFilm:
    """Test suite for normalize_watchlist_film function"""

    def test_normalize_complete_film(self):
        """Test normalizing a film with all fields"""
        film_data = {"name": "The Godfather", "year": 1972, "url": "https://letterboxd.com/film/the-godfather/"}

        result = normalize_watchlist_film("the-godfather", film_data)

        assert result["title"] == "The Godfather"
        assert result["year"] == 1972
        assert result["url"] == "https://letterboxd.com/film/the-godfather/"

    def test_normalize_film_without_year(self):
        """Test normalizing a film without year"""
        film_data = {"name": "Unknown Year Film", "url": "https://letterboxd.com/film/unknown-year-film/"}

        result = normalize_watchlist_film("unknown-year-film", film_data)

        assert result["title"] == "Unknown Year Film"
        assert result["year"] is None
        assert result["url"] == "https://letterboxd.com/film/unknown-year-film/"

    def test_normalize_film_missing_fields(self):
        """Test normalizing a film with missing fields"""
        film_data = {}

        result = normalize_watchlist_film("test-film", film_data)

        assert result["title"] is None
        assert result["year"] is None
        assert result["url"] is None

    def test_normalize_film_slug_not_used_in_result(self):
        """Test that slug parameter is not included in result"""
        film_data = {"name": "Test Film", "year": 2020, "url": "https://letterboxd.com/film/test-film/"}

        result = normalize_watchlist_film("test-film", film_data)

        # Result should only have title, year, url (not slug)
        assert set(result.keys()) == {"title", "year", "url"}

    def test_normalize_film_with_extra_fields(self):
        """Test that extra fields in film data are ignored"""
        film_data = {
            "name": "Test Film",
            "year": 2020,
            "url": "https://letterboxd.com/film/test-film/",
            "rating": 5.0,
            "director": "Some Director",
            "extra_field": "Extra value",
        }

        result = normalize_watchlist_film("test-film", film_data)

        # Should only extract the three expected fields
        assert set(result.keys()) == {"title", "year", "url"}
        assert result["title"] == "Test Film"
        assert result["year"] == 2020
        assert result["url"] == "https://letterboxd.com/film/test-film/"

    def test_normalize_film_year_zero(self):
        """Test normalizing a film with year 0"""
        film_data = {"name": "Ancient Film", "year": 0, "url": "https://letterboxd.com/film/ancient-film/"}

        result = normalize_watchlist_film("ancient-film", film_data)

        assert result["year"] == 0

    def test_normalize_film_various_slugs(self):
        """Test that slug parameter doesn't affect the result"""
        film_data = {"name": "Test Film", "year": 2020, "url": "https://letterboxd.com/film/test-film/"}

        # Different slugs should not affect normalization
        result1 = normalize_watchlist_film("test-film", film_data)
        result2 = normalize_watchlist_film("different-slug", film_data)

        assert result1 == result2

    def test_normalize_preserves_url_format(self):
        """Test that URL is preserved exactly as provided"""
        urls = [
            "https://letterboxd.com/film/test/",
            "http://letterboxd.com/film/test/",
            "https://letterboxd.com/film/test",
        ]

        for url in urls:
            film_data = {"name": "Test", "url": url}
            result = normalize_watchlist_film("test", film_data)
            assert result["url"] == url

    def test_normalize_film_with_special_characters_in_title(self):
        """Test normalizing films with special characters in title"""
        film_data = {
            "name": "Film: With-Special_Characters & Symbols!",
            "year": 2020,
            "url": "https://letterboxd.com/film/special/",
        }

        result = normalize_watchlist_film("special", film_data)

        assert result["title"] == "Film: With-Special_Characters & Symbols!"

    def test_normalize_film_empty_string_values(self):
        """Test normalizing film with empty string values"""
        film_data = {"name": "", "year": 2020, "url": ""}

        result = normalize_watchlist_film("test", film_data)

        assert result["title"] == ""
        assert result["year"] == 2020
        assert result["url"] == ""
