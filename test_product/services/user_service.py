"""
User service with authentication bugs for testing incident detection.
"""

import random
import time
from typing import Dict, Any, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .base_service import BaseService
from ..logging_system import StructuredLogger
from ..config import TestConfig


class UserService(BaseService):
    """
    User service with intentional authentication bugs for testing.
    
    Contains three specific bugs:
    1. NameError in authenticate_user() - undefined variable reference
    2. KeyError in get_user_profile() - missing dictionary key
    3. AttributeError in update_user_data() - calling method on None
    """
    
    def __init__(self, logger: StructuredLogger, config: Optional[TestConfig] = None):
        super().__init__("UserService", logger, error_probability=0.08, config=config)
        
        # Mock user database
        self.users_db = {
            "user123": {
                "username": "john_doe",
                "email": "john@example.com",
                "profile": {
                    "name": "John Doe",
                    "age": 30,
                    "preferences": {"theme": "dark", "notifications": True}
                }
            },
            "user456": {
                "username": "jane_smith", 
                "email": "jane@example.com",
                "profile": {
                    "name": "Jane Smith",
                    "age": 28,
                    "preferences": {"theme": "light", "notifications": False}
                }
            }
        }
        
        # Mock session storage
        self.active_sessions = {}
    
    def get_service_name(self) -> str:
        """Get the service name."""
        return "UserService"
    
    def get_available_operations(self) -> list:
        """Get list of available operations."""
        return ["authenticate_user", "get_user_profile", "update_user_data"]
    
    def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user with NameError bug.
        
        Bug: References undefined variable 'auth_token' instead of 'token'
        """
        def normal_operation():
            # Simulate authentication logic
            user_id = None
            for uid, user_data in self.users_db.items():
                if user_data["username"] == username:
                    user_id = uid
                    break
            
            if user_id:
                token = f"token_{user_id}_{int(time.time())}"
                self.active_sessions[token] = {
                    "user_id": user_id,
                    "username": username,
                    "created_at": time.time()
                }
                
                return {
                    "success": True,
                    "user_id": user_id,
                    "token": token,
                    "message": "Authentication successful"
                }
            else:
                return {
                    "success": False,
                    "message": "Invalid credentials"
                }
        
        def error_operation():
            # Bug: NameError - undefined variable reference
            user_id = None
            for uid, user_data in self.users_db.items():
                if user_data["username"] == username:
                    user_id = uid
                    break
            
            if user_id:
                token = f"token_{user_id}_{int(time.time())}"
                self.active_sessions[token] = {
                    "user_id": user_id,
                    "username": username,
                    "created_at": time.time()
                }
                
                # BUG: Reference undefined variable 'auth_token' instead of 'token'
                return {
                    "success": True,
                    "user_id": user_id,
                    "token": auth_token,  # NameError: name 'auth_token' is not defined
                    "message": "Authentication successful"
                }
            else:
                return {
                    "success": False,
                    "message": "Invalid credentials"
                }
        
        return self._execute_with_error_handling(
            "authenticate_user",
            normal_operation,
            error_operation,
            username=username
        )
    
    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Get user profile with KeyError bug.
        
        Bug: Tries to access missing 'settings' key in user data
        """
        def normal_operation():
            if user_id not in self.users_db:
                return {
                    "success": False,
                    "message": "User not found"
                }
            
            user_data = self.users_db[user_id]
            return {
                "success": True,
                "profile": user_data["profile"],
                "username": user_data["username"],
                "email": user_data["email"]
            }
        
        def error_operation():
            # Bug: KeyError - accessing missing dictionary key
            if user_id not in self.users_db:
                return {
                    "success": False,
                    "message": "User not found"
                }
            
            user_data = self.users_db[user_id]
            
            # BUG: Try to access 'settings' key that doesn't exist
            return {
                "success": True,
                "profile": user_data["profile"],
                "username": user_data["username"],
                "email": user_data["email"],
                "settings": user_data["settings"]  # KeyError: 'settings'
            }
        
        return self._execute_with_error_handling(
            "get_user_profile",
            normal_operation,
            error_operation,
            user_id=user_id
        )
    
    def update_user_data(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user data with AttributeError bug.
        
        Bug: Calls method on None object
        """
        def normal_operation():
            if user_id not in self.users_db:
                return {
                    "success": False,
                    "message": "User not found"
                }
            
            # Update user data
            user_data = self.users_db[user_id]
            for key, value in updates.items():
                if key in ["username", "email"]:
                    user_data[key] = value
                elif key == "profile":
                    user_data["profile"].update(value)
            
            return {
                "success": True,
                "message": "User data updated successfully",
                "updated_fields": list(updates.keys())
            }
        
        def error_operation():
            # Bug: AttributeError - calling method on None
            if user_id not in self.users_db:
                return {
                    "success": False,
                    "message": "User not found"
                }
            
            # Simulate getting None from some operation
            validation_result = None
            
            # BUG: Try to call method on None object
            if validation_result.is_valid():  # AttributeError: 'NoneType' object has no attribute 'is_valid'
                user_data = self.users_db[user_id]
                for key, value in updates.items():
                    if key in ["username", "email"]:
                        user_data[key] = value
                    elif key == "profile":
                        user_data["profile"].update(value)
                
                return {
                    "success": True,
                    "message": "User data updated successfully",
                    "updated_fields": list(updates.keys())
                }
            else:
                return {
                    "success": False,
                    "message": "Validation failed"
                }
        
        return self._execute_with_error_handling(
            "update_user_data",
            normal_operation,
            error_operation,
            user_id=user_id,
            update_count=len(updates)
        )
    
    def get_active_sessions(self) -> Dict[str, Any]:
        """Get information about active user sessions."""
        return {
            "total_sessions": len(self.active_sessions),
            "sessions": list(self.active_sessions.keys())
        }
    
    def logout_user(self, token: str) -> Dict[str, Any]:
        """Logout user by removing their session."""
        if token in self.active_sessions:
            del self.active_sessions[token]
            return {
                "success": True,
                "message": "User logged out successfully"
            }
        else:
            return {
                "success": False,
                "message": "Invalid or expired token"
            }