"""
Test script for the ScheduledErrorGenerator.

This script demonstrates how to use the ScheduledErrorGenerator class
to generate errors with different timing patterns.
"""

import os
import sys
import time
from pathlib import Path

# Add parent directory to path to allow importing test_product modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_product.config import TestConfig, ErrorConfig
from test_product.logging_system import create_logger
from test_product.scheduled_error_generator import ScheduledErrorGenerator
from test_product.services.user_service import UserService
from test_product.services.payment_service import PaymentService
from test_product.services.data_processing_service import DataProcessingService
from test_product.services.auth_service import AuthService


def main():
    """Test the ScheduledErrorGenerator with different patterns."""
    # Create configuration
    config = TestConfig()
    config.error_probability = 0.3  # Higher probability for testing
    config.generation_interval = 1.0  # Faster interval for testing
    config.ensure_log_directory()
    
    # Create logger
    logger = create_logger("ScheduledGeneratorTest", config.log_file)
    logger.log_info("Starting ScheduledErrorGenerator test")
    
    # Create services
    services = {}
    services["UserService"] = UserService(create_logger("UserService", config.log_file), config)
    services["PaymentService"] = PaymentService(create_logger("PaymentService", config.log_file), config)
    services["DataProcessingService"] = DataProcessingService(create_logger("DataProcessingService", config.log_file), config)
    services["AuthService"] = AuthService(create_logger("AuthService", config.log_file), config)
    
    # Create scheduled error generator
    error_generator = ScheduledErrorGenerator(services, config, logger=logger)
    
    try:
        # Test random pattern
        logger.log_info("Testing random error pattern")
        print("\nTesting random error pattern:")
        error_generator.set_pattern("random")
        error_generator.start()
        
        # Let it run for a few seconds
        print("Running for 5 seconds...")
        time.sleep(5)
        
        # Get statistics
        stats = error_generator.get_stats()
        logger.log_info("Random pattern statistics", stats)
        print("\nRandom Pattern Statistics:")
        print(f"Total errors generated: {stats['total_errors_generated']}")
        print(f"Errors by service: {stats['errors_by_service']}")
        print(f"Errors by pattern: {stats['errors_by_pattern']}")
        print(f"Runtime: {stats['runtime_seconds']:.2f} seconds")
        print(f"Errors per minute: {stats['errors_per_minute']:.2f}")
        
        # Stop generator
        error_generator.stop()
        
        # Test burst pattern
        logger.log_info("Testing burst error pattern")
        print("\nTesting burst error pattern:")
        error_generator.set_pattern("burst")
        error_generator.set_base_interval(2.0)  # Longer interval between bursts
        error_generator.reset_stats()
        error_generator.start()
        
        # Let it run for a few seconds
        print("Running for 10 seconds...")
        time.sleep(10)
        
        # Get statistics
        stats = error_generator.get_stats()
        logger.log_info("Burst pattern statistics", stats)
        print("\nBurst Pattern Statistics:")
        print(f"Total errors generated: {stats['total_errors_generated']}")
        print(f"Bursts triggered: {stats['bursts_triggered']}")
        print(f"Total burst errors: {stats['total_burst_errors']}")
        print(f"Errors by pattern: {stats['errors_by_pattern']}")
        print(f"Runtime: {stats['runtime_seconds']:.2f} seconds")
        
        # Stop generator
        error_generator.stop()
        
        # Test wave pattern
        logger.log_info("Testing wave error pattern")
        print("\nTesting wave error pattern:")
        error_generator.set_pattern("wave")
        error_generator.set_base_interval(0.5)  # Faster interval for wave pattern
        error_generator.reset_stats()
        error_generator.start()
        
        # Let it run for a few seconds
        print("Running for 10 seconds...")
        time.sleep(10)
        
        # Get statistics
        stats = error_generator.get_stats()
        logger.log_info("Wave pattern statistics", stats)
        print("\nWave Pattern Statistics:")
        print(f"Total errors generated: {stats['total_errors_generated']}")
        print(f"Errors by pattern: {stats['errors_by_pattern']}")
        print(f"Runtime: {stats['runtime_seconds']:.2f} seconds")
        print(f"Errors per minute: {stats['errors_per_minute']:.2f}")
        
        # Test time-based patterns
        logger.log_info("Testing time-based patterns")
        print("\nTesting time-based patterns:")
        error_generator.set_pattern("random")
        error_generator.set_time_patterns(True)
        error_generator.configure_peak_hours([(9, 12), (14, 17)])
        error_generator.reset_stats()
        error_generator.start()
        
        # Let it run for a few seconds
        print("Running for 10 seconds with time-based patterns...")
        time.sleep(10)
        
        # Get statistics
        stats = error_generator.get_stats()
        logger.log_info("Time-based pattern statistics", stats)
        print("\nTime-Based Pattern Statistics:")
        print(f"Total errors generated: {stats['total_errors_generated']}")
        print(f"Errors by service: {stats['errors_by_service']}")
        print(f"Runtime: {stats['runtime_seconds']:.2f} seconds")
        print(f"Errors per minute: {stats['errors_per_minute']:.2f}")
        
    finally:
        # Stop error generation
        logger.log_info("Stopping error generation")
        error_generator.stop()
        logger.log_info("Test completed")


if __name__ == "__main__":
    main()