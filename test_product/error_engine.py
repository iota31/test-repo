"""
Error generation engine for the test product application.

This module provides the ErrorGenerationEngine class that manages scheduled and
on-demand error generation across all services in the test product.
"""

import asyncio
import random
import time
import threading
from typing import Dict, List, Any, Optional, Callable, Type, Union
import logging

from .config import TestConfig, ErrorConfig
from .logging_system import StructuredLogger
from .services.base_service import BaseService
from .scheduled_error_generator import ScheduledErrorGenerator


class ErrorGenerationEngine:
    """
    Manages scheduled and on-demand error generation across services.
    
    This class is responsible for:
    1. Scheduling background tasks for continuous error generation
    2. Managing error type and probability distributions
    3. Providing on-demand error triggering capabilities
    4. Tracking error generation statistics
    """
    
    def __init__(self, services: Dict[str, BaseService], config: TestConfig, 
                 error_config: Optional[ErrorConfig] = None, 
                 logger: Optional[StructuredLogger] = None):
        """
        Initialize the error generation engine.
        
        Args:
            services: Dictionary mapping service names to service instances
            config: Test configuration instance
            error_config: Optional error configuration instance
            logger: Optional structured logger instance
        """
        self.services = services
        self.config = config
        self.error_config = error_config or ErrorConfig()
        self.logger = logger
        
        # Background task management
        self.running = False
        self.scheduler_thread = None
        self.generation_interval = config.generation_interval
        
        # Create scheduled error generator
        self.scheduled_generator = ScheduledErrorGenerator(
            services=services,
            config=config,
            error_config=self.error_config,
            logger=logger
        )
        
        # Error generation statistics
        self.stats = {
            "total_errors_generated": 0,
            "errors_by_service": {},
            "errors_by_type": {},
            "last_error_time": None,
            "generation_start_time": None
        }
        
        # Initialize statistics for each service
        for service_name in services:
            self.stats["errors_by_service"][service_name] = 0
        
        # Initialize statistics for each error type
        for error_type in self.error_config.get_error_type_probabilities():
            self.stats["errors_by_type"][error_type] = 0
    
    def start_scheduled_generation(self) -> None:
        """
        Start the background error generation scheduler.
        
        This method launches a background thread that periodically triggers
        errors across the registered services based on configured probabilities.
        """
        if self.running:
            if self.logger:
                self.logger.log_warning("Error generation scheduler is already running", {
                    "component": "ErrorGenerationEngine",
                    "operation": "start_scheduled_generation"
                })
            return
        
        self.running = True
        self.stats["generation_start_time"] = time.time()
        
        if self.logger:
            self.logger.log_info("Starting scheduled error generation", {
                "component": "ErrorGenerationEngine",
                "interval": self.generation_interval,
                "services": list(self.services.keys()),
                "error_probability": self.config.error_probability
            })
        
        # Use the scheduled error generator
        self.scheduled_generator.set_pattern("random")  # Default to random pattern
        self.scheduled_generator.set_base_interval(self.generation_interval)
        self.scheduled_generator.start()
        
        # Also start the legacy error generation for backward compatibility
        # Create and start the scheduler thread
        self.scheduler_thread = threading.Thread(
            target=self._error_generation_loop,
            daemon=True,
            name="ErrorGenerationThread"
        )
        self.scheduler_thread.start()
    
    def stop_scheduled_generation(self) -> None:
        """Stop the background error generation scheduler."""
        if not self.running:
            if self.logger:
                self.logger.log_warning("Error generation scheduler is not running", {
                    "component": "ErrorGenerationEngine",
                    "operation": "stop_scheduled_generation"
                })
            return
        
        self.running = False
        
        # Stop the scheduled error generator
        self.scheduled_generator.stop()
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=2.0)
        
        if self.logger:
            self.logger.log_info("Stopped scheduled error generation", {
                "component": "ErrorGenerationEngine",
                "total_errors": self.stats["total_errors_generated"],
                "runtime_seconds": time.time() - (self.stats["generation_start_time"] or time.time())
            })
    
    def _error_generation_loop(self) -> None:
        """
        Background loop for scheduled error generation.
        
        This method runs in a separate thread and periodically triggers
        errors across services based on configured probabilities.
        """
        while self.running:
            try:
                # Generate errors across services
                self._generate_random_errors()
                
                # Sleep for the configured interval
                time.sleep(self.generation_interval)
                
            except Exception as e:
                if self.logger:
                    self.logger.log_error(e, {
                        "component": "ErrorGenerationEngine",
                        "operation": "error_generation_loop"
                    })
                # Sleep briefly to avoid tight loop in case of persistent errors
                time.sleep(1.0)
    
    def _generate_random_errors(self) -> None:
        """
        Generate random errors across services based on configured probabilities.
        
        This method selects a random service and operation based on the
        configured probabilities and triggers an error.
        """
        # Select a random service based on service error rates
        service_name = self._select_random_service()
        if not service_name or service_name not in self.services:
            return
        
        service = self.services[service_name]
        
        # Get available operations for the selected service
        operations = service.get_available_operations()
        if not operations:
            return
        
        # Select a random operation
        operation = random.choice(operations)
        
        # Trigger the error
        try:
            self._trigger_service_operation(service_name, operation)
            
            # Update statistics
            self.stats["total_errors_generated"] += 1
            self.stats["errors_by_service"][service_name] = self.stats["errors_by_service"].get(service_name, 0) + 1
            self.stats["last_error_time"] = time.time()
            
            # Try to determine error type from the exception
            error_type = None
            try:
                # This will intentionally fail with an exception that we can capture
                result = getattr(service, operation)(*[], **{})
            except Exception as e:
                error_type = type(e).__name__
                if error_type in self.stats["errors_by_type"]:
                    self.stats["errors_by_type"][error_type] += 1
            
            if self.logger:
                self.logger.log_info(f"Generated error in {service_name}.{operation}", {
                    "component": "ErrorGenerationEngine",
                    "service": service_name,
                    "operation": operation,
                    "error_type": error_type,
                    "total_errors": self.stats["total_errors_generated"]
                })
                
        except Exception as e:
            if self.logger:
                self.logger.log_error(e, {
                    "component": "ErrorGenerationEngine",
                    "operation": "generate_random_errors",
                    "service": service_name,
                    "attempted_operation": operation
                })
    
    def _select_random_service(self) -> Optional[str]:
        """
        Select a random service based on configured error rates.
        
        Returns:
            str: Selected service name or None if no service is selected
        """
        # Get service error rates from configuration
        service_rates = self.error_config.get_service_error_rates()
        
        # Filter to only include enabled services
        enabled_services = {
            name: rate for name, rate in service_rates.items() 
            if name in self.services and name in self.config.services_enabled
        }
        
        if not enabled_services:
            return None
        
        # Select a service based on weighted probabilities
        services = list(enabled_services.keys())
        weights = list(enabled_services.values())
        
        return random.choices(services, weights=weights, k=1)[0]
    
    def trigger_specific_error(self, service_name: str, operation: str, 
                             error_type: str = None, parameters: Dict[str, Any] = None) -> bool:
        """
        Trigger a specific error in a service on demand.
        
        Args:
            service_name: Name of the service to trigger an error in
            operation: Name of the operation to trigger
            error_type: Optional specific error type to trigger
            parameters: Optional parameters for the operation
            
        Returns:
            bool: True if the error was triggered successfully, False otherwise
        """
        if service_name not in self.services:
            if self.logger:
                self.logger.log_warning(f"Service {service_name} not found", {
                    "component": "ErrorGenerationEngine",
                    "operation": "trigger_specific_error",
                    "available_services": list(self.services.keys())
                })
            return False
        
        service = self.services[service_name]
        
        if operation not in service.get_available_operations():
            if self.logger:
                self.logger.log_warning(f"Operation {operation} not found in {service_name}", {
                    "component": "ErrorGenerationEngine",
                    "operation": "trigger_specific_error",
                    "service": service_name,
                    "available_operations": service.get_available_operations()
                })
            return False
        
        try:
            # Force error probability to ensure error is triggered
            original_probability = service.error_probability
            service.error_probability = 1.0
            
            # Trigger the operation with parameters if provided
            if parameters:
                result = self._trigger_service_operation(service_name, operation, parameters=parameters)
            else:
                result = self._trigger_service_operation(service_name, operation)
            
            # Restore original probability
            service.error_probability = original_probability
            
            # Update statistics
            self.stats["total_errors_generated"] += 1
            self.stats["errors_by_service"][service_name] = self.stats["errors_by_service"].get(service_name, 0) + 1
            self.stats["last_error_time"] = time.time()
            
            # Try to determine the error type
            actual_error_type = None
            try:
                # This will intentionally fail with an exception that we can capture
                if parameters:
                    getattr(service, operation)(**parameters)
                else:
                    getattr(service, operation)(*[], **{})
            except Exception as e:
                actual_error_type = type(e).__name__
                
                # Update error type statistics
                if actual_error_type in self.stats["errors_by_type"]:
                    self.stats["errors_by_type"][actual_error_type] += 1
                else:
                    self.stats["errors_by_type"][actual_error_type] = 1
            
            # Log with error type information
            if self.logger:
                log_context = {
                    "component": "ErrorGenerationEngine",
                    "service": service_name,
                    "operation": operation,
                    "total_errors": self.stats["total_errors_generated"],
                    "on_demand": True,
                    "actual_error_type": actual_error_type
                }
                
                if error_type:
                    log_context["requested_error_type"] = error_type
                    
                    if actual_error_type and error_type != actual_error_type:
                        self.logger.log_warning(
                            f"Requested error type '{error_type}' but got '{actual_error_type}' in {service_name}.{operation}",
                            log_context
                        )
                    else:
                        self.logger.log_info(
                            f"Triggered specific error in {service_name}.{operation}",
                            log_context
                        )
                else:
                    self.logger.log_info(
                        f"Triggered specific error in {service_name}.{operation}",
                        log_context
                    )
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.log_error(e, {
                    "component": "ErrorGenerationEngine",
                    "operation": "trigger_specific_error",
                    "service": service_name,
                    "attempted_operation": operation,
                    "requested_error_type": error_type if error_type else None
                })
            return False
    
    def _trigger_service_operation(self, service_name: str, operation: str, parameters: Dict[str, Any] = None) -> Any:
        """
        Trigger a specific operation on a service.
        
        Args:
            service_name: Name of the service
            operation: Name of the operation to trigger
            parameters: Optional custom parameters for the operation
            
        Returns:
            Any: Result of the operation
            
        Raises:
            AttributeError: If the operation doesn't exist on the service
            Exception: Any exception raised by the operation
        """
        service = self.services[service_name]
        
        # Get the operation method
        operation_method = getattr(service, operation)
        
        if parameters:
            # Use provided parameters
            return operation_method(**parameters)
        else:
            # Prepare mock arguments based on the operation
            args, kwargs = self._prepare_mock_arguments(service_name, operation)
            
            # Call the operation with mock arguments
            return operation_method(*args, **kwargs)
    
    def _prepare_mock_arguments(self, service_name: str, operation: str) -> tuple:
        """
        Prepare mock arguments for a service operation.
        
        Args:
            service_name: Name of the service
            operation: Name of the operation
            
        Returns:
            tuple: (args, kwargs) to pass to the operation
        """
        # Define mock arguments for known operations
        mock_args = {
            "UserService": {
                "authenticate_user": ([], {"username": "test_user", "password": "password123"}),
                "get_user_profile": ([], {"user_id": "user123"}),
                "update_user_data": ([], {"user_id": "user123", "updates": {"email": "new@example.com"}})
            },
            "PaymentService": {
                "process_payment": ([], {"amount": 100.0, "payment_method": "credit_card"}),
                "calculate_tax": ([], {"amount": 100.0, "tax_rate": 0.1}),
                "validate_card": ([], {"card_number": "4111111111111111", "expiry": "12/25"})
            },
            "DataProcessingService": {
                "process_batch": ([], {"batch_id": "batch123", "items": ["item1", "item2"]}),
                "transform_data": ([], {"data": {"key": "value"}, "format": "json"}),
                "aggregate_results": ([], {"results": [1, 2, 3, 4, 5]})
            },
            "AuthService": {
                "generate_token": ([], {"user_id": "user123", "scopes": ["read", "write"]}),
                "validate_permissions": ([], {"token": "test_token", "required_permission": "admin"}),
                "refresh_session": ([], {"session_id": "session123"})
            }
        }
        
        # Return default empty arguments if not found
        if service_name not in mock_args or operation not in mock_args.get(service_name, {}):
            return [], {}
        
        return mock_args[service_name][operation]
    
    def update_error_probabilities(self, service_probabilities: Dict[str, float] = None,
                                 error_type_probabilities: Dict[str, float] = None) -> None:
        """
        Update error probabilities for services and error types.
        
        Args:
            service_probabilities: Dictionary mapping service names to error probabilities
            error_type_probabilities: Dictionary mapping error types to probabilities
        """
        # Update service error probabilities
        if service_probabilities:
            for service_name, probability in service_probabilities.items():
                if service_name in self.services:
                    self.services[service_name].update_error_probability(probability)
                    
                    if self.logger:
                        self.logger.log_info(f"Updated error probability for {service_name}", {
                            "component": "ErrorGenerationEngine",
                            "operation": "update_error_probabilities",
                            "service": service_name,
                            "new_probability": probability
                        })
        
        # Update error type probabilities in error config
        if error_type_probabilities and hasattr(self.error_config, "__dict__"):
            for error_type, probability in error_type_probabilities.items():
                attr_name = f"{error_type.lower()}_probability"
                if hasattr(self.error_config, attr_name):
                    setattr(self.error_config, attr_name, probability)
                    
                    if self.logger:
                        self.logger.log_info(f"Updated probability for {error_type}", {
                            "component": "ErrorGenerationEngine",
                            "operation": "update_error_probabilities",
                            "error_type": error_type,
                            "new_probability": probability
                        })
    
    def get_error_generation_stats(self) -> Dict[str, Any]:
        """
        Get error generation statistics.
        
        Returns:
            Dict containing error generation statistics
        """
        # Calculate runtime
        runtime = 0
        if self.stats["generation_start_time"]:
            runtime = time.time() - self.stats["generation_start_time"]
        
        # Calculate errors per minute
        errors_per_minute = 0
        if runtime > 0:
            errors_per_minute = (self.stats["total_errors_generated"] * 60) / runtime
        
        # Get scheduled generator stats
        scheduled_stats = self.scheduled_generator.get_stats()
        
        # Combine stats
        combined_stats = {
            "total_errors_generated": self.stats["total_errors_generated"] + scheduled_stats["total_errors_generated"],
            "errors_by_service": self._combine_dicts(self.stats["errors_by_service"], scheduled_stats["errors_by_service"]),
            "errors_by_type": self._combine_dicts(self.stats["errors_by_type"], scheduled_stats["errors_by_type"]),
            "last_error_time": max(filter(None, [self.stats["last_error_time"], scheduled_stats["last_error_time"]])) if any(filter(None, [self.stats["last_error_time"], scheduled_stats["last_error_time"]])) else None,
            "generation_start_time": self.stats["generation_start_time"],
            "runtime_seconds": runtime,
            "errors_per_minute": errors_per_minute,
            "is_running": self.running,
            "generation_interval": self.generation_interval,
            "scheduled_generator": {
                "pattern_type": scheduled_stats["pattern_type"],
                "errors_by_pattern": scheduled_stats["errors_by_pattern"],
                "bursts_triggered": scheduled_stats["bursts_triggered"],
                "total_burst_errors": scheduled_stats["total_burst_errors"]
            }
        }
        
        return combined_stats
        
    def _combine_dicts(self, dict1: Dict, dict2: Dict) -> Dict:
        """
        Combine two dictionaries by adding values for matching keys.
        
        Args:
            dict1: First dictionary
            dict2: Second dictionary
            
        Returns:
            Dict: Combined dictionary
        """
        result = dict1.copy()
        for key, value in dict2.items():
            if key in result:
                result[key] += value
            else:
                result[key] = value
        return result
    
    def reset_stats(self) -> None:
        """Reset error generation statistics."""
        self.stats = {
            "total_errors_generated": 0,
            "errors_by_service": {service: 0 for service in self.services},
            "errors_by_type": {error_type: 0 for error_type in self.error_config.get_error_type_probabilities()},
            "last_error_time": None,
            "generation_start_time": self.stats["generation_start_time"]
        }
        
        # Reset scheduled generator stats
        self.scheduled_generator.reset_stats()
        
        if self.logger:
            self.logger.log_info("Reset error generation statistics", {
                "component": "ErrorGenerationEngine",
                "operation": "reset_stats"
            })
    
    def update_generation_interval(self, interval: float) -> None:
        """
        Update the error generation interval.
        
        Args:
            interval: New interval in seconds
        """
        if interval <= 0:
            if self.logger:
                self.logger.log_warning("Invalid generation interval", {
                    "component": "ErrorGenerationEngine",
                    "operation": "update_generation_interval",
                    "attempted_interval": interval
                })
            return
        
        old_interval = self.generation_interval
        self.generation_interval = interval
        
        # Update scheduled generator interval
        self.scheduled_generator.set_base_interval(interval)
        
        if self.logger:
            self.logger.log_info(f"Updated error generation interval", {
                "component": "ErrorGenerationEngine",
                "operation": "update_generation_interval",
                "old_interval": old_interval,
                "new_interval": interval
            })
    
    def set_error_pattern(self, pattern: str) -> bool:
        """
        Set the error generation pattern.
        
        Args:
            pattern: Pattern type ("random", "burst", "periodic", "wave")
            
        Returns:
            bool: True if pattern was set successfully
        """
        return self.scheduled_generator.set_pattern(pattern)
    
    def configure_time_patterns(self, enabled: bool, peak_hours: List[tuple] = None) -> None:
        """
        Configure time-based error patterns.
        
        Args:
            enabled: Whether time-based patterns should be enabled
            peak_hours: Optional list of (start_hour, end_hour) tuples in 24-hour format
        """
        self.scheduled_generator.set_time_patterns(enabled)
        
        if peak_hours:
            self.scheduled_generator.configure_peak_hours(peak_hours)
            
        if self.logger:
            self.logger.log_info(f"Configured time-based error patterns", {
                "component": "ErrorGenerationEngine",
                "operation": "configure_time_patterns",
                "enabled": enabled,
                "peak_hours": peak_hours if peak_hours else "default"
            })