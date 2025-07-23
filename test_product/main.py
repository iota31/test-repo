"""
Main entry point for the test product application.

This module provides the main entry point for running the test product application,
including proper initialization, graceful shutdown handling, and signal handling
for clean termination.
"""

import argparse
import os
import signal
import sys
import time
import threading
import uvicorn
from pathlib import Path
from typing import Optional, Dict, Any

from .config import TestConfig, ErrorConfig
from .logging_system import create_logger, StructuredLogger
from .error_engine import ErrorGenerationEngine
from .services.user_service import UserService
from .services.payment_service import PaymentService
from .services.data_processing_service import DataProcessingService
from .services.auth_service import AuthService
from .api_service import TestProductAPI


def create_argument_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Test Product Application - Generate realistic errors for incident agent testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
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
  
For detailed documentation, run:
  python -m test_product.cli_help
"""
    )
    
    # General application configuration
    general_group = parser.add_argument_group('General Options')
    general_group.add_argument(
        "--config", "-c",
        help="Configuration file path (optional, uses environment variables by default)"
    )
    
    general_group.add_argument(
        "--log-file", "-l",
        default="logs/test_product.log",
        help="Log file path (default: logs/test_product.log)"
    )
    
    general_group.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level (default: INFO)"
    )
    
    general_group.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode with verbose console output"
    )
    
    # Server configuration
    server_group = parser.add_argument_group('Server Options')
    server_group.add_argument(
        "--port", "-p",
        type=int,
        default=8000,
        help="Port to run the application on (default: 8000)"
    )
    
    server_group.add_argument(
        "--host", "-H",
        default="0.0.0.0",
        help="Host to bind the application to (default: 0.0.0.0)"
    )
    
    server_group.add_argument(
        "--no-api",
        action="store_true",
        help="Disable FastAPI server and run in console mode only"
    )
    
    # Error generation configuration
    error_group = parser.add_argument_group('Error Generation Options')
    error_group.add_argument(
        "--error-rate", "-e",
        type=float,
        default=0.05,
        help="Overall error generation probability (0-1, default: 0.05)"
    )
    
    error_group.add_argument(
        "--warning-rate", "-w",
        type=float,
        default=0.15,
        help="Warning generation probability (0-1, default: 0.15)"
    )
    
    error_group.add_argument(
        "--critical-rate", "-C",
        type=float,
        default=0.01,
        help="Critical error generation probability (0-1, default: 0.01)"
    )
    
    error_group.add_argument(
        "--interval", "-i",
        type=float,
        default=2.0,
        help="Error generation interval in seconds (default: 2.0)"
    )
    
    # Service configuration
    service_group = parser.add_argument_group('Service Options')
    service_group.add_argument(
        "--services",
        nargs="+",
        default=["UserService", "PaymentService", "DataProcessingService", "AuthService"],
        help="Services to enable (default: all services)"
    )
    
    service_group.add_argument(
        "--service-error-rates",
        nargs="+",
        metavar="SERVICE:RATE",
        help="Set error rates for specific services (e.g., UserService:0.1 PaymentService:0.05)"
    )
    
    # Error type configuration
    error_type_group = parser.add_argument_group('Error Type Options')
    error_type_group.add_argument(
        "--error-types",
        nargs="+",
        help="Specific error types to enable (default: all error types)"
    )
    
    error_type_group.add_argument(
        "--error-type-rates",
        nargs="+",
        metavar="ERROR:RATE",
        help="Set probabilities for specific error types (e.g., NameError:0.3 KeyError:0.2)"
    )
    
    return parser


def initialize_services(config: TestConfig, logger):
    """Initialize service instances."""
    services = {}
    
    # Create service loggers
    service_loggers = {
        "UserService": create_logger("UserService", config.log_file),
        "PaymentService": create_logger("PaymentService", config.log_file),
        "DataProcessingService": create_logger("DataProcessingService", config.log_file),
        "AuthService": create_logger("AuthService", config.log_file)
    }
    
    # Initialize enabled services
    if "UserService" in config.services_enabled:
        services["UserService"] = UserService("UserService", service_loggers["UserService"], config.error_probability, config)
        logger.log_info("Initialized UserService")
    
    if "PaymentService" in config.services_enabled:
        services["PaymentService"] = PaymentService("PaymentService", service_loggers["PaymentService"], config.error_probability, config)
        logger.log_info("Initialized PaymentService")
    
    if "DataProcessingService" in config.services_enabled:
        services["DataProcessingService"] = DataProcessingService("DataProcessingService", service_loggers["DataProcessingService"], config.error_probability, config)
        logger.log_info("Initialized DataProcessingService")
    
    if "AuthService" in config.services_enabled:
        services["AuthService"] = AuthService("AuthService", service_loggers["AuthService"], config.error_probability, config)
        logger.log_info("Initialized AuthService")
    
    return services


# This function is now handled by the TestProductApplication class
# and has been replaced by the _run_console_mode method


def load_config_from_file(file_path: str) -> TestConfig:
    """Load configuration from a file."""
    import json
    import yaml
    
    config = TestConfig()
    
    try:
        file_path = Path(file_path)
        if not file_path.exists():
            print(f"Config file not found: {file_path}")
            return config
        
        if file_path.suffix.lower() in ['.yaml', '.yml']:
            # Load YAML config
            try:
                import yaml
                with open(file_path, 'r') as f:
                    config_data = yaml.safe_load(f)
            except ImportError:
                print("YAML support requires PyYAML. Install with: pip install pyyaml")
                return config
        elif file_path.suffix.lower() == '.json':
            # Load JSON config
            with open(file_path, 'r') as f:
                config_data = json.load(f)
        else:
            print(f"Unsupported config file format: {file_path.suffix}")
            return config
        
        # Update config with file values
        for key, value in config_data.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        return config
    except Exception as e:
        print(f"Error loading config file: {e}")
        return config


def parse_key_value_pairs(pairs_list, default_dict=None):
    """Parse a list of key:value pairs into a dictionary."""
    if not pairs_list:
        return default_dict or {}
    
    result = default_dict.copy() if default_dict else {}
    
    for pair in pairs_list:
        try:
            key, value = pair.split(':')
            result[key.strip()] = float(value.strip())
        except ValueError:
            print(f"Warning: Invalid format for key-value pair: {pair}. Expected format: key:value")
    
    return result


class TestProductApplication:
    """
    Main application class that manages the lifecycle of the test product application.
    
    This class is responsible for:
    1. Initializing all components of the application
    2. Managing the application lifecycle
    3. Handling signals for graceful shutdown
    4. Providing clean termination of all resources
    """
    
    def __init__(self, config: TestConfig, error_config: ErrorConfig, logger: StructuredLogger):
        """
        Initialize the application with the given configuration.
        
        Args:
            config: Application configuration
            error_config: Error generation configuration
            logger: Application logger
        """
        self.config = config
        self.error_config = error_config
        self.logger = logger
        self.services = {}
        self.error_engine = None
        self.api = None
        self.app = None
        self.uvicorn_server = None
        self.running = False
        self.shutdown_event = threading.Event()
        self.start_time = time.time()
        
        # Signal handlers will be registered during startup
        self.original_sigint_handler = None
        self.original_sigterm_handler = None
    
    def initialize(self) -> bool:
        """
        Initialize all components of the application.
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        try:
            self.logger.log_info("Initializing Test Product Application", {
                "host": self.config.host,
                "port": self.config.port,
                "error_rate": self.config.error_probability,
                "warning_rate": self.config.warning_probability,
                "critical_rate": self.config.critical_probability,
                "services": self.config.services_enabled,
                "log_file": self.config.log_file,
                "log_level": self.config.log_level
            })
            
            # Initialize services
            self.services = initialize_services(self.config, self.logger)
            
            if not self.services:
                self.logger.log_warning("No services were enabled", {
                    "configured_services": self.config.services_enabled
                })
                print("Warning: No services were enabled. Check your configuration.")
                return False
            
            # Initialize error generation engine
            self.error_engine = ErrorGenerationEngine(
                self.services, 
                self.config, 
                self.error_config, 
                self.logger
            )
            
            self.logger.log_info("Test Product Application initialized successfully")
            return True
            
        except Exception as e:
            self.logger.log_critical(e, {"operation": "application_initialization"})
            print(f"Application initialization failed: {e}")
            return False
    
    def start(self, no_api: bool = False) -> bool:
        """
        Start the application.
        
        Args:
            no_api: Whether to run in console mode without API server
            
        Returns:
            bool: True if startup was successful, False otherwise
        """
        if self.running:
            self.logger.log_warning("Application is already running", {
                "operation": "application_start"
            })
            return True
        
        try:
            # Register signal handlers
            self._register_signal_handlers()
            
            # Start error generation
            self.logger.log_info("Starting error generation engine")
            self.error_engine.start_scheduled_generation()
            print(f"Error generation engine started with interval: {self.config.generation_interval}s")
            
            self.running = True
            
            if no_api:
                # Run in console mode
                print("Running in console mode. Press Ctrl+C to exit.")
                self._run_console_mode()
            else:
                # Initialize and start FastAPI application
                self._start_api_server()
            
            return True
            
        except Exception as e:
            self.logger.log_critical(e, {"operation": "application_start"})
            print(f"Application startup failed: {e}")
            self._restore_signal_handlers()
            return False
    
    def _start_api_server(self) -> None:
        """Start the FastAPI server."""
        # Initialize FastAPI application
        self.api = TestProductAPI(self.config, self.logger, self.error_engine)
        self.app = self.api.get_app()
        
        # Start FastAPI server
        self.logger.log_info("Starting FastAPI server", {
            "host": self.config.host,
            "port": self.config.port
        })
        print(f"Starting FastAPI server on http://{self.config.host}:{self.config.port}")
        print(f"API documentation available at http://{self.config.host}:{self.config.port}/docs")
        
        # Run the server with graceful shutdown support
        uvicorn.run(
            self.app, 
            host=self.config.host, 
            port=self.config.port,
            log_level="error"  # Use our own logging system
        )
    
    def _run_console_mode(self) -> None:
        """Run the application in console mode."""
        self.logger.log_info("Running in console mode (no API server)")
        
        try:
            while not self.shutdown_event.is_set():
                # Sleep for a while, checking for shutdown periodically
                self.shutdown_event.wait(10)
                
                # Log statistics periodically
                if not self.shutdown_event.is_set():
                    stats = self.error_engine.get_error_generation_stats()
                    self.logger.log_info("Error generation statistics", stats)
                    if self.config.debug:
                        print(f"Errors generated: {stats['total_errors_generated']} "
                              f"(~{stats['errors_per_minute']:.1f}/min)")
        except KeyboardInterrupt:
            # This should be caught by signal handler, but just in case
            self.shutdown()
    
    def get_app(self):
        """
        Get the FastAPI application instance.
        
        This method is useful for ASGI servers or testing.
        
        Returns:
            FastAPI application instance or None if not initialized
        """
        if not self.api:
            return None
        
        return self.api.get_app()
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current application status.
        
        Returns:
            Dict containing application status information
        """
        status = {
            "running": self.running,
            "uptime_seconds": time.time() - self.start_time,
            "services_count": len(self.services),
            "services": list(self.services.keys()),
            "error_engine_running": self.error_engine.running if self.error_engine else False,
            "api_initialized": self.api is not None
        }
        
        # Add error generation stats if available
        if self.error_engine:
            status["error_stats"] = self.error_engine.get_error_generation_stats()
        
        return status
    
    def shutdown(self) -> None:
        """
        Perform a graceful shutdown of the application.
        
        This method ensures all resources are properly released and
        background tasks are terminated.
        """
        if not self.running:
            return
        
        self.logger.log_info("Shutting down Test Product Application", {
            "uptime_seconds": time.time() - self.start_time
        })
        print("\nShutting down Test Product Application...")
        
        # Signal shutdown to all components
        self.shutdown_event.set()
        
        # Stop error generation engine
        if self.error_engine and self.error_engine.running:
            print("Stopping error generation engine...")
            self.error_engine.stop_scheduled_generation()
            self.logger.log_info("Error generation engine stopped")
        
        # Stop API server if running
        if self.api:
            print("Stopping API server...")
            # The API server should handle its own shutdown via FastAPI lifecycle events
        
        # Restore original signal handlers
        self._restore_signal_handlers()
        
        self.running = False
        self.logger.log_info("Application shutdown complete")
        print("Application shutdown complete")
    
    def _register_signal_handlers(self) -> None:
        """Register signal handlers for graceful shutdown."""
        # Save original handlers
        self.original_sigint_handler = signal.getsignal(signal.SIGINT)
        self.original_sigterm_handler = signal.getsignal(signal.SIGTERM)
        
        # Register new handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.log_info("Registered signal handlers for graceful shutdown")
    
    def _restore_signal_handlers(self) -> None:
        """Restore original signal handlers."""
        if self.original_sigint_handler:
            signal.signal(signal.SIGINT, self.original_sigint_handler)
        
        if self.original_sigterm_handler:
            signal.signal(signal.SIGTERM, self.original_sigterm_handler)
    
    def _signal_handler(self, sig, frame) -> None:
        """
        Handle termination signals.
        
        Args:
            sig: Signal number
            frame: Current stack frame
        """
        signal_name = "SIGINT" if sig == signal.SIGINT else "SIGTERM"
        self.logger.log_info(f"Received {signal_name} signal, initiating graceful shutdown")
        print(f"\nReceived {signal_name} signal, initiating graceful shutdown...")
        self.shutdown()


def main():
    """Main application entry point."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Create configuration
    if args.config:
        config = load_config_from_file(args.config)
    else:
        config = TestConfig.from_env()
    
    # Override config with command line arguments
    config.log_file = args.log_file
    config.log_level = args.log_level
    config.port = args.port
    config.host = args.host
    config.error_probability = args.error_rate
    config.warning_probability = args.warning_rate
    config.critical_probability = args.critical_rate
    config.generation_interval = args.interval
    config.services_enabled = args.services
    config.debug = args.debug
    
    # Create error configuration
    error_config = ErrorConfig()
    
    # Process service-specific error rates if provided
    if args.service_error_rates:
        service_rates = parse_key_value_pairs(args.service_error_rates, error_config.get_service_error_rates())
        for service, rate in service_rates.items():
            attr_name = f"{service.lower()}_error_rate"
            if hasattr(error_config, attr_name):
                setattr(error_config, attr_name, rate)
    
    # Process error type rates if provided
    if args.error_type_rates:
        error_type_rates = parse_key_value_pairs(args.error_type_rates, error_config.get_error_type_probabilities())
        for error_type, rate in error_type_rates.items():
            attr_name = f"{error_type.lower()}_probability"
            if hasattr(error_config, attr_name):
                setattr(error_config, attr_name, rate)
    
    # Filter error types if specified
    if args.error_types:
        # Create a new dictionary with only the specified error types
        error_types = error_config.get_error_type_probabilities()
        filtered_types = {k: v for k, v in error_types.items() if k in args.error_types}
        
        # Normalize probabilities
        if filtered_types:
            total = sum(filtered_types.values())
            if total > 0:
                for error_type in filtered_types:
                    attr_name = f"{error_type.lower()}_probability"
                    if hasattr(error_config, attr_name):
                        # Normalize but keep relative weights
                        setattr(error_config, attr_name, getattr(error_config, attr_name) / total)
            
            # Set non-selected error types to 0
            for error_type in error_types:
                if error_type not in filtered_types:
                    attr_name = f"{error_type.lower()}_probability"
                    if hasattr(error_config, attr_name):
                        setattr(error_config, attr_name, 0.0)
    
    # Ensure log directory exists
    config.ensure_log_directory()
    
    # Create main application logger
    logger = create_logger("TestProductApp", config.log_file)
    
    # Print startup information
    print(f"Test Product Application starting...")
    print(f"Host: {config.host}")
    print(f"Port: {config.port}")
    print(f"Log file: {config.log_file}")
    print(f"Log level: {config.log_level}")
    print(f"Error rate: {config.error_probability}")
    print(f"Warning rate: {config.warning_probability}")
    print(f"Critical rate: {config.critical_probability}")
    print(f"Error generation interval: {config.generation_interval}s")
    print(f"Services: {', '.join(config.services_enabled)}")
    
    if config.debug:
        print("\nService-specific error rates:")
        for service, rate in error_config.get_service_error_rates().items():
            print(f"  {service}: {rate}")
        
        print("\nError type probabilities:")
        for error_type, prob in error_config.get_error_type_probabilities().items():
            if prob > 0:  # Only show enabled error types
                print(f"  {error_type}: {prob}")
    
    print(f"Debug mode: {config.debug}")
    print(f"API server: {'Disabled' if args.no_api else 'Enabled'}")
    
    # Create and start the application
    app = TestProductApplication(config, error_config, logger)
    
    try:
        # Initialize the application
        if not app.initialize():
            logger.log_critical(Exception("Application initialization failed"), {
                "operation": "main"
            })
            return 1
        
        # Start the application
        app.start(no_api=args.no_api)
        
    except KeyboardInterrupt:
        # This should be caught by the signal handler, but just in case
        logger.log_info("Application shutdown requested by user")
        print("\nApplication shutdown requested by user")
        app.shutdown()
    except Exception as e:
        logger.log_critical(e, {"operation": "main"})
        print(f"Application startup failed: {e}")
        return 1
    
    return 0


def run_application():
    """
    Run the application as a module.
    
    This function is the entry point when running the application as a module:
    python -m test_product
    """
    return main()


if __name__ == "__main__":
    sys.exit(main())