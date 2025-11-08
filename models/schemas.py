"""Pydantic models for request/response validation"""

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class Film(BaseModel):
    """Film model"""

    model_config = {"exclude_none": True}

    title: str
    slug: str
    year: Optional[int] = None
    rating: Optional[float] = None
    url: str
    source: Optional[str] = None
    rated_date: Optional[str] = None


class UserStats(BaseModel):
    """User statistics model"""

    films_watched: int
    lists: int
    following: int
    followers: int


class UserProfileResponse(BaseModel):
    """User profile response model"""

    username: str
    display_name: str
    bio: Optional[str] = None
    stats: UserStats
    url: str


class WatchlistResponse(BaseModel):
    """Watchlist response model with pagination"""

    username: str
    total_watchlist: int
    films_count: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool
    films: List[dict]


class TopRatedResponse(BaseModel):
    """Top rated films response model with pagination"""

    username: str
    total_rated: int
    films_count: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool
    films: List[Film]


class UsernameValidator(BaseModel):
    """Username validation model"""

    username: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format"""
        if not v or v.isspace():
            raise ValueError("Username cannot be empty or whitespace")
        return v.lower()
