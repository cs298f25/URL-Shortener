# Testing Architecture

## Overview

The application now uses **dependency injection** to enable comprehensive testing of each layer. Services use instance methods instead of static methods, allowing database dependencies to be mocked for testing.

## Architecture Changes for Testability

### Before (Static Methods - Hard to Test)
```python
class AuthService:
    @staticmethod
    def create_user(email: str, password: str):
        # Hard-coded db access - can't be mocked
        db.hash_set_mapping(...)
```

### After (Instance Methods with Dependency Injection - Testable)
```python
class AuthService:
    def __init__(self, database: DatabaseInterface = None):
        self.db = database if database is not None else db
    
    def create_user(self, email: str, password: str):
        # Uses self.db - can be mocked!
        self.db.hash_set_mapping(...)
```

## Testing Each Layer

### 1. Data Access Layer (`db.py`)

**Test File:** `tests/test_db.py`

**Strategy:** Mock the Redis client directly

```python
@patch('db.redis_client')
def test_get(self, mock_redis):
    mock_redis.get.return_value = "test_value"
    result = db.get("test_key")
    self.assertEqual(result, "test_value")
```

**Tests:** All Redis operations (get, set, hash operations, sets, etc.)

### 2. Service Layer (`services.py`)

**Test File:** `tests/test_services.py`

**Strategy:** Use `MockDatabase` class that implements the database interface

```python
class MockDatabase:
    """Mock database for testing services."""
    def get(self, key: str): ...
    def set_value(self, key: str, value: str): ...
    # ... implements all database methods

def setUp(self):
    self.mock_db = MockDatabase()
    self.auth_service = AuthService(database=self.mock_db)
    
def test_create_user_success(self):
    user = self.auth_service.create_user("test@example.com", "password")
    self.assertIsNotNone(user)
```

**Tests:**
- Authentication business logic
- Link management business logic
- Validation rules
- Helper functions

### 3. API Layer (`app.py`)

**Test File:** `tests/test_api.py`

**Strategy:** Use Flask test client + mock services

```python
@patch('app.auth_service')
def test_signup_success(self, mock_auth_service):
    mock_auth_service.create_user.return_value = mock_user
    response = self.app.post('/api/signup', ...)
    self.assertEqual(response.status_code, 201)
```

**Tests:**
- All HTTP endpoints
- Request/response handling
- Authentication decorators
- Error responses

## Running Tests

### Install Dependencies
```bash
cd app
pip install -r requirements.txt
```

### Run All Tests
```bash
python -m unittest discover tests
```

### Run Specific Layer Tests
```bash
# Test data access layer
python -m unittest tests.test_db

# Test service layer
python -m unittest tests.test_services

# Test API layer
python -m unittest tests.test_api
```

### Run with Coverage
```bash
pip install pytest pytest-cov
pytest tests/ --cov=. --cov-report=html
```

## Benefits

1. **Isolation**: Each layer can be tested independently
2. **Speed**: Tests don't require actual Redis/database connections
3. **Reliability**: Mocked dependencies ensure consistent test results
4. **Maintainability**: Changes to one layer don't break tests for others
5. **Dependency Injection**: Services can use real or mocked databases

## Example Test Flow

```
┌─────────────────────────────────────┐
│ test_api.py                         │
│  - Mocks: auth_service, link_service│
│  - Tests: HTTP endpoints            │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ test_services.py                    │
│  - Mocks: MockDatabase              │
│  - Tests: Business logic            │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ test_db.py                          │
│  - Mocks: redis_client              │
│  - Tests: Database operations       │
└─────────────────────────────────────┘
```

## Key Design Decisions

1. **No Static Methods**: All services use instance methods for testability
2. **Dependency Injection**: Services accept database as constructor parameter
3. **Protocol Interface**: `DatabaseInterface` Protocol defines contract
4. **Default Behavior**: If no database provided, uses real `db` module
5. **Mock Database**: `MockDatabase` class simulates Redis for service tests

## Next Steps

- Add integration tests that test all layers together
- Add performance/load tests
- Set up CI/CD pipeline to run tests automatically
- Increase test coverage to >90%

