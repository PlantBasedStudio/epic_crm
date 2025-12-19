"""
Unit tests for authentication module
"""

import pytest
import os
import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth import AuthManager, AuthenticationError, AuthorizationError


@pytest.fixture
def auth_manager():
    """Create an AuthManager instance for testing"""
    manager = AuthManager()
    # Use system temp directory for cross-platform compatibility
    temp_dir = tempfile.gettempdir()
    manager.token_file = Path(temp_dir) / '.test_epic_events_token'
    return manager


@pytest.fixture
def mock_user():
    """Create a mock user object"""
    user = MagicMock()
    user.id = 1
    user.employee_id = "EMP001"
    user.name = "Test User"
    user.email = "test@epic.com"
    user.department = MagicMock()
    user.department.name = "Commercial"
    return user


class TestAuthManager:
    """Tests for AuthManager class"""

    def test_generate_token(self, auth_manager, mock_user):
        """Test JWT token generation"""
        token = auth_manager.generate_token(mock_user)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_valid_token(self, auth_manager, mock_user):
        """Test verification of a valid token"""
        token = auth_manager.generate_token(mock_user)
        payload = auth_manager.verify_token(token)

        assert payload is not None
        assert payload['user_id'] == mock_user.id
        assert payload['name'] == mock_user.name
        assert payload['email'] == mock_user.email
        assert payload['department'] == "Commercial"

    def test_verify_invalid_token(self, auth_manager):
        """Test verification of an invalid token"""
        invalid_token = "invalid.token.here"
        payload = auth_manager.verify_token(invalid_token)

        assert payload is None

    def test_verify_expired_token(self, auth_manager, mock_user):
        """Test verification of an expired token"""
        # Create a token with past expiry
        auth_manager.token_expiry = timedelta(seconds=-1)
        token = auth_manager.generate_token(mock_user)
        auth_manager.token_expiry = timedelta(hours=24)

        payload = auth_manager.verify_token(token)
        assert payload is None

    def test_store_and_load_token(self, auth_manager, mock_user):
        """Test token storage and retrieval"""
        token = auth_manager.generate_token(mock_user)
        auth_manager.store_token(token)

        loaded_token = auth_manager.load_token()
        assert loaded_token == token

        # Cleanup
        auth_manager.clear_token()

    def test_clear_token(self, auth_manager, mock_user):
        """Test token clearing"""
        token = auth_manager.generate_token(mock_user)
        auth_manager.store_token(token)
        auth_manager.clear_token()

        loaded_token = auth_manager.load_token()
        assert loaded_token is None

    def test_get_current_user(self, auth_manager, mock_user):
        """Test getting current user from stored token"""
        token = auth_manager.generate_token(mock_user)
        auth_manager.store_token(token)

        user = auth_manager.get_current_user()
        assert user is not None
        assert user['name'] == mock_user.name

        # Cleanup
        auth_manager.clear_token()

    def test_get_current_user_no_token(self, auth_manager):
        """Test getting current user with no token"""
        auth_manager.clear_token()
        user = auth_manager.get_current_user()
        assert user is None


class TestPermissions:
    """Tests for permission checking"""

    def test_commercial_permissions(self, auth_manager):
        """Test Commercial department permissions"""
        user_data = {'department': 'Commercial'}

        assert auth_manager.has_permission(user_data, 'create_client')
        assert auth_manager.has_permission(user_data, 'update_own_client')
        assert auth_manager.has_permission(user_data, 'view_all_data')
        assert not auth_manager.has_permission(user_data, 'create_user')

    def test_support_permissions(self, auth_manager):
        """Test Support department permissions"""
        user_data = {'department': 'Support'}

        assert auth_manager.has_permission(user_data, 'filter_own_events')
        assert auth_manager.has_permission(user_data, 'update_own_event')
        assert auth_manager.has_permission(user_data, 'view_all_data')
        assert not auth_manager.has_permission(user_data, 'create_client')

    def test_management_permissions(self, auth_manager):
        """Test Management department permissions"""
        user_data = {'department': 'Management'}

        assert auth_manager.has_permission(user_data, 'create_user')
        assert auth_manager.has_permission(user_data, 'update_user')
        assert auth_manager.has_permission(user_data, 'delete_user')
        assert auth_manager.has_permission(user_data, 'create_contract')
        assert auth_manager.has_permission(user_data, 'view_all_data')

    def test_unknown_department_permissions(self, auth_manager):
        """Test unknown department has no permissions"""
        user_data = {'department': 'Unknown'}

        assert not auth_manager.has_permission(user_data, 'view_all_data')
        assert not auth_manager.has_permission(user_data, 'create_user')


class TestDecorators:
    """Tests for authentication/authorization decorators"""

    def test_require_authentication_success(self, auth_manager, mock_user):
        """Test require_authentication decorator with valid token"""
        token = auth_manager.generate_token(mock_user)
        auth_manager.store_token(token)

        @auth_manager.require_authentication
        def protected_function():
            return "success"

        result = protected_function()
        assert result == "success"

        # Cleanup
        auth_manager.clear_token()

    def test_require_authentication_failure(self, auth_manager):
        """Test require_authentication decorator without token"""
        auth_manager.clear_token()

        @auth_manager.require_authentication
        def protected_function():
            return "success"

        with pytest.raises(AuthenticationError):
            protected_function()

    def test_require_permission_success(self, auth_manager, mock_user):
        """Test require_permission decorator with valid permission"""
        token = auth_manager.generate_token(mock_user)
        auth_manager.store_token(token)

        @auth_manager.require_permission('view_all_data')
        def protected_function():
            return "success"

        result = protected_function()
        assert result == "success"

        # Cleanup
        auth_manager.clear_token()

    def test_require_permission_failure(self, auth_manager, mock_user):
        """Test require_permission decorator without required permission"""
        token = auth_manager.generate_token(mock_user)
        auth_manager.store_token(token)

        @auth_manager.require_permission('create_user')
        def protected_function():
            return "success"

        with pytest.raises(AuthorizationError):
            protected_function()

        # Cleanup
        auth_manager.clear_token()
