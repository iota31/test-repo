"""
Test script for the ErrorGenerationEngine.

This script demonstrates how to use the ErrorGenerationEngine class
to generate errors in the test product services.
"""

import os
import sys
import time
from pathlib import Path

# Add parent directory to path to allow importing test_product modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_product.config import TestConfig, ErrorConfig
from test_product.logging_system import create_logger
from test_product.error_engine import ErrorGenerationEngine
from test_product.services.user_service import UserService
from test_product.services.payment_service import PaymentService
from test_product.services.data_processing_service import DataProcessingService
from test_product.services.auth_service import AuthService


def main():
    """Test the ErrorGenerationEngine."""
    # Create configuration
    config = TestConfig()
    config.error_probability = 0.3  # Higher probability for testing
    config.generation_interval = 1.0  # Faster interval for testing
    config.ensure_log_directory()
    
    # Create logger
    logger = create_logger("ErrorEngineTest", config.log_file)
    logger.log_info("Starting ErrorGenerationEngine test")
    
    # Create services
    services = {}
    services["UserService"] = UserService(create_logger("UserService", config.log_file), config)
    services["PaymentService"] = PaymentService(create_logger("PaymentService", config.log_file), config)
    services["DataProcessingService"] = DataProcessingService(create_logger("DataProcessingService", config.log_file), config)
    services["AuthService"] = AuthService(create_logger("AuthService", config.log_file), config)
    
    # Create error generation engine
    error_engine = ErrorGenerationEngine(services, config, logger=logger)
    
    try:
        # Start scheduled error generation
        logger.log_info("Starting scheduled error generation")
        error_engine.start_scheduled_generation()
        
        # Let it run for a few seconds
        logger.log_info("Running for 5 seconds...")
        time.sleep(5)
        
        # Get statistics
        stats = error_engine.get_error_generation_stats()
        logger.log_info("Error generation statistics", stats)
        print("\nError Generation Statistics:")
        print(f"Total errors generated: {stats['total_errors_generated']}")
        print(f"Errors by service: {stats['errors_by_service']}")
        print(f"Runtime: {stats['runtime_seconds']:.2f} seconds")
        print(f"Errors per minute: {stats['errors_per_minute']:.2f}")
        
        # Test different error patterns
        logger.log_info("Testing burst error pattern")
        print("\nTesting burst error pattern:")
        error_engine.set_error_pattern("burst")
        error_engine.update_generation_interval(2.0)
        error_engine.reset_stats()
        
        # Let it run for a few seconds
        print("Running for 5 seconds with burst pattern...")
        time.sleep(5)
        
        # Get statistics
        stats = error_engine.get_error_generation_stats()
        logger.log_info("Burst pattern statistics", stats)
        print("\nBurst Pattern Statistics:")
        print(f"Total errors generated: {stats['total_errors_generated']}")
        print(f"Errors by pattern: {stats['scheduled_generator']['errors_by_pattern']}")
        print(f"Bursts triggered: {stats['scheduled_generator']['bursts_triggered']}")
        print(f"Total burst errors: {stats['scheduled_generator']['total_burst_errors']}")
        
        # Test time-based patterns
        logger.log_info("Testing time-based patterns")
        print("\nTesting time-based patterns:")
        error_engine.set_error_pattern("random")
        error_engine.configure_time_patterns(True, [(9, 12), (14, 17)])
        error_engine.reset_stats()
        
        # Let it run for a few seconds
        print("Running for 5 seconds with time-based patterns...")
        time.sleep(5)
        
        # Test on-demand error triggering
        logger.log_info("Testing on-demand error triggering")
        print("\nTesting on-demand error triggering:")
        
        # Try to trigger a specific error
        service_name = "UserService"
        operation = "authenticate_user"
        print(f"Triggering error in {service_name}.{operation}...")
        
        success = error_engine.trigger_specific_error(service_name, operation)
        print(f"Error triggered successfully: {success}")
        
        # Update error probabilities
        logger.log_info("Testing probability updates")
        print("\nUpdating error probabilities:")
        
        service_probabilities = {
            "UserService": 0.5,
            "PaymentService": 0.4
        }
        
        error_engine.update_error_probabilities(service_probabilities=service_probabilities)
        print(f"Updated service probabilities: {service_probabilities}")
        
        # Let it run with new probabilities
        logger.log_info("Running with updated probabilities for 5 seconds...")
        print("Running with updated probabilities for 5 seconds...")
        time.sleep(5)
        
        # Get updated statistics
        stats = error_engine.get_error_generation_stats()
        logger.log_info("Updated error generation statistics", stats)
        print("\nUpdated Error Generation Statistics:")
        print(f"Total errors generated: {stats['total_errors_generated']}")
        print(f"Errors by service: {stats['errors_by_service']}")
        print(f"Runtime: {stats['runtime_seconds']:.2f} seconds")
        print(f"Errors per minute: {stats['errors_per_minute']:.2f}")
        
    finally:
        # Stop error generation
        logger.log_info("Stopping error generation")
        error_engine.stop_scheduled_generation()
        logger.log_info("Test completed")


if __name__ == "__main__":
    main()