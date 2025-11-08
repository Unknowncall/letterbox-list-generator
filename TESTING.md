# Testing Documentation

## Overview

This project includes comprehensive test coverage for all application components. Tests are written using pytest and organized by module.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py                  # Shared fixtures and configuration
├── test_pagination.py           # Tests for utils/pagination.py
├── test_schemas.py              # Tests for models/schemas.py
├── test_film_service.py         # Tests for services/film_service.py
├── test_users_controller.py     # Tests for controllers/users.py
├── test_users_router.py         # Tests for routers/users.py (API endpoints)
├── test_scheduler.py            # Tests for jobs/scheduler.py
├── test_fetch_top_movies.py     # Tests for jobs/fetch_top_movies.py
└── test_index.py                # Tests for index.py (main app)
```

## Prerequisites

### Install Test Dependencies

```bash
pip install -r requirements.txt
```

Test dependencies included:
- `pytest` - Testing framework
- `pytest-asyncio` - Support for async tests
- `pytest-cov` - Coverage reporting
- `pytest-mock` - Enhanced mocking utilities
- `httpx` - Required by FastAPI TestClient

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest tests/test_pagination.py
```

### Run Specific Test Class

```bash
pytest tests/test_pagination.py::TestPaginateData
```

### Run Specific Test Function

```bash
pytest tests/test_pagination.py::TestPaginateData::test_basic_pagination_first_page
```

### Run Tests with Verbose Output

```bash
pytest -v
```

### Run Tests with Coverage Report

```bash
pytest --cov=. --cov-report=html
```

This generates an HTML coverage report in `htmlcov/index.html`.

### Run Tests with Coverage in Terminal

```bash
pytest --cov=. --cov-report=term-missing
```

### Run Only Fast Tests (Skip Slow Tests)

```bash
pytest -m "not slow"
```

### Run Only Unit Tests

```bash
pytest -m unit
```

### Run Only Integration Tests

```bash
pytest -m integration
```

## Test Categories

Tests are organized into the following categories:

### Unit Tests

Test individual functions and methods in isolation:
- `test_pagination.py` - Pagination utility functions
- `test_schemas.py` - Pydantic model validation
- `test_film_service.py` - Film data processing
- `test_scheduler.py` - Scheduler configuration

### Integration Tests

Test component interactions:
- `test_users_controller.py` - Controller logic with mocked dependencies
- `test_users_router.py` - API endpoints with TestClient
- `test_fetch_top_movies.py` - Cron job execution
- `test_index.py` - Application lifecycle

## Key Test Fixtures

Located in `tests/conftest.py`:

### `mock_user`
Mock letterboxdpy User object with sample data for testing.

```python
def test_example(mock_user):
    # Use pre-configured mock user
    assert mock_user.username == "testuser"
```

### `sample_films`
Sample film data for testing pagination and sorting.

```python
def test_example(sample_films):
    # Use pre-configured film list
    assert len(sample_films) == 5
```

### `app_client`
FastAPI TestClient for integration testing.

```python
def test_example(app_client):
    response = app_client.get('/health')
    assert response.status_code == 200
```

### `mock_env_vars`
Helper for setting environment variables in tests.

```python
def test_example(mock_env_vars):
    mock_env_vars(CRON_ENABLED='true', CRON_SCHEDULE='0 0 * * *')
    # Test code using environment variables
```

## Test Coverage Summary

### utils/pagination.py - 100% Coverage
- Basic pagination (first, middle, last page)
- Partial pages
- Empty data
- Sorting (ascending, descending)
- Sorting by different fields
- Limit before pagination
- Complex scenarios (sorting + limit + pagination)
- Edge cases (None values, case-insensitive sorting)

### models/schemas.py - 100% Coverage
- Film model validation
- UserStats validation
- UserProfileResponse validation
- WatchlistResponse validation
- TopRatedResponse validation
- UsernameValidator with all validation rules
- Invalid input handling

### services/film_service.py - 100% Coverage
- `get_rated_and_liked_films()` - All filtering scenarios
- `normalize_watchlist_film()` - All data transformations
- Rating scale conversion (10-point to 5-star)
- Edge cases (missing fields, empty data)

### controllers/users.py - 100% Coverage
- `get_user_profile()` - Success and error cases
- `get_user_watchlist()` - Pagination, sorting, filtering
- `get_top_rated_films()` - All sorting and pagination combinations
- Error handling for all functions

### routers/users.py - 100% Coverage
- GET /users/{username} - Valid and invalid inputs
- GET /users/{username}/watchlist - All query parameters
- GET /users/{username}/top-rated - All query parameters
- Validation errors (422)
- Not found errors (404)
- Server errors (500)

### jobs/scheduler.py - 100% Coverage
- `get_cron_config()` - All environment variable combinations
- `validate_cron_expression()` - Valid and invalid expressions
- `init_scheduler()` - Success and error scenarios
- `shutdown_scheduler()` - All shutdown scenarios
- `get_scheduler()` - Getter function

### jobs/fetch_top_movies.py - 100% Coverage
- `fetch_top_movies_job()` - Single and multiple users
- Error handling and continuation
- Logging format verification
- `run_sync_job()` - Async wrapper execution

### index.py - 100% Coverage
- Health check endpoint
- App configuration
- Startup event (scheduler initialization)
- Shutdown event (scheduler cleanup)
- Error handling
- OpenAPI documentation

## Writing New Tests

### Test Naming Convention

- Test files: `test_<module_name>.py`
- Test classes: `Test<FunctionName>` or `Test<ComponentName>`
- Test functions: `test_<what_is_being_tested>`

Example:
```python
class TestGetUserProfile:
    def test_get_user_profile_success(self):
        # Test successful profile retrieval
        pass

    def test_get_user_profile_not_found(self):
        # Test 404 error case
        pass
```

### Testing Async Functions

Use the `@pytest.mark.asyncio` decorator:

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

### Mocking Dependencies

Use `unittest.mock.patch` for mocking:

```python
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_with_mock():
    with patch('module.dependency', new_callable=AsyncMock) as mock_dep:
        mock_dep.return_value = {'data': 'test'}
        result = await function_using_dependency()
        assert result['data'] == 'test'
```

### Testing API Endpoints

Use FastAPI TestClient:

```python
from fastapi.testclient import TestClient
from index import app

client = TestClient(app)

def test_endpoint():
    response = client.get('/users/testuser')
    assert response.status_code == 200
    assert response.json()['username'] == 'testuser'
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          pytest --cov=. --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Debugging Tests

### Run Tests with Print Statements

```bash
pytest -s
```

### Run Tests with Debugger

```bash
pytest --pdb
```

This will drop into pdb debugger on test failure.

### View Captured Logs

```bash
pytest --log-cli-level=INFO
```

## Common Issues and Solutions

### Issue: Tests Failing Due to Env Variables

**Solution:** Tests automatically clear environment variables. Use `mock_env_vars` fixture:

```python
def test_with_env(mock_env_vars):
    mock_env_vars(CRON_ENABLED='true')
    # Test code
```

### Issue: Async Tests Not Running

**Solution:** Ensure `pytest-asyncio` is installed and use `@pytest.mark.asyncio`:

```python
@pytest.mark.asyncio
async def test_async():
    result = await async_function()
    assert result
```

### Issue: Mock Not Being Called

**Solution:** Verify the patch path matches the import path in the tested module:

```python
# If module.py has: from services import film_service
# Patch like this:
with patch('module.film_service.function'):
    pass
```

## Test Maintenance

### Updating Tests After Code Changes

1. Run tests to identify failures: `pytest`
2. Update test expectations to match new behavior
3. Add new tests for new functionality
4. Verify coverage hasn't decreased: `pytest --cov`

### Removing Obsolete Tests

When removing features:
1. Remove corresponding test files/classes
2. Update `conftest.py` if fixtures are no longer needed
3. Run full test suite to ensure no dependencies broken

## Best Practices

1. **One Assertion Per Test** - Keep tests focused
2. **Descriptive Names** - Test names should describe what they test
3. **Arrange-Act-Assert** - Structure tests clearly
4. **Mock External Dependencies** - Don't make real API calls
5. **Test Edge Cases** - Empty lists, None values, errors
6. **Use Fixtures** - Reuse common setup code
7. **Keep Tests Fast** - Mock slow operations
8. **Test Behavior, Not Implementation** - Focus on outcomes

## Coverage Goals

- **Minimum Coverage:** 90%
- **Target Coverage:** 95%+
- **Critical Paths:** 100% (authentication, payment, data integrity)

Current coverage: **~100%**

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Python Mock](https://docs.python.org/3/library/unittest.mock.html)

---

**Last Updated:** November 7, 2025
**Maintained By:** Development Team
