"""
Auth service with system-level bugs for testing incident detection.
"""

import random
import time
from typing import Dict, Any, Optional, List
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .base_service import BaseService
from ..logging_system import StructuredLogger
from ..config import TestConfig


class AuthService(BaseService):
    """
    Auth service with intentional system-level bugs for testing.
    
    Contains three specific bugs:
    1. ImportError in generate_token() - missing module
    2. RecursionError in validate_permissions() - infinite recursion
    3. ConnectionError in refresh_session() - simulated network failure
    """
    
    def __init__(self, logger: StructuredLogger, config: Optional[TestConfig] = None):
        super().__init__("AuthService", logger, error_probability=0.05, config=config)
        
        # Mock auth data
        self.permissions = {
            "admin": ["read", "write", "delete", "manage_users"],
            "manager": ["read", "write", "manage_users"],
            "user": ["read", "write"],
            "guest": ["read"]
        }
        
        # Mock active sessions
        self.active_sessions = {}
        
        # Mock token storage
        self.tokens = {}
    
    def get_service_name(self) -> str:
        """Get the service name."""
        return "AuthService"
    
    def get_available_operations(self) -> list:
        """Get list of available operations."""
        return ["generate_token", "validate_permissions", "refresh_session"]
    
    def generate_token(self, user_id: str, role: str, expiry_minutes: int = 60) -> Dict[str, Any]:
        """
        Generate authentication token with ImportError bug.
        
        Bug: Tries to import a non-existent module
        """
        def normal_operation():
            # Generate a simple token
            token = f"{user_id}_{role}_{int(time.time())}_{random.randint(1000, 9999)}"
            
            # Store token information
            expiry_time = time.time() + (expiry_minutes * 60)
            self.tokens[token] = {
                "user_id": user_id,
                "role": role,
                "created_at": time.time(),
                "expires_at": expiry_time
            }
            
            return {
                "success": True,
                "token": token,
                "expires_at": expiry_time,
                "permissions": self.permissions.get(role, [])
            }
        
        def error_operation():
            # BUG: ImportError - missing module
            # This simulates a bug where the code tries to import a non-existent module
            # for token generation
            
            # Try to import a non-existent module
            import secure_token_generator  # ImportError: No module named 'secure_token_generator'
            
            # Generate token using the non-existent module
            token = secure_token_generator.create_token(user_id, role)
            
            # Store token information
            expiry_time = time.time() + (expiry_minutes * 60)
            self.tokens[token] = {
                "user_id": user_id,
                "role": role,
                "created_at": time.time(),
                "expires_at": expiry_time
            }
            
            return {
                "success": True,
                "token": token,
                "expires_at": expiry_time,
                "permissions": self.permissions.get(role, [])
            }
        
        return self._execute_with_error_handling(
            "generate_token",
            normal_operation,
            error_operation,
            user_id=user_id,
            role=role
        )
    
    def validate_permissions(self, token: str, required_permission: str) -> Dict[str, Any]:
        """
        Validate user permissions with RecursionError bug.
        
        Bug: Causes infinite recursion through mutual recursive calls
        """
        def normal_operation():
            # Check if token exists
            if token not in self.tokens:
                return {
                    "success": False,
                    "message": "Invalid or expired token"
                }
            
            # Get token data
            token_data = self.tokens[token]
            
            # Check if token is expired
            if token_data["expires_at"] < time.time():
                # Remove expired token
                del self.tokens[token]
                return {
                    "success": False,
                    "message": "Token expired"
                }
            
            # Get role and check permissions
            role = token_data["role"]
            user_permissions = self.permissions.get(role, [])
            
            has_permission = required_permission in user_permissions
            
            return {
                "success": True,
                "has_permission": has_permission,
                "user_id": token_data["user_id"],
                "role": role,
                "permissions": user_permissions
            }
        
        def error_operation():
            # Helper functions that will cause infinite recursion
            def check_permission_recursive(permission, depth=0):
                # This will call itself recursively until stack overflow
                if depth > 1000:  # This condition is never reached due to the bug
                    return True
                
                # BUG: RecursionError - infinite recursion
                # The two functions call each other in an infinite loop
                return validate_permission_recursive(permission, depth + 1)
            
            def validate_permission_recursive(permission, depth=0):
                # This will call the other function, creating infinite recursion
                return check_permission_recursive(permission, depth + 1)
            
            # Check if token exists
            if token not in self.tokens:
                return {
                    "success": False,
                    "message": "Invalid or expired token"
                }
            
            # Get token data
            token_data = self.tokens[token]
            
            # Check if token is expired
            if token_data["expires_at"] < time.time():
                # Remove expired token
                del self.tokens[token]
                return {
                    "success": False,
                    "message": "Token expired"
                }
            
            # Get role and check permissions
            role = token_data["role"]
            user_permissions = self.permissions.get(role, [])
            
            # Use the recursive function that will cause RecursionError
            has_permission = check_permission_recursive(required_permission)
            
            return {
                "success": True,
                "has_permission": has_permission,
                "user_id": token_data["user_id"],
                "role": role,
                "permissions": user_permissions
            }
        
        return self._execute_with_error_handling(
            "validate_permissions",
            normal_operation,
            error_operation,
            token=token,
            permission=required_permission
        )
    
    def refresh_session(self, token: str) -> Dict[str, Any]:
        """
        Refresh user session with ConnectionError bug.
        
        Bug: Simulates network failure with ConnectionError
        """
        def normal_operation():
            # Check if token exists
            if token not in self.tokens:
                return {
                    "success": False,
                    "message": "Invalid or expired token"
                }
            
            # Get token data
            token_data = self.tokens[token]
            
            # Check if token is expired
            if token_data["expires_at"] < time.time():
                # Remove expired token
                del self.tokens[token]
                return {
                    "success": False,
                    "message": "Token expired, cannot refresh"
                }
            
            # Create new token
            new_token = f"{token_data['user_id']}_{token_data['role']}_{int(time.time())}_{random.randint(1000, 9999)}"
            
            # Copy data to new token with extended expiry
            self.tokens[new_token] = {
                "user_id": token_data["user_id"],
                "role": token_data["role"],
                "created_at": time.time(),
                "expires_at": time.time() + (60 * 60)  # 1 hour
            }
            
            # Remove old token
            del self.tokens[token]
            
            return {
                "success": True,
                "token": new_token,
                "expires_at": self.tokens[new_token]["expires_at"],
                "message": "Session refreshed successfully"
            }
        
        def error_operation():
            # Check if token exists
            if token not in self.tokens:
                return {
                    "success": False,
                    "message": "Invalid or expired token"
                }
            
            # Get token data
            token_data = self.tokens[token]
            
            # BUG: ConnectionError - simulated network failure
            # This simulates a bug where the session refresh requires a network call
            # to an authentication server that fails
            
            # Simulate trying to connect to an authentication server
            auth_server = "auth.example.com"
            
            # Raise ConnectionError to simulate network failure
            raise ConnectionError(f"Failed to connect to authentication server at {auth_server}")
        
        return self._execute_with_error_handling(
            "refresh_session",
            normal_operation,
            error_operation,
            token=token
        )
    
    def revoke_token(self, token: str) -> Dict[str, Any]:
        """Revoke an authentication token."""
        if token in self.tokens:
            del self.tokens[token]
            return {
                "success": True,
                "message": "Token revoked successfully"
            }
        else:
            return {
                "success": False,
                "message": "Invalid or expired token"
            }
    
    def get_active_tokens(self) -> Dict[str, Any]:
        """Get information about active tokens."""
        return {
            "total_tokens": len(self.tokens),
            "tokens": list(self.tokens.keys())
        }