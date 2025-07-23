# Test Repository

This repository contains a test product application that generates realistic production-like errors and logs for testing the incident agent system.

## Overview

The test product is a Python application that:

1. Runs continuously and generates logs
2. Contains actual buggy code that produces various types of exceptions
3. Produces logs at different severity levels with appropriate frequency
4. Represents common real-world programming errors
5. Is easily configurable and controllable

## Directory Structure

```
test-repo/
├── Dockerfile                  # Docker configuration for the test product
├── docker-compose.yml          # Docker Compose configuration for integration
├── docker-compose.override.yml # Docker Compose override for standalone mode
├── logs/                       # Log files directory
│   └── test_product.log        # Main log file
└── test_product/               # Test product application code
    ├── __init__.py             # Package initialization
    ├── api_service.py          # FastAPI application and endpoints
    ├── cli_help.py             # Detailed CLI help documentation
    ├── config.py               # Configuration management
    ├── error_engine.py         # Error generation engine
    ├── logging_system.py       # Structured logging system
    ├── main.py                 # Application entry point
    ├── README.md               # API documentation
    ├── requirements.txt        # Python dependencies
    ├── scheduled_error_generator.py # Background error generation
    ├── services/               # Buggy service implementations
    │   ├── __init__.py
    │   ├── auth_service.py     # Authentication service with bugs
    │   ├── base_service.py     # Base service class
    │   ├── data_processing_service.py # Data processing with bugs
    │   ├── payment_service.py  # Payment service with bugs
    │   └── user_service.py     # User service with bugs
    └── test_*.py               # Test files
```

## Running the Application

### Using Python Directly

```bash
# Install dependencies
pip install -r test_product/requirements.txt

# Run with default settings
python -m test_product.main

# Run with custom error rate and interval
python -m test_product.main --error-rate 0.1 --interval 5.0

# Get detailed help
python -m test_product.cli_help
```

### Using Docker

#### Standalone Mode

```bash
# Build and run the Docker container
docker-compose build
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

#### Integration with Incident Agent System

```bash
# Build the test product image
docker-compose build

# Stop the standalone container if running
docker-compose down

# Run with the incident agent system (from parent directory)
cd ..
docker-compose -f docker-compose.yml -f test-repo/docker-compose.yml up -d test-product

# View logs
docker-compose logs -f test-product

# Stop all containers
docker-compose down
```

## API Documentation

See the [test_product/README.md](test_product/README.md) file for detailed API documentation.

## Configuration

The application can be configured using:

1. Command-line arguments
2. Environment variables
3. Configuration files (YAML or JSON)

See the help documentation for details:

```bash
python -m test_product.cli_help
```