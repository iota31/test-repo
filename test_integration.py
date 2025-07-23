#!/usr/bin/env python3
"""
Integration test to verify all components of Task 1 work together.
"""

import json
import os
import sys
from pathlib import Path

# Add test_product to path
sys.path.insert(0, str(Path(__file__).parent))

from test_product.config import TestConfig, ErrorConfig
from test_product.logging_system import StructuredLogger, LogLevelManager, create_logger


def test_config_system():
    """Test the configuration system."""
    print("Testing configuration system...")
    
    # Test default config
    config = TestConfig()
    assert config.log_file == "logs/test_product.log"
    assert config.error_probability == 0.05
    assert config.port == 8000
    
    # Test environment config
    os.environ["TEST_PRODUCT_PORT"] = "9000"
    os.environ["TEST_PRODUCT_ERROR_RATE"] = "0.1"
    
    env_config = TestConfig.from_env()
    assert env_config.port == 9000
    assert env_config.error_probability == 0.1
    
    # Test error config
    error_config = ErrorConfig()
    probabilities = error_config.get_error_type_probabilities()
    assert "NameError" in probabilities
    assert "ZeroDivisionError" in probabilities
    
    service_rates = error_config.get_service_error_rates()
    assert "UserService" in service_rates
    assert "PaymentService" in service_rates
    
    print("✓ Configuration system test passed!")


def test_logging_integration():
    """Test the complete logging system integration."""
    print("Testing logging system integration...")
    
    # Create test config
    config = TestConfig(log_file="logs/integration_test.log")
    config.ensure_log_directory()
    
    # Test factory function
    logger = create_logger("IntegrationTest", config.log_file)
    assert isinstance(logger, StructuredLogger)
    
    # Test all log levels
    logger.log_info("Integration test started", {"test_id": "int_001"})
    logger.log_warning("Test warning message", {"warning_type": "test"})
    
    # Test error logging
    try:
        raise ValueError("Test error for integration")
    except ValueError as e:
        logger.log_error(e, {"test_context": "integration_test"})
    
    # Test critical logging
    try:
        raise RuntimeError("Test critical error")
    except RuntimeError as e:
        logger.log_critical(e, {"severity": "high"})
    
    # Verify log file was created and contains valid JSON
    assert Path(config.log_file).exists()
    
    with open(config.log_file, 'r') as f:
        lines = f.readlines()
        assert len(lines) >= 4
        
        for line in lines:
            log_entry = json.loads(line.strip())
            assert "timestamp" in log_entry
            assert "level" in log_entry
            assert "service" in log_entry
            assert "message" in log_entry
            assert "hostname" in log_entry
            assert "thread" in log_entry
            
            if log_entry["level"] in ("ERROR", "CRITICAL"):
                assert "stack_trace" in log_entry
                assert "error_type" in log_entry
                assert "function_name" in log_entry
                assert "line_number" in log_entry
    
    print("✓ Logging system integration test passed!")


def test_log_level_manager():
    """Test log level manager functionality."""
    print("Testing log level manager...")
    
    manager = LogLevelManager()
    
    # Test individual level checks
    levels = ["INFO", "WARNING", "ERROR", "CRITICAL"]
    for level in levels:
        result = manager.should_log_at_level(level)
        assert isinstance(result, bool)
    
    # Test random level generation
    for _ in range(100):
        level = manager.get_random_log_level()
        assert level in levels
    
    print("✓ Log level manager test passed!")


def test_directory_structure():
    """Test that the directory structure is properly created."""
    print("Testing directory structure...")
    
    # Check main package
    assert Path("test_product/__init__.py").exists()
    assert Path("test_product/config.py").exists()
    assert Path("test_product/logging_system.py").exists()
    assert Path("test_product/main.py").exists()
    assert Path("test_product/README.md").exists()
    
    # Check services directory
    assert Path("test_product/services/__init__.py").exists()
    
    # Check logs directory is created when needed
    config = TestConfig()
    config.ensure_log_directory()
    assert Path("logs").exists()
    
    print("✓ Directory structure test passed!")


def test_main_application():
    """Test the main application entry point."""
    print("Testing main application...")
    
    # Test that main module can be imported
    from test_product.main import create_argument_parser, main
    
    # Test argument parser
    parser = create_argument_parser()
    args = parser.parse_args(["--port", "9000", "--debug"])
    assert args.port == 9000
    assert args.debug is True
    
    print("✓ Main application test passed!")


def cleanup_test_files():
    """Clean up test files."""
    test_files = [
        "logs/integration_test.log",
        "logs/test_format.log",
        "logs/test_product.log"
    ]
    
    for file_path in test_files:
        if Path(file_path).exists():
            Path(file_path).unlink()
    
    # Clean up environment variables
    env_vars = ["TEST_PRODUCT_PORT", "TEST_PRODUCT_ERROR_RATE"]
    for var in env_vars:
        if var in os.environ:
            del os.environ[var]


def main():
    """Run all integration tests."""
    print("Running Task 1 integration tests...\n")
    
    try:
        test_config_system()
        test_logging_integration()
        test_log_level_manager()
        test_directory_structure()
        test_main_application()
        
        print("\n🎉 All Task 1 integration tests passed!")
        print("\nTask 1 Implementation Summary:")
        print("✅ Directory structure created")
        print("✅ Configuration management system implemented")
        print("✅ Logging system matching log_generator.py format")
        print("✅ Command-line interface")
        print("✅ Environment variable support")
        print("✅ Comprehensive testing")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        cleanup_test_files()


if __name__ == "__main__":
    sys.exit(main())