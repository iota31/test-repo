"""
Payment service with calculation bugs for testing incident detection.
"""

import random
import time
from typing import Dict, Any, Optional, List
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .base_service import BaseService
from ..logging_system import StructuredLogger
from ..config import TestConfig


class PaymentService(BaseService):
    """
    Payment service with intentional calculation bugs for testing.
    
    Contains three specific bugs:
    1. ZeroDivisionError in process_payment() - division by zero
    2. TypeError in calculate_tax() - string + int operation
    3. IndexError in validate_card() - list index out of bounds
    """
    
    def __init__(self, logger: StructuredLogger, config: Optional[TestConfig] = None):
        super().__init__("PaymentService", logger, error_probability=0.06, config=config)
        
        # Mock payment data
        self.payment_methods = {
            "card1": {
                "type": "credit",
                "last_four": "1234",
                "expiry": "12/25",
                "holder": "John Doe"
            },
            "card2": {
                "type": "debit",
                "last_four": "5678",
                "expiry": "03/26",
                "holder": "Jane Smith"
            }
        }
        
        # Mock transaction history
        self.transactions = []
        
        # Tax rates by region
        self.tax_rates = {
            "US": 0.08,
            "EU": 0.20,
            "CA": 0.13,
            "JP": 0.10
        }
    
    def get_service_name(self) -> str:
        """Get the service name."""
        return "PaymentService"
    
    def get_available_operations(self) -> list:
        """Get list of available operations."""
        return ["process_payment", "calculate_tax", "validate_card"]
    
    def process_payment(self, amount: float, payment_method_id: str, discount_code: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a payment with ZeroDivisionError bug.
        
        Bug: Divides by zero when calculating fee
        """
        def normal_operation():
            # Validate payment method
            if payment_method_id not in self.payment_methods:
                return {
                    "success": False,
                    "message": "Invalid payment method"
                }
            
            # Apply discount if provided
            discount_amount = 0
            if discount_code:
                # Simple discount logic - 10% off
                discount_amount = amount * 0.1
            
            # Calculate final amount
            final_amount = amount - discount_amount
            
            # Calculate processing fee (2%)
            processing_fee = final_amount * 0.02
            
            # Create transaction record
            transaction_id = f"tx_{int(time.time())}_{random.randint(1000, 9999)}"
            transaction = {
                "id": transaction_id,
                "amount": final_amount,
                "payment_method": payment_method_id,
                "timestamp": time.time(),
                "status": "completed",
                "fee": processing_fee
            }
            
            self.transactions.append(transaction)
            
            return {
                "success": True,
                "transaction_id": transaction_id,
                "amount": final_amount,
                "fee": processing_fee,
                "message": "Payment processed successfully"
            }
        
        def error_operation():
            # Validate payment method
            if payment_method_id not in self.payment_methods:
                return {
                    "success": False,
                    "message": "Invalid payment method"
                }
            
            # Apply discount if provided
            discount_amount = 0
            if discount_code:
                # Simple discount logic - 10% off
                discount_amount = amount * 0.1
            
            # Calculate final amount
            final_amount = amount - discount_amount
            
            # BUG: ZeroDivisionError - division by zero
            # Calculate processing fee with a bug that divides by zero
            # This simulates a bug where the fee divisor becomes zero due to some logic error
            fee_divisor = 0 if final_amount > 10 else 50  # Bug: divisor becomes 0 for amounts > 10
            processing_fee = final_amount / fee_divisor  # ZeroDivisionError for amounts > 10
            
            # Create transaction record
            transaction_id = f"tx_{int(time.time())}_{random.randint(1000, 9999)}"
            transaction = {
                "id": transaction_id,
                "amount": final_amount,
                "payment_method": payment_method_id,
                "timestamp": time.time(),
                "status": "completed",
                "fee": processing_fee
            }
            
            self.transactions.append(transaction)
            
            return {
                "success": True,
                "transaction_id": transaction_id,
                "amount": final_amount,
                "fee": processing_fee,
                "message": "Payment processed successfully"
            }
        
        return self._execute_with_error_handling(
            "process_payment",
            normal_operation,
            error_operation,
            amount=amount,
            payment_method=payment_method_id
        )
    
    def calculate_tax(self, amount: float, region: str) -> Dict[str, Any]:
        """
        Calculate tax for a given amount and region with TypeError bug.
        
        Bug: Tries to add string and int
        """
        def normal_operation():
            # Check if region has a defined tax rate
            if region not in self.tax_rates:
                return {
                    "success": False,
                    "message": f"Unknown tax region: {region}"
                }
            
            # Calculate tax
            tax_rate = self.tax_rates[region]
            tax_amount = amount * tax_rate
            total_amount = amount + tax_amount
            
            return {
                "success": True,
                "amount": amount,
                "tax_rate": tax_rate,
                "tax_amount": tax_amount,
                "total_amount": total_amount,
                "region": region
            }
        
        def error_operation():
            # Check if region has a defined tax rate
            if region not in self.tax_rates:
                return {
                    "success": False,
                    "message": f"Unknown tax region: {region}"
                }
            
            # Calculate tax
            tax_rate = self.tax_rates[region]
            tax_amount = amount * tax_rate
            
            # BUG: TypeError - string + int operation
            # This simulates a bug where the amount is accidentally converted to a string
            # before adding the tax amount
            amount_str = str(amount)  # Convert amount to string
            total_amount = amount_str + tax_amount  # TypeError: can only concatenate str (not "float") to str
            
            return {
                "success": True,
                "amount": amount,
                "tax_rate": tax_rate,
                "tax_amount": tax_amount,
                "total_amount": total_amount,
                "region": region
            }
        
        return self._execute_with_error_handling(
            "calculate_tax",
            normal_operation,
            error_operation,
            amount=amount,
            region=region
        )
    
    def validate_card(self, card_number: str, expiry_date: str, cvv: str) -> Dict[str, Any]:
        """
        Validate a credit card with IndexError bug.
        
        Bug: Accesses an index beyond the list bounds
        """
        def normal_operation():
            # Basic validation
            if not card_number or len(card_number) < 13:
                return {
                    "success": False,
                    "message": "Invalid card number"
                }
            
            if not expiry_date or len(expiry_date) != 5:  # Format: MM/YY
                return {
                    "success": False,
                    "message": "Invalid expiry date"
                }
            
            if not cvv or len(cvv) < 3:
                return {
                    "success": False,
                    "message": "Invalid CVV"
                }
            
            # Simple Luhn algorithm check (simplified)
            digits = [int(d) for d in card_number if d.isdigit()]
            checksum = sum(digits[-1::-2]) + sum(sum(divmod(d * 2, 10)) for d in digits[-2::-2])
            is_valid = checksum % 10 == 0
            
            # Check expiry
            try:
                month, year = expiry_date.split('/')
                month_int = int(month)
                year_int = int(year)
                
                if not (1 <= month_int <= 12 and year_int >= 23):  # Assuming 2023+
                    return {
                        "success": False,
                        "message": "Card expired or invalid date"
                    }
            except ValueError:
                return {
                    "success": False,
                    "message": "Invalid expiry date format"
                }
            
            return {
                "success": True,
                "is_valid": is_valid,
                "card_type": self._detect_card_type(card_number),
                "message": "Card validation successful"
            }
        
        def error_operation():
            # Basic validation
            if not card_number or len(card_number) < 13:
                return {
                    "success": False,
                    "message": "Invalid card number"
                }
            
            if not expiry_date or len(expiry_date) != 5:  # Format: MM/YY
                return {
                    "success": False,
                    "message": "Invalid expiry date"
                }
            
            if not cvv or len(cvv) < 3:
                return {
                    "success": False,
                    "message": "Invalid CVV"
                }
            
            # BUG: IndexError - list index out of bounds
            # This simulates a bug where we try to access an index beyond the list bounds
            # when processing the card number segments
            card_segments = card_number.split('-') if '-' in card_number else [card_number]
            
            # Try to access a segment that might not exist
            # This will cause an IndexError if there aren't enough segments
            first_segment = card_segments[0]
            middle_segment = card_segments[1]  # IndexError if card_number doesn't have a hyphen
            last_segment = card_segments[2]    # IndexError even if it has one hyphen
            
            # Check expiry
            try:
                month, year = expiry_date.split('/')
                month_int = int(month)
                year_int = int(year)
                
                if not (1 <= month_int <= 12 and year_int >= 23):  # Assuming 2023+
                    return {
                        "success": False,
                        "message": "Card expired or invalid date"
                    }
            except ValueError:
                return {
                    "success": False,
                    "message": "Invalid expiry date format"
                }
            
            return {
                "success": True,
                "is_valid": True,
                "card_type": self._detect_card_type(card_number),
                "message": "Card validation successful"
            }
        
        return self._execute_with_error_handling(
            "validate_card",
            normal_operation,
            error_operation,
            card_number=self._mask_card_number(card_number)
        )
    
    def _detect_card_type(self, card_number: str) -> str:
        """Detect the card type based on the card number."""
        # Remove any non-digit characters
        card_number = ''.join(c for c in card_number if c.isdigit())
        
        # Simple detection based on first digits
        if card_number.startswith('4'):
            return "Visa"
        elif card_number.startswith(('51', '52', '53', '54', '55')):
            return "MasterCard"
        elif card_number.startswith(('34', '37')):
            return "American Express"
        elif card_number.startswith('6'):
            return "Discover"
        else:
            return "Unknown"
    
    def _mask_card_number(self, card_number: str) -> str:
        """Mask the card number for logging purposes."""
        # Remove any non-digit characters
        card_number = ''.join(c for c in card_number if c.isdigit())
        
        if len(card_number) <= 4:
            return card_number
        
        # Mask all but the last 4 digits
        return '*' * (len(card_number) - 4) + card_number[-4:]
    
    def get_transaction_history(self) -> List[Dict[str, Any]]:
        """Get transaction history."""
        return self.transactions
    
    def get_payment_methods(self) -> Dict[str, Any]:
        """Get available payment methods."""
        # Return masked payment methods for security
        masked_methods = {}
        for key, method in self.payment_methods.items():
            masked_methods[key] = {
                "type": method["type"],
                "last_four": method["last_four"],
                "expiry": method["expiry"],
                "holder": method["holder"]
            }
        
        return masked_methods