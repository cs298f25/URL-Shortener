# URL Shortener API Documentation

Complete API reference for the URL Shortener application.

## Table of Contents

- [Authentication](#authentication)
- [Public Endpoints](#public-endpoints)
- [Protected Endpoints](#protected-endpoints)
- [Error Responses](#error-responses)
- [Examples](#examples)

---

## Authentication

The API uses **session-based authentication** with HTTP-only cookies. After successful login or signup, a session cookie is automatically set and must be included in subsequent requests.

### Session Management

- Sessions are created automatically upon successful login or signup
- Sessions persist for 1 year (or until logout)
- Session cookies are HTTP-only and use SameSite=Lax
- Include cookies in requests using `credentials: 'include'` (fetch) or automatic cookie handling

### Authentication Flow

1. **Sign Up** or **Log In** to create a session
2. Session cookie is automatically set in the response
3. Include the session cookie in all subsequent requests
4. **Log Out** to clear the session

---

## Public Endpoints

Endpoints that do not require authentication.

### **GET `/`**

Returns the main application page.

**Description:** Serves the HTML interface for the URL shortener. If the user is not authenticated, they are redirected to `/login`.

**Response:**
- `200 OK` — Returns `index.html` (if authenticated)
- `302 Found` — Redirects to `/login` (if not authenticated)

**Content-Type:** `text/html`

---

### **GET `/signup`**

Returns the sign up page.

**Description:** Serves the HTML sign up form. If the user is already authenticated, they are redirected to the main page.

**Response:**
- `200 OK` — Returns `signup.html`
- `302 Found` — Redirects to `/` (if already authenticated)

**Content-Type:** `text/html`

---

### **GET `/login`**

Returns the login page.

**Description:** Serves the HTML login form. If the user is already authenticated, they are redirected to the main page.

**Response:**
- `200 OK` — Returns `login.html`
- `302 Found` — Redirects to `/` (if already authenticated)

**Content-Type:** `text/html`

---

### **POST `/signup`**

Creates a new user account and establishes a session.

**Description:** Registers a new user with email and password. Upon successful registration, a session is automatically created and the user is logged in.

**Request Headers:**
```
Content-Type: application/json
```

**Request Body (JSON):**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Fields:**
- `email` (string, required) — User's email address. Will be normalized to lowercase.
- `password` (string, required) — User's password. Must be at least 6 characters.

**Response Codes:**
- `201 Created` — Account created successfully, session established
- `400 Bad Request` — Validation error (missing fields, password too short, or email already registered)
- `500 Internal Server Error` — Server error during account creation

**Success Response (201):**
```json
{
  "success": true,
  "message": "Account created successfully",
  "user": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com"
  }
}
```

**Error Response (400):**
```json
{
  "error": "Email already registered"
}
```

**CORS:** Supports OPTIONS preflight requests.

---

### **POST `/login`**

Authenticates a user and creates a session.

**Description:** Verifies user credentials and establishes a session if valid.

**Request Headers:**
```
Content-Type: application/json
```

**Request Body (JSON):**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Fields:**
- `email` (string, required) — User's email address
- `password` (string, required) — User's password

**Response Codes:**
- `200 OK` — Login successful, session established
- `400 Bad Request` — Missing email or password
- `401 Unauthorized` — Invalid email or password

**Success Response (200):**
```json
{
  "success": true,
  "message": "Logged in successfully",
  "user": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com"
  }
}
```

**Error Response (401):**
```json
{
  "error": "Invalid email or password"
}
```

**CORS:** Supports OPTIONS preflight requests.

---

### **GET `/<short_code>`**

Redirects to the original URL associated with a short code.

**Description:** Public endpoint that redirects users to the original URL. No authentication required. Automatically handles expired links.

**URL Parameters:**
- `short_code` (path parameter) — The shortened code to look up

**Response Codes:**
- `302 Found` — Redirects to the original URL (if link exists and is not expired)
- `404 Not Found` — Short code does not exist
- `410 Gone` — Link exists but has expired

**Behavior:**
- Paths containing periods (e.g., `/favicon.ico`, `/static/style.css`) are ignored and return 404
- Expired links return a JSON error with 410 status
- Non-existent links return a JSON error with 404 status

**Success Response (302):**
```
Location: https://example.com/original-url
```

**Error Response (410 - Expired):**
```json
{
  "error": "This link has expired",
  "message": "The shortened link you're trying to access is no longer available."
}
```

**Error Response (404 - Not Found):**
```json
{
  "error": "Short code not found"
}
```

---

## Protected Endpoints

All endpoints below require a valid session cookie. Unauthenticated requests return `401 Unauthorized` (for JSON requests) or redirect to `/login` (for HTML requests).

### **POST `/logout`**

Logs out the current user and clears the session.

**Description:** Invalidates the current session and logs the user out.

**Request Headers:**
```
Content-Type: application/json (optional)
```

**Response Codes:**
- `200 OK` — Logout successful
- `401 Unauthorized` — Not authenticated

**Success Response (200):**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

**CORS:** Supports OPTIONS preflight requests.

---

### **GET `/user`**

Gets information about the currently authenticated user.

**Description:** Retrieves the current user's account information.

**Request Headers:**
```
Accept: application/json (recommended)
```

**Response Codes:**
- `200 OK` — User information retrieved
- `401 Unauthorized` — Not authenticated
- `404 Not Found` — User not found (session invalid)
- `500 Internal Server Error` — Server error

**Success Response (200):**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "created_at": "1234567890"
}
```

**Fields:**
- `user_id` (string) — Unique user identifier (UUID)
- `email` (string) — User's email address
- `created_at` (string) — Unix timestamp when account was created

---

### **POST `/add`**

Creates a new shortened URL.

**Description:** Creates a shortened link associated with the authenticated user. Can generate a random code or use a custom code.

**Request Headers:**
```
Content-Type: application/json
```

**Request Body (JSON):**
```json
{
  "url": "https://example.com/very/long/url/path",
  "code": "my-custom-code",
  "expires_in": "7d"
}
```

**Fields:**
- `url` (string, required) — The original URL to shorten. Must be a valid, non-empty URL.
- `code` (string, optional) — Custom short code. If not provided, a random 6-character code is generated. Must be unique across all users.
- `expires_in` (string, optional) — Expiration time. Options:
  - `"1h"` — Expires in 1 hour
  - `"24h"` — Expires in 24 hours
  - `"7d"` — Expires in 7 days
  - `"30d"` — Expires in 30 days
  - `"never"` — Never expires (default)

**Response Codes:**
- `201 Created` — Link created successfully
- `400 Bad Request` — Validation error (missing URL, invalid URL, or code already exists)
- `401 Unauthorized` — Not authenticated
- `500 Internal Server Error` — Server error

**Success Response (201):**
```json
{
  "success": true,
  "short_code": "my-custom-code",
  "original_url": "https://example.com/very/long/url/path",
  "expires_at": 1735689600
}
```

**Fields:**
- `short_code` (string) — The shortened code (custom or generated)
- `original_url` (string) — The original URL that was shortened
- `expires_at` (integer|null) — Unix timestamp when link expires, or `null` if never expires

**Error Response (400):**
```json
{
  "error": "URL is required"
}
```

or

```json
{
  "error": "Short code already exists"
}
```

**CORS:** Supports OPTIONS preflight requests.

---

### **POST `/delete`**

Deletes an existing shortened link.

**Description:** Removes a shortened link. Only the owner of the link can delete it.

**Request Headers:**
```
Content-Type: application/json
```

**Request Body (JSON):**
```json
{
  "code": "my-custom-code"
}
```

**Fields:**
- `code` (string, required) — The short code to delete

**Response Codes:**
- `200 OK` — Link deleted successfully
- `400 Bad Request` — Missing short code
- `401 Unauthorized` — Not authenticated
- `403 Forbidden` — User doesn't own this link
- `404 Not Found` — Short code not found
- `500 Internal Server Error` — Server error

**Success Response (200):**
```json
{
  "success": true,
  "message": "Link deleted successfully"
}
```

**Error Response (403):**
```json
{
  "error": "Forbidden: You don't own this link"
}
```

**Error Response (404):**
```json
{
  "error": "Short code not found"
}
```

**CORS:** Supports OPTIONS preflight requests.

---

### **GET `/links`**

Retrieves all shortened links for the authenticated user.

**Description:** Returns a list of all links created by the current user, including expired links. Links are sorted by creation time.

**Request Headers:**
```
Accept: application/json (recommended)
```

**Response Codes:**
- `200 OK` — Links retrieved successfully
- `401 Unauthorized` — Not authenticated
- `500 Internal Server Error` — Server error

**Success Response (200):**
```json
[
  {
    "short_code": "abc123",
    "url": "https://example.com/page1",
    "created_at": "1234567890",
    "expires_at": "1735689600",
    "is_expired": false
  },
  {
    "short_code": "xyz789",
    "url": "https://example.com/page2",
    "created_at": "1234567800",
    "expires_at": "",
    "is_expired": false
  },
  {
    "short_code": "expired",
    "url": "https://example.com/old",
    "created_at": "1000000000",
    "expires_at": "1000003600",
    "is_expired": true
  }
]
```

**Fields (per link object):**
- `short_code` (string) — The shortened code
- `url` (string) — The original URL
- `created_at` (string) — Unix timestamp when link was created
- `expires_at` (string) — Unix timestamp when link expires, or empty string if never expires
- `is_expired` (boolean) — Whether the link has expired

**Empty Response:**
If the user has no links, an empty array is returned:
```json
[]
```

---

## Error Responses

All endpoints may return error responses in the following format:

### Error Response Format

```json
{
  "error": "Error message describing what went wrong"
}
```

### HTTP Status Codes

| Status Code | Meaning | Common Causes |
|------------|---------|---------------|
| `400 Bad Request` | Invalid request data | Missing required fields, validation errors, duplicate resources |
| `401 Unauthorized` | Authentication required | Not logged in, invalid credentials, expired session |
| `403 Forbidden` | Permission denied | User doesn't own the resource |
| `404 Not Found` | Resource not found | Short code doesn't exist, user not found |
| `410 Gone` | Resource expired | Link has expired |
| `500 Internal Server Error` | Server error | Unexpected server error |

### Common Error Messages

**Authentication Errors:**
- `"Authentication required"` — No valid session
- `"Invalid email or password"` — Login credentials incorrect

**Validation Errors:**
- `"Email and password are required"` — Missing required fields
- `"Password must be at least 6 characters"` — Password too short
- `"Email already registered"` — Email already in use
- `"URL is required"` — Missing URL field
- `"Short code is required"` — Missing code field

**Resource Errors:**
- `"Short code not found"` — Link doesn't exist
- `"Short code already exists"` — Custom code already in use
- `"Forbidden: You don't own this link"` — Ownership violation
- `"User not found"` — User account doesn't exist
- `"This link has expired"` — Link has passed expiration date

---

## Examples

### Complete Authentication Flow

```javascript
// 1. Sign Up
const signupResponse = await fetch('/signup', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include',
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'securepass123'
  })
});
const signupData = await signupResponse.json();
// Session cookie is automatically set

// 2. Create a Link
const addResponse = await fetch('/add', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include', // Include session cookie
  body: JSON.stringify({
    url: 'https://example.com/very/long/url',
    expires_in: '7d'
  })
});
const linkData = await addResponse.json();
console.log(linkData.short_code); // e.g., "aB3xY9"

// 3. Get All Links
const linksResponse = await fetch('/links', {
  credentials: 'include',
  headers: { 'Accept': 'application/json' }
});
const links = await linksResponse.json();

// 4. Delete a Link
const deleteResponse = await fetch('/delete', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include',
  body: JSON.stringify({
    code: 'aB3xY9'
  })
});

// 5. Log Out
const logoutResponse = await fetch('/logout', {
  method: 'POST',
  credentials: 'include'
});
```

### Using Custom Short Codes

```javascript
// Create link with custom code
const response = await fetch('/add', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include',
  body: JSON.stringify({
    url: 'https://example.com',
    code: 'my-link',
    expires_in: 'never'
  })
});

// Access the shortened URL
// https://yourdomain.com/my-link
```

### Handling Expired Links

```javascript
// Try to access a link
const response = await fetch('/expired-code');
if (response.status === 410) {
  const data = await response.json();
  console.log(data.error); // "This link has expired"
}
```

---

## CORS Support

The API supports Cross-Origin Resource Sharing (CORS) with the following configuration:

- **Allowed Origins:** All origins (`*`)
- **Credentials:** Supported (`supports_credentials: true`)
- **Preflight:** OPTIONS requests are supported for all endpoints

When making cross-origin requests, include:
```javascript
credentials: 'include'
```

---

## Rate Limiting

Currently, there is no rate limiting implemented. Consider implementing rate limiting for production deployments.

---

## Versioning

The API does not currently use versioning. All endpoints are at the root level without version prefixes.

---

## Base URL

For local development:
```
http://localhost:5000
```

For production, use your deployed domain.

---

## Support

For issues or questions, please refer to:
- [Architecture Documentation](ARCHITECTURE.md)
- [Testing Documentation](TESTING.md)
- [Deployment Documentation](deploy.md)
