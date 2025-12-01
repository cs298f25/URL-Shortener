# TESTING.md

## Overview

This project uses a layered architecture with **dependency injection** so every layer (database, services, API) can be cleanly and independently tested using **pytest**.

```
tests/
│── test_db.py
│── test_services.py
└── test_api.py
```

Each layer is isolated using mocks or fake implementations.

---

# 1. Architecture Overview

The system has three testable layers:

## 1. Data Access Layer (`db.py`)
- Wraps all Redis operations  
- Tested by mocking the Redis client

## 2. Service Layer (`services.py`)
- Contains business logic for users and links  
- Tested using a simple in-memory mock database

## 3. API Layer (`app.py`)
- Flask routes and HTTP behavior  
- Tested with Flask’s test client and mocked services

Services use **instance methods** and accept a database dependency:

```python
class AuthService:
    def __init__(self, database: DatabaseInterface):
        self.db = database
```

This allows each layer to be tested in isolation.

---

# 2. Running Tests

## Install dependencies
```bash
pip install -r requirements.txt
```

## Run all tests
```bash
pytest -q
```

## Run individual test files
```bash
pytest tests/test_db.py
pytest tests/test_services.py
pytest tests/test_api.py
```

## Run with coverage
```bash
pytest --cov=. --cov-report=html
```

---

# 3. Test Strategy

## 3.1 Data Access Layer — `test_db.py`

**Goal:** Validate Redis wrapper functions without a real Redis instance.

**Strategy:** Mock the Redis client:

```python
from unittest.mock import patch

@patch("db.redis_client")
def test_get(mock_redis):
    mock_redis.get.return_value = "test_value"
    assert db.get("key") == "test_value"
```

**What to test:** get, set_value, hash operations, sets, error handling

## 3.2 Service Layer — `test_services.py`

**Goal:** Test business logic independently of Redis.

**Strategy:** Use an in-memory mock database:

```python
class MockDatabase:
    def __init__(self):
        self.data = {}

    def get(self, key):
        return self.data.get(key)

    def set_value(self, key, value):
        self.data[key] = value
```

Inject into services:

```python
mock_db = MockDatabase()
auth = AuthService(database=mock_db)
```

**What to test:** user creation, login, link management, validation, error cases

## 3.3 API Layer — `test_api.py`

**Goal:** Verify all HTTP endpoints behave correctly.

**Strategy:** Use Flask test client + mocked services:

```python
@patch("app.auth_service")
def test_signup_success(mock_auth):
    mock_auth.create_user.return_value = {"email": "test@example.com"}
    res = client.post("/api/signup", json={"email": "...", "password": "..."})

    assert res.status_code == 201
```

**What to test:** signup, login, link CRUD endpoints, authentication, validation, error responses

---

# 4. Benefits

- **Isolation:** No tests require a real Redis or external service  
- **Fast:** All tests run in-memory  
- **Stable:** Tests are environment-independent  
- **Maintainable:** Each layer is independently verifiable  
- **Extensible:** Easy to swap real or mock implementations

---

# 5. Next Steps

- Add integration tests using a real Redis (Docker)  
- Add performance/load tests  
- Set up CI/CD pipeline to run tests automatically  
- Increase test coverage to >90%
