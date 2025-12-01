"""
Service Layer - Business logic for authentication and link management.
Handles validation, business rules, and coordinates data access.

Services use dependency injection for testability - db layer can be mocked.
"""
import random
import string
import time
import uuid
from typing import Dict, List, Optional, Protocol

import bcrypt

import db


class DatabaseInterface(Protocol):
    """Protocol defining the database interface for dependency injection."""
    
    def get(self, key: str) -> Optional[str]: ...
    def set_value(self, key: str, value: str) -> None: ...
    def delete(self, key: str) -> int: ...
    def exists(self, key: str) -> bool: ...
    def list_keys(self, pattern: str = "*") -> List[str]: ...
    def hash_get_all(self, key: str) -> Dict[str, str]: ...
    def hash_set_mapping(self, key: str, mapping: Dict[str, str]) -> int: ...
    def set_add(self, key: str, *members: str) -> int: ...
    def set_remove(self, key: str, *members: str) -> int: ...
    def set_members(self, key: str) -> set: ...


def is_expired(expires_at: Optional[str]) -> bool:
    """Check if a timestamp has expired. Returns False if never expires."""
    if not expires_at or expires_at == "":
        return False
    try:
        expires_timestamp = int(expires_at)
        return time.time() > expires_timestamp
    except (ValueError, TypeError):
        return False


def parse_expires_in(expires_in: Optional[str]) -> Optional[int]:
    """
    Parse expires_in parameter and return Unix timestamp.
    Returns None if 'never' or invalid.
    Options: '1h', '24h', '7d', '30d', 'never'
    """
    if not expires_in or expires_in.lower() == 'never':
        return None
    
    current_time = int(time.time())
    
    try:
        if expires_in.endswith('h'):
            hours = int(expires_in[:-1])
            return current_time + (hours * 60 * 60)
        elif expires_in.endswith('d'):
            days = int(expires_in[:-1])
            return current_time + (days * 24 * 60 * 60)
        else:
            seconds = int(expires_in)
            return current_time + seconds
    except (ValueError, AttributeError):
        return None


class AuthService:
    """Service for user authentication and account management."""
    
    def __init__(self, database: DatabaseInterface = None):
        """
        Initialize AuthService with database dependency.
        If database is None, uses default db module.
        """
        self.db = database if database is not None else db
    
    def create_user(self, email: str, password: str) -> Optional[Dict[str, str]]:
        """
        Create a new user account.
        Returns user dict with user_id, email, created_at if successful.
        Returns None if email already exists.
        """
        email_lower = email.lower().strip()
        
        email_key = db.email_index_key(email_lower)
        if self.db.exists(email_key):
            return None
        
        user_id = str(uuid.uuid4())
        
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        created_at = int(time.time())
        account_key = db.user_account_key(user_id)
        self.db.hash_set_mapping(account_key, {
            "user_id": user_id,
            "email": email_lower,
            "password_hash": password_hash,
            "created_at": str(created_at)
        })
        
        self.db.set_value(email_key, user_id)
        
        return {
            "user_id": user_id,
            "email": email_lower,
            "created_at": str(created_at)
        }
    
    def verify_user(self, email: str, password: str) -> Optional[Dict[str, str]]:
        """
        Verify user credentials and return user data if valid.
        Returns user dict with user_id, email, created_at if valid.
        Returns None if invalid credentials.
        """
        email_lower = email.lower().strip()
        
        email_key = db.email_index_key(email_lower)
        user_id = self.db.get(email_key)
        
        if not user_id:
            return None
        
        account_key = db.user_account_key(user_id)
        user_data = self.db.hash_get_all(account_key)
        
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
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, str]]:
        """Get user account by user_id. Returns None if not found."""
        account_key = db.user_account_key(user_id)
        user_data = self.db.hash_get_all(account_key)
        
        if not user_data:
            return None
        
        user_data.pop("password_hash", None)
        return user_data
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, str]]:
        """Get user account by email. Returns None if not found."""
        email_lower = email.lower().strip()
        email_key = db.email_index_key(email_lower)
        user_id = self.db.get(email_key)
        
        if not user_id:
            return None
        
        return self.get_user_by_id(user_id)
    
    def email_exists(self, email: str) -> bool:
        """Check if an email is already registered."""
        email_lower = email.lower().strip()
        email_key = db.email_index_key(email_lower)
        return self.db.exists(email_key)


class LinkService:
    """Service for link management operations."""
    
    def __init__(self, database: DatabaseInterface = None, auth_service: AuthService = None):
        """
        Initialize LinkService with database and auth service dependencies.
        If database is None, uses default db module.
        If auth_service is None, creates a new AuthService.
        """
        self.db = database if database is not None else db
        self.auth_service = auth_service if auth_service is not None else AuthService(self.db)
    
    def _link_exists(self, short_code: str) -> bool:
        """Check if a short_code exists across all users (and is not expired)."""
        pattern = f"{db.LINK_KEY_PREFIX}*:{short_code}"
        keys = self.db.list_keys(pattern)
        
        if not keys:
            return False
        
        for key in keys:
            link_data = self.db.hash_get_all(key)
            if link_data:
                expires_at = link_data.get("expires_at", "")
                if not is_expired(expires_at):
                    return True
        
        return False
    
    def _generate_short_code(self, length: int = 6) -> str:
        """Generate a unique short code that doesn't exist across all users."""
        chars = string.ascii_letters + string.digits
        max_attempts = 1000
        attempts = 0
        
        while attempts < max_attempts:
            code = "".join(random.choice(chars) for _ in range(length))
            if not self._link_exists(code):
                return code
            attempts += 1
        
        raise Exception("Failed to generate unique short code")
    
    def create_link(self, user_id: str, url: str, custom_code: Optional[str] = None, 
                   expires_in: Optional[str] = None) -> Dict[str, any]:
        """
        Create a new shortened link.
        Returns dict with short_code, url, expires_at, created_at.
        Raises ValueError if custom_code already exists or validation fails.
        """
        if not url or not url.strip():
            raise ValueError("URL is required")
        
        expires_at = parse_expires_in(expires_in)
        expires_at_str = str(expires_at) if expires_at else ""
        
        if custom_code:
            if self._link_exists(custom_code):
                raise ValueError("Short code already exists")
            short_code = custom_code
        else:
            short_code = self._generate_short_code()
        
        created_at = int(time.time())
        link_key = db.link_key(user_id, short_code)
        self.db.hash_set_mapping(link_key, {
            "url": url,
            "created_at": str(created_at),
            "expires_at": expires_at_str,
            "user_id": user_id
        })
        
        user_links_key = db.user_links_key(user_id)
        self.db.set_add(user_links_key, short_code)
        
        return {
            "short_code": short_code,
            "url": url,
            "created_at": created_at,
            "expires_at": expires_at
        }
    
    def get_link(self, short_code: str) -> Optional[Dict[str, str]]:
        """
        Get link data by short_code, checking across all users.
        Returns None if not found or expired.
        Returns dict with url, created_at, expires_at, user_id if found and not expired.
        """
        pattern = f"{db.LINK_KEY_PREFIX}*:{short_code}"
        keys = self.db.list_keys(pattern)
        
        if not keys:
            return None
        
        key = keys[0]
        link_data = self.db.hash_get_all(key)
        
        if not link_data:
            return None
        
        expires_at = link_data.get("expires_at", "")
        if is_expired(expires_at):
            return None
        
        return link_data
    
    def delete_link(self, user_id: str, short_code: str) -> bool:
        """
        Delete a link if owned by user_id.
        Returns True if deleted, False if not found or not owned by user.
        """
        link_key = db.link_key(user_id, short_code)
        
        if not self.db.exists(link_key):
            return False
        
        self.db.delete(link_key)
        
        user_links_key = db.user_links_key(user_id)
        self.db.set_remove(user_links_key, short_code)
        
        return True
    
    def get_user_links(self, user_id: str) -> List[Dict[str, str]]:
        """
        Get all links belonging to a user, including expired ones.
        Returns list of dicts with short_code, url, created_at, expires_at, is_expired.
        """
        user_links_key = db.user_links_key(user_id)
        short_codes = self.db.set_members(user_links_key)
        
        if not short_codes:
            return []
        
        links = []
        for short_code in short_codes:
            link_key = db.link_key(user_id, short_code)
            link_data = self.db.hash_get_all(link_key)
            
            if link_data:
                expires_at = link_data.get("expires_at", "")
                link_data["short_code"] = short_code
                link_data["is_expired"] = is_expired(expires_at)
                links.append(link_data)
        
        return links
    
    def get_link_owner(self, short_code: str) -> Optional[str]:
        """
        Get the user_id who owns a short_code.
        Returns None if not found.
        """
        pattern = f"{db.LINK_KEY_PREFIX}*:{short_code}"
        keys = self.db.list_keys(pattern)
        
        if not keys:
            return None
        
        key = keys[0]
        link_data = self.db.hash_get_all(key)
        
        if link_data:
            return link_data.get("user_id")
        
        return None
