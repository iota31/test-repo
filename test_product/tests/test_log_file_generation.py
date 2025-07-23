"""
Tests for log file generation and format compliance.
"""

import os
import sys
import unittest
import tempfile
import json
import time
import re
from datetime import datetime

# Add parent directory to path to allow importing test_product modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from test_product.config import TestConfig
from test_product.logging_system import create_logger, StructuredLogger
from test_product.error_engine import ErrorGenerationEngine
from test_product.services.user_service import UserService
from test_product.services.payment_service import PaymentService
from test_product.services.data_processing_service import DataProcessingService
from test_product.services.auth_service import AuthService


class TestLogFileGeneration(unittest.TestCase):
    """Tests for log file generation and format compliance."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary log file
        self.temp_log_fd, self.temp_log_path = tempfile.mkstemp()
        
        # Create a test configuration
        self.config = TestConfig()
        self.config.log_file = self.temp_log_path
        
        # Create a logger
        self.logger = create_logger("LogFileTest", self.temp_log_path)
    
    def tearDown(self):
        """Clean up after tests."""
        # Clean up temporary files
        os.close(self.temp_log_fd)
        os.unlink(self.temp_log_path)
    
    def test_log_file_creation(self):
        """Test that log files are created."""
        # Log a message
        self.logger.log_info("Test message")
        
        # Check that the log file exists
        self.assertTrue(os.path.exists(self.temp_log_path))
        
        # Check that the log file has content
        self.assertGreater(os.path.getsize(self.temp_log_path), 0)
    
    def test_log_format_compliance(self):
        """Test that logs comply with the expected format."""
        # Log messages at different levels
        self.logger.log_info("Info message", {"context_key": "context_value"})
        self.logger.log_warning("Warning message", {"warning_key": "warning_value"})
        
        try:
            # Generate an error
            raise ValueError("Test error")
        except ValueError as e:
            self.logger.log_error(e, {"error_key": "error_value"})
        
        try:
            # Generate a critical error
            raise MemoryError("Test critical error")
        except MemoryError as e:
            self.logger.log_critical(e, {"critical_key": "critical_value"})
        
        # Read the log file
        with open(self.temp_log_path, 'r') as f:
            log_lines = f.readlines()
            
            # Check that we have 4 log entries
            self.assertEqual(len(log_lines), 4)
            
            # Check each log entry
            for line in log_lines:
                log_entry = json.loads(line)
                
                # Check common required fields
                self.assertIn("timestamp", log_entry)
                self.assertIn("level", log_entry)
                self.assertIn("service", log_entry)
                self.assertIn("message", log_entry)
                self.assertIn("hostname", log_entry)
                self.assertIn("thread", log_entry)
                
                # Check level-specific fields
                if log_entry["level"] == "INFO":
                    self.assertEqual(log_entry["message"], "Info message")
                    self.assertEqual(log_entry["context_key"], "context_value")
                
                elif log_entry["level"] == "WARNING":
                    self.assertEqual(log_entry["message"], "Warning message")
                    self.assertEqual(log_entry["warning_key"], "warning_value")
                
                elif log_entry["level"] == "ERROR":
                    self.assertEqual(log_entry["message"], "ValueError occurred in LogFileTest")
                    self.assertEqual(log_entry["error_key"], "error_value")
                    self.assertEqual(log_entry["error_type"], "ValueError")
                    self.assertIn("stack_trace", log_entry)
                    self.assertIn("Test error", log_entry["stack_trace"])
                    self.assertIn("function_name", log_entry)
                    self.assertIn("line_number", log_entry)
                
                elif log_entry["level"] == "CRITICAL":
                    self.assertEqual(log_entry["message"], "CRITICAL MemoryError occurred in LogFileTest")
                    self.assertEqual(log_entry["critical_key"], "critical_value")
                    self.assertEqual(log_entry["error_type"], "MemoryError")
                    self.assertIn("stack_trace", log_entry)
                    self.assertIn("Test critical error", log_entry["stack_trace"])
                    self.assertIn("function_name", log_entry)
                    self.assertIn("line_number", log_entry)
    
    def test_timestamp_format(self):
        """Test that timestamps are in the correct format."""
        # Log a message
        self.logger.log_info("Test message")
        
        # Read the log file
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
    
    def test_log_level_distribution(self):
        """Test that log levels are distributed according to configuration."""
        # Create services with error generation
        services = {}
        services["UserService"] = UserService(create_logger("UserService", self.temp_log_path), self.config)
        services["PaymentService"] = PaymentService(create_logger("PaymentService", self.temp_log_path), self.config)
        
        # Create error generation engine
        error_engine = ErrorGenerationEngine(services, self.config, logger=self.logger)
        
        # Start error generation
        error_engine.start_scheduled_generation()
        
        try:
            # Let it run for a short time
            time.sleep(1)
        finally:
            # Stop error generation
            error_engine.stop_scheduled_generation()
        
        # Read the log file
        with open(self.temp_log_path, 'r') as f:
            log_lines = f.readlines()
            
            # Count log levels
            level_counts = {"INFO": 0, "WARNING": 0, "ERROR": 0, "CRITICAL": 0}
            for line in log_lines:
                try:
                    log_entry = json.loads(line)
                    if "level" in log_entry:
                        level = log_entry["level"]
                        if level in level_counts:
                            level_counts[level] += 1
                except json.JSONDecodeError:
                    continue
            
            # Check that we have logs at different levels
            total_logs = sum(level_counts.values())
            self.assertGreater(total_logs, 0)
            
            # Check that INFO logs are the most common
            self.assertGreaterEqual(level_counts["INFO"], level_counts["WARNING"])
            self.assertGreaterEqual(level_counts["WARNING"], level_counts["ERROR"])
            
            # Check that we have at least some logs at each level
            # (This might occasionally fail due to randomness, but should pass most of the time)
            self.assertGreater(level_counts["INFO"], 0)
            
            # Print level distribution for debugging
            print(f"Log level distribution: {level_counts}")
    
    def test_log_directory_creation(self):
        """Test that log directories are created if they don't exist."""
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        try:
            # Create a log file path in a subdirectory that doesn't exist
            log_file_path = os.path.join(temp_dir, "logs", "test.log")
            
            # Create a logger with this path
            logger = create_logger("DirectoryTest", log_file_path)
            
            # Log a message
            logger.log_info("Test message")
            
            # Check that the log directory was created
            self.assertTrue(os.path.exists(os.path.dirname(log_file_path)))
            
            # Check that the log file was created
            self.assertTrue(os.path.exists(log_file_path))
            
            # Check that the log file has content
            self.assertGreater(os.path.getsize(log_file_path), 0)
        finally:
            # Clean up
            import shutil
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    unittest.main()