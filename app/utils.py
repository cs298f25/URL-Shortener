import os
import random
import string
from typing import Dict, List, Optional

import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
LINK_KEY_PREFIX = os.getenv("LINK_KEY_PREFIX", "link:")

redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)


def _link_key(short_code: str) -> str:
    return f"{LINK_KEY_PREFIX}{short_code}"


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


def get_link(short_code: str) -> Optional[str]:
    return get_item(_link_key(short_code))


def save_link(short_code: str, url: str) -> None:
    set_item(_link_key(short_code), url)


def remove_link(short_code: str) -> int:
    return delete_item(_link_key(short_code))


def link_exists(short_code: str) -> bool:
    return redis_client.exists(_link_key(short_code)) == 1


def get_all_links() -> Dict[str, str]:
    keys = list_keys(f"{LINK_KEY_PREFIX}*")
    if not keys:
        return {}
    values = redis_client.mget(keys)
    links: Dict[str, str] = {}
    for key, value in zip(keys, values):
        if value is None:
            continue
        short_code = key[len(LINK_KEY_PREFIX):]
        links[short_code] = value
    return links


def generate_short_code(length: int = 6) -> str:
    chars = string.ascii_letters + string.digits
    while True:
        code = "".join(random.choice(chars) for _ in range(length))
        if not link_exists(code):
            return code