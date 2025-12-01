"""
Tests for API/Endpoint Layer (app.py)
Tests HTTP request/response handling with mocked services.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from services import AuthService, LinkService


class TestAPILayer(unittest.TestCase):
    """Test cases for API endpoint layer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.app = app.test_client()
        self.app.testing = True
    
    def test_index_redirects_to_login_when_not_authenticated(self):
        """Test index redirects to login when not authenticated."""
        with self.app:
            response = self.app.get('/')
            
            self.assertEqual(response.status_code, 302)
            self.assertIn('/login', response.location)
    
    @patch('app.auth_service')
    @patch('app.link_service')
    def test_signup_success(self, mock_link_service, mock_auth_service):
        """Test successful user signup."""
        mock_user = {
            "user_id": "user123",
            "email": "test@example.com",
            "created_at": "1234567890"
        }
        mock_auth_service.email_exists.return_value = False
        mock_auth_service.create_user.return_value = mock_user
        
        response = self.app.post(
            '/signup',
            data=json.dumps({
                "email": "test@example.com",
                "password": "password123"
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        mock_auth_service.create_user.assert_called_once()
    
    @patch('app.auth_service')
    def test_signup_duplicate_email(self, mock_auth_service):
        """Test signup fails with duplicate email."""
        mock_auth_service.email_exists.return_value = True
        
        response = self.app.post(
            '/signup',
            data=json.dumps({
                "email": "test@example.com",
                "password": "password123"
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn("error", data)
    
    @patch('app.auth_service')
    def test_signup_validation_errors(self, mock_auth_service):
        """Test signup validation errors."""
        # Missing email
        response = self.app.post(
            '/signup',
            data=json.dumps({
                "password": "password123"
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        
        # Short password
        response = self.app.post(
            '/signup',
            data=json.dumps({
                "email": "test@example.com",
                "password": "12345"
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
    
    @patch('app.auth_service')
    def test_login_success(self, mock_auth_service):
        """Test successful login."""
        mock_user = {
            "user_id": "user123",
            "email": "test@example.com",
            "created_at": "1234567890"
        }
        mock_auth_service.verify_user.return_value = mock_user
        
        response = self.app.post(
            '/login',
            data=json.dumps({
                "email": "test@example.com",
                "password": "password123"
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data["success"])
    
    @patch('app.auth_service')
    def test_login_invalid_credentials(self, mock_auth_service):
        """Test login fails with invalid credentials."""
        mock_auth_service.verify_user.return_value = None
        
        response = self.app.post(
            '/login',
            data=json.dumps({
                "email": "test@example.com",
                "password": "wrongpassword"
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertIn("error", data)
    
    @patch('app.link_service')
    def test_add_link_requires_authentication(self, mock_link_service):
        """Test adding link requires authentication."""
        response = self.app.post(
            '/add',
            data=json.dumps({
                "url": "https://example.com"
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 401)
    
    @patch('app.link_service')
    def test_add_link_success(self, mock_link_service):
        """Test successful link creation."""
        mock_link = {
            "short_code": "abc123",
            "url": "https://example.com",
            "created_at": 1234567890,
            "expires_at": None
        }
        mock_link_service.create_link.return_value = mock_link
        
        # Simulate authenticated session
        with self.app.session_transaction() as sess:
            sess['user_id'] = 'user123'
        
        response = self.app.post(
            '/add',
            data=json.dumps({
                "url": "https://example.com",
                "expires_in": "never"
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertEqual(data["short_code"], "abc123")
        mock_link_service.create_link.assert_called_once()
    
    @patch('app.link_service')
    def test_add_link_invalid_url(self, mock_link_service):
        """Test link creation fails with invalid URL."""
        mock_link_service.create_link.side_effect = ValueError("URL is required")
        
        with self.app.session_transaction() as sess:
            sess['user_id'] = 'user123'
        
        response = self.app.post(
            '/add',
            data=json.dumps({
                "url": "",
                "expires_in": "never"
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn("error", data)
    
    @patch('app.link_service')
    def test_get_links_requires_authentication(self, mock_link_service):
        """Test getting links requires authentication."""
        response = self.app.get('/links', headers={'Accept': 'application/json'})
        
        self.assertEqual(response.status_code, 401)
    
    @patch('app.link_service')
    def test_get_links_success(self, mock_link_service):
        """Test successful link retrieval."""
        mock_links = [
            {
                "short_code": "abc123",
                "url": "https://example.com",
                "created_at": "1234567890",
                "expires_at": "",
                "is_expired": False
            }
        ]
        mock_link_service.get_user_links.return_value = mock_links
        
        with self.app.session_transaction() as sess:
            sess['user_id'] = 'user123'
        
        response = self.app.get('/links')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        mock_link_service.get_user_links.assert_called_once_with('user123')
    
    @patch('app.link_service')
    def test_redirect_short_code_success(self, mock_link_service):
        """Test successful redirect to original URL."""
        mock_link = {
            "url": "https://example.com",
            "created_at": "1234567890",
            "expires_at": "",
            "user_id": "user123"
        }
        mock_link_service.get_link.return_value = mock_link
        
        response = self.app.get('/abc123')
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, "https://example.com")
    
    @patch('app.link_service')
    def test_redirect_expired_link(self, mock_link_service):
        """Test redirect returns 410 for expired link."""
        mock_link_service.get_link.return_value = None
        mock_link_service.get_link_owner.return_value = "user123"
        
        response = self.app.get('/expired123')
        
        self.assertEqual(response.status_code, 410)
        data = json.loads(response.data)
        self.assertIn("error", data)


if __name__ == '__main__':
    unittest.main()

