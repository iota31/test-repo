"""
Unit tests for the UserService class.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import tempfile
import json

# Add parent directory to path to allow importing test_product modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from test_product.services.user_service import UserService
from test_product.logging_system import StructuredLogger
from test_product.config import TestConfig


class TestUserService(unittest.TestCase):
    """Test cases for the UserService class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary log file
        self.temp_log_fd, self.temp_log_path = tempfile.mkstemp()
        
        # Create a logger
        self.logger = StructuredLogger("UserService", self.temp_log_path)
        
        # Create a service with 100% error probability for testing errors
        self.error_service = UserService(self.logger)
        self.error_service.error_probability = 1.0
        
        # Create a service with 0% error probability for testing normal operation
        self.normal_service = UserService(self.logger)
        self.normal_service.error_probability = 0.0
    
    def tearDown(self):
        """Clean up after tests."""
        os.close(self.temp_log_fd)
        os.unlink(self.temp_log_path)
    
    def test_get_service_name(self):
        """Test the get_service_name method."""
        self.assertEqual(self.normal_service.get_service_name(), "UserService")
    
    def test_get_available_operations(self):
        """Test the get_available_operations method."""
        operations = self.normal_service.get_available_operations()
        self.assertIn("authenticate_user", operations)
        self.assertIn("get_user_profile", operations)
        self.assertIn("update_user_data", operations)
    
    def test_authenticate_user_success(self):
        """Test the authenticate_user method with successful execution."""
        result = self.normal_service.authenticate_user("john_doe", "password")
        
        # Check result
        self.assertTrue(result["success"])
        self.assertIn("token", result)
        self.assertIn("user_id", result)
        
        # Check that a token was created
        token = result["token"]
        self.assertIn(token, self.normal_service.active_sessions)
    
    def test_authenticate_user_error(self):
        """Test the authenticate_user method with error execution."""
        # Should raise NameError due to undefined variable 'auth_token'
        with self.assertRaises(NameError):
            self.error_service.authenticate_user("john_doe", "password")
        
        # Check log file for error
        with open(self.temp_log_path, 'r') as f:
            log_content = f.read()
            log_entry = json.loads(log_content.strip())
            
            # Check log entry fields
            self.assertEqual(log_entry["level"], "ERROR")
            self.assertEqual(log_entry["service"], "UserService")
            self.assertEqual(log_entry["error_type"], "NameError")
            self.assertEqual(log_entry["operation"], "authenticate_user")
            self.assertIn("stack_trace", log_entry)
            self.assertIn("auth_token", log_entry["stack_trace"])
    
    def test_get_user_profile_success(self):
        """Test the get_user_profile method with successful execution."""
        result = self.normal_service.get_user_profile("user123")
        
        # Check result
        self.assertTrue(result["success"])
        self.assertIn("profile", result)
        self.assertEqual(result["username"], "john_doe")
        self.assertEqual(result["email"], "john@example.com")
    
    def test_get_user_profile_error(self):
        """Test the get_user_profile method with error execution."""
        # Should raise KeyError due to missing 'settings' key
        with self.assertRaises(KeyError):
            self.error_service.get_user_profile("user123")
        
        # Check log file for error
        with open(self.temp_log_path, 'r') as f:
            log_content = f.read()
            log_entry = json.loads(log_content.strip())
            
            # Check log entry fields
            self.assertEqual(log_entry["level"], "ERROR")
            self.assertEqual(log_entry["service"], "UserService")
            self.assertEqual(log_entry["error_type"], "KeyError")
            self.assertEqual(log_entry["operation"], "get_user_profile")
            self.assertIn("stack_trace", log_entry)
            self.assertIn("settings", log_entry["stack_trace"])
    
    def test_update_user_data_success(self):
        """Test the update_user_data method with successful execution."""
        updates = {"username": "new_username", "profile": {"age": 31}}
        result = self.normal_service.update_user_data("user123", updates)
        
        # Check result
        self.assertTrue(result["success"])
        self.assertIn("updated_fields", result)
        
        # Check that user data was updated
        self.assertEqual(self.normal_service.users_db["user123"]["username"], "new_username")
        self.assertEqual(self.normal_service.users_db["user123"]["profile"]["age"], 31)
    
    def test_update_user_data_error(self):
        """Test the update_user_data method with error execution."""
        # Should raise AttributeError due to calling method on None
        with self.assertRaises(AttributeError):
            self.error_service.update_user_data("user123", {"username": "new_username"})
        
        # Check log file for error
        with open(self.temp_log_path, 'r') as f:
            log_content = f.read()
            log_entry = json.loads(log_content.strip())
            
            # Check log entry fields
            self.assertEqual(log_entry["level"], "ERROR")
            self.assertEqual(log_entry["service"], "UserService")
            self.assertEqual(log_entry["error_type"], "AttributeError")
            self.assertEqual(log_entry["operation"], "update_user_data")
            self.assertIn("stack_trace", log_entry)
            self.assertIn("'NoneType' object has no attribute 'is_valid'", log_entry["stack_trace"])
    
    def test_get_active_sessions(self):
        """Test the get_active_sessions method."""
        # Create a session
        self.normal_service.authenticate_user("john_doe", "password")
        
        # Get active sessions
        sessions = self.normal_service.get_active_sessions()
        
        # Check result
        self.assertEqual(sessions["total_sessions"], 1)
        self.assertEqual(len(sessions["sessions"]), 1)
    
    def test_logout_user(self):
        """Test the logout_user method."""
        # Create a session
        result = self.normal_service.authenticate_user("john_doe", "password")
        token = result["token"]
        
        # Logout user
        logout_result = self.normal_service.logout_user(token)
        
        # Check result
        self.assertTrue(logout_result["success"])
        
        # Check that session was removed
        self.assertNotIn(token, self.normal_service.active_sessions)
    
    def test_logout_user_invalid_token(self):
        """Test the logout_user method with invalid token."""
        # Logout with invalid token
        result = self.normal_service.logout_user("invalid_token")
        
        # Check result
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "Invalid or expired token")


if __name__ == "__main__":
    unittest.main()