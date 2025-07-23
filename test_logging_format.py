#!/usr/bin/env python3
"""
Test script to verify the logging system matches log_generator.py format.
"""

import json
import sys
from pathlib import Path

# Add test_product to path
sys.path.insert(0, str(Path(__file__).parent))

from test_product.config import TestConfig
from test_product.logging_system import StructuredLogger, LogLevelManager


def test_logging_format():
    """Test that our logging format matches log_generator.py output."""
    
    # Create test configuration
    config = TestConfig(log_file="logs/test_format.log")
    config.ensure_log_directory()
    
    # Create logger
    logger = StructuredLogger("TestService", config.log_file)
    
    # Test INFO log
    logger.log_info("TestService processed request successfully", {
        "user_id": "test_user_123",
        "request_id": "req_456"
    })
    
    # Test WARNING log
    logger.log_warning("Potential issue detected in TestService", {
        "response_time": 2.5,
        "threshold": 2.0
    })
    
    # Test ERROR log with exception
    try:
        # Simulate a NameError
        undefined_variable  # This will raise NameError
    except NameError as e:
        logger.log_error(e, {
            "user_id": "test_user_123",
            "operation": "authenticate_user"
        })
    
    # Test CRITICAL log with exception
    try:
        # Simulate a ZeroDivisionError
        result = 10 / 0
    except ZeroDivisionError as e:
        logger.log_critical(e, {
            "payment_amount": 100.0,
            "operation": "process_payment"
        })
    
    print("Test logs generated successfully!")
    print(f"Check {config.log_file} for output")
    
    # Read and display the generated logs
    try:
        with open(config.log_file, 'r') as f:
            lines = f.readlines()
            print(f"\nGenerated {len(lines)} log entries:")
            for i, line in enumerate(lines[-4:], 1):  # Show last 4 entries
                try:
                    log_entry = json.loads(line.strip())
                    print(f"\n{i}. {log_entry['level']} - {log_entry['message']}")
                    print(f"   Service: {log_entry['service']}")
                    print(f"   Timestamp: {log_entry['timestamp']}")
                    if 'stack_trace' in log_entry:
                        print(f"   Error Type: {log_entry['error_type']}")
                        print(f"   Function: {log_entry.get('function_name', 'N/A')}")
                except json.JSONDecodeError:
                    print(f"   Invalid JSON: {line.strip()}")
    except FileNotFoundError:
        print(f"Log file {config.log_file} not found")


def test_log_level_manager():
    """Test the log level manager probabilities."""
    
    manager = LogLevelManager()
    
    # Generate 1000 samples to test distribution
    samples = [manager.get_random_log_level() for _ in range(1000)]
    
    # Count occurrences
    counts = {
        "INFO": samples.count("INFO"),
        "WARNING": samples.count("WARNING"), 
        "ERROR": samples.count("ERROR"),
        "CRITICAL": samples.count("CRITICAL")
    }
    
    print("\nLog Level Distribution Test (1000 samples):")
    for level, count in counts.items():
        percentage = (count / 1000) * 100
        print(f"  {level}: {count} ({percentage:.1f}%)")
    
    # Verify roughly correct distribution (allow for statistical variance)
    assert 750 <= counts["INFO"] <= 850, f"INFO ratio should be ~80%, got {counts['INFO']/10}%"
    assert 100 <= counts["WARNING"] <= 200, f"WARNING ratio should be ~15%, got {counts['WARNING']/10}%"
    assert 20 <= counts["ERROR"] <= 80, f"ERROR ratio should be ~4%, got {counts['ERROR']/10}%"
    assert 0 <= counts["CRITICAL"] <= 40, f"CRITICAL ratio should be ~1%, got {counts['CRITICAL']/10}%"
    
    print("✓ Log level distribution test passed!")


if __name__ == "__main__":
    print("Testing logging system format compatibility...")
    test_logging_format()
    test_log_level_manager()
    print("\n✓ All tests passed!")