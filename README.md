# Letterbox List Generator

A FastAPI-based service that integrates with Letterboxd to fetch user profiles, watchlists, and top-rated movies, with automatic synchronization to TMDb lists.

[![CI/CD Pipeline](https://github.com/Unknowncall/letterbox-list-generator/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/Unknowncall/letterbox-list-generator/actions/workflows/ci-cd.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- 🎬 **Letterboxd Integration** - Fetch user profiles, watchlists, and top-rated films
- 📊 **Pagination & Sorting** - Flexible pagination with multiple sorting options
- 🎯 **TMDb Sync** - Automatically sync top-rated movies to TMDb lists (one list per user)
- 🔄 **Scheduled Jobs** - Cron-based automated syncing with configurable schedules
- 🐳 **Docker Ready** - Production-ready Docker and Docker Compose setup
- 🧪 **100% Test Coverage** - Comprehensive test suite with 278+ tests
- 📡 **REST API** - Well-documented API with Postman collection

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/Unknowncall/letterbox-list-generator.git
cd letterbox-list-generator

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your configuration

# Start the application
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

The API will be available at `http://localhost:8000`

### Using Pre-built Docker Image

Pull and run the latest image from GitHub Container Registry:

```bash
# Pull the latest image
docker pull ghcr.io/Unknowncall/letterbox-list-generator:latest

# Run the container
docker run -d \
  --name letterbox-list-generator \
  -p 8000:8000 \
  --env-file .env \
  ghcr.io/Unknowncall/letterbox-list-generator:latest
```

### Local Development

```bash
# Install dependencies
make install

# Run the application
make run

# Run tests
make test

# Run tests with coverage
make test-cov
```

## API Endpoints

### Health Check
```http
GET /health
```

### User Profile
```http
GET /users/{username}
```
Get detailed Letterboxd user profile with stats.

### Watchlist
```http
GET /users/{username}/watchlist?page=1&page_size=20&sort_by=title&sort_order=asc
```
Fetch user's watchlist with pagination and sorting.

**Query Parameters:**
- `page` - Page number (default: 1)
- `page_size` - Items per page, 1-100 (default: 20)
- `limit` - Optional limit on total films
- `sort_by` - `title` or `year` (default: title)
- `sort_order` - `asc` or `desc` (default: asc)

### Top Rated Films
```http
GET /users/{username}/top-rated?page=1&page_size=20&sort_by=rating&sort_order=desc
```
Fetch user's top-rated and liked movies (requires both rating AND like).

**Query Parameters:**
- `page` - Page number (default: 1)
- `page_size` - Items per page, 1-100 (default: 20)
- `limit` - Optional limit on total films
- `sort_by` - `rating`, `title`, or `year` (default: rating)
- `sort_order` - `asc` or `desc` (default: desc)

### TMDb Sync (On-Demand)
```http
POST /jobs/sync-tmdb
Content-Type: application/json

{
  "usernames": ["ian_fried", "username2"]
}
```
Trigger TMDb sync for specified users. Each user gets their own list.

## TMDb Integration

The service can automatically sync your top-rated Letterboxd films to TMDb lists.

### Setup

1. **Get TMDb API Key**
   - Sign up at [https://www.themoviedb.org](https://www.themoviedb.org)
   - Go to Settings → API → Create API Key

2. **Get TMDb v4 Access Token** (optional, for read operations)
   - Go to Settings → API → API Read Access Token

3. **Configure Authentication** (required for list management)
   - Add your TMDb username and password to `.env`:

```bash
TMDB_API_KEY=your_api_key_here
TMDB_V4_ACCESS_TOKEN=your_v4_token_here
TMDB_USERNAME=your_tmdb_username
TMDB_PASSWORD=your_tmdb_password
TMDB_SYNC_ENABLED=true
```

### How It Works

- **Per-User Lists**: Each Letterboxd user gets their own TMDb list
- **Auto-Naming**: Lists are named `{username}'s Top Rated Movies`
- **Auto-Mapping**: List IDs are stored in `tmdb_list_mappings.json`
- **Top 15 Films**: Syncs the top 15 rated and liked films
- **Rate Limited**: Built-in rate limiting to respect TMDb API limits

### Usage Options

**1. On-Demand (API)**
```bash
curl -X POST http://localhost:8000/jobs/sync-tmdb \
  -H "Content-Type: application/json" \
  -d '{"usernames": ["ian_fried"]}'
```

**2. Scheduled (Cron)**
Configure in `.env`:
```bash
CRON_ENABLED=true
CRON_SCHEDULE=0 2 * * *  # Daily at 2 AM
CRON_TIMEZONE=America/Chicago
CRON_TARGET_USERS=ian_fried,username2
```

## Configuration

All configuration is done via environment variables in `.env`:

```bash
# Cron Job Configuration
CRON_ENABLED=true
CRON_SCHEDULE=0 0 * * *
CRON_TIMEZONE=UTC
CRON_TARGET_USERS=ian_fried

# TMDb Configuration
TMDB_API_KEY=your_api_key
TMDB_V4_ACCESS_TOKEN=your_v4_token
TMDB_USERNAME=your_tmdb_username
TMDB_PASSWORD=your_tmdb_password
TMDB_SYNC_ENABLED=true
```

See `.env.example` for all available options.

## API Documentation

### Interactive Docs
Once the application is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Postman Collection
Import `postman_collection.json` into Postman for ready-to-use API requests.

## Development

### Prerequisites
- Python 3.11+
- pip
- virtualenv (optional but recommended)

### Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
uvicorn index:app --reload --host 0.0.0.0 --port 8000
```

### Available Make Commands
```bash
make help          # Show all commands
make install       # Setup environment
make run           # Run with hot reload
make test          # Run tests
make test-cov      # Run tests with coverage
make test-cov-html # Generate HTML coverage report
make clean         # Clean cache files
make docker-build  # Build Docker image
make docker-run    # Run Docker container
```

### Running Tests
```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run with HTML coverage report
make test-cov-html
open htmlcov/index.html

# Run specific test file
pytest tests/test_users_router.py -v
```

## Project Structure

```
letterbox-list-generator/
├── index.py                    # Main application entry
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker configuration
├── docker-compose.yml          # Docker Compose setup
├── .env.example               # Environment template
├── Makefile                   # Development commands
├── controllers/               # Business logic
│   └── users.py
├── routers/                   # API routes
│   ├── users.py
│   └── jobs.py
├── services/                  # External service integrations
│   ├── film_service.py
│   └── tmdb_service.py
├── models/                    # Pydantic schemas
│   └── schemas.py
├── utils/                     # Utilities
│   └── pagination.py
├── jobs/                      # Background jobs
│   ├── scheduler.py
│   ├── fetch_top_movies.py
│   └── sync_to_tmdb.py
└── tests/                     # Test suite (278+ tests)
    ├── test_users_router.py
    ├── test_tmdb_service.py
    └── ...
```

## CI/CD

GitHub Actions automatically:
- ✅ Lints code with flake8 and pylint
- ✅ Runs all 266+ tests
- ✅ Builds and pushes Docker images to GHCR
- ✅ Creates pre-releases on main branch pushes
- ✅ Creates production releases on version tags

### Release Workflow

**Pre-Releases (Automatic)**
- Push to `main` → Creates `v0.0.1-pre.3`
- Images tagged: `latest-pre`

**Production Releases (Manual)**
```bash
git tag v1.0.0
git push origin v1.0.0
```
- Images tagged: `v1.0.0`, `1.0`, `1`, `latest`
- Full GitHub release created with changelog

See `.github/GITHUB_ACTIONS_SETUP.md` for detailed instructions.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Write tests for new features
- Maintain 100% test coverage
- Follow PEP 8 style guidelines
- Update documentation as needed

## Documentation

- **Main Documentation**: `.claude/CLAUDE.md` - Comprehensive project documentation
- **Testing Guide**: `TESTING.md` - Testing strategies and examples
- **Cron Setup**: `CRON_SETUP.md` - Scheduled job configuration
- **GitHub Actions**: `.github/GITHUB_ACTIONS_SETUP.md` - CI/CD setup guide

## Tech Stack

- **Framework**: FastAPI 0.115.5
- **Server**: Uvicorn 0.34.0
- **Letterboxd**: letterboxdpy 5.3.7
- **TMDb**: tmdbapis 1.2.11
- **Scheduler**: APScheduler 3.10.4
- **Testing**: pytest + pytest-cov
- **Containerization**: Docker + Docker Compose

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Letterboxd](https://letterboxd.com) - Film social network
- [TMDb](https://www.themoviedb.org) - Movie database API
- [letterboxdpy](https://github.com/nmcassa/letterboxdpy) - Letterboxd API wrapper
- [tmdbapis](https://github.com/Kometa-Team/TMDbAPIs) - TMDb API wrapper

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing documentation
- Review the test suite for usage examples

---

**Note**: This project is not affiliated with Letterboxd or TMDb. Make sure to comply with their terms of service when using this application.
