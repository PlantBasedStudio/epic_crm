"""
Authentication and authorization system using JWT tokens
"""

import jwt
import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class AuthenticationError(Exception):
    """Custom exception for authentication errors"""
    pass

class AuthorizationError(Exception):
    """Custom exception for authorization errors"""
    pass

class AuthManager:
    """JWT Authentication and Authorization Manager"""
    
    def __init__(self):
        self.secret_key = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-change-this-in-production')
        self.algorithm = 'HS256'
        self.token_expiry = timedelta(hours=24)
        self.token_file = Path.home() / '.epic_events_token'
        
        self.permissions = {
            'Commercial': [
                'create_client',
                'update_own_client',
                'update_own_contract',
                'create_event_for_signed_contract',
                'filter_contracts',
                'view_all_data'
            ],
            'Support': [
                'filter_own_events',
                'update_own_event',
                'view_all_data'
            ],
            'Management': [
                'create_user',
                'update_user',
                'delete_user',
                'create_contract',
                'update_contract',
                'filter_events',
                'update_event',
                'assign_support_to_event',
                'view_all_data'
            ]
        }
    
    def generate_token(self, user) -> str:
        """Generate JWT token for authenticated user"""
        payload = {
            'user_id': user.id,
            'employee_id': user.employee_id,
            'name': user.name,
            'email': user.email,
            'department': user.department.name,
            'exp': datetime.utcnow() + self.token_expiry,
            'iat': datetime.utcnow()
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None
    
    def store_token(self, token: str):
        """Store token to file for persistent authentication"""
        try:
            with open(self.token_file, 'w') as f:
                json.dump({'token': token, 'created_at': datetime.utcnow().isoformat()}, f)
            # 0o600 owner can read et wirte
            os.chmod(self.token_file, 0o600)
        except Exception as e:
            logger.error(f"Error storing token: {e}")
    
    def load_token(self) -> Optional[str]:
        """Load stored token from file"""
        try:
            if self.token_file.exists():
                with open(self.token_file, 'r') as f:
                    data = json.load(f)
                    return data.get('token')
        except Exception as e:
            logger.error(f"Error loading token: {e}")
        return None
    
    def clear_token(self):
        """Clear stored token"""
        try:
            if self.token_file.exists():
                self.token_file.unlink()
        except Exception as e:
            logger.error(f"Error clearing token: {e}")
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current authenticated user from stored token"""
        token = self.load_token()
        if token:
            return self.verify_token(token)
        return None
    
    def has_permission(self, user_data: Dict[str, Any], permission: str) -> bool:
        """Check if user has specific permission"""
        department = user_data.get('department')
        if department in self.permissions:
            return permission in self.permissions[department]
        return False
    
    def require_permission(self, permission: str):
        """Decorator to require specific permission"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                user = self.get_current_user()
                if not user:
                    raise AuthenticationError("Authentication required")
                
                if not self.has_permission(user, permission):
                    raise AuthorizationError(f"Permission '{permission}' required")
                
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def require_authentication(self, func):
        """Decorator to require authentication"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = self.get_current_user()
            if not user:
                raise AuthenticationError("Authentication required")
            return func(*args, **kwargs)
        return wrapper

auth_manager = AuthManager()
