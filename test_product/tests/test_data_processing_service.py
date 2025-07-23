"""
Unit tests for the DataProcessingService class.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import tempfile
import json

# Add parent directory to path to allow importing test_product modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from test_product.services.data_processing_service import DataProcessingService
from test_product.logging_system import StructuredLogger
from test_product.config import TestConfig


class TestDataProcessingService(unittest.TestCase):
    """Test cases for the DataProcessingService class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary log file
        self.temp_log_fd, self.temp_log_path = tempfile.mkstemp()
        
        # Create a logger
        self.logger = StructuredLogger("DataProcessingService", self.temp_log_path)
        
        # Create a service with 100% error probability for testing errors
        self.error_service = DataProcessingService(self.logger)
        self.error_service.error_probability = 1.0
        
        # Create a service with 0% error probability for testing normal operation
        self.normal_service = DataProcessingService(self.logger)
        self.normal_service.error_probability = 0.0
    
    def tearDown(self):
        """Clean up after tests."""
        os.close(self.temp_log_fd)
        os.unlink(self.temp_log_path)
    
    def test_get_service_name(self):
        """Test the get_service_name method."""
        self.assertEqual(self.normal_service.get_service_name(), "DataProcessingService")
    
    def test_get_available_operations(self):
        """Test the get_available_operations method."""
        operations = self.normal_service.get_available_operations()
        self.assertIn("process_batch", operations)
        self.assertIn("transform_data", operations)
        self.assertIn("aggregate_results", operations)
    
    def test_process_batch_success(self):
        """Test the process_batch method with successful execution."""
        # Get a batch ID from the available batches
        batches = self.normal_service.get_available_batches()
        self.assertGreater(len(batches["batches"]), 0)
        batch_id = batches["batches"][0]
        
        # Process the batch
        result = self.normal_service.process_batch(batch_id)
        
        # Check result
        self.assertTrue(result["success"])
        self.assertIn("result_id", result)
        self.assertIn("record_count", result)
        
        # Check that a result was created
        results = self.normal_service.get_processing_results()
        self.assertGreater(results["total_results"], 0)
    
    def test_process_batch_invalid_id(self):
        """Test the process_batch method with invalid batch ID."""
        result = self.normal_service.process_batch("invalid_batch_id")
        
        # Check result
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "Batch invalid_batch_id not found")
    
    def test_process_batch_error(self):
        """Test the process_batch method with error execution."""
        # Get a batch ID from the available batches
        batches = self.error_service.get_available_batches()
        self.assertGreater(len(batches["batches"]), 0)
        batch_id = batches["batches"][0]
        
        # Should raise FileNotFoundError due to missing file
        with self.assertRaises(FileNotFoundError):
            self.error_service.process_batch(batch_id)
        
        # Check log file for error
        with open(self.temp_log_path, 'r') as f:
            log_content = f.read()
            log_entry = json.loads(log_content.strip())
            
            # Check log entry fields
            self.assertEqual(log_entry["level"], "ERROR")
            self.assertEqual(log_entry["service"], "DataProcessingService")
            self.assertEqual(log_entry["error_type"], "FileNotFoundError")
            self.assertEqual(log_entry["operation"], "process_batch")
            self.assertIn("stack_trace", log_entry)
            self.assertIn("No such file or directory", log_entry["stack_trace"])
    
    def test_transform_data_success(self):
        """Test the transform_data method with successful execution."""
        # Create test data
        test_data = [
            {"id": 1, "value": 10},
            {"id": 2, "value": 20},
            {"id": 3, "value": 30}
        ]
        
        # Transform the data
        result = self.normal_service.transform_data(test_data, "numeric")
        
        # Check result
        self.assertTrue(result["success"])
        self.assertEqual(len(result["transformed_data"]), 3)
        self.assertEqual(result["transformed_data"][0]["value"], 15.0)  # 10 * 1.5
        self.assertEqual(result["transformed_data"][1]["value"], 30.0)  # 20 * 1.5
        self.assertEqual(result["transformed_data"][2]["value"], 45.0)  # 30 * 1.5
    
    def test_transform_data_text(self):
        """Test the transform_data method with text transformation."""
        # Create test data
        test_data = [
            {"id": 1, "text": "hello"},
            {"id": 2, "text": "world"},
            {"id": 3, "text": "test"}
        ]
        
        # Transform the data
        result = self.normal_service.transform_data(test_data, "text")
        
        # Check result
        self.assertTrue(result["success"])
        self.assertEqual(len(result["transformed_data"]), 3)
        self.assertEqual(result["transformed_data"][0]["text"], "HELLO")
        self.assertEqual(result["transformed_data"][1]["text"], "WORLD")
        self.assertEqual(result["transformed_data"][2]["text"], "TEST")
    
    def test_transform_data_boolean(self):
        """Test the transform_data method with boolean transformation."""
        # Create test data
        test_data = [
            {"id": 1, "active": True},
            {"id": 2, "active": False},
            {"id": 3, "active": True}
        ]
        
        # Transform the data
        result = self.normal_service.transform_data(test_data, "boolean")
        
        # Check result
        self.assertTrue(result["success"])
        self.assertEqual(len(result["transformed_data"]), 3)
        self.assertEqual(result["transformed_data"][0]["active"], False)
        self.assertEqual(result["transformed_data"][1]["active"], True)
        self.assertEqual(result["transformed_data"][2]["active"], False)
    
    def test_transform_data_unknown_type(self):
        """Test the transform_data method with unknown transformation type."""
        # Create test data
        test_data = [{"id": 1, "value": 10}]
        
        # Transform the data
        result = self.normal_service.transform_data(test_data, "unknown")
        
        # Check result
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "Unknown transformation type: unknown")
    
    def test_transform_data_empty(self):
        """Test the transform_data method with empty data."""
        result = self.normal_service.transform_data([], "numeric")
        
        # Check result
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "No data provided for transformation")
    
    def test_transform_data_error(self):
        """Test the transform_data method with error execution."""
        # Create test data with a string value that will cause ValueError
        test_data = [
            {"id": 1, "value": "abc"},  # This will cause ValueError when converting to int
            {"id": 2, "value": 20}
        ]
        
        # Should raise ValueError due to invalid conversion
        with self.assertRaises(ValueError):
            self.error_service.transform_data(test_data, "numeric")
        
        # Check log file for error
        with open(self.temp_log_path, 'r') as f:
            log_content = f.read()
            log_entry = json.loads(log_content.strip())
            
            # Check log entry fields
            self.assertEqual(log_entry["level"], "ERROR")
            self.assertEqual(log_entry["service"], "DataProcessingService")
            self.assertEqual(log_entry["error_type"], "ValueError")
            self.assertEqual(log_entry["operation"], "transform_data")
            self.assertIn("stack_trace", log_entry)
            self.assertIn("invalid literal for int", log_entry["stack_trace"])
    
    def test_aggregate_results_success(self):
        """Test the aggregate_results method with successful execution."""
        # First, process a batch to create a result
        batches = self.normal_service.get_available_batches()
        batch_id = batches["batches"][0]
        process_result = self.normal_service.process_batch(batch_id)
        result_id = process_result["result_id"]
        
        # Aggregate the result
        result = self.normal_service.aggregate_results([result_id], "sum")
        
        # Check result
        self.assertTrue(result["success"])
        self.assertEqual(result["aggregation_method"], "sum")
        self.assertIn("aggregated_value", result)
        self.assertGreater(result["record_count"], 0)
    
    def test_aggregate_results_average(self):
        """Test the aggregate_results method with average aggregation."""
        # First, process a batch to create a result
        batches = self.normal_service.get_available_batches()
        batch_id = batches["batches"][0]
        process_result = self.normal_service.process_batch(batch_id)
        result_id = process_result["result_id"]
        
        # Aggregate the result
        result = self.normal_service.aggregate_results([result_id], "average")
        
        # Check result
        self.assertTrue(result["success"])
        self.assertEqual(result["aggregation_method"], "average")
        self.assertIn("aggregated_value", result)
    
    def test_aggregate_results_max(self):
        """Test the aggregate_results method with max aggregation."""
        # First, process a batch to create a result
        batches = self.normal_service.get_available_batches()
        batch_id = batches["batches"][0]
        process_result = self.normal_service.process_batch(batch_id)
        result_id = process_result["result_id"]
        
        # Aggregate the result
        result = self.normal_service.aggregate_results([result_id], "max")
        
        # Check result
        self.assertTrue(result["success"])
        self.assertEqual(result["aggregation_method"], "max")
        self.assertIn("aggregated_value", result)
    
    def test_aggregate_results_min(self):
        """Test the aggregate_results method with min aggregation."""
        # First, process a batch to create a result
        batches = self.normal_service.get_available_batches()
        batch_id = batches["batches"][0]
        process_result = self.normal_service.process_batch(batch_id)
        result_id = process_result["result_id"]
        
        # Aggregate the result
        result = self.normal_service.aggregate_results([result_id], "min")
        
        # Check result
        self.assertTrue(result["success"])
        self.assertEqual(result["aggregation_method"], "min")
        self.assertIn("aggregated_value", result)
    
    def test_aggregate_results_unknown_method(self):
        """Test the aggregate_results method with unknown aggregation method."""
        # First, process a batch to create a result
        batches = self.normal_service.get_available_batches()
        batch_id = batches["batches"][0]
        process_result = self.normal_service.process_batch(batch_id)
        result_id = process_result["result_id"]
        
        # Aggregate the result
        result = self.normal_service.aggregate_results([result_id], "unknown")
        
        # Check result
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "Unknown aggregation method: unknown")
    
    def test_aggregate_results_empty(self):
        """Test the aggregate_results method with empty result IDs."""
        result = self.normal_service.aggregate_results([], "sum")
        
        # Check result
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "No result IDs provided for aggregation")
    
    def test_aggregate_results_invalid_ids(self):
        """Test the aggregate_results method with invalid result IDs."""
        result = self.normal_service.aggregate_results(["invalid_id"], "sum")
        
        # Check result
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "No valid results found for aggregation")
    
    def test_aggregate_results_error(self):
        """Test the aggregate_results method with error execution."""
        # First, process a batch to create a result
        batches = self.error_service.get_available_batches()
        batch_id = batches["batches"][0]
        
        # Reset error probability temporarily to process the batch successfully
        original_probability = self.error_service.error_probability
        self.error_service.error_probability = 0.0
        process_result = self.error_service.process_batch(batch_id)
        result_id = process_result["result_id"]
        self.error_service.error_probability = original_probability
        
        # Should raise MemoryError during aggregation
        with self.assertRaises(MemoryError):
            self.error_service.aggregate_results([result_id], "sum")
        
        # Check log file for error
        with open(self.temp_log_path, 'r') as f:
            log_content = f.read()
            log_entry = json.loads(log_content.strip())
            
            # Check log entry fields
            self.assertEqual(log_entry["level"], "CRITICAL")  # MemoryError is logged as CRITICAL
            self.assertEqual(log_entry["service"], "DataProcessingService")
            self.assertEqual(log_entry["error_type"], "MemoryError")
            self.assertEqual(log_entry["operation"], "aggregate_results")
            self.assertIn("stack_trace", log_entry)
            self.assertIn("Simulated memory error", log_entry["stack_trace"])
    
    def test_get_available_batches(self):
        """Test the get_available_batches method."""
        batches = self.normal_service.get_available_batches()
        
        # Check result
        self.assertIn("total_batches", batches)
        self.assertIn("batches", batches)
        self.assertGreater(len(batches["batches"]), 0)
    
    def test_get_batch_details(self):
        """Test the get_batch_details method."""
        # Get a batch ID from the available batches
        batches = self.normal_service.get_available_batches()
        batch_id = batches["batches"][0]
        
        # Get batch details
        details = self.normal_service.get_batch_details(batch_id)
        
        # Check result
        self.assertTrue(details["success"])
        self.assertEqual(details["batch_id"], batch_id)
        self.assertIn("source", details)
        self.assertIn("record_count", details)
        self.assertIn("created_at", details)
    
    def test_get_batch_details_invalid_id(self):
        """Test the get_batch_details method with invalid batch ID."""
        details = self.normal_service.get_batch_details("invalid_batch_id")
        
        # Check result
        self.assertFalse(details["success"])
        self.assertEqual(details["message"], "Batch invalid_batch_id not found")
    
    def test_get_processing_results(self):
        """Test the get_processing_results method."""
        # First, process a batch to create a result
        batches = self.normal_service.get_available_batches()
        batch_id = batches["batches"][0]
        self.normal_service.process_batch(batch_id)
        
        # Get processing results
        results = self.normal_service.get_processing_results()
        
        # Check result
        self.assertIn("total_results", results)
        self.assertIn("results", results)
        self.assertGreater(len(results["results"]), 0)


if __name__ == "__main__":
    unittest.main()