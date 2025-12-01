# Application Architecture

This application follows a **three-layer architecture** pattern for clean separation of concerns:

## Layer 1: Data Access Layer (`db.py`)

**Purpose**: Pure database operations with Redis. No business logic.

**Responsibilities**:
- Direct Redis interactions (get, set, hash operations, sets, etc.)
- Key generation helpers
- Raw data storage and retrieval

**Key Functions**:
- `get()`, `set_value()`, `delete()` - Basic Redis operations
- `hash_get_all()`, `hash_set_mapping()` - Hash operations
- `set_add()`, `set_remove()`, `set_members()` - Set operations
- Key generation helpers: `link_key()`, `user_account_key()`, etc.

**No business logic** - just data operations.

---

## Layer 2: Service Layer (`services.py`)

**Purpose**: Business logic and application rules.

**Responsibilities**:
- Authentication logic (signup, login, password hashing)
- Link management logic (create, validate, expire checks)
- Data validation
- Business rules enforcement
- Coordinates multiple database operations

**Key Services**:
- `AuthService` - User authentication and account management
- `LinkService` - Link creation, retrieval, deletion
- Helper functions: `parse_expires_in()`, `generate_short_code()`, `is_expired()`

**No HTTP/Flask code** - just business logic.

---

## Layer 3: API/Endpoint Layer (`app.py`)

**Purpose**: HTTP request/response handling.

**Responsibilities**:
- Route definitions
- Request parsing and validation
- Response formatting
- Session management
- Error handling and HTTP status codes
- Delegates to service layer for business logic

**Key Features**:
- Flask route handlers
- `@login_required` decorator for protected routes
- Request/response JSON formatting
- Calls services, never directly accesses database

**No business logic** - just HTTP handling.

---

## Data Flow Example

### Creating a Link:

```
Client Request
    ↓
app.py: POST /api/add
    ↓ (validates request, extracts data)
services.py: LinkService.create_link()
    ↓ (business logic: validates URL, generates code, parses expiration)
db.py: hash_set_mapping(), set_add()
    ↓ (stores data in Redis)
Response back through layers
```

### User Login:

```
Client Request
    ↓
app.py: POST /api/login
    ↓ (validates email/password present)
services.py: AuthService.verify_user()
    ↓ (business logic: checks password hash)
db.py: get(), hash_get_all()
    ↓ (retrieves user data from Redis)
Response + session setup
```

---

## Benefits of This Architecture

1. **Separation of Concerns**: Each layer has a single, clear responsibility
2. **Testability**: Easy to mock database layer when testing services
3. **Maintainability**: Changes to database structure don't affect business logic
4. **Reusability**: Services can be used by other interfaces (CLI, background jobs, etc.)
5. **Scalability**: Can swap database implementations without changing business logic

---

## File Structure

```
app/
├── app.py          # API/Endpoint Layer (HTTP routes)
├── services.py     # Service Layer (business logic)
├── db.py           # Data Access Layer (Redis operations)
├── utils.py        # (Legacy - can be removed)
└── ...
```