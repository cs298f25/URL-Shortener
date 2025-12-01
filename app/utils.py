import os
import random
import string
import time
import uuid
from typing import Dict, List, Optional

import redis
import bcrypt

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
LINK_KEY_PREFIX = os.getenv("LINK_KEY_PREFIX", "link:")
USER_LINKS_PREFIX = os.getenv("USER_LINKS_PREFIX", "user:")
USER_ACCOUNT_PREFIX = os.getenv("USER_ACCOUNT_PREFIX", "account:")
USER_EMAIL_INDEX_PREFIX = os.getenv("USER_EMAIL_INDEX_PREFIX", "email:")

redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)


def _link_key(user_id: str, short_code: str) -> str:
    """Generate Redis key for a link hash."""
    return f"{LINK_KEY_PREFIX}{user_id}:{short_code}"

def _user_links_key(user_id: str) -> str:
    """Generate Redis key for user's link set."""
    return f"{USER_LINKS_PREFIX}{user_id}:links"


def get_item(key: str) -> Optional[str]:
    """Return the string value stored at key, or None if it is missing."""
    return redis_client.get(key)

def set_item(key: str, value: str) -> None:
    """Set key to value in Redis."""
    redis_client.set(key, value)


def delete_item(key: str) -> int:
    """Delete key from Redis. Returns the number of keys removed."""
    return redis_client.delete(key)


def list_keys(pattern: str = "*") -> List[str]:
    """Return a list of keys matching the provided glob-style pattern."""
    return list(redis_client.scan_iter(match=pattern))


def is_link_expired(link_data: Dict[str, str]) -> bool:
    expires_at = link_data.get("expires_at", "")
    if not expires_at or expires_at == "":
        return False
    try:
        expires_timestamp = int(expires_at)
        return time.time() > expires_timestamp
    except (ValueError, TypeError):
        return False


def get_link(short_code: str) -> Optional[Dict[str, str]]:
    """
    Get link data by short_code, checking across all users.
    """
    pattern = f"{LINK_KEY_PREFIX}*:{short_code}"
    keys = list_keys(pattern)
    
    if not keys:
        return None
    
    key = keys[0]
    link_data = redis_client.hgetall(key)
    
    if not link_data:
        return None
    
    if is_link_expired(link_data):
        return None
    
    return link_data


def save_link(user_id: str, short_code: str, url: str, expires_at: Optional[int] = None) -> None:
    """
    Save a link with expiration. If expires_at is None, link never expires.
    Also maintains reverse index in user's link set.
    """
    created_at = int(time.time())
    expires_at_str = str(expires_at) if expires_at else ""
    
    link_key = _link_key(user_id, short_code)
    redis_client.hset(link_key, mapping={
        "url": url,
        "created_at": str(created_at),
        "expires_at": expires_at_str,
        "user_id": user_id
    })
    
    user_links_key = _user_links_key(user_id)
    redis_client.sadd(user_links_key, short_code)


def remove_link(user_id: str, short_code: str) -> int:
    """
    Remove a link if owned by user_id.
    Returns 1 if deleted, 0 if not found or not owned by user.
    """
    link_key = _link_key(user_id, short_code)
    
    if not redis_client.exists(link_key):
        return 0
    
    deleted = redis_client.delete(link_key)
    
    user_links_key = _user_links_key(user_id)
    redis_client.srem(user_links_key, short_code)
    
    return deleted


def link_exists(short_code: str) -> bool:
    pattern = f"{LINK_KEY_PREFIX}*:{short_code}"
    keys = list_keys(pattern)
    
    if not keys:
        return False
    
    for key in keys:
        link_data = redis_client.hgetall(key)
        if link_data and not is_link_expired(link_data):
            return True
    
    return False


def get_user_links(user_id: str) -> List[Dict[str, str]]:
    """
    Returns list of dicts with short_code, url, created_at, expires_at, is_expired.
    """
    user_links_key = _user_links_key(user_id)
    short_codes = redis_client.smembers(user_links_key)
    
    if not short_codes:
        return []
    
    links = []
    for short_code in short_codes:
        link_key = _link_key(user_id, short_code)
        link_data = redis_client.hgetall(link_key)
        
        if link_data:
            link_data["short_code"] = short_code
            link_data["is_expired"] = is_link_expired(link_data)
            links.append(link_data)
    
    return links


def get_link_owner(short_code: str) -> Optional[str]:
    """
    Get the user_id who owns a short_code.
    Returns None if not found.
    """
    pattern = f"{LINK_KEY_PREFIX}*:{short_code}"
    keys = list_keys(pattern)
    
    if not keys:
        return None
    
    key = keys[0]
    link_data = redis_client.hgetall(key)
    
    if link_data:
        return link_data.get("user_id")
    
    return None


def cleanup_expired_links() -> int:
    """
    """
    pattern = f"{LINK_KEY_PREFIX}*"
    keys = list_keys(pattern)
    
    cleaned = 0
    for key in keys:
        link_data = redis_client.hgetall(key)
        if link_data and is_link_expired(link_data):
            user_id = link_data.get("user_id")
            if user_id:
                parts = key.split(":")
                if len(parts) >= 3:
                    short_code = ":".join(parts[2:])
                    user_links_key = _user_links_key(user_id)
                    redis_client.srem(user_links_key, short_code)
                    cleaned += 1
    
    return cleaned


def generate_short_code(length: int = 6) -> str:
    """Generate a unique short code that doesn't exist across all users."""
    chars = string.ascii_letters + string.digits
    while True:
        code = "".join(random.choice(chars) for _ in range(length))
        if not link_exists(code):
            return code


# ==================== Authentication Functions ====================

def _user_account_key(user_id: str) -> str:
    """Generate Redis key for user account hash."""
    return f"{USER_ACCOUNT_PREFIX}{user_id}"


def _email_index_key(email: str) -> str:
    """Generate Redis key for email to user_id mapping."""
    return f"{USER_EMAIL_INDEX_PREFIX}{email.lower()}"


def create_user(email: str, password: str) -> Optional[Dict[str, str]]:
    """
    Create a new user account.
    Returns user dict with user_id, email, created_at if successful.
    Returns None if email already exists.
    """
    email_lower = email.lower().strip()
    
    email_key = _email_index_key(email_lower)
    if redis_client.exists(email_key):
        return None
    
    user_id = str(uuid.uuid4())
    
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    created_at = int(time.time())
    account_key = _user_account_key(user_id)
    redis_client.hset(account_key, mapping={
        "user_id": user_id,
        "email": email_lower,
        "password_hash": password_hash,
        "created_at": str(created_at)
    })
    
    # Create email index
    redis_client.set(email_key, user_id)
    
    return {
        "user_id": user_id,
        "email": email_lower,
        "created_at": str(created_at)
    }


def verify_user(email: str, password: str) -> Optional[Dict[str, str]]:
    """
    Verify user credentials and return user data if valid.
    Returns user dict with user_id, email, created_at if valid.
    Returns None if invalid credentials.
    """
    email_lower = email.lower().strip()
    
    email_key = _email_index_key(email_lower)
    user_id = redis_client.get(email_key)
    
    if not user_id:
        return None
    
    account_key = _user_account_key(user_id)
    user_data = redis_client.hgetall(account_key)
    
    if not user_data:
        return None
    
    stored_hash = user_data.get("password_hash", "")
    if not stored_hash:
        return None
    
    if not bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
        return None
    
    return {
        "user_id": user_id,
        "email": user_data.get("email"),
        "created_at": user_data.get("created_at")
    }

def get_user_by_id(user_id: str) -> Optional[Dict[str, str]]:
    """Get user account by user_id. Returns None if not found."""
    account_key = _user_account_key(user_id)
    user_data = redis_client.hgetall(account_key)
    
    if not user_data:
        return None
    
    user_data.pop("password_hash", None)
    return user_data

def get_user_by_email(email: str) -> Optional[Dict[str, str]]:
    """Get user account by email. Returns None if not found."""
    email_lower = email.lower().strip()
    email_key = _email_index_key(email_lower)
    user_id = redis_client.get(email_key)
    
    if not user_id:
        return None
    
    return get_user_by_id(user_id)


def email_exists(email: str) -> bool:
    """Check if an email is already registered."""
    email_lower = email.lower().strip()
    email_key = _email_index_key(email_lower)
    return redis_client.exists(email_key) == 1
