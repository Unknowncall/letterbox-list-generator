"""API routes for job management"""

from typing import List

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field, field_validator

from jobs.sync_to_tmdb import get_tmdb_config, run_sync_job
from utils.logger import logger

router = APIRouter(prefix="/jobs", tags=["jobs"])


class SyncTMDbRequest(BaseModel):
    """Request model for TMDb sync job"""

    usernames: List[str] = Field(
        ...,
        min_length=1,
        description="List of Letterboxd usernames to sync to TMDb",
        examples=[["ian_fried", "username2"]],
    )

    @field_validator("usernames")
    @classmethod
    def validate_usernames(cls, v):
        """Validate username list"""
        if not v:
            raise ValueError("At least one username is required")

        # Validate each username
        for username in v:
            if not username or not username.strip():
                raise ValueError("Username cannot be empty")
            if len(username) > 100:
                raise ValueError(f"Username too long: {username}")
            # Basic pattern validation
            if not all(c.isalnum() or c in "_-" for c in username):
                raise ValueError(f"Invalid username format: {username}")

        return v


class SyncTMDbResponse(BaseModel):
    """Response model for TMDb sync job"""

    message: str
    usernames: List[str]
    job_started: bool


@router.post("/sync-tmdb", response_model=SyncTMDbResponse)
async def trigger_tmdb_sync(request: SyncTMDbRequest, background_tasks: BackgroundTasks):
    """
    Trigger TMDb sync job for specified users

    Creates or updates TMDb lists for each Letterboxd user with their top-rated movies.
    Each user gets their own list. Job runs in the background.

    **Requirements:**
    - TMDB_SYNC_ENABLED must be true
    - TMDB_API_KEY must be configured
    - TMDB_V4_ACCESS_TOKEN must be configured

    **Process:**
    1. For each username, fetches top 100 rated & liked films from Letterboxd
    2. Creates TMDb list if doesn't exist (named "{username}'s Top Rated Movies")
    3. Clears existing list and adds current top-rated films
    4. Logs results including match rate and any unmatched films

    **Returns:**
    - message: Confirmation message
    - usernames: List of usernames being processed
    - job_started: Whether the job was successfully queued

    **Errors:**
    - 503: TMDb sync is disabled in configuration
    - 503: TMDb API credentials not configured
    - 422: Invalid username format
    """
    # Check if TMDb sync is enabled
    config = get_tmdb_config()

    if not config["enabled"]:
        raise HTTPException(status_code=503, detail="TMDb sync is disabled. Set TMDB_SYNC_ENABLED=true in .env")

    if not config["api_key"]:
        raise HTTPException(status_code=503, detail="TMDb API key not configured. Set TMDB_API_KEY in .env")

    if not config["v4_access_token"]:
        raise HTTPException(
            status_code=503, detail="TMDb v4 access token not configured. Set TMDB_V4_ACCESS_TOKEN in .env"
        )

    # Queue the sync job in background
    background_tasks.add_task(run_sync_job, request.usernames)

    logger.info("TMDb sync job queued for %d user(s): %s", len(request.usernames), ", ".join(request.usernames))

    return SyncTMDbResponse(
        message=f"TMDb sync job started for {len(request.usernames)} user(s). Each user will get their own list.",
        usernames=request.usernames,
        job_started=True,
    )
