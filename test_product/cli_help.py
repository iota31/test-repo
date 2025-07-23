"""
Command-line help module for the test product application.
"""

import argparse
import sys
from typing import List, Optional


def print_detailed_help():
    """Print detailed help information for the test product CLI."""
    help_text = """
Test Product Application - CLI Documentation
===========================================

The Test Product Application is designed to generate realistic error logs for testing
incident agent systems. This document provides detailed information about the available
command-line options.

General Usage
------------
python -m test_product.main [options]

Configuration Options
-------------------
--config, -c CONFIG_FILE
    Load configuration from a YAML or JSON file. This allows you to define all settings
    in a single file rather than using command-line arguments.
    
    Example YAML format:
    ```yaml
    log_file: logs/custom.log
    error_probability: 0.1
    warning_probability: 0.2
    critical_probability: 0.02
    generation_interval: 5.0
    services_enabled:
      - UserService
      - PaymentService
    port: 8080
    host: 127.0.0.1
    debug: true
    ```

--log-file, -l LOG_FILE
    Path to the log file where the application will write logs.
    Default: logs/test_product.log

--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
    Set the logging level for the application.
    Default: INFO

--debug
    Enable debug mode with additional console output.

Server Options
------------
--port, -p PORT
    Port to run the FastAPI server on.
    Default: 8000

--host, -H HOST
    Host to bind the FastAPI server to.
    Default: 0.0.0.0

--no-api
    Run in console mode without starting the FastAPI server.

Error Generation Options
----------------------
--error-rate, -e RATE
    Overall probability (0-1) of generating errors.
    Default: 0.05

--warning-rate, -w RATE
    Probability (0-1) of generating warning logs.
    Default: 0.15

--critical-rate, -C RATE
    Probability (0-1) of generating critical error logs.
    Default: 0.01

--interval, -i SECONDS
    Time interval in seconds between error generation attempts.
    Default: 2.0

Service Options
-------------
--services SERVICE [SERVICE ...]
    List of services to enable. Available services:
    - UserService: Authentication and user management (NameError, KeyError, AttributeError)
    - PaymentService: Payment processing (ZeroDivisionError, TypeError, IndexError)
    - DataProcessingService: Data handling (FileNotFoundError, ValueError, MemoryError)
    - AuthService: Authorization (ImportError, RecursionError, ConnectionError)
    
    Default: All services are enabled

--service-error-rates SERVICE:RATE [SERVICE:RATE ...]
    Set error rates for specific services.
    Example: --service-error-rates UserService:0.1 PaymentService:0.05

Error Type Options
----------------
--error-types ERROR_TYPE [ERROR_TYPE ...]
    List of specific error types to enable. Available error types:
    - NameError: Undefined variable reference
    - KeyError: Missing dictionary key
    - AttributeError: Accessing attribute on None
    - ZeroDivisionError: Division by zero
    - TypeError: Type mismatch (e.g., string + int)
    - IndexError: List index out of bounds
    - FileNotFoundError: Missing file
    - ValueError: Invalid value conversion
    - MemoryError: Simulated memory error
    - ImportError: Missing module
    - RecursionError: Infinite recursion
    - ConnectionError: Network failure
    
    Default: All error types are enabled

--error-type-rates ERROR:RATE [ERROR:RATE ...]
    Set probabilities for specific error types.
    Example: --error-type-rates NameError:0.3 KeyError:0.2

Examples
-------
# Run with default settings
python -m test_product.main

# Run with custom error rate and interval
python -m test_product.main --error-rate 0.1 --interval 5.0

# Run with specific services only
python -m test_product.main --services UserService PaymentService

# Run in console mode (no API server)
python -m test_product.main --no-api

# Run with custom log file location
python -m test_product.main --log-file /path/to/custom/log/file.log

# Run with specific error types enabled
python -m test_product.main --error-types NameError KeyError ZeroDivisionError

# Set custom error rates for specific services
python -m test_product.main --service-error-rates UserService:0.2 PaymentService:0.1

# Set custom probabilities for specific error types
python -m test_product.main --error-type-rates NameError:0.4 ValueError:0.3

# Load configuration from a file
python -m test_product.main --config my_config.yaml
"""
    print(help_text)


def main(args: Optional[List[str]] = None):
    """Main entry point for the CLI help module."""
    parser = argparse.ArgumentParser(
        description="Test Product Application - CLI Help",
        add_help=False
    )
    
    parser.add_argument(
        "--topic",
        choices=["general", "config", "server", "errors", "services", "examples"],
        help="Show help for a specific topic"
    )
    
    args = parser.parse_args(args)
    
    # For now, just print the full help
    print_detailed_help()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())