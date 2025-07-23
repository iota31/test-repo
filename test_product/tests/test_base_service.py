"""
Unit tests for the BaseService class.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import tempfile
import json

# Add parent directory to path to allow importing test_product modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from test_product.services.base_service import BaseService
from test_product.logging_system import StructuredLogger
from test_product.config import TestConfig


class TestBaseService(unittest.TestCase):
    """Test cases for the BaseService class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary log file
        self.temp_log_fd, self.temp_log_path = tempfile.mkstemp()
        
        # Create a logger
        self.logger = StructuredLogger("TestService", self.temp_log_path)
        
        # Create a concrete implementation of BaseService for testing
        class ConcreteService(BaseService):
            def get_service_name(self):
                return "TestService"
            
            def get_available_operations(self):
                return ["test_operation"]
            
            def test_operation(self, succeed=True):
                def normal_operation():
                    return "Success"
                
                def error_operation():
                    raise ValueError("Test error")
                
                return self._execute_with_error_handling(
                    "test_operation",
                    normal_operation,
                    error_operation if not succeed else None
                )
        
        # Create an instance with 100% error probability for testing
        self.service = ConcreteService("TestService", self.logger, error_probability=1.0)
        
        # Create an instance with 0% error probability for testing
        self.no_error_service = ConcreteService("TestService", self.logger, error_probability=0.0)
    
    def tearDown(self):
        """Clean up after tests."""
        os.close(self.temp_log_fd)
        os.unlink(self.temp_log_path)
    
    def test_should_trigger_error(self):
        """Test the _should_trigger_error method."""
        # Service with 100% error probability should always return True
        self.assertTrue(self.service._should_trigger_error())
        
        # Service with 0% error probability should always return False
        self.assertFalse(self.no_error_service._should_trigger_error())
    
    def test_get_operation_context(self):
        """Test the _get_operation_context method."""
        context = self.service._get_operation_context("test_operation", param1="value1")
        
        # Check required fields
        self.assertEqual(context["operation"], "test_operation")
        self.assertEqual(context["service"], "TestService")
        self.assertEqual(context["operation_count"], 0)
        self.assertIn("timestamp", context)
        
        # Check additional context
        self.assertEqual(context["param1"], "value1")
    
    def test_log_error(self):
        """Test the _log_error method."""
        error = ValueError("Test error")
        self.service._log_error(error, "test_operation", param1="value1")
        
        # Check that error count was incremented
        self.assertEqual(self.service.error_count, 1)
        
        # Check log file content
        with open(self.temp_log_path, 'r') as f:
            log_content = f.read()
            log_entry = json.loads(log_content.strip())
            
            # Check log entry fields
            self.assertEqual(log_entry["level"], "ERROR")
            self.assertEqual(log_entry["service"], "TestService")
            self.assertEqual(log_entry["error_type"], "ValueError")
            self.assertEqual(log_entry["operation"], "test_operation")
            self.assertEqual(log_entry["param1"], "value1")
            self.assertIn("stack_trace", log_entry)
    
    def test_log_success(self):
        """Test the _log_success method."""
        self.service._log_success("test_operation", param1="value1")
        
        # Check that success count was incremented
        self.assertEqual(self.service.success_count, 1)
        
        # Check log file content
        with open(self.temp_log_path, 'r') as f:
            log_content = f.read()
            log_entry = json.loads(log_content.strip())
            
            # Check log entry fields
            self.assertEqual(log_entry["level"], "INFO")
            self.assertEqual(log_entry["service"], "TestService")
            self.assertEqual(log_entry["operation"], "test_operation")
            self.assertEqual(log_entry["param1"], "value1")
    
    def test_log_warning(self):
        """Test the _log_warning method."""
        self.service._log_warning("Test warning", "test_operation", param1="value1")
        
        # Check log file content
        with open(self.temp_log_path, 'r') as f:
            log_content = f.read()
            log_entry = json.loads(log_content.strip())
            
            # Check log entry fields
            self.assertEqual(log_entry["level"], "WARNING")
            self.assertEqual(log_entry["service"], "TestService")
            self.assertEqual(log_entry["message"], "Test warning")
            self.assertEqual(log_entry["operation"], "test_operation")
            self.assertEqual(log_entry["param1"], "value1")
    
    def test_execute_with_error_handling_success(self):
        """Test the _execute_with_error_handling method with successful execution."""
        result = self.no_error_service.test_operation()
        
        # Check result
        self.assertEqual(result, "Success")
        
        # Check operation counts
        self.assertEqual(self.no_error_service.operation_count, 1)
        self.assertEqual(self.no_error_service.success_count, 1)
        self.assertEqual(self.no_error_service.error_count, 0)
    
    def test_execute_with_error_handling_error(self):
        """Test the _execute_with_error_handling method with error execution."""
        # Service with error_probability=1.0 should always trigger the error function
        with self.assertRaises(ValueError):
            self.service.test_operation(succeed=False)
        
        # Check operation counts
        self.assertEqual(self.service.operation_count, 1)
        self.assertEqual(self.service.success_count, 0)
        self.assertEqual(self.service.error_count, 1)
    
    def test_get_service_stats(self):
        """Test the get_service_stats method."""
        # Perform some operations
        self.no_error_service.test_operation()
        try:
            self.service.test_operation(succeed=False)
        except ValueError:
            pass
        
        # Check stats for service with success
        stats = self.no_error_service.get_service_stats()
        self.assertEqual(stats["service_name"], "TestService")
        self.assertEqual(stats["total_operations"], 1)
        self.assertEqual(stats["successful_operations"], 1)
        self.assertEqual(stats["failed_operations"], 0)
        self.assertEqual(stats["error_rate"], 0.0)
        self.assertEqual(stats["success_rate"], 1.0)
        
        # Check stats for service with error
        stats = self.service.get_service_stats()
        self.assertEqual(stats["service_name"], "TestService")
        self.assertEqual(stats["total_operations"], 1)
        self.assertEqual(stats["successful_operations"], 0)
        self.assertEqual(stats["failed_operations"], 1)
        self.assertEqual(stats["error_rate"], 1.0)
        self.assertEqual(stats["success_rate"], 0.0)
    
    def test_reset_stats(self):
        """Test the reset_stats method."""
        # Perform some operations
        self.no_error_service.test_operation()
        try:
            self.service.test_operation(succeed=False)
        except ValueError:
            pass
        
        # Reset stats
        self.no_error_service.reset_stats()
        self.service.reset_stats()
        
        # Check that stats were reset
        self.assertEqual(self.no_error_service.operation_count, 0)
        self.assertEqual(self.no_error_service.success_count, 0)
        self.assertEqual(self.no_error_service.error_count, 0)
        
        self.assertEqual(self.service.operation_count, 0)
        self.assertEqual(self.service.success_count, 0)
        self.assertEqual(self.service.error_count, 0)
    
    def test_update_error_probability(self):
        """Test the update_error_probability method."""
        # Update error probability
        self.service.update_error_probability(0.5)
        
        # Check that error probability was updated
        self.assertEqual(self.service.error_probability, 0.5)
        
        # Check that a warning was logged
        with open(self.temp_log_path, 'r') as f:
            log_content = f.readlines()[-1]  # Get the last line
            log_entry = json.loads(log_content.strip())
            
            # Check log entry fields
            self.assertEqual(log_entry["level"], "WARNING")
            self.assertEqual(log_entry["operation"], "config_update")
            self.assertEqual(log_entry["old_probability"], 1.0)
            self.assertEqual(log_entry["new_probability"], 0.5)
    
    def test_update_error_probability_invalid(self):
        """Test the update_error_probability method with invalid values."""
        # Try to update with invalid values
        with self.assertRaises(ValueError):
            self.service.update_error_probability(-0.1)
        
        with self.assertRaises(ValueError):
            self.service.update_error_probability(1.1)
    
    def test_health_check(self):
        """Test the health_check method."""
        # Perform some operations to affect health
        for _ in range(10):
            self.no_error_service.test_operation()
        
        for _ in range(10):
            try:
                self.service.test_operation(succeed=False)
            except ValueError:
                pass
        
        # Check health for healthy service
        health = self.no_error_service.health_check()
        self.assertEqual(health["service"], "TestService")
        self.assertEqual(health["status"], "healthy")
        self.assertEqual(health["error_rate"], 0.0)
        self.assertEqual(health["total_operations"], 10)
        
        # Check health for unhealthy service
        health = self.service.health_check()
        self.assertEqual(health["service"], "TestService")
        self.assertEqual(health["status"], "unhealthy")
        self.assertEqual(health["error_rate"], 1.0)
        self.assertEqual(health["total_operations"], 10)


if __name__ == "__main__":
    unittest.main()