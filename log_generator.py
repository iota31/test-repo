"""
Log generator utility for simulating production logs.
This is useful for testing the monitoring system.
"""

import argparse
import json
import logging
import os
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Sample exception types for simulating errors
EXCEPTION_TYPES = [
    "NullPointerException",
    "IndexOutOfBoundsException",
    "IllegalArgumentException",
    "RuntimeException",
    "IOException",
    "DatabaseConnectionException",
    "AuthenticationFailedException",
    "ServiceUnavailableException",
    "TimeoutException",
    "ValidationException",
]

# Sample service names
SERVICES = [
    "UserService",
    "PaymentService",
    "AuthService",
    "NotificationService",
    "DataProcessingService",
    "ApiGateway",
    "InventoryService",
    "OrderService",
    "RecommendationEngine",
    "SearchService",
]


# Sample stack traces
def generate_stack_trace(exception_type, service):
    """Generate a realistic-looking stack trace."""
    class_name = service
    method_name = random.choice(
        [
            "process",
            "handle",
            "execute",
            "validate",
            "authenticate",
            "authorize",
            "fetch",
            "save",
            "delete",
            "update",
        ]
    )
    line_number = random.randint(10, 500)

    trace = [
        f"{exception_type}: An error occurred in {service}",
        f"    at com.example.{class_name}.{method_name}({class_name}.java:{line_number})",
    ]

    # Add random number of additional frames
    frames = random.randint(2, 5)
    for i in range(frames):
        sub_class = random.choice(SERVICES)
        sub_method = random.choice(
            [
                "callService",
                "processRequest",
                "validateInput",
                "executeQuery",
                "transform",
                "buildResponse",
                "checkPermissions",
                "fetchData",
            ]
        )
        sub_line = random.randint(10, 500)
        trace.append(
            f"    at com.example.{sub_class}.{sub_method}({sub_class}.java:{sub_line})"
        )

    return "\n".join(trace)


def generate_log_entry(level="INFO", use_json=True):
    """Generate a single log entry."""
    # Use timezone-aware UTC datetime; `datetime.utcnow()` is deprecated.
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    service = random.choice(SERVICES)

    # Determine message based on level
    if level == "ERROR" or level == "CRITICAL":
        exception_type = random.choice(EXCEPTION_TYPES)
        message = f"{exception_type} occurred in {service}"
        stack_trace = generate_stack_trace(exception_type, service)
        detail = f"{message}\n{stack_trace}"
    elif level == "WARNING":
        message = random.choice(
            [
                f"Potential issue detected in {service}",
                f"Slow response from {service} detected",
                f"Unexpected response from {service}",
                f"Missing optional parameter in request to {service}",
                f"Rate limit warning for {service}",
            ]
        )
        detail = message
    else:  # INFO or DEBUG
        message = random.choice(
            [
                f"{service} processed request successfully",
                f"User authenticated via {service}",
                f"Data retrieved from {service}",
                f"Request completed in {service}",
                f"Cache updated in {service}",
            ]
        )
        detail = message

    # Generate either JSON or plain text log
    if use_json:
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "service": service,
            "message": message,
            "hostname": f"srv-{random.randint(1, 20):02d}",
            "thread": f"thread-{random.randint(1, 100)}",
        }

        if level in ("ERROR", "CRITICAL"):
            log_entry["stack_trace"] = stack_trace

        return json.dumps(log_entry)
    else:
        # Plain text format
        return f"{timestamp} {level} [{service}] [{f'srv-{random.randint(1, 20):02d}'}] {detail}"


def generate_logs(
    output_file,
    count=100,
    interval=0.5,
    json_format=True,
    error_probability=0.05,
    warning_probability=0.15,
    append=False,
):
    """
    Generate sample logs to a file.

    Args:
        output_file: Path to the output log file
        count: Number of log entries to generate
        interval: Time interval between log entries in seconds
        json_format: Whether to use JSON format (True) or plain text (False)
        error_probability: Probability of generating an error log (0-1)
        warning_probability: Probability of generating a warning log (0-1)
        append: Whether to append to the file (True) or overwrite (False)
    """
    # Create directory if it doesn't exist
    output_path = Path(output_file)
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)

    # Determine file mode based on append flag
    file_mode = "a" if append else "w"

    with open(output_file, file_mode) as f:
        for i in range(count):
            # Determine log level based on probabilities
            rand = random.random()
            if rand < error_probability:
                level = random.choice(["ERROR", "CRITICAL"])
            elif rand < error_probability + warning_probability:
                level = "WARNING"
            else:
                level = "INFO"

            log_entry = generate_log_entry(level, json_format)
            f.write(log_entry + "\n")
            f.flush()  # Ensure log is written immediately

            # Log to console as well
            print(f"Generated {level} log entry #{i+1}/{count}")

            # Sleep between logs to simulate realistic timing
            if i < count - 1:  # No need to sleep after the last entry
                time.sleep(interval)


def main():
    """Main function to run the log generator."""
    parser = argparse.ArgumentParser(description="Generate sample logs for testing")
    parser.add_argument(
        "--output", "-o", default="logs/test_app.log", help="Output log file path"
    )
    parser.add_argument(
        "--count", "-c", type=int, default=100, help="Number of log entries to generate"
    )
    parser.add_argument(
        "--interval",
        "-i",
        type=float,
        default=0.5,
        help="Time interval between log entries in seconds",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["json", "text"],
        default="json",
        help="Log format (json or text)",
    )
    parser.add_argument(
        "--error-rate",
        "-e",
        type=float,
        default=0.05,
        help="Probability of generating error logs (0-1)",
    )
    parser.add_argument(
        "--warning-rate",
        "-w",
        type=float,
        default=0.15,
        help="Probability of generating warning logs (0-1)",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append to the output file instead of overwriting",
    )

    args = parser.parse_args()

    try:
        print(f"Generating {args.count} log entries to {args.output}")
        print(
            f"Format: {args.format}, Error rate: {args.error_rate}, Warning rate: {args.warning_rate}, Append: {args.append}"
        )

        generate_logs(
            args.output,
            count=args.count,
            interval=args.interval,
            json_format=(args.format == "json"),
            error_probability=args.error_rate,
            warning_probability=args.warning_rate,
            append=args.append,
        )

        print(f"Log generation complete. Output written to {args.output}")
    except KeyboardInterrupt:
        print("\nLog generation interrupted by user")
    except Exception as e:
        print(f"Error generating logs: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
