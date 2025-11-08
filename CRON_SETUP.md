# Cron Job Setup Guide

## Overview

This project includes a configurable cron job system that fetches the top 15 movies for specified Letterboxd users. The cron job uses APScheduler and respects standard crontab syntax with timezone support.

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` to configure your cron job:

```bash
# Enable or disable the cron job
CRON_ENABLED=true

# Cron schedule (standard crontab format)
CRON_SCHEDULE=0 0 * * *

# Timezone for cron execution
CRON_TIMEZONE=UTC

# Comma-separated list of usernames
CRON_TARGET_USERS=user1,user2,user3
```

### 3. Cron Schedule Format

The `CRON_SCHEDULE` follows standard crontab syntax:

```
* * * * *
│ │ │ │ │
│ │ │ │ └─── Day of week (0-7, Sunday = 0 or 7)
│ │ │ └───── Month (1-12)
│ │ └─────── Day of month (1-31)
│ └───────── Hour (0-23)
└─────────── Minute (0-59)
```

**Examples:**
- `0 0 * * *` - Daily at midnight
- `0 */6 * * *` - Every 6 hours
- `0 9 * * 1` - Every Monday at 9 AM
- `30 2 * * *` - Daily at 2:30 AM
- `0 0 1 * *` - First day of every month at midnight

### 4. Timezone Configuration

Set `CRON_TIMEZONE` to your desired timezone. Examples:
- `UTC`
- `America/New_York`
- `America/Los_Angeles`
- `Europe/London`
- `Asia/Tokyo`

See [List of tz database time zones](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) for all options.

## Usage

### Running the Application

The cron job starts automatically when you run the FastAPI application:

```bash
python index.py
```

Or with uvicorn:

```bash
uvicorn index:app --host 0.0.0.0 --port 8000
```

### Logs

The cron job logs its activity to the console:

```
INFO:jobs.scheduler:Scheduler started successfully:
  - Schedule: 0 0 * * *
  - Timezone: UTC
  - Target users: user1, user2
  - Next run: 2025-11-08 00:00:00+00:00

INFO:jobs.fetch_top_movies:[2025-11-08 00:00:00] Starting top movies fetch job for 2 user(s)
INFO:jobs.fetch_top_movies:Fetching top 15 movies for user: user1
INFO:jobs.fetch_top_movies:Successfully fetched 15 top movies for user1
INFO:jobs.fetch_top_movies:  1. The Shawshank Redemption (1994) - Rating: 5.0/5.0
...
```

### Disabling the Cron Job

Set `CRON_ENABLED=false` in your `.env` file to disable the cron job without removing the configuration.

## Architecture

```
jobs/
├── __init__.py
├── scheduler.py           # APScheduler configuration and lifecycle
└── fetch_top_movies.py    # Job implementation
```

### Key Components

1. **scheduler.py**: Manages the APScheduler instance, validates cron expressions and timezones, and handles graceful shutdown.

2. **fetch_top_movies.py**: Contains the job logic that fetches top 15 movies for each configured user.

3. **index.py**: Integrates the scheduler with FastAPI's startup/shutdown lifecycle.

## Customization

### Modifying the Job

Edit `jobs/fetch_top_movies.py` to customize what happens with the fetched movies. Current implementation logs the results, but you could:

- Save results to a database
- Send email notifications
- Post to a webhook
- Generate reports
- Update a cache

### Changing Fetch Parameters

Modify the parameters in `fetch_top_movies.py`:

```python
result = await get_top_rated_films(
    username=username,
    limit=15,          # Change number of movies
    page=1,
    page_size=15,
    sort_by="rating",  # Or "title", "year"
    sort_order="desc"  # Or "asc"
)
```

## Troubleshooting

### Cron job not running

1. Check that `CRON_ENABLED=true` in `.env`
2. Verify `CRON_TARGET_USERS` has at least one username
3. Check logs for validation errors
4. Ensure cron expression is valid

### Invalid timezone error

Use a valid tz database timezone name. Common mistake: using abbreviations like "EST" instead of "America/New_York".

### Missed job executions

The scheduler has a 1-hour grace period (`misfire_grace_time=3600`). If the application is down when a job should run, it will execute within 1 hour of restart if still within the grace period.
