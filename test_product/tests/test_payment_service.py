"""
Unit tests for the PaymentService class.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import tempfile
import json

# Add parent directory to path to allow importing test_product modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from test_product.services.payment_service import PaymentService
from test_product.logging_system import StructuredLogger
from test_product.config import TestConfig


class TestPaymentService(unittest.TestCase):
    """Test cases for the PaymentService class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary log file
        self.temp_log_fd, self.temp_log_path = tempfile.mkstemp()
        
        # Create a logger
        self.logger = StructuredLogger("PaymentService", self.temp_log_path)
        
        # Create a service with 100% error probability for testing errors
        self.error_service = PaymentService(self.logger)
        self.error_service.error_probability = 1.0
        
        # Create a service with 0% error probability for testing normal operation
        self.normal_service = PaymentService(self.logger)
        self.normal_service.error_probability = 0.0
    
    def tearDown(self):
        """Clean up after tests."""
        os.close(self.temp_log_fd)
        os.unlink(self.temp_log_path)
    
    def test_get_service_name(self):
        """Test the get_service_name method."""
        self.assertEqual(self.normal_service.get_service_name(), "PaymentService")
    
    def test_get_available_operations(self):
        """Test the get_available_operations method."""
        operations = self.normal_service.get_available_operations()
        self.assertIn("process_payment", operations)
        self.assertIn("calculate_tax", operations)
        self.assertIn("validate_card", operations)
    
    def test_process_payment_success(self):
        """Test the process_payment method with successful execution."""
        result = self.normal_service.process_payment(100.0, "card1")
        
        # Check result
        self.assertTrue(result["success"])
        self.assertIn("transaction_id", result)
        self.assertEqual(result["amount"], 100.0)
        self.assertEqual(result["fee"], 2.0)  # 2% of 100
        
        # Check that a transaction was created
        self.assertEqual(len(self.normal_service.transactions), 1)
        self.assertEqual(self.normal_service.transactions[0]["amount"], 100.0)
    
    def test_process_payment_with_discount(self):
        """Test the process_payment method with discount code."""
        result = self.normal_service.process_payment(100.0, "card1", "DISCOUNT10")
        
        # Check result
        self.assertTrue(result["success"])
        self.assertEqual(result["amount"], 90.0)  # 100 - 10% discount
        self.assertEqual(result["fee"], 1.8)  # 2% of 90
    
    def test_process_payment_error(self):
        """Test the process_payment method with error execution."""
        # Should raise ZeroDivisionError due to division by zero
        with self.assertRaises(ZeroDivisionError):
            self.error_service.process_payment(100.0, "card1")
        
        # Check log file for error
        with open(self.temp_log_path, 'r') as f:
            log_content = f.read()
            log_entry = json.loads(log_content.strip())
            
            # Check log entry fields
            self.assertEqual(log_entry["level"], "ERROR")
            self.assertEqual(log_entry["service"], "PaymentService")
            self.assertEqual(log_entry["error_type"], "ZeroDivisionError")
            self.assertEqual(log_entry["operation"], "process_payment")
            self.assertIn("stack_trace", log_entry)
            self.assertIn("division by zero", log_entry["stack_trace"])
    
    def test_calculate_tax_success(self):
        """Test the calculate_tax method with successful execution."""
        result = self.normal_service.calculate_tax(100.0, "US")
        
        # Check result
        self.assertTrue(result["success"])
        self.assertEqual(result["amount"], 100.0)
        self.assertEqual(result["tax_rate"], 0.08)  # US tax rate
        self.assertEqual(result["tax_amount"], 8.0)  # 8% of 100
        self.assertEqual(result["total_amount"], 108.0)  # 100 + 8
    
    def test_calculate_tax_unknown_region(self):
        """Test the calculate_tax method with unknown region."""
        result = self.normal_service.calculate_tax(100.0, "UNKNOWN")
        
        # Check result
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "Unknown tax region: UNKNOWN")
    
    def test_calculate_tax_error(self):
        """Test the calculate_tax method with error execution."""
        # Should raise TypeError due to string + int operation
        with self.assertRaises(TypeError):
            self.error_service.calculate_tax(100.0, "US")
        
        # Check log file for error
        with open(self.temp_log_path, 'r') as f:
            log_content = f.read()
            log_entry = json.loads(log_content.strip())
            
            # Check log entry fields
            self.assertEqual(log_entry["level"], "ERROR")
            self.assertEqual(log_entry["service"], "PaymentService")
            self.assertEqual(log_entry["error_type"], "TypeError")
            self.assertEqual(log_entry["operation"], "calculate_tax")
            self.assertIn("stack_trace", log_entry)
            self.assertIn("can only concatenate str", log_entry["stack_trace"])
    
    def test_validate_card_success(self):
        """Test the validate_card method with successful execution."""
        result = self.normal_service.validate_card("4111111111111111", "12/25", "123")
        
        # Check result
        self.assertTrue(result["success"])
        self.assertEqual(result["card_type"], "Visa")
    
    def test_validate_card_invalid_number(self):
        """Test the validate_card method with invalid card number."""
        result = self.normal_service.validate_card("411", "12/25", "123")
        
        # Check result
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "Invalid card number")
    
    def test_validate_card_invalid_expiry(self):
        """Test the validate_card method with invalid expiry date."""
        result = self.normal_service.validate_card("4111111111111111", "1225", "123")
        
        # Check result
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "Invalid expiry date")
    
    def test_validate_card_invalid_cvv(self):
        """Test the validate_card method with invalid CVV."""
        result = self.normal_service.validate_card("4111111111111111", "12/25", "1")
        
        # Check result
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "Invalid CVV")
    
    def test_validate_card_error(self):
        """Test the validate_card method with error execution."""
        # Should raise IndexError due to list index out of bounds
        with self.assertRaises(IndexError):
            self.error_service.validate_card("4111111111111111", "12/25", "123")
        
        # Check log file for error
        with open(self.temp_log_path, 'r') as f:
            log_content = f.read()
            log_entry = json.loads(log_content.strip())
            
            # Check log entry fields
            self.assertEqual(log_entry["level"], "ERROR")
            self.assertEqual(log_entry["service"], "PaymentService")
            self.assertEqual(log_entry["error_type"], "IndexError")
            self.assertEqual(log_entry["operation"], "validate_card")
            self.assertIn("stack_trace", log_entry)
            self.assertIn("list index out of range", log_entry["stack_trace"])
    
    def test_detect_card_type(self):
        """Test the _detect_card_type method."""
        self.assertEqual(self.normal_service._detect_card_type("4111111111111111"), "Visa")
        self.assertEqual(self.normal_service._detect_card_type("5111111111111111"), "MasterCard")
        self.assertEqual(self.normal_service._detect_card_type("341111111111111"), "American Express")
        self.assertEqual(self.normal_service._detect_card_type("6111111111111111"), "Discover")
        self.assertEqual(self.normal_service._detect_card_type("9111111111111111"), "Unknown")
    
    def test_mask_card_number(self):
        """Test the _mask_card_number method."""
        self.assertEqual(self.normal_service._mask_card_number("4111111111111111"), "************1111")
        self.assertEqual(self.normal_service._mask_card_number("411"), "411")  # Too short to mask
    
    def test_get_transaction_history(self):
        """Test the get_transaction_history method."""
        # Create a transaction
        self.normal_service.process_payment(100.0, "card1")
        
        # Get transaction history
        transactions = self.normal_service.get_transaction_history()
        
        # Check result
        self.assertEqual(len(transactions), 1)
        self.assertEqual(transactions[0]["amount"], 100.0)
    
    def test_get_payment_methods(self):
        """Test the get_payment_methods method."""
        methods = self.normal_service.get_payment_methods()
        
        # Check result
        self.assertEqual(len(methods), 2)
        self.assertIn("card1", methods)
        self.assertIn("card2", methods)
        self.assertEqual(methods["card1"]["type"], "credit")
        self.assertEqual(methods["card1"]["last_four"], "1234")


if __name__ == "__main__":
    unittest.main()