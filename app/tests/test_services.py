"""
Tests for Service Layer (services.py)
Tests business logic with mocked database layer.
"""
import unittest
from unittest.mock import Mock, MagicMock, patch
import sys
import os
import fnmatch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import AuthService, LinkService, is_expired, parse_expires_in
import db
import bcrypt


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
        """Pattern matching that handles Redis-style glob patterns."""
        keys = []
        
        # Collect all keys
        all_keys = list(self.data.keys()) + list(self.hashes.keys())
        
        # Filter using fnmatch for proper glob pattern matching
        for key in all_keys:
            if fnmatch.fnmatch(key, pattern):
                keys.append(key)
        
        return keys
    
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
        count = 0
        for member in members:
            if member not in self.sets[key]:
                self.sets[key].add(member)
                count += 1
        return count
    
    def set_remove(self, key: str, *members: str):
        if key not in self.sets:
            return 0
        count = 0
        for member in members:
            if member in self.sets[key]:
                self.sets[key].remove(member)
                count += 1
        return count
    
    def set_members(self, key: str):
        return self.sets.get(key, set())


class TestAuthService(unittest.TestCase):
    """Test cases for authentication service."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_db = MockDatabase()
        self.auth_service = AuthService(database=self.mock_db)
    
    @patch('services.bcrypt')
    def test_create_user_success(self, mock_bcrypt):
        """Test successful user creation."""
        mock_bcrypt.hashpw.return_value = b"hashed_password"
        mock_bcrypt.gensalt.return_value = b"salt"
        
        user = self.auth_service.create_user("test@example.com", "password123")
        
        self.assertIsNotNone(user)
        self.assertEqual(user["email"], "test@example.com")
        self.assertIn("user_id", user)
        self.assertIn("created_at", user)
        
        # Verify email index was created
        email_key = db.email_index_key("test@example.com")
        self.assertIn(email_key, self.mock_db.data)
    
    def test_create_user_duplicate_email(self):
        """Test user creation with duplicate email fails."""
        self.mock_db.set_value(db.email_index_key("test@example.com"), "user123")
        
        user = self.auth_service.create_user("test@example.com", "password123")
        
        self.assertIsNone(user)
    
    @patch('services.bcrypt')
    def test_verify_user_success(self, mock_bcrypt):
        """Test successful user verification."""
        # Set up mock user data
        user_id = "user123"
        email = "test@example.com"
        password = "password123"
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Store user in mock database
        account_key = db.user_account_key(user_id)
        self.mock_db.hash_set_mapping(account_key, {
            "user_id": user_id,
            "email": email,
            "password_hash": password_hash,
            "created_at": "1234567890"
        })
        self.mock_db.set_value(db.email_index_key(email), user_id)
        
        mock_bcrypt.checkpw.return_value = True
        
        user = self.auth_service.verify_user(email, password)
        
        self.assertIsNotNone(user)
        self.assertEqual(user["email"], email)
        self.assertEqual(user["user_id"], user_id)
    
    def test_verify_user_invalid_email(self):
        """Test verification with non-existent email."""
        user = self.auth_service.verify_user("nonexistent@example.com", "password")
        
        self.assertIsNone(user)
    
    def test_email_exists(self):
        """Test checking if email exists."""
        email = "test@example.com"
        self.mock_db.set_value(db.email_index_key(email), "user123")
        
        self.assertTrue(self.auth_service.email_exists(email))
        self.assertFalse(self.auth_service.email_exists("other@example.com"))


class TestLinkService(unittest.TestCase):
    """Test cases for link service."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_db = MockDatabase()
        self.link_service = LinkService(database=self.mock_db)
        self.user_id = "user123"
    
    @patch('services.time')
    def test_create_link_success(self, mock_time):
        """Test successful link creation."""
        mock_time.time.return_value = 1234567890
        
        link = self.link_service.create_link(
            user_id=self.user_id,
            url="https://example.com",
            expires_in="1h"
        )
        
        self.assertIsNotNone(link)
        self.assertEqual(link["url"], "https://example.com")
        self.assertIn("short_code", link)
        self.assertIsNotNone(link["expires_at"])
        self.assertEqual(link["created_at"], 1234567890)
        
        # Verify link was stored
        link_key = db.link_key(self.user_id, link["short_code"])
        self.assertIn(link_key, self.mock_db.hashes)
    
    def test_create_link_custom_code(self):
        """Test link creation with custom code."""
        link = self.link_service.create_link(
            user_id=self.user_id,
            url="https://example.com",
            custom_code="mycode"
        )
        
        self.assertEqual(link["short_code"], "mycode")
    
    def test_create_link_duplicate_code(self):
        """Test link creation fails with duplicate code."""
        # Create first link
        self.link_service.create_link(
            user_id=self.user_id,
            url="https://example.com",
            custom_code="mycode"
        )
        
        # Try to create duplicate
        with self.assertRaises(ValueError):
            self.link_service.create_link(
                user_id=self.user_id,
                url="https://other.com",
                custom_code="mycode"
            )
    
    def test_create_link_invalid_url(self):
        """Test link creation fails with invalid URL."""
        with self.assertRaises(ValueError):
            self.link_service.create_link(
                user_id=self.user_id,
                url="",
                custom_code="mycode"
            )
    
    def test_get_link_success(self):
        """Test getting a link successfully."""
        # Create a link
        created_link = self.link_service.create_link(
            user_id=self.user_id,
            url="https://example.com"
        )
        
        # Retrieve it
        link = self.link_service.get_link(created_link["short_code"])
        
        self.assertIsNotNone(link)
        self.assertEqual(link["url"], "https://example.com")
    
    def test_delete_link_success(self):
        """Test deleting a link successfully."""
        # Create a link
        created_link = self.link_service.create_link(
            user_id=self.user_id,
            url="https://example.com",
            custom_code="testcode"
        )
        
        # Delete it
        result = self.link_service.delete_link(self.user_id, created_link["short_code"])
        
        self.assertTrue(result)
        
        # Verify it's gone
        link = self.link_service.get_link(created_link["short_code"])
        self.assertIsNone(link)


class TestHelperFunctions(unittest.TestCase):
    """Test cases for helper functions."""
    
    @patch('services.time')
    def test_is_expired(self, mock_time):
        """Test expiration checking."""
        mock_time.time.return_value = 1000
        
        # Not expired
        self.assertFalse(is_expired("2000"))
        
        # Expired
        self.assertTrue(is_expired("500"))
        
        # Never expires
        self.assertFalse(is_expired(""))
        self.assertFalse(is_expired(None))
    
    def test_parse_expires_in(self):
        """Test expiration parsing."""
        # Never expires
        self.assertIsNone(parse_expires_in("never"))
        self.assertIsNone(parse_expires_in(None))
        
        # Hours
        result = parse_expires_in("2h")
        self.assertIsNotNone(result)
        
        # Days
        result = parse_expires_in("7d")
        self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()

