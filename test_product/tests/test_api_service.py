"""
Unit tests for the API service.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import tempfile
import json
from fastapi.testclient import TestClient

# Add parent directory to path to allow importing test_product modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from test_product.api_service import create_app
from test_product.config import TestConfig
from test_product.logging_system import create_logger
from test_product.error_engine import ErrorGenerationEngine
from test_product.services.user_service import UserService
from test_product.services.payment_service import PaymentService
from test_product.services.data_processing_service import DataProcessingService
from test_product.services.auth_service import AuthService


class TestAPIService(unittest.TestCase):
    """Test cases for the API service."""
    
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
        
        # Create services
        cls.services = {}
        cls.services["UserService"] = UserService(create_logger("UserService", cls.temp_log_path), cls.config)
        cls.services["PaymentService"] = PaymentService(create_logger("PaymentService", cls.temp_log_path), cls.config)
        cls.services["DataProcessingService"] = DataProcessingService(create_logger("DataProcessingService", cls.temp_log_path), cls.config)
        cls.services["AuthService"] = AuthService(create_logger("AuthService", cls.temp_log_path), cls.config)
        
        # Create error generation engine
        cls.logger = create_logger("APIServiceTest", cls.temp_log_path)
        cls.error_engine = ErrorGenerationEngine(cls.services, cls.config, logger=cls.logger)
        
        # Create FastAPI app
        cls.app = create_app(cls.config, cls.services, cls.error_engine)
        
        # Create test client
        cls.client = TestClient(cls.app)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        # Clean up temporary files
        os.close(cls.temp_log_fd)
        os.unlink(cls.temp_log_path)
    
    def test_health_endpoint(self):
        """Test the health endpoint."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        
        # Check response content
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertIn("version", data)
        self.assertIn("timestamp", data)
        self.assertIn("error_engine", data)
        self.assertIn("uptime_seconds", data)
    
    def test_status_endpoint(self):
        """Test the status endpoint."""
        response = self.client.get("/status")
        self.assertEqual(response.status_code, 200)
        
        # Check response content
        data = response.json()
        self.assertIn("services", data)
        self.assertIn("error_generation", data)
        self.assertIn("version", data)
        self.assertIn("uptime_seconds", data)
        
        # Check that all services are included
        services = data["services"]
        self.assertIn("UserService", services)
        self.assertIn("PaymentService", services)
        self.assertIn("DataProcessingService", services)
        self.assertIn("AuthService", services)
    
    def test_trigger_error_endpoint(self):
        """Test the trigger error endpoint."""
        # Trigger a specific error
        response = self.client.post(
            "/trigger",
            json={"service": "UserService", "operation": "authenticate_user"}
        )
        self.assertEqual(response.status_code, 200)
        
        # Check response content
        data = response.json()
        self.assertIn("success", data)
        self.assertEqual(data["service"], "UserService")
        self.assertEqual(data["operation"], "authenticate_user")
    
    def test_trigger_error_get_endpoint(self):
        """Test the GET trigger error endpoint."""
        response = self.client.get("/trigger/UserService/authenticate_user")
        self.assertEqual(response.status_code, 200)
        
        # Check response content
        data = response.json()
        self.assertIn("success", data)
        self.assertEqual(data["service"], "UserService")
        self.assertEqual(data["operation"], "authenticate_user")
    
    def test_trigger_invalid_service(self):
        """Test triggering an error with an invalid service."""
        response = self.client.post(
            "/trigger",
            json={"service": "InvalidService", "operation": "authenticate_user"}
        )
        self.assertEqual(response.status_code, 404)
    
    def test_trigger_invalid_operation(self):
        """Test triggering an error with an invalid operation."""
        response = self.client.post(
            "/trigger",
            json={"service": "UserService", "operation": "invalid_operation"}
        )
        self.assertEqual(response.status_code, 404)
    
    def test_list_services_endpoint(self):
        """Test the list services endpoint."""
        response = self.client.get("/trigger/services")
        self.assertEqual(response.status_code, 200)
        
        # Check response content
        data = response.json()
        self.assertIn("UserService", data)
        self.assertIn("PaymentService", data)
        self.assertIn("DataProcessingService", data)
        self.assertIn("AuthService", data)
        
        # Check that operations are listed
        self.assertIn("authenticate_user", data["UserService"])
        self.assertIn("process_payment", data["PaymentService"])
    
    def test_get_service_details_endpoint(self):
        """Test the get service details endpoint."""
        response = self.client.get("/trigger/services/UserService")
        self.assertEqual(response.status_code, 200)
        
        # Check response content
        data = response.json()
        self.assertIn("operations", data)
        self.assertIn("authenticate_user", data["operations"])
        self.assertIn("get_user_profile", data["operations"])
        self.assertIn("update_user_data", data["operations"])
    
    def test_list_error_types_endpoint(self):
        """Test the list error types endpoint."""
        response = self.client.get("/trigger/error-types")
        self.assertEqual(response.status_code, 200)
        
        # Check response content
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertIn("NameError", data)
        self.assertIn("KeyError", data)
        self.assertIn("AttributeError", data)
        self.assertIn("ZeroDivisionError", data)
    
    def test_config_endpoint(self):
        """Test the config endpoint."""
        response = self.client.get("/config")
        self.assertEqual(response.status_code, 200)
        
        # Check response content
        data = response.json()
        self.assertIn("application", data)
        self.assertIn("logging", data)
        self.assertIn("error_generation", data)
        
        # Check specific config values
        self.assertEqual(data["logging"]["log_file"], self.config.log_file)
        self.assertEqual(data["error_generation"]["error_probability"], self.config.error_probability)
    
    def test_update_config_endpoint(self):
        """Test the update config endpoint."""
        # Update configuration
        new_probability = 0.3
        response = self.client.post(
            "/config",
            json={"error_probability": new_probability}
        )
        self.assertEqual(response.status_code, 200)
        
        # Check response content
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["updated_config"]["error_probability"], new_probability)
        
        # Check that config was actually updated
        self.assertEqual(self.config.error_probability, new_probability)
    
    def test_stats_endpoint(self):
        """Test the stats endpoint."""
        response = self.client.get("/stats")
        self.assertEqual(response.status_code, 200)
        
        # Check response content
        data = response.json()
        self.assertIn("total_errors_generated", data)
        self.assertIn("errors_by_service", data)
        self.assertIn("application_uptime_seconds", data)
    
    def test_reset_stats_endpoint(self):
        """Test the reset stats endpoint."""
        # First, trigger some errors to generate stats
        self.client.post(
            "/trigger",
            json={"service": "UserService", "operation": "authenticate_user"}
        )
        
        # Reset stats
        response = self.client.post("/stats/reset")
        self.assertEqual(response.status_code, 200)
        
        # Check response content
        data = response.json()
        self.assertEqual(data["status"], "success")
        
        # Check that stats were reset
        stats_response = self.client.get("/stats")
        stats_data = stats_response.json()
        self.assertEqual(stats_data["total_errors_generated"], 0)
    
    def test_metrics_endpoint(self):
        """Test the metrics endpoint."""
        response = self.client.get("/metrics")
        self.assertEqual(response.status_code, 200)
        
        # Check response content
        data = response.json()
        self.assertIn("application", data)
        self.assertIn("errors", data)
        self.assertIn("patterns", data)
    
    def test_error_metrics_endpoint(self):
        """Test the error metrics endpoint."""
        response = self.client.get("/metrics/errors")
        self.assertEqual(response.status_code, 200)
        
        # Check response content
        data = response.json()
        self.assertIn("total", data)
        self.assertIn("by_service", data)
        self.assertIn("by_type", data)


if __name__ == "__main__":
    unittest.main()