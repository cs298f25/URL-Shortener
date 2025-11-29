"""
Tests for Data Access Layer (db.py)
Tests direct Redis operations without business logic.
"""
import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db


class TestDBLayer(unittest.TestCase):
    """Test cases for database access layer."""
    
    @patch('db.redis_client')
    def test_get(self, mock_redis):
        """Test getting a value from Redis."""
        mock_redis.get.return_value = "test_value"
        
        result = db.get("test_key")
        
        self.assertEqual(result, "test_value")
        mock_redis.get.assert_called_once_with("test_key")
    
    @patch('db.redis_client')
    def test_set_value(self, mock_redis):
        """Test setting a value in Redis."""
        db.set_value("test_key", "test_value")
        
        mock_redis.set.assert_called_once_with("test_key", "test_value")
    
    @patch('db.redis_client')
    def test_delete(self, mock_redis):
        """Test deleting a key from Redis."""
        mock_redis.delete.return_value = 1
        
        result = db.delete("test_key")
        
        self.assertEqual(result, 1)
        mock_redis.delete.assert_called_once_with("test_key")
    
    @patch('db.redis_client')
    def test_exists(self, mock_redis):
        """Test checking if a key exists."""
        mock_redis.exists.return_value = 1
        
        result = db.exists("test_key")
        
        self.assertTrue(result)
        mock_redis.exists.assert_called_once_with("test_key")
    
    @patch('db.redis_client')
    def test_hash_get_all(self, mock_redis):
        """Test getting all fields from a hash."""
        mock_data = {"field1": "value1", "field2": "value2"}
        mock_redis.hgetall.return_value = mock_data
        
        result = db.hash_get_all("test_key")
        
        self.assertEqual(result, mock_data)
        mock_redis.hgetall.assert_called_once_with("test_key")
    
    @patch('db.redis_client')
    def test_hash_set_mapping(self, mock_redis):
        """Test setting multiple hash fields."""
        mapping = {"field1": "value1", "field2": "value2"}
        
        db.hash_set_mapping("test_key", mapping)
        
        mock_redis.hset.assert_called_once_with("test_key", mapping=mapping)
    
    @patch('db.redis_client')
    def test_set_add(self, mock_redis):
        """Test adding members to a set."""
        mock_redis.sadd.return_value = 2
        
        result = db.set_add("test_key", "member1", "member2")
        
        self.assertEqual(result, 2)
        mock_redis.sadd.assert_called_once_with("test_key", "member1", "member2")
    
    @patch('db.redis_client')
    def test_set_members(self, mock_redis):
        """Test getting all members of a set."""
        mock_redis.smembers.return_value = {"member1", "member2"}
        
        result = db.set_members("test_key")
        
        self.assertEqual(result, {"member1", "member2"})
        mock_redis.smembers.assert_called_once_with("test_key")
    
    def test_link_key(self):
        """Test link key generation."""
        result = db.link_key("user123", "abc")
        
        self.assertEqual(result, "link:user123:abc")
    
    def test_user_account_key(self):
        """Test user account key generation."""
        result = db.user_account_key("user123")
        
        self.assertEqual(result, "account:user123")
    
    def test_email_index_key(self):
        """Test email index key generation."""
        result = db.email_index_key("test@example.com")
        
        self.assertEqual(result, "email:test@example.com")


if __name__ == '__main__':
    unittest.main()

