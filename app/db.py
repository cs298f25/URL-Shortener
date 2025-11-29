"""
Data Access Layer - Pure database operations with Redis.
No business logic, just direct database interactions.
"""
import os
from typing import Dict, List, Optional, Set

import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Redis key prefixes
LINK_KEY_PREFIX = "link:"
USER_LINKS_PREFIX = "user:"
USER_ACCOUNT_PREFIX = "account:"
USER_EMAIL_INDEX_PREFIX = "email:"

redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)


# ==================== Key Generation Helpers ====================

def link_key(user_id: str, short_code: str) -> str:
    """Generate Redis key for a link hash."""
    return f"{LINK_KEY_PREFIX}{user_id}:{short_code}"


def user_links_key(user_id: str) -> str:
    """Generate Redis key for user's link set."""
    return f"{USER_LINKS_PREFIX}{user_id}:links"


def user_account_key(user_id: str) -> str:
    """Generate Redis key for user account hash."""
    return f"{USER_ACCOUNT_PREFIX}{user_id}"


def email_index_key(email: str) -> str:
    """Generate Redis key for email to user_id mapping."""
    return f"{USER_EMAIL_INDEX_PREFIX}{email.lower()}"


# ==================== Generic Redis Operations ====================

def get(key: str) -> Optional[str]:
    """Get string value from Redis."""
    return redis_client.get(key)


def set_value(key: str, value: str) -> None:
    """Set string value in Redis."""
    redis_client.set(key, value)


def delete(key: str) -> int:
    """Delete key from Redis. Returns number of keys deleted."""
    return redis_client.delete(key)


def exists(key: str) -> bool:
    """Check if key exists in Redis."""
    return redis_client.exists(key) == 1


def list_keys(pattern: str = "*") -> List[str]:
    """Get list of keys matching pattern."""
    return list(redis_client.scan_iter(match=pattern))


# ==================== Hash Operations ====================

def hash_get(key: str, field: str) -> Optional[str]:
    """Get field from hash."""
    return redis_client.hget(key, field)


def hash_get_all(key: str) -> Dict[str, str]:
    """Get all fields from hash."""
    return redis_client.hgetall(key)


def hash_set(key: str, field: str, value: str) -> int:
    """Set field in hash."""
    return redis_client.hset(key, field, value)


def hash_set_mapping(key: str, mapping: Dict[str, str]) -> int:
    """Set multiple fields in hash at once."""
    return redis_client.hset(key, mapping=mapping)


def hash_delete(key: str, *fields: str) -> int:
    """Delete fields from hash."""
    return redis_client.hdel(key, *fields)


# ==================== Set Operations ====================

def set_add(key: str, *members: str) -> int:
    """Add members to set. Returns number of members added."""
    return redis_client.sadd(key, *members)


def set_remove(key: str, *members: str) -> int:
    """Remove members from set. Returns number of members removed."""
    return redis_client.srem(key, *members)


def set_members(key: str) -> Set[str]:
    """Get all members of a set."""
    return redis_client.smembers(key)


def set_contains(key: str, member: str) -> bool:
    """Check if set contains member."""
    return redis_client.sismember(key, member)


# ==================== Multi-Get Operations ====================

def multi_get(keys: List[str]) -> List[Optional[str]]:
    """Get multiple keys at once."""
    return redis_client.mget(keys)

