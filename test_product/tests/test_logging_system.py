"""
Unit tests for the logging system.
"""

import os
import sys
import unittest
import tempfile
import json
import time
from datetime import datetime
import re

# Add parent directory to path to allow importing test_product modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from test_product.logging_system import StructuredLogger, LogLevelManager, create_logger


class TestStructuredLogger(unittest.TestCase):
    """Test cases for the StructuredLogger class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary log file
        self.temp_log_fd, self.temp_log_path = tempfile.mkstemp()
        
        # Create a logger
        self.logger = StructuredLogger("TestService", self.temp_log_path)
    
    def tearDown(self):
        """Clean up after tests."""
        os.close(self.temp_log_fd)
        os.unlink(self.temp_log_path)
    
    def test_log_info(self):
        """Test the log_info method."""
        self.logger.log_info("Test info message", {"key": "value"})
        
        # Check log file content
        with open(self.temp_log_path, 'r') as f:
            log_content = f.read()
            log_entry = json.loads(log_content.strip())
            
            # Check log entry fields
            self.assertEqual(log_entry["level"], "INFO")
            self.assertEqual(log_entry["service"], "TestService")
            self.assertEqual(log_entry["message"], "Test info message")
            self.assertEqual(log_entry["key"], "value")
            self.assertIn("timestamp", log_entry)
            self.assertIn("hostname", log_entry)
            self.assertIn("thread", log_entry)
    
    def test_log_warning(self):
        """Test the log_warning method."""
        self.logger.log_warning("Test warning message", {"key": "value"})
        
        # Check log file content
        with open(self.temp_log_path, 'r') as f:
            log_content = f.read()
            log_entry = json.loads(log_content.strip())
            
            # Check log entry fields
            self.assertEqual(log_entry["level"], "WARNING")
            self.assertEqual(log_entry["service"], "TestService")
            self.assertEqual(log_entry["message"], "Test warning message")
            self.assertEqual(log_entry["key"], "value")
    
    def test_log_error(self):
        """Test the log_error method."""
        try:
            # Generate an exception
            raise ValueError("Test error")
        except ValueError as e:
            self.logger.log_error(e, {"key": "value"})
        
        # Check log file content
        with open(self.temp_log_path, 'r') as f:
            log_content = f.read()
            log_entry = json.loads(log_content.strip())
            
            # Check log entry fields
            self.assertEqual(log_entry["level"], "ERROR")
            self.assertEqual(log_entry["service"], "TestService")
            self.assertEqual(log_entry["message"], "ValueError occurred in TestService")
            self.assertEqual(log_entry["key"], "value")
            self.assertEqual(log_entry["error_type"], "ValueError")
            self.assertIn("stack_trace", log_entry)
            self.assertIn("Test error", log_entry["stack_trace"])
            self.assertIn("function_name", log_entry)
            self.assertIn("line_number", log_entry)
    
    def test_log_critical(self):
        """Test the log_critical method."""
        try:
            # Generate an exception
            raise MemoryError("Test critical error")
        except MemoryError as e:
            self.logger.log_critical(e, {"key": "value"})
        
        # Check log file content
        with open(self.temp_log_path, 'r') as f:
            log_content = f.read()
            log_entry = json.loads(log_content.strip())
            
            # Check log entry fields
            self.assertEqual(log_entry["level"], "CRITICAL")
            self.assertEqual(log_entry["service"], "TestService")
            self.assertEqual(log_entry["message"], "CRITICAL MemoryError occurred in TestService")
            self.assertEqual(log_entry["key"], "value")
            self.assertEqual(log_entry["error_type"], "MemoryError")
            self.assertIn("stack_trace", log_entry)
            self.assertIn("Test critical error", log_entry["stack_trace"])
    
    def test_timestamp_format(self):
        """Test that timestamp is in the correct format."""
        self.logger.log_info("Test timestamp")
        
        # Check log file content
        with open(self.temp_log_path, 'r') as f:
            log_content = f.read()
            log_entry = json.loads(log_content.strip())
            
            # Check timestamp format (ISO 8601 with Z suffix)
            timestamp = log_entry["timestamp"]
            # Regex for ISO 8601 format with Z suffix
            iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z$'
            self.assertTrue(re.match(iso_pattern, timestamp), f"Timestamp '{timestamp}' does not match ISO 8601 format")
            
            # Try to parse the timestamp to ensure it's valid
            try:
                # Remove Z and parse
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                self.assertIsInstance(dt, datetime)
            except ValueError:
                self.fail(f"Timestamp '{timestamp}' is not a valid ISO 8601 datetime")
    
    def test_create_logger_factory(self):
        """Test the create_logger factory function."""
        temp_fd, temp_path = tempfile.mkstemp()
        try:
            # Create logger using factory function
            logger = create_logger("FactoryService", temp_path, "WARNING")
            
            # Check that logger was created correctly
            self.assertIsInstance(logger, StructuredLogger)
            self.assertEqual(logger.service_name, "FactoryService")
            self.assertEqual(logger.log_file, temp_path)
            
            # Test logging
            logger.log_warning("Factory test")
            
            # Check log file content
            with open(temp_path, 'r') as f:
                log_content = f.read()
                log_entry = json.loads(log_content.strip())
                
                # Check log entry fields
                self.assertEqual(log_entry["level"], "WARNING")
                self.assertEqual(log_entry["service"], "FactoryService")
                self.assertEqual(log_entry["message"], "Factory test")
        finally:
            os.close(temp_fd)
            os.unlink(temp_path)


class TestLogLevelManager(unittest.TestCase):
    """Test cases for the LogLevelManager class."""
    
    def test_initialization(self):
        """Test initialization with default values."""
        manager = LogLevelManager()
        self.assertEqual(manager.info_ratio, 0.8)
        self.assertEqual(manager.warning_ratio, 0.15)
        self.assertEqual(manager.error_ratio, 0.04)
        self.assertEqual(manager.critical_ratio, 0.01)
    
    def test_initialization_custom(self):
        """Test initialization with custom values."""
        manager = LogLevelManager(0.7, 0.2, 0.05, 0.05)
        self.assertEqual(manager.info_ratio, 0.7)
        self.assertEqual(manager.warning_ratio, 0.2)
        self.assertEqual(manager.error_ratio, 0.05)
        self.assertEqual(manager.critical_ratio, 0.05)
    
    def test_initialization_invalid(self):
        """Test initialization with invalid values."""
        with self.assertRaises(ValueError):
            LogLevelManager(0.7, 0.2, 0.05, 0.1)  # Sum > 1.0
    
    def test_get_random_log_level(self):
        """Test the get_random_log_level method."""
        # Create a manager with extreme probabilities for testing
        manager = LogLevelManager(0.0, 0.0, 0.0, 1.0)  # 100% CRITICAL
        self.assertEqual(manager.get_random_log_level(), "CRITICAL")
        
        manager = LogLevelManager(0.0, 0.0, 1.0, 0.0)  # 100% ERROR
        self.assertEqual(manager.get_random_log_level(), "ERROR")
        
        manager = LogLevelManager(0.0, 1.0, 0.0, 0.0)  # 100% WARNING
        self.assertEqual(manager.get_random_log_level(), "WARNING")
        
        manager = LogLevelManager(1.0, 0.0, 0.0, 0.0)  # 100% INFO
        self.assertEqual(manager.get_random_log_level(), "INFO")
    
    def test_should_log_at_level(self):
        """Test the should_log_at_level method."""
        # Create a manager with extreme probabilities for testing
        manager = LogLevelManager(1.0, 1.0, 1.0, 1.0)  # Always log
        self.assertTrue(manager.should_log_at_level("INFO"))
        self.assertTrue(manager.should_log_at_level("WARNING"))
        self.assertTrue(manager.should_log_at_level("ERROR"))
        self.assertTrue(manager.should_log_at_level("CRITICAL"))
        
        manager = LogLevelManager(0.0, 0.0, 0.0, 0.0)  # Never log
        self.assertFalse(manager.should_log_at_level("INFO"))
        self.assertFalse(manager.should_log_at_level("WARNING"))
        self.assertFalse(manager.should_log_at_level("ERROR"))
        self.assertFalse(manager.should_log_at_level("CRITICAL"))


if __name__ == "__main__":
    unittest.main()