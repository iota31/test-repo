"""
Unit tests for the AuthService class.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import tempfile
import json
import time

# Add parent directory to path to allow importing test_product modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from test_product.services.auth_service import AuthService
from test_product.logging_system import StructuredLogger
from test_product.config import TestConfig


class TestAuthService(unittest.TestCase):
    """Test cases for the AuthService class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary log file
        self.temp_log_fd, self.temp_log_path = tempfile.mkstemp()
        
        # Create a logger
        self.logger = StructuredLogger("AuthService", self.temp_log_path)
        
        # Create a service with 100% error probability for testing errors
        self.error_service = AuthService(self.logger)
        self.error_service.error_probability = 1.0
        
        # Create a service with 0% error probability for testing normal operation
        self.normal_service = AuthService(self.logger)
        self.normal_service.error_probability = 0.0
    
    def tearDown(self):
        """Clean up after tests."""
        os.close(self.temp_log_fd)
        os.unlink(self.temp_log_path)
    
    def test_get_service_name(self):
        """Test the get_service_name method."""
        self.assertEqual(self.normal_service.get_service_name(), "AuthService")
    
    def test_get_available_operations(self):
        """Test the get_available_operations method."""
        operations = self.normal_service.get_available_operations()
        self.assertIn("generate_token", operations)
        self.assertIn("validate_permissions", operations)
        self.assertIn("refresh_session", operations)
    
    def test_generate_token_success(self):
        """Test the generate_token method with successful execution."""
        result = self.normal_service.generate_token("user123", "admin", 60)
        
        # Check result
        self.assertTrue(result["success"])
        self.assertIn("token", result)
        self.assertIn("expires_at", result)
        self.assertIn("permissions", result)
        
        # Check that token was stored
        token = result["token"]
        self.assertIn(token, self.normal_service.tokens)
        
        # Check token data
        token_data = self.normal_service.tokens[token]
        self.assertEqual(token_data["user_id"], "user123")
        self.assertEqual(token_data["role"], "admin")
        self.assertIn("created_at", token_data)
        self.assertIn("expires_at", token_data)
    
    def test_generate_token_error(self):
        """Test the generate_token method with error execution."""
        # Should raise ImportError due to missing module
        with self.assertRaises(ImportError):
            self.error_service.generate_token("user123", "admin", 60)
        
        # Check log file for error
        with open(self.temp_log_path, 'r') as f:
            log_content = f.read()
            log_entry = json.loads(log_content.strip())
            
            # Check log entry fields
            self.assertEqual(log_entry["level"], "ERROR")
            self.assertEqual(log_entry["service"], "AuthService")
            self.assertEqual(log_entry["error_type"], "ImportError")
            self.assertEqual(log_entry["operation"], "generate_token")
            self.assertIn("stack_trace", log_entry)
            self.assertIn("No module named", log_entry["stack_trace"])
            self.assertIn("secure_token_generator", log_entry["stack_trace"])
    
    def test_validate_permissions_success(self):
        """Test the validate_permissions method with successful execution."""
        # First, generate a token
        token_result = self.normal_service.generate_token("user123", "admin", 60)
        token = token_result["token"]
        
        # Validate permissions
        result = self.normal_service.validate_permissions(token, "read")
        
        # Check result
        self.assertTrue(result["success"])
        self.assertTrue(result["has_permission"])
        self.assertEqual(result["user_id"], "user123")
        self.assertEqual(result["role"], "admin")
        self.assertIn("permissions", result)
    
    def test_validate_permissions_no_permission(self):
        """Test the validate_permissions method with permission not granted."""
        # Generate a token with guest role (only has read permission)
        token_result = self.normal_service.generate_token("guest123", "guest", 60)
        token = token_result["token"]
        
        # Validate permissions for write (which guest doesn't have)
        result = self.normal_service.validate_permissions(token, "write")
        
        # Check result
        self.assertTrue(result["success"])
        self.assertFalse(result["has_permission"])
        self.assertEqual(result["role"], "guest")
    
    def test_validate_permissions_invalid_token(self):
        """Test the validate_permissions method with invalid token."""
        result = self.normal_service.validate_permissions("invalid_token", "read")
        
        # Check result
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "Invalid or expired token")
    
    def test_validate_permissions_expired_token(self):
        """Test the validate_permissions method with expired token."""
        # Generate a token that expires immediately
        token_result = self.normal_service.generate_token("user123", "admin", 0)
        token = token_result["token"]
        
        # Wait a moment to ensure token expires
        time.sleep(0.1)
        
        # Validate permissions
        result = self.normal_service.validate_permissions(token, "read")
        
        # Check result
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "Token expired")
        
        # Check that token was removed
        self.assertNotIn(token, self.normal_service.tokens)
    
    def test_validate_permissions_error(self):
        """Test the validate_permissions method with error execution."""
        # First, generate a token
        # Reset error probability temporarily to generate a token successfully
        original_probability = self.error_service.error_probability
        self.error_service.error_probability = 0.0
        token_result = self.error_service.generate_token("user123", "admin", 60)
        token = token_result["token"]
        self.error_service.error_probability = original_probability
        
        # Should raise RecursionError due to infinite recursion
        with self.assertRaises(RecursionError):
            self.error_service.validate_permissions(token, "read")
        
        # Check log file for error
        with open(self.temp_log_path, 'r') as f:
            log_content = f.read()
            log_entry = json.loads(log_content.strip())
            
            # Check log entry fields
            self.assertEqual(log_entry["level"], "CRITICAL")  # RecursionError is logged as CRITICAL
            self.assertEqual(log_entry["service"], "AuthService")
            self.assertEqual(log_entry["error_type"], "RecursionError")
            self.assertEqual(log_entry["operation"], "validate_permissions")
            self.assertIn("stack_trace", log_entry)
            self.assertIn("maximum recursion depth exceeded", log_entry["stack_trace"])
    
    def test_refresh_session_success(self):
        """Test the refresh_session method with successful execution."""
        # First, generate a token
        token_result = self.normal_service.generate_token("user123", "admin", 60)
        old_token = token_result["token"]
        
        # Refresh session
        result = self.normal_service.refresh_session(old_token)
        
        # Check result
        self.assertTrue(result["success"])
        self.assertIn("token", result)
        self.assertIn("expires_at", result)
        self.assertEqual(result["message"], "Session refreshed successfully")
        
        # Check that old token was removed
        self.assertNotIn(old_token, self.normal_service.tokens)
        
        # Check that new token was created
        new_token = result["token"]
        self.assertIn(new_token, self.normal_service.tokens)
        
        # Check new token data
        token_data = self.normal_service.tokens[new_token]
        self.assertEqual(token_data["user_id"], "user123")
        self.assertEqual(token_data["role"], "admin")
    
    def test_refresh_session_invalid_token(self):
        """Test the refresh_session method with invalid token."""
        result = self.normal_service.refresh_session("invalid_token")
        
        # Check result
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "Invalid or expired token")
    
    def test_refresh_session_expired_token(self):
        """Test the refresh_session method with expired token."""
        # Generate a token that expires immediately
        token_result = self.normal_service.generate_token("user123", "admin", 0)
        token = token_result["token"]
        
        # Wait a moment to ensure token expires
        time.sleep(0.1)
        
        # Refresh session
        result = self.normal_service.refresh_session(token)
        
        # Check result
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "Token expired, cannot refresh")
        
        # Check that token was removed
        self.assertNotIn(token, self.normal_service.tokens)
    
    def test_refresh_session_error(self):
        """Test the refresh_session method with error execution."""
        # First, generate a token
        # Reset error probability temporarily to generate a token successfully
        original_probability = self.error_service.error_probability
        self.error_service.error_probability = 0.0
        token_result = self.error_service.generate_token("user123", "admin", 60)
        token = token_result["token"]
        self.error_service.error_probability = original_probability
        
        # Should raise ConnectionError due to simulated network failure
        with self.assertRaises(ConnectionError):
            self.error_service.refresh_session(token)
        
        # Check log file for error
        with open(self.temp_log_path, 'r') as f:
            log_content = f.read()
            log_entry = json.loads(log_content.strip())
            
            # Check log entry fields
            self.assertEqual(log_entry["level"], "CRITICAL")  # ConnectionError is logged as CRITICAL
            self.assertEqual(log_entry["service"], "AuthService")
            self.assertEqual(log_entry["error_type"], "ConnectionError")
            self.assertEqual(log_entry["operation"], "refresh_session")
            self.assertIn("stack_trace", log_entry)
            self.assertIn("Failed to connect to authentication server", log_entry["stack_trace"])
    
    def test_revoke_token(self):
        """Test the revoke_token method."""
        # First, generate a token
        token_result = self.normal_service.generate_token("user123", "admin", 60)
        token = token_result["token"]
        
        # Revoke token
        result = self.normal_service.revoke_token(token)
        
        # Check result
        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "Token revoked successfully")
        
        # Check that token was removed
        self.assertNotIn(token, self.normal_service.tokens)
    
    def test_revoke_token_invalid(self):
        """Test the revoke_token method with invalid token."""
        result = self.normal_service.revoke_token("invalid_token")
        
        # Check result
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "Invalid or expired token")
    
    def test_get_active_tokens(self):
        """Test the get_active_tokens method."""
        # First, generate some tokens
        self.normal_service.generate_token("user1", "admin", 60)
        self.normal_service.generate_token("user2", "user", 60)
        
        # Get active tokens
        result = self.normal_service.get_active_tokens()
        
        # Check result
        self.assertEqual(result["total_tokens"], 2)
        self.assertEqual(len(result["tokens"]), 2)


if __name__ == "__main__":
    unittest.main()