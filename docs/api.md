# URL Shortener API — Endpoint Documentation

---

## **GET `/`**
Returns the main HTML page (`index.html`) for the URL shortener interface.

---

## **POST `/add`**
Creates a new shortened URL.

**Request Body (JSON):**
- `url` — the original URL (required)
- `code` — a custom short code (optional)

**Behavior:**
- Generates a random short code if none is provided.
- Saves mapping to storage.

**Returns:** JSON containing `short_code` and `original_url`.

---

## **POST `/delete`**
Deletes an existing short code mapping.

**Request Body (JSON):**
- `code` — the short code to delete (required)

**Returns:** Success message or error if code does not exist.

---

## **GET `/links`**
Returns all short codes and their corresponding URLs.

**Returns:** A JSON dictionary of all mappings.

---

## **GET `/map?code=VALUE`**
Looks up a short code without redirecting.

**Query Parameter:**
- `code` — the short code to look up (required)

**Returns:** The original URL or an error.

---

## **GET `/<short_code>`**
Redirects the user to the original URL associated with the given short code.

**Behavior:**
- Redirects with HTTP 302 if found.
- Returns an error JSON if short code does not exist.
- Ignores paths containing periods (e.g., `/favicon.ico`).