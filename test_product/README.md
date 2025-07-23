# Test Product API

This application provides a test environment for generating realistic production-like errors and logs for testing the incident agent system.

## Overview

The Test Product API is designed to generate realistic error logs from actual code bugs, following the established logging patterns used by the log_generator.py utility. It serves as a controlled environment for testing the incident agent's ability to detect, classify, and fix real code issues.

## Features

- Continuous generation of realistic error logs with proper stack traces
- Multiple buggy services that produce various types of exceptions
- Configurable error rates and log levels
- REST API for controlling error generation and application behavior
- Docker support for containerized deployment
- Integration with the incident agent system

## Installation

### Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose (for containerized deployment)
- pip (Python package manager)

### Local Installation

```bash
# Clone the repository
git clone https://github.com/your-org/incident-agent.git
cd incident-agent/test-repo

# Install dependencies
pip install -r test_product/requirements.txt
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

# Run with specific services only
python -m test_product.main --services UserService PaymentService

# Run in console mode (no API server)
python -m test_product.main --no-api

# Get detailed help
python -m test_product.cli_help
```

### Using Docker

#### Standalone Mode

```bash
# Build and run the Docker container
cd test-repo
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
cd test-repo
docker-compose build

# Stop the standalone container if running
docker-compose down

# Run with the incident agent system
cd ..  # Go to the parent directory with the main docker-compose.yml
docker-compose -f docker-compose.yml -f test-repo/docker-compose.yml up -d test-product

# View logs
docker-compose logs -f test-product

# Stop all containers
docker-compose down
```

## Configuration

### Command Line Options

The application supports various command-line options for customization:

#### General Options

| Option | Description | Default |
|--------|-------------|---------|
| `--config`, `-c` | Configuration file path (YAML or JSON) | None |
| `--log-file`, `-l` | Log file path | logs/test_product.log |
| `--log-level` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) | INFO |
| `--debug` | Enable debug mode with verbose console output | False |

#### Server Options

| Option | Description | Default |
|--------|-------------|---------|
| `--port`, `-p` | Port to run the application on | 8000 |
| `--host`, `-H` | Host to bind the application to | 0.0.0.0 |
| `--no-api` | Disable FastAPI server and run in console mode only | False |

#### Error Generation Options

| Option | Description | Default |
|--------|-------------|---------|
| `--error-rate`, `-e` | Overall error generation probability (0-1) | 0.05 |
| `--warning-rate`, `-w` | Warning generation probability (0-1) | 0.15 |
| `--critical-rate`, `-C` | Critical error generation probability (0-1) | 0.01 |
| `--interval`, `-i` | Error generation interval in seconds | 2.0 |

#### Service Options

| Option | Description | Default |
|--------|-------------|---------|
| `--services` | Services to enable | All services |
| `--service-error-rates` | Set error rates for specific services (e.g., UserService:0.1) | Default rates |

#### Error Type Options

| Option | Description | Default |
|--------|-------------|---------|
| `--error-types` | Specific error types to enable | All error types |
| `--error-type-rates` | Set probabilities for specific error types (e.g., NameError:0.3) | Default rates |

### Configuration File

You can use a YAML or JSON configuration file instead of command-line arguments:

#### YAML Example (config.yaml)

```yaml
# Logging configuration
log_file: logs/custom.log
log_level: INFO

# Error generation probabilities
error_probability: 0.1
warning_probability: 0.2
critical_probability: 0.02

# Generation timing
generation_interval: 5.0

# Service configuration
services_enabled:
  - UserService
  - PaymentService
  - DataProcessingService

# Application configuration
port: 8080
host: 127.0.0.1
debug: true
```

#### JSON Example (config.json)

```json
{
  "log_file": "logs/custom.log",
  "log_level": "INFO",
  "error_probability": 0.1,
  "warning_probability": 0.2,
  "critical_probability": 0.02,
  "generation_interval": 5.0,
  "services_enabled": ["UserService", "PaymentService", "DataProcessingService"],
  "port": 8080,
  "host": "127.0.0.1",
  "debug": true
}
```

### Docker Environment Variables

You can customize the test product behavior using environment variables in the docker-compose.yml file:

```yaml
environment:
  - TEST_PRODUCT_LOG_FILE=/app/logs/test_product.log
  - TEST_PRODUCT_LOG_LEVEL=INFO
  - TEST_PRODUCT_ERROR_RATE=0.05
  - TEST_PRODUCT_WARNING_RATE=0.15
  - TEST_PRODUCT_CRITICAL_RATE=0.01
  - TEST_PRODUCT_INTERVAL=2.0
  - TEST_PRODUCT_SERVICES=UserService,PaymentService,DataProcessingService,AuthService
  - TEST_PRODUCT_PORT=8000
  - TEST_PRODUCT_HOST=0.0.0.0
  - TEST_PRODUCT_DEBUG=true
```

## Test Scenarios

Here are some common test scenarios you can use with the Test Product API:

### Scenario 1: High Error Rate

Generate a high volume of errors to test the incident agent's ability to handle multiple issues:

```bash
python -m test_product.main --error-rate 0.3 --interval 1.0
```

### Scenario 2: Specific Error Types

Focus on specific error types to test targeted fix capabilities:

```bash
python -m test_product.main --error-types NameError KeyError AttributeError
```

### Scenario 3: Service-Specific Testing

Test with specific services to focus on particular error patterns:

```bash
python -m test_product.main --services UserService AuthService --service-error-rates UserService:0.2 AuthService:0.3
```

### Scenario 4: Burst Error Pattern

Generate errors in bursts to test the incident agent's ability to handle sudden spikes:

```bash
# Start the application normally
python -m test_product.main

# Use the API to switch to burst pattern
curl -X POST "http://localhost:8000/config" -H "Content-Type: application/json" -d '{"error_pattern": "burst"}'
```

### Scenario 5: Long-Running Test

Run a long-term test with lower error rates to simulate a production environment:

```bash
python -m test_product.main --error-rate 0.02 --warning-rate 0.1 --critical-rate 0.005 --interval 10.0
```

## API Endpoints

### Error Trigger Endpoints

The following endpoints allow you to trigger specific errors on demand:

#### POST /trigger

Trigger a specific error in a service.

**Request Body:**
```json
{
  "service": "UserService",
  "operation": "authenticate_user",
  "error_type": "NameError",
  "parameters": {
    "username": "test_user",
    "password": "password123"
  }
}
```

**Response:**
```json
{
  "success": true,
  "service": "UserService",
  "operation": "authenticate_user",
  "error_type": "NameError",
  "message": "Successfully triggered NameError in UserService.authenticate_user",
  "stack_trace": "Traceback (most recent call last):\n...",
  "timestamp": 1626912345.6789,
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### GET /trigger/{service}/{operation}

Trigger a specific error in a service using path parameters.

**Parameters:**
- `service` (path): Service name to trigger error in
- `operation` (path): Operation name to trigger
- `error_type` (query, optional): Specific error type to trigger
- `param_name` (query, optional): Parameter name for the operation
- `param_value` (query, optional): Parameter value for the operation

**Example:**
```
GET /trigger/UserService/authenticate_user?error_type=NameError&param_name=username&param_value=test_user
```

#### GET /trigger/services

List all available services and their operations.

**Response:**
```json
{
  "UserService": ["authenticate_user", "get_user_profile", "update_user_data"],
  "PaymentService": ["process_payment", "calculate_tax", "validate_card"],
  "DataProcessingService": ["process_batch", "transform_data", "aggregate_results"],
  "AuthService": ["generate_token", "validate_permissions", "refresh_session"]
}
```

#### GET /trigger/services/{service}

Get detailed information about a specific service.

**Parameters:**
- `service` (path): Service name

**Response:**
```json
{
  "service_name": "UserService",
  "operations": ["authenticate_user", "get_user_profile", "update_user_data"],
  "operation_error_types": {
    "authenticate_user": "NameError",
    "get_user_profile": "KeyError",
    "update_user_data": "AttributeError"
  },
  "error_probability": 0.08,
  "health_status": {
    "service": "UserService",
    "status": "healthy",
    "error_rate": 0.05,
    "total_operations": 120,
    "last_check": 1626912345.6789
  },
  "statistics": {
    "service_name": "UserService",
    "total_operations": 120,
    "successful_operations": 114,
    "failed_operations": 6,
    "error_rate": 0.05,
    "success_rate": 0.95
  }
}
```

#### GET /trigger/error-types

List all possible error types that can be triggered.

**Response:**
```json
[
  "AttributeError",
  "ConnectionError",
  "FileNotFoundError",
  "ImportError",
  "IndexError",
  "KeyError",
  "MemoryError",
  "NameError",
  "RecursionError",
  "TypeError",
  "ValueError",
  "ZeroDivisionError"
]
```

### Health Check Endpoints

#### GET /health

Basic health check endpoint that returns the current status of the application.

**Response:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "timestamp": 1626912345.6789,
  "error_engine": "running",
  "uptime_seconds": 3600,
  "uptime": "0d 1h 0m 0s",
  "hostname": "test-product-container"
}
```

#### GET /status

Detailed application status endpoint that provides comprehensive information about the application state.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 3600,
  "services": {
    "UserService": {
      "status": "healthy",
      "error_rate": 0.05,
      "total_operations": 120
    },
    "PaymentService": {
      "status": "healthy",
      "error_rate": 0.06,
      "total_operations": 80
    },
    "DataProcessingService": {
      "status": "healthy",
      "error_rate": 0.07,
      "total_operations": 50
    },
    "AuthService": {
      "status": "healthy",
      "error_rate": 0.05,
      "total_operations": 90
    },
    "system": {
      "hostname": "test-product-container",
      "python_version": "3.11.0",
      "platform": "linux",
      "cpu_count": 4,
      "process_id": 1234,
      "memory_usage_mb": 45.6,
      "cpu_percent": 2.3
    }
  },
  "error_generation": {
    "total_errors_generated": 20,
    "errors_per_minute": 0.33,
    "runtime_seconds": 3600,
    "runtime_formatted": "0d 1h 0m 0s",
    "errors_by_service": {
      "UserService": 8,
      "PaymentService": 5,
      "DataProcessingService": 4,
      "AuthService": 3
    },
    "errors_by_type": {
      "NameError": 4,
      "KeyError": 3,
      "AttributeError": 3,
      "ZeroDivisionError": 2,
      "TypeError": 2,
      "IndexError": 2,
      "FileNotFoundError": 1,
      "ValueError": 1,
      "MemoryError": 0,
      "ImportError": 1,
      "RecursionError": 0,
      "ConnectionError": 1
    },
    "error_rates_per_minute": {
      "UserService": 0.13,
      "PaymentService": 0.08,
      "DataProcessingService": 0.07,
      "AuthService": 0.05
    }
  }
}
```

### Configuration Endpoints

#### POST /config

Update application configuration.

**Request Body:**
```json
{
  "error_probability": 0.1,
  "warning_probability": 0.2,
  "critical_probability": 0.02,
  "generation_interval": 5.0,
  "error_pattern": "burst",
  "services_enabled": ["UserService", "PaymentService"]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully updated 6 configuration values",
  "updated_config": {
    "error_probability": 0.1,
    "warning_probability": 0.2,
    "critical_probability": 0.02,
    "generation_interval": 5.0,
    "error_pattern": "burst",
    "services_enabled": ["UserService", "PaymentService"]
  }
}
```

#### GET /config

Get current application configuration.

**Response:**
```json
{
  "application": {
    "version": "1.0.0",
    "host": "0.0.0.0",
    "port": 8000,
    "environment": "development",
    "debug": true
  },
  "logging": {
    "log_file": "logs/test_product.log",
    "log_level": "INFO"
  },
  "error_generation": {
    "error_probability": 0.1,
    "warning_probability": 0.2,
    "critical_probability": 0.02,
    "services_enabled": ["UserService", "PaymentService"],
    "running": true,
    "generation_interval": 5.0,
    "pattern_type": "burst"
  }
}
```

### Statistics Endpoints

#### GET /stats

Get error generation statistics.

**Response:**
```json
{
  "total_errors_generated": 20,
  "errors_per_minute": 0.33,
  "runtime_seconds": 3600,
  "errors_by_service": {
    "UserService": 8,
    "PaymentService": 5,
    "DataProcessingService": 4,
    "AuthService": 3
  },
  "errors_by_type": {
    "NameError": 4,
    "KeyError": 3,
    "AttributeError": 3,
    "ZeroDivisionError": 2,
    "TypeError": 2,
    "IndexError": 2,
    "FileNotFoundError": 1,
    "ValueError": 1,
    "MemoryError": 0,
    "ImportError": 1,
    "RecursionError": 0,
    "ConnectionError": 1
  },
  "application_uptime_seconds": 3600
}
```

#### POST /stats/reset

Reset error generation statistics.

**Response:**
```json
{
  "status": "success",
  "message": "Statistics reset successfully"
}
```

### Metrics Endpoints

- `GET /metrics` - Get all metrics
- `GET /metrics/errors` - Get detailed error metrics
- `GET /metrics/services` - Get service-specific metrics
- `GET /metrics/patterns` - Get error pattern metrics

## Error Types

The application can generate the following types of errors:

- `NameError` - Undefined variable reference
- `KeyError` - Missing dictionary key
- `AttributeError` - Calling method on None
- `ZeroDivisionError` - Division by zero
- `TypeError` - String + int operation
- `IndexError` - List index out of bounds
- `FileNotFoundError` - Missing file
- `ValueError` - Invalid conversion
- `MemoryError` - Simulated memory error
- `ImportError` - Missing module
- `RecursionError` - Infinite recursion
- `ConnectionError` - Simulated network failure

## Services

The application includes the following services:

### UserService

- `authenticate_user()` - NameError (undefined variable reference)
- `get_user_profile()` - KeyError (missing dictionary key)
- `update_user_data()` - AttributeError (calling method on None)

### PaymentService

- `process_payment()` - ZeroDivisionError (division by zero)
- `calculate_tax()` - TypeError (string + int operation)
- `validate_card()` - IndexError (list index out of range)

### DataProcessingService

- `process_batch()` - FileNotFoundError (missing file)
- `transform_data()` - ValueError (invalid conversion)
- `aggregate_results()` - MemoryError (simulated large data)

### AuthService

- `generate_token()` - ImportError (missing module)
- `validate_permissions()` - RecursionError (infinite recursion)
- `refresh_session()` - ConnectionError (simulated network failure)

## Integration with Incident Agent

The Test Product API is designed to work seamlessly with the incident agent system. When integrated, the incident agent can:

1. Monitor the logs generated by the Test Product API
2. Detect and classify errors based on log patterns
3. Generate fixes for the buggy code
4. Deploy hotfixes to resolve the issues

### Integration Steps

1. Ensure both the incident agent system and Test Product API are running
2. Configure the incident agent to monitor the Test Product API logs
3. Trigger errors using the Test Product API endpoints
4. Observe the incident agent's response to the generated errors

## Troubleshooting

### Common Issues

#### Application fails to start

- Check if the port is already in use
- Verify that the log directory exists and is writable
- Ensure all dependencies are installed

#### No errors are being generated

- Check the error rate configuration (--error-rate)
- Verify that services are enabled
- Check the error generation interval

#### API endpoints return 503 errors

- Ensure the error generation engine is running
- Check if the application was started with --no-api flag

#### Docker container exits immediately

- Check the container logs for error messages
- Verify that the environment variables are set correctly
- Ensure the healthcheck is passing

## Contributing

Contributions to the Test Product API are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.