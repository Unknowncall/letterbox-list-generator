"""Tests for models/schemas.py"""
import pytest
from pydantic import ValidationError
from models.schemas import (
    Film,
    UserStats,
    UserProfileResponse,
    WatchlistResponse,
    TopRatedResponse,
    UsernameValidator
)


class TestFilm:
    """Test suite for Film model"""

    def test_film_with_all_fields(self):
        """Test Film model with all fields"""
        film = Film(
            title="The Godfather",
            slug="the-godfather",
            year=1972,
            rating=5.0,
            url="https://letterboxd.com/film/the-godfather/",
            source="letterboxd",
            rated_date="2024-01-15"
        )

        assert film.title == "The Godfather"
        assert film.slug == "the-godfather"
        assert film.year == 1972
        assert film.rating == 5.0
        assert film.url == "https://letterboxd.com/film/the-godfather/"
        assert film.source == "letterboxd"
        assert film.rated_date == "2024-01-15"

    def test_film_with_required_fields_only(self):
        """Test Film model with only required fields"""
        film = Film(
            title="Pulp Fiction",
            slug="pulp-fiction",
            url="https://letterboxd.com/film/pulp-fiction/"
        )

        assert film.title == "Pulp Fiction"
        assert film.slug == "pulp-fiction"
        assert film.url == "https://letterboxd.com/film/pulp-fiction/"
        assert film.year is None
        assert film.rating is None

    def test_film_exclude_none(self):
        """Test Film model excludes None values in serialization"""
        film = Film(
            title="Test Film",
            slug="test-film",
            url="https://letterboxd.com/film/test-film/"
        )

        # Convert to dict with exclude_none
        film_dict = film.model_dump(exclude_none=True)
        assert 'year' not in film_dict
        assert 'rating' not in film_dict
        assert 'source' not in film_dict
        assert 'rated_date' not in film_dict

    def test_film_missing_required_field(self):
        """Test Film model fails without required fields"""
        with pytest.raises(ValidationError) as exc_info:
            Film(title="Test", slug="test")  # Missing url

        errors = exc_info.value.errors()
        assert any(error['loc'] == ('url',) for error in errors)


class TestUserStats:
    """Test suite for UserStats model"""

    def test_user_stats_valid(self):
        """Test UserStats model with valid data"""
        stats = UserStats(
            films_watched=100,
            lists=5,
            following=50,
            followers=75
        )

        assert stats.films_watched == 100
        assert stats.lists == 5
        assert stats.following == 50
        assert stats.followers == 75

    def test_user_stats_zero_values(self):
        """Test UserStats model with zero values"""
        stats = UserStats(
            films_watched=0,
            lists=0,
            following=0,
            followers=0
        )

        assert stats.films_watched == 0
        assert stats.lists == 0

    def test_user_stats_missing_field(self):
        """Test UserStats fails with missing required field"""
        with pytest.raises(ValidationError):
            UserStats(films_watched=100, lists=5, following=50)


class TestUserProfileResponse:
    """Test suite for UserProfileResponse model"""

    def test_user_profile_with_bio(self):
        """Test UserProfileResponse with bio"""
        stats = UserStats(
            films_watched=100,
            lists=5,
            following=50,
            followers=75
        )
        profile = UserProfileResponse(
            username="testuser",
            display_name="Test User",
            bio="Film enthusiast",
            stats=stats,
            url="https://letterboxd.com/testuser/"
        )

        assert profile.username == "testuser"
        assert profile.display_name == "Test User"
        assert profile.bio == "Film enthusiast"
        assert profile.stats.films_watched == 100
        assert profile.url == "https://letterboxd.com/testuser/"

    def test_user_profile_without_bio(self):
        """Test UserProfileResponse without bio"""
        stats = UserStats(
            films_watched=50,
            lists=0,
            following=25,
            followers=30
        )
        profile = UserProfileResponse(
            username="testuser",
            display_name="Test User",
            stats=stats,
            url="https://letterboxd.com/testuser/"
        )

        assert profile.bio is None

    def test_user_profile_nested_stats(self):
        """Test UserProfileResponse with nested stats dict"""
        profile = UserProfileResponse(
            username="testuser",
            display_name="Test User",
            stats={
                "films_watched": 100,
                "lists": 5,
                "following": 50,
                "followers": 75
            },
            url="https://letterboxd.com/testuser/"
        )

        assert isinstance(profile.stats, UserStats)
        assert profile.stats.films_watched == 100


class TestWatchlistResponse:
    """Test suite for WatchlistResponse model"""

    def test_watchlist_response_valid(self):
        """Test WatchlistResponse with valid data"""
        films = [
            {"title": "Film A", "year": 2000, "url": "https://letterboxd.com/film/film-a/"},
            {"title": "Film B", "year": 2010, "url": "https://letterboxd.com/film/film-b/"}
        ]

        response = WatchlistResponse(
            username="testuser",
            total_watchlist=50,
            films_count=2,
            page=1,
            page_size=20,
            total_pages=3,
            has_next=True,
            has_previous=False,
            films=films
        )

        assert response.username == "testuser"
        assert response.total_watchlist == 50
        assert response.films_count == 2
        assert response.page == 1
        assert len(response.films) == 2
        assert response.has_next is True
        assert response.has_previous is False

    def test_watchlist_response_empty_films(self):
        """Test WatchlistResponse with empty films list"""
        response = WatchlistResponse(
            username="testuser",
            total_watchlist=0,
            films_count=0,
            page=1,
            page_size=20,
            total_pages=1,
            has_next=False,
            has_previous=False,
            films=[]
        )

        assert response.films == []
        assert response.films_count == 0

    def test_watchlist_response_pagination_metadata(self):
        """Test WatchlistResponse pagination metadata"""
        response = WatchlistResponse(
            username="testuser",
            total_watchlist=100,
            films_count=20,
            page=3,
            page_size=20,
            total_pages=5,
            has_next=True,
            has_previous=True,
            films=[]
        )

        assert response.page == 3
        assert response.total_pages == 5
        assert response.has_next is True
        assert response.has_previous is True


class TestTopRatedResponse:
    """Test suite for TopRatedResponse model"""

    def test_top_rated_response_valid(self):
        """Test TopRatedResponse with valid film objects"""
        films = [
            Film(
                title="The Godfather",
                slug="the-godfather",
                year=1972,
                rating=5.0,
                url="https://letterboxd.com/film/the-godfather/"
            ),
            Film(
                title="Pulp Fiction",
                slug="pulp-fiction",
                year=1994,
                rating=5.0,
                url="https://letterboxd.com/film/pulp-fiction/"
            )
        ]

        response = TopRatedResponse(
            username="testuser",
            total_rated=100,
            films_count=2,
            page=1,
            page_size=20,
            total_pages=5,
            has_next=True,
            has_previous=False,
            films=films
        )

        assert response.username == "testuser"
        assert response.total_rated == 100
        assert response.films_count == 2
        assert len(response.films) == 2
        assert isinstance(response.films[0], Film)
        assert response.films[0].rating == 5.0

    def test_top_rated_response_from_dicts(self):
        """Test TopRatedResponse accepts film dicts and converts to Film objects"""
        films_data = [
            {
                "title": "The Godfather",
                "slug": "the-godfather",
                "year": 1972,
                "rating": 5.0,
                "url": "https://letterboxd.com/film/the-godfather/"
            }
        ]

        response = TopRatedResponse(
            username="testuser",
            total_rated=10,
            films_count=1,
            page=1,
            page_size=20,
            total_pages=1,
            has_next=False,
            has_previous=False,
            films=films_data
        )

        assert isinstance(response.films[0], Film)
        assert response.films[0].title == "The Godfather"

    def test_top_rated_response_empty(self):
        """Test TopRatedResponse with no films"""
        response = TopRatedResponse(
            username="testuser",
            total_rated=0,
            films_count=0,
            page=1,
            page_size=20,
            total_pages=1,
            has_next=False,
            has_previous=False,
            films=[]
        )

        assert response.films == []
        assert response.total_rated == 0


class TestUsernameValidator:
    """Test suite for UsernameValidator model"""

    def test_valid_username_alphanumeric(self):
        """Test valid alphanumeric username"""
        validator = UsernameValidator(username="testuser123")
        assert validator.username == "testuser123"

    def test_valid_username_with_underscore(self):
        """Test valid username with underscore"""
        validator = UsernameValidator(username="test_user")
        assert validator.username == "test_user"

    def test_valid_username_with_hyphen(self):
        """Test valid username with hyphen"""
        validator = UsernameValidator(username="test-user")
        assert validator.username == "test-user"

    def test_valid_username_mixed(self):
        """Test valid username with mixed valid characters"""
        validator = UsernameValidator(username="Test_User-123")
        assert validator.username == "test_user-123"  # Should be lowercased

    def test_username_lowercase_conversion(self):
        """Test username is converted to lowercase"""
        validator = UsernameValidator(username="TestUser")
        assert validator.username == "testuser"

    def test_invalid_username_with_spaces(self):
        """Test username fails with spaces"""
        with pytest.raises(ValidationError) as exc_info:
            UsernameValidator(username="test user")

        errors = exc_info.value.errors()
        assert any('pattern' in str(error) for error in errors)

    def test_invalid_username_with_special_chars(self):
        """Test username fails with special characters"""
        with pytest.raises(ValidationError):
            UsernameValidator(username="test@user")

    def test_invalid_username_empty(self):
        """Test username fails when empty"""
        with pytest.raises(ValidationError) as exc_info:
            UsernameValidator(username="")

        errors = exc_info.value.errors()
        # Should fail min_length validation
        assert any(error['type'] == 'string_too_short' for error in errors)

    def test_invalid_username_whitespace_only(self):
        """Test username fails with only whitespace"""
        with pytest.raises(ValidationError) as exc_info:
            UsernameValidator(username="   ")

        errors = exc_info.value.errors()
        # Should fail the custom validator or pattern
        assert len(errors) > 0

    def test_invalid_username_too_long(self):
        """Test username fails when too long"""
        long_username = "a" * 101
        with pytest.raises(ValidationError) as exc_info:
            UsernameValidator(username=long_username)

        errors = exc_info.value.errors()
        assert any(error['type'] == 'string_too_long' for error in errors)

    def test_valid_username_max_length(self):
        """Test username at maximum allowed length"""
        max_username = "a" * 100
        validator = UsernameValidator(username=max_username)
        assert len(validator.username) == 100

    def test_valid_username_single_char(self):
        """Test username with single character"""
        validator = UsernameValidator(username="a")
        assert validator.username == "a"

    def test_invalid_username_dots(self):
        """Test username fails with dots"""
        with pytest.raises(ValidationError):
            UsernameValidator(username="test.user")

    def test_invalid_username_forward_slash(self):
        """Test username fails with forward slash"""
        with pytest.raises(ValidationError):
            UsernameValidator(username="test/user")

    def test_username_numbers_only(self):
        """Test username with only numbers"""
        validator = UsernameValidator(username="123456")
        assert validator.username == "123456"

    def test_username_starting_with_number(self):
        """Test username starting with number"""
        validator = UsernameValidator(username="123user")
        assert validator.username == "123user"

    def test_username_starting_with_underscore(self):
        """Test username starting with underscore"""
        validator = UsernameValidator(username="_user")
        assert validator.username == "_user"

    def test_username_starting_with_hyphen(self):
        """Test username starting with hyphen"""
        validator = UsernameValidator(username="-user")
        assert validator.username == "-user"
