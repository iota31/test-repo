"""
Integration tests for the full test product application.
"""

import os
import sys
import unittest
import tempfile
import json
import time
import threading
import requests
from unittest.mock import patch
import asyncio
import signal
from concurrent.futures import ThreadPoolExecutor

# Add parent directory to path to allow importing test_product modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from test_product.config import TestConfig
from test_product.logging_system import create_logger
from test_product.error_engine import ErrorGenerationEngine
from test_product.services.user_service import UserService
from test_product.services.payment_service import PaymentService
from test_product.services.data_processing_service import DataProcessingService
from test_product.services.auth_service import AuthService


class TestApplicationIntegration(unittest.TestCase):
    """Integration tests for the full test product application."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests."""
        # Create a temporary log file
        cls.temp_log_fd, cls.temp_log_path = tempfile.mkstemp()
        
        # Create a test configuration
        cls.config = TestConfig()
        cls.config.log_file = cls.temp_log_path
        cls.config.error_probability = 0.2  # Higher probability for testing
        cls.config.generation_interval = 0.5  # Faster interval for testing
        cls.config.port = 8765  # Use a different port for testing
        
        # Create services
        cls.services = {}
        cls.services["UserService"] = UserService(create_logger("UserService", cls.temp_log_path), cls.config)
        cls.services["PaymentService"] = PaymentService(create_logger("PaymentService", cls.temp_log_path), cls.config)
        cls.services["DataProcessingService"] = DataProcessingService(create_logger("DataProcessingService", cls.temp_log_path), cls.config)
        cls.services["AuthService"] = AuthService(create_logger("AuthService", cls.temp_log_path), cls.config)
        
        # Create error generation engine
        cls.logger = create_logger("IntegrationTest", cls.temp_log_path)
        cls.error_engine = ErrorGenerationEngine(cls.services, cls.config, logger=cls.logger)
        
        # Start the application in a separate thread
        cls.app_thread = None
        cls.app_running = False
        cls.start_application()
        
        # Wait for the application to start
        time.sleep(2)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        # Stop the application
        cls.stop_application()
        
        # Clean up temporary files
        os.close(cls.temp_log_fd)
        os.unlink(cls.temp_log_path)
    
    @classmethod
    def start_application(cls):
        """Start the application in a separate thread."""
        # Import here to avoid circular imports
        from test_product.api_service import create_app
        
        # Create the FastAPI app
        app = create_app(cls.config, cls.services, cls.error_engine)
        
        # Function to run the app
        def run_app():
            import uvicorn
            cls.app_running = True
            uvicorn.run(app, host=cls.config.host, port=cls.config.port)
            cls.app_running = False
        
        # Start the app in a separate thread
        cls.app_thread = threading.Thread(target=run_app)
        cls.app_thread.daemon = True
        cls.app_thread.start()
    
    @classmethod
    def stop_application(cls):
        """Stop the application."""
        if cls.app_running:
            # Send a request to shut down the server
            try:
                requests.get(f"http://{cls.config.host}:{cls.config.port}/shutdown")
            except:
                pass
            
            # Wait for the thread to finish
            cls.app_thread.join(timeout=5)
    
    def test_application_startup(self):
        """Test that the application starts up correctly."""
        # Check that the application is running
        self.assertTrue(self.__class__.app_running)
        
        # Check that we can access the health endpoint
        response = requests.get(f"http://{self.config.host}:{self.config.port}/health")
        self.assertEqual(response.status_code, 200)
        
        # Check the response content
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("version", data)
    
    def test_status_endpoint(self):
        """Test the status endpoint."""
        response = requests.get(f"http://{self.config.host}:{self.config.port}/status")
        self.assertEqual(response.status_code, 200)
        
        # Check the response content
        data = response.json()
        self.assertIn("services", data)
        self.assertIn("error_engine", data)
        
        # Check that all services are included
        services = data["services"]
        self.assertEqual(len(services), 4)
        service_names = [service["service"] for service in services]
        self.assertIn("UserService", service_names)
        self.assertIn("PaymentService", service_names)
        self.assertIn("DataProcessingService", service_names)
        self.assertIn("AuthService", service_names)
    
    def test_trigger_error_endpoint(self):
        """Test the trigger error endpoint."""
        # Trigger a specific error
        response = requests.post(
            f"http://{self.config.host}:{self.config.port}/trigger/error",
            json={"service": "UserService", "operation": "authenticate_user"}
        )
        self.assertEqual(response.status_code, 200)
        
        # Check the response content
        data = response.json()
        self.assertIn("triggered", data)
        self.assertTrue(data["triggered"])
        self.assertEqual(data["service"], "UserService")
        self.assertEqual(data["operation"], "authenticate_user")
    
    def test_trigger_invalid_service(self):
        """Test triggering an error with an invalid service."""
        response = requests.post(
            f"http://{self.config.host}:{self.config.port}/trigger/error",
            json={"service": "InvalidService", "operation": "authenticate_user"}
        )
        self.assertEqual(response.status_code, 404)
    
    def test_trigger_invalid_operation(self):
        """Test triggering an error with an invalid operation."""
        response = requests.post(
            f"http://{self.config.host}:{self.config.port}/trigger/error",
            json={"service": "UserService", "operation": "invalid_operation"}
        )
        self.assertEqual(response.status_code, 404)
    
    def test_log_file_generation(self):
        """Test that log files are generated."""
        # Trigger some errors to generate logs
        requests.post(
            f"http://{self.config.host}:{self.config.port}/trigger/error",
            json={"service": "UserService", "operation": "authenticate_user"}
        )
        requests.post(
            f"http://{self.config.host}:{self.config.port}/trigger/error",
            json={"service": "PaymentService", "operation": "process_payment"}
        )
        
        # Wait for logs to be written
        time.sleep(1)
        
        # Check that the log file exists and has content
        self.assertTrue(os.path.exists(self.temp_log_path))
        self.assertGreater(os.path.getsize(self.temp_log_path), 0)
        
        # Check log file content
        with open(self.temp_log_path, 'r') as f:
            log_content = f.read()
            
            # Check for expected log entries
            self.assertIn("UserService", log_content)
            self.assertIn("PaymentService", log_content)
            self.assertIn("ERROR", log_content)
    
    def test_log_format_compliance(self):
        """Test that logs comply with the expected format."""
        # Trigger an error to generate a log
        requests.post(
            f"http://{self.config.host}:{self.config.port}/trigger/error",
            json={"service": "UserService", "operation": "authenticate_user"}
        )
        
        # Wait for logs to be written
        time.sleep(1)
        
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
    
    def test_continuous_operation(self):
        """Test that the application runs continuously and generates errors."""
        # Start the error generation engine
        self.error_engine.start_scheduled_generation()
        
        try:
            # Let it run for a few seconds
            time.sleep(5)
            
            # Check that errors were generated
            stats = self.error_engine.get_error_generation_stats()
            self.assertGreater(stats["total_errors_generated"], 0)
            
            # Check that logs were written
            self.assertGreater(os.path.getsize(self.temp_log_path), 0)
        finally:
            # Stop the error generation engine
            self.error_engine.stop_scheduled_generation()


if __name__ == "__main__":
    unittest.main()