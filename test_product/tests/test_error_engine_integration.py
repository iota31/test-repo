"""
Integration tests for the ErrorGenerationEngine.
"""

import os
import sys
import unittest
import tempfile
import json
import time
import threading

# Add parent directory to path to allow importing test_product modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from test_product.config import TestConfig
from test_product.logging_system import create_logger
from test_product.error_engine import ErrorGenerationEngine
from test_product.services.user_service import UserService
from test_product.services.payment_service import PaymentService
from test_product.services.data_processing_service import DataProcessingService
from test_product.services.auth_service import AuthService


class TestErrorEngineIntegration(unittest.TestCase):
    """Integration tests for the ErrorGenerationEngine."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary log file
        self.temp_log_fd, self.temp_log_path = tempfile.mkstemp()
        
        # Create a test configuration
        self.config = TestConfig()
        self.config.log_file = self.temp_log_path
        self.config.error_probability = 0.5  # Higher probability for testing
        self.config.generation_interval = 0.1  # Faster interval for testing
        
        # Create services
        self.services = {}
        self.services["UserService"] = UserService(create_logger("UserService", self.temp_log_path), self.config)
        self.services["PaymentService"] = PaymentService(create_logger("PaymentService", self.temp_log_path), self.config)
        self.services["DataProcessingService"] = DataProcessingService(create_logger("DataProcessingService", self.temp_log_path), self.config)
        self.services["AuthService"] = AuthService(create_logger("AuthService", self.temp_log_path), self.config)
        
        # Create error generation engine
        self.logger = create_logger("ErrorEngineTest", self.temp_log_path)
        self.error_engine = ErrorGenerationEngine(self.services, self.config, logger=self.logger)
    
    def tearDown(self):
        """Clean up after tests."""
        # Stop error generation if running
        if self.error_engine.running:
            self.error_engine.stop_scheduled_generation()
        
        # Clean up temporary files
        os.close(self.temp_log_fd)
        os.unlink(self.temp_log_path)
    
    def test_continuous_error_generation(self):
        """Test that the error engine generates errors continuously."""
        # Start error generation
        self.error_engine.start_scheduled_generation()
        
        # Let it run for a short time
        time.sleep(1)
        
        # Stop error generation
        self.error_engine.stop_scheduled_generation()
        
        # Check that errors were generated
        stats = self.error_engine.get_error_generation_stats()
        self.assertGreater(stats["total_errors_generated"], 0)
        
        # Check that logs were written
        self.assertGreater(os.path.getsize(self.temp_log_path), 0)
    
    def test_error_distribution(self):
        """Test that errors are distributed across services."""
        # Start error generation
        self.error_engine.start_scheduled_generation()
        
        # Let it run for a longer time to get a good distribution
        time.sleep(2)
        
        # Stop error generation
        self.error_engine.stop_scheduled_generation()
        
        # Check that errors were generated in multiple services
        stats = self.error_engine.get_error_generation_stats()
        errors_by_service = stats.get("errors_by_service", {})
        
        # We should have errors in at least 2 services
        services_with_errors = [service for service, count in errors_by_service.items() if count > 0]
        self.assertGreaterEqual(len(services_with_errors), 2)
    
    def test_error_type_distribution(self):
        """Test that different types of errors are generated."""
        # Start error generation
        self.error_engine.start_scheduled_generation()
        
        # Let it run for a longer time to get a good distribution
        time.sleep(2)
        
        # Stop error generation
        self.error_engine.stop_scheduled_generation()
        
        # Check that different types of errors were generated
        stats = self.error_engine.get_error_generation_stats()
        errors_by_type = stats.get("errors_by_type", {})
        
        # We should have at least 2 different error types
        error_types = [error_type for error_type, count in errors_by_type.items() if count > 0]
        self.assertGreaterEqual(len(error_types), 2)
    
    def test_error_pattern_random(self):
        """Test the random error pattern."""
        # Set error pattern to random
        self.error_engine.set_error_pattern("random")
        
        # Start error generation
        self.error_engine.start_scheduled_generation()
        
        # Let it run for a short time
        time.sleep(1)
        
        # Stop error generation
        self.error_engine.stop_scheduled_generation()
        
        # Check that errors were generated
        stats = self.error_engine.get_error_generation_stats()
        self.assertGreater(stats["total_errors_generated"], 0)
    
    def test_error_pattern_burst(self):
        """Test the burst error pattern."""
        # Set error pattern to burst
        self.error_engine.set_error_pattern("burst")
        
        # Start error generation
        self.error_engine.start_scheduled_generation()
        
        # Let it run for a longer time to catch a burst
        time.sleep(3)
        
        # Stop error generation
        self.error_engine.stop_scheduled_generation()
        
        # Check that errors were generated
        stats = self.error_engine.get_error_generation_stats()
        self.assertGreater(stats["total_errors_generated"], 0)
        
        # Check burst statistics if available
        scheduled_generator = stats.get("scheduled_generator", {})
        if "bursts_triggered" in scheduled_generator:
            self.assertGreaterEqual(scheduled_generator["bursts_triggered"], 0)
    
    def test_trigger_specific_error(self):
        """Test triggering a specific error."""
        # Trigger a specific error
        success = self.error_engine.trigger_specific_error("UserService", "authenticate_user")
        
        # Check that the error was triggered
        self.assertTrue(success)
        
        # Check that logs were written
        self.assertGreater(os.path.getsize(self.temp_log_path), 0)
        
        # Check that the error was recorded in statistics
        stats = self.error_engine.get_error_generation_stats()
        self.assertGreaterEqual(stats["total_errors_generated"], 1)
        
        # Check that the error was recorded for the correct service
        errors_by_service = stats.get("errors_by_service", {})
        self.assertGreaterEqual(errors_by_service.get("UserService", 0), 1)
    
    def test_update_error_probabilities(self):
        """Test updating error probabilities."""
        # Update service-specific error probabilities
        service_probabilities = {
            "UserService": 0.8,
            "PaymentService": 0.2
        }
        
        self.error_engine.update_error_probabilities(service_probabilities=service_probabilities)
        
        # Check that probabilities were updated
        self.assertEqual(self.services["UserService"].error_probability, 0.8)
        self.assertEqual(self.services["PaymentService"].error_probability, 0.2)
        
        # Other services should keep their original probability
        self.assertEqual(self.services["DataProcessingService"].error_probability, self.config.error_probability)
        self.assertEqual(self.services["AuthService"].error_probability, self.config.error_probability)
    
    def test_update_generation_interval(self):
        """Test updating the generation interval."""
        # Update generation interval
        new_interval = 0.5
        self.error_engine.update_generation_interval(new_interval)
        
        # Check that interval was updated
        self.assertEqual(self.error_engine.generation_interval, new_interval)
    
    def test_reset_stats(self):
        """Test resetting statistics."""
        # Start error generation
        self.error_engine.start_scheduled_generation()
        
        # Let it run for a short time
        time.sleep(1)
        
        # Stop error generation
        self.error_engine.stop_scheduled_generation()
        
        # Check that errors were generated
        stats_before = self.error_engine.get_error_generation_stats()
        self.assertGreater(stats_before["total_errors_generated"], 0)
        
        # Reset statistics
        self.error_engine.reset_stats()
        
        # Check that statistics were reset
        stats_after = self.error_engine.get_error_generation_stats()
        self.assertEqual(stats_after["total_errors_generated"], 0)
    
    def test_log_format_compliance(self):
        """Test that generated logs comply with the expected format."""
        # Trigger a specific error
        self.error_engine.trigger_specific_error("UserService", "authenticate_user")
        
        # Wait for logs to be written
        time.sleep(0.1)
        
        # Read the log file
        with open(self.temp_log_path, 'r') as f:
            log_lines = f.readlines()
            
            # Find an ERROR log entry
            error_log = None
            for line in log_lines:
                if '"level": "ERROR"' in line:
                    error_log = line
                    break
            
            # Check that we found an ERROR log
            self.assertIsNotNone(error_log)
            
            # Parse the log entry
            log_entry = json.loads(error_log)
            
            # Check required fields
            self.assertIn("timestamp", log_entry)
            self.assertIn("level", log_entry)
            self.assertIn("service", log_entry)
            self.assertIn("message", log_entry)
            self.assertIn("hostname", log_entry)
            self.assertIn("thread", log_entry)
            self.assertIn("stack_trace", log_entry)
            self.assertIn("error_type", log_entry)
            
            # Check field values
            self.assertEqual(log_entry["level"], "ERROR")
            self.assertEqual(log_entry["service"], "UserService")
            self.assertEqual(log_entry["error_type"], "NameError")


if __name__ == "__main__":
    unittest.main()