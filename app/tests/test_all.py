"""
Unified pytest test suite for:
- db.py  (Data Access Layer)
- services.py (Business Logic Layer)
- Helper functions
"""

from unittest.mock import Mock, MagicMock, patch
import pytest
import sys
import os
import fnmatch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db
from services import AuthService, LinkService, is_expired, parse_expires_in
import bcrypt


# ============================================================
#  MOCK DATABASE
# ============================================================

class MockDatabase:
    """Mock database for testing services."""

    def __init__(self):
        self.data = {}
        self.hashes = {}
        self.sets = {}

    def get(self, key: str):
        return self.data.get(key)

    def set_value(self, key: str, value: str):
        self.data[key] = value

    def delete(self, key: str):
        deleted = 0
        if key in self.data:
            del self.data[key]
            deleted = 1
        if key in self.hashes:
            del self.hashes[key]
            deleted = 1
        return deleted

    def exists(self, key: str):
        return key in self.data or key in self.hashes

    def list_keys(self, pattern: str = "*"):
        all_keys = list(self.data.keys()) + list(self.hashes.keys())
        return [k for k in all_keys if fnmatch.fnmatch(k, pattern)]

    def hash_get_all(self, key: str):
        return self.hashes.get(key, {})

    def hash_set_mapping(self, key: str, mapping: dict):
        if key not in self.hashes:
            self.hashes[key] = {}
        self.hashes[key].update(mapping)
        return len(mapping)

    def set_add(self, key: str, *members: str):
        if key not in self.sets:
            self.sets[key] = set()
        before = len(self.sets[key])
        for m in members:
            self.sets[key].add(m)
        return len(self.sets[key]) - before

    def set_remove(self, key: str, *members: str):
        if key not in self.sets:
            return 0
        before = len(self.sets[key])
        for m in members:
            self.sets[key].discard(m)
        return before - len(self.sets[key])

    def set_members(self, key: str):
        return self.sets.get(key, set())


# ============================================================
#  DB LAYER TESTS (pytest)
# ============================================================

def test_db_get():
    with patch("db.redis_client") as mock_redis:
        mock_redis.get.return_value = "test_value"
        assert db.get("x") == "test_value"
        mock_redis.get.assert_called_once_with("x")


def test_db_set_value():
    with patch("db.redis_client") as mock_redis:
        db.set_value("k", "v")
        mock_redis.set.assert_called_once_with("k", "v")


def test_db_delete():
    with patch("db.redis_client") as mock_redis:
        mock_redis.delete.return_value = 1
        assert db.delete("k") == 1
        mock_redis.delete.assert_called_once_with("k")


def test_db_exists():
    with patch("db.redis_client") as mock_redis:
        mock_redis.exists.return_value = 1
        assert db.exists("k") is True
        mock_redis.exists.assert_called_once_with("k")


def test_db_hash_get_all():
    with patch("db.redis_client") as mock_redis:
        mock_redis.hgetall.return_value = {"f": "v"}
        assert db.hash_get_all("k") == {"f": "v"}
        mock_redis.hgetall.assert_called_once_with("k")


def test_db_hash_set_mapping():
    with patch("db.redis_client") as mock_redis:
        mapping = {"a": 1}
        db.hash_set_mapping("k", mapping)
        mock_redis.hset.assert_called_once_with("k", mapping=mapping)


def test_db_set_add():
    with patch("db.redis_client") as mock_redis:
        mock_redis.sadd.return_value = 2
        assert db.set_add("k", "a", "b") == 2
        mock_redis.sadd.assert_called_once_with("k", "a", "b")


def test_db_set_members():
    with patch("db.redis_client") as mock_redis:
        mock_redis.smembers.return_value = {"a"}
        assert db.set_members("k") == {"a"}
        mock_redis.smembers.assert_called_once_with("k")


# ============================================================
#  AUTH SERVICE TESTS
# ============================================================

@pytest.fixture
def auth():
    return AuthService(database=MockDatabase())


@patch("services.bcrypt")
def test_auth_create_user_success(mock_bcrypt, auth):
    mock_bcrypt.hashpw.return_value = b"hashed"
    mock_bcrypt.gensalt.return_value = b"salt"

    user = auth.create_user("test@example.com", "pass")
    assert user is not None
    assert user["email"] == "test@example.com"

    email_key = db.email_index_key("test@example.com")
    assert email_key in auth.db.data


def test_auth_duplicate_email(auth):
    auth.db.set_value(db.email_index_key("test@example.com"), "user123")
    assert auth.create_user("test@example.com", "pass") is None


@patch("services.bcrypt")
def test_auth_verify_user_success(mock_bcrypt, auth):
    mock_bcrypt.checkpw.return_value = True

    uid = "u1"
    email = "test@example.com"
    pwd = "123"
    hashed = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()

    key = db.user_account_key(uid)
    auth.db.hash_set_mapping(
        key,
        {"user_id": uid, "email": email, "password_hash": hashed}
    )
    auth.db.set_value(db.email_index_key(email), uid)

    user = auth.verify_user(email, pwd)
    assert user is not None
    assert user["user_id"] == uid


def test_auth_verify_user_no_email(auth):
    assert auth.verify_user("missing@example.com", "pw") is None


def test_auth_email_exists(auth):
    auth.db.set_value(db.email_index_key("a@a.com"), "u1")
    assert auth.email_exists("a@a.com") is True
    assert auth.email_exists("x@x.com") is False


# ============================================================
#  LINK SERVICE TESTS
# ============================================================

@pytest.fixture
def links():
    return LinkService(database=MockDatabase())


@patch("services.time")
def test_link_create_success(mock_time, links):
    mock_time.time.return_value = 1000

    link = links.create_link("u1", "https://a.com", expires_in="1h")
    assert link["url"] == "https://a.com"

    key = db.link_key("u1", link["short_code"])
    assert key in links.db.hashes


def test_link_create_custom_code(links):
    link = links.create_link("u1", "https://a.com", custom_code="abc")
    assert link["short_code"] == "abc"


def test_link_create_duplicate_code(links):
    links.create_link("u1", "https://x.com", custom_code="abc")
    with pytest.raises(ValueError):
        links.create_link("u1", "https://y.com", custom_code="abc")


def test_link_create_invalid_url(links):
    with pytest.raises(ValueError):
        links.create_link("u1", "", custom_code="abc")


def test_link_get_success(links):
    created = links.create_link("u1", "https://a.com")
    fetched = links.get_link(created["short_code"])
    assert fetched is not None
    assert fetched["url"] == "https://a.com"


def test_link_delete_success(links):
    created = links.create_link("u1", "https://a.com", custom_code="abc")
    assert links.delete_link("u1", "abc") is True
    assert links.get_link("abc") is None


# ============================================================
#  HELPER FUNCTIONS
# ============================================================

@patch("services.time")
def test_is_expired(mock_time):
    mock_time.time.return_value = 1000

    assert is_expired("2000") is False
    assert is_expired("500") is True
    assert is_expired("") is False
    assert is_expired(None) is False


def test_parse_expires_in():
    assert parse_expires_in("never") is None
    assert parse_expires_in(None) is None

    assert parse_expires_in("2h") is not None
    assert parse_expires_in("7d") is not None
