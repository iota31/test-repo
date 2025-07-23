"""
Scheduled error generation for the test product application.

This module provides the ScheduledErrorGenerator class that manages
scheduled error generation with configurable intervals and patterns.
"""

import asyncio
import random
import time
import threading
import math
from typing import Dict, List, Any, Optional, Callable, Type, Union
import logging
from datetime import datetime, timedelta

from .config import TestConfig, ErrorConfig
from .logging_system import StructuredLogger
from .services.base_service import BaseService


class ScheduledErrorGenerator:
    """
    Manages scheduled error generation with configurable patterns.
    
    This class is responsible for:
    1. Scheduling errors at configurable intervals
    2. Implementing realistic error timing patterns
    3. Distributing errors across services based on configured weights
    4. Tracking and reporting error generation statistics
    """
    
    def __init__(self, services: Dict[str, BaseService], config: TestConfig, 
                 error_config: Optional[ErrorConfig] = None, 
                 logger: Optional[StructuredLogger] = None):
        """
        Initialize the scheduled error generator.
        
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
        self.base_interval = config.generation_interval
        
        # Error timing pattern configuration
        self.pattern_type = "random"  # Options: "random", "burst", "periodic", "wave"
        self.burst_probability = 0.2  # Probability of triggering a burst of errors
        self.burst_size_range = (3, 8)  # Min/max errors in a burst
        self.burst_interval = 0.2  # Time between errors in a burst (seconds)
        self.wave_period = 60.0  # Period of the wave pattern (seconds)
        self.wave_amplitude = 0.5  # Amplitude of the wave pattern
        
        # Time-based patterns
        self.time_patterns_enabled = True
        self.peak_hours = [(9, 12), (14, 17)]  # Peak error hours (24-hour format)
        self.weekend_reduction = 0.5  # Reduction factor for weekends
        self.night_reduction = 0.7  # Reduction factor for night hours (22:00-06:00)
        
        # Error generation statistics
        self.stats = {
            "total_errors_generated": 0,
            "errors_by_service": {},
            "errors_by_type": {},
            "errors_by_pattern": {
                "random": 0,
                "burst": 0,
                "periodic": 0,
                "wave": 0
            },
            "last_error_time": None,
            "generation_start_time": None,
            "bursts_triggered": 0,
            "total_burst_errors": 0
        }
        
        # Initialize statistics for each service
        for service_name in services:
            self.stats["errors_by_service"][service_name] = 0
        
        # Initialize statistics for each error type
        for error_type in self.error_config.get_error_type_probabilities():
            self.stats["errors_by_type"][error_type] = 0
    
    def start(self) -> None:
        """
        Start the scheduled error generation.
        
        This method launches a background thread that generates errors
        according to the configured timing patterns.
        """
        if self.running:
            if self.logger:
                self.logger.log_warning("Scheduled error generator is already running", {
                    "component": "ScheduledErrorGenerator",
                    "operation": "start"
                })
            return
        
        self.running = True
        self.stats["generation_start_time"] = time.time()
        
        if self.logger:
            self.logger.log_info("Starting scheduled error generation", {
                "component": "ScheduledErrorGenerator",
                "base_interval": self.base_interval,
                "pattern_type": self.pattern_type,
                "services": list(self.services.keys()),
                "time_patterns_enabled": self.time_patterns_enabled
            })
        
        # Create and start the scheduler thread
        self.scheduler_thread = threading.Thread(
            target=self._error_generation_loop,
            daemon=True,
            name="ScheduledErrorGeneratorThread"
        )
        self.scheduler_thread.start()
    
    def stop(self) -> None:
        """Stop the scheduled error generation."""
        if not self.running:
            if self.logger:
                self.logger.log_warning("Scheduled error generator is not running", {
                    "component": "ScheduledErrorGenerator",
                    "operation": "stop"
                })
            return
        
        self.running = False
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=2.0)
        
        if self.logger:
            self.logger.log_info("Stopped scheduled error generation", {
                "component": "ScheduledErrorGenerator",
                "total_errors": self.stats["total_errors_generated"],
                "runtime_seconds": time.time() - (self.stats["generation_start_time"] or time.time()),
                "bursts_triggered": self.stats["bursts_triggered"]
            })
    
    def _error_generation_loop(self) -> None:
        """
        Background loop for scheduled error generation.
        
        This method runs in a separate thread and generates errors
        according to the configured timing patterns.
        """
        while self.running:
            try:
                # Determine the current pattern to use
                current_pattern = self._select_pattern()
                
                # Generate errors based on the selected pattern
                if current_pattern == "burst":
                    self._generate_error_burst()
                elif current_pattern == "wave":
                    self._generate_wave_pattern_error()
                else:  # random or periodic
                    self._generate_single_error()
                
                # Calculate next interval based on pattern and time factors
                next_interval = self._calculate_next_interval(current_pattern)
                
                # Sleep until next error generation
                time.sleep(next_interval)
                
            except Exception as e:
                if self.logger:
                    self.logger.log_error(e, {
                        "component": "ScheduledErrorGenerator",
                        "operation": "error_generation_loop"
                    })
                # Sleep briefly to avoid tight loop in case of persistent errors
                time.sleep(1.0)
    
    def _select_pattern(self) -> str:
        """
        Select the error generation pattern to use.
        
        Returns:
            str: Pattern type to use ("random", "burst", "periodic", "wave")
        """
        if self.pattern_type == "random":
            # Randomly select between patterns with burst having lower probability
            if random.random() < self.burst_probability:
                return "burst"
            elif random.random() < 0.3:
                return "wave"
            else:
                return "random"
        else:
            # Use the configured pattern
            return self.pattern_type
    
    def _generate_single_error(self) -> None:
        """Generate a single error in a randomly selected service."""
        # Select a service based on configured weights
        service_name = self._select_weighted_service()
        if not service_name:
            return
        
        # Get the service instance
        service = self.services.get(service_name)
        if not service:
            return
        
        # Get available operations for the service
        operations = service.get_available_operations()
        if not operations:
            return
        
        # Select a random operation
        operation = random.choice(operations)
        
        # Trigger the error
        try:
            self._trigger_service_operation(service_name, operation)
            
            # Update statistics
            self._update_error_stats(service_name, "random")
            
            if self.logger:
                self.logger.log_info(f"Generated error in {service_name}.{operation}", {
                    "component": "ScheduledErrorGenerator",
                    "pattern": "random",
                    "service": service_name,
                    "operation": operation,
                    "total_errors": self.stats["total_errors_generated"]
                })
                
        except Exception as e:
            if self.logger:
                self.logger.log_error(e, {
                    "component": "ScheduledErrorGenerator",
                    "operation": "generate_single_error",
                    "service": service_name,
                    "attempted_operation": operation
                })
    
    def _generate_error_burst(self) -> None:
        """
        Generate a burst of errors in rapid succession.
        
        This simulates a cascade of failures that often happen in real systems.
        """
        # Determine burst size
        burst_size = random.randint(*self.burst_size_range)
        
        # Select a primary service for the burst
        primary_service = self._select_weighted_service()
        if not primary_service:
            return
        
        # Track burst statistics
        burst_start_time = time.time()
        burst_errors_generated = 0
        
        if self.logger:
            self.logger.log_info(f"Starting error burst", {
                "component": "ScheduledErrorGenerator",
                "pattern": "burst",
                "burst_size": burst_size,
                "primary_service": primary_service
            })
        
        # Generate the burst of errors
        for i in range(burst_size):
            try:
                # For the first half of errors, use the primary service
                # For the second half, potentially use related services
                if i < burst_size / 2:
                    service_name = primary_service
                else:
                    # 70% chance to stay with primary service, 30% to switch
                    if random.random() < 0.7:
                        service_name = primary_service
                    else:
                        service_name = self._select_weighted_service()
                
                service = self.services.get(service_name)
                if not service:
                    continue
                
                # Get available operations
                operations = service.get_available_operations()
                if not operations:
                    continue
                
                # Select an operation
                operation = random.choice(operations)
                
                # Trigger the error
                self._trigger_service_operation(service_name, operation)
                
                # Update statistics
                self._update_error_stats(service_name, "burst")
                burst_errors_generated += 1
                
                # Sleep briefly between burst errors
                time.sleep(self.burst_interval)
                
            except Exception as e:
                if self.logger:
                    self.logger.log_error(e, {
                        "component": "ScheduledErrorGenerator",
                        "operation": "generate_error_burst",
                        "burst_index": i,
                        "burst_size": burst_size
                    })
        
        # Update burst statistics
        self.stats["bursts_triggered"] += 1
        self.stats["total_burst_errors"] += burst_errors_generated
        
        if self.logger:
            self.logger.log_info(f"Completed error burst", {
                "component": "ScheduledErrorGenerator",
                "pattern": "burst",
                "burst_size": burst_size,
                "errors_generated": burst_errors_generated,
                "duration_seconds": time.time() - burst_start_time,
                "total_bursts": self.stats["bursts_triggered"]
            })
    
    def _generate_wave_pattern_error(self) -> None:
        """
        Generate errors following a wave pattern.
        
        This creates a sinusoidal pattern of error frequency over time,
        simulating natural cycles in system load and error rates.
        """
        # Calculate current position in the wave
        if not self.stats["generation_start_time"]:
            return
        
        elapsed_time = time.time() - self.stats["generation_start_time"]
        wave_position = (elapsed_time % self.wave_period) / self.wave_period
        
        # Calculate probability multiplier based on wave position (0.5 to 1.5)
        # Using sine wave shifted to be positive: 0.5 + 0.5*sin(2π*position)
        probability_multiplier = 1.0 + self.wave_amplitude * (
            0.5 + 0.5 * math.sin(2 * math.pi * wave_position)
        )
        
        # Generate error with adjusted probability
        if random.random() < probability_multiplier * 0.8:  # Base chance * multiplier
            self._generate_single_error()
            
            # Update wave pattern statistics
            self.stats["errors_by_pattern"]["wave"] += 1
            
            if self.logger:
                self.logger.log_info(f"Generated wave pattern error", {
                    "component": "ScheduledErrorGenerator",
                    "pattern": "wave",
                    "wave_position": wave_position,
                    "probability_multiplier": probability_multiplier,
                    "total_wave_errors": self.stats["errors_by_pattern"]["wave"]
                })
    
    def _calculate_next_interval(self, pattern: str) -> float:
        """
        Calculate the next error generation interval based on pattern and time factors.
        
        Args:
            pattern: Current error generation pattern
            
        Returns:
            float: Next interval in seconds
        """
        base = self.base_interval
        
        # Apply pattern-specific adjustments
        if pattern == "burst":
            # Longer interval after a burst
            return base * random.uniform(1.5, 2.5)
        elif pattern == "wave":
            # Wave pattern has its own timing
            elapsed_time = time.time() - (self.stats["generation_start_time"] or time.time())
            wave_position = (elapsed_time % self.wave_period) / self.wave_period
            # More frequent at peak, less frequent at trough
            return base * (1.0 - 0.5 * math.sin(2 * math.pi * wave_position))
        
        # Apply time-based factors if enabled
        if self.time_patterns_enabled:
            # Get current time
            now = datetime.now()
            
            # Apply weekend reduction
            if now.weekday() >= 5:  # 5=Saturday, 6=Sunday
                base *= (1.0 + self.weekend_reduction)
            
            # Apply night reduction (10PM-6AM)
            hour = now.hour
            if hour < 6 or hour >= 22:
                base *= (1.0 + self.night_reduction)
            
            # Apply peak hour adjustment
            in_peak_hour = False
            for start_hour, end_hour in self.peak_hours:
                if start_hour <= hour < end_hour:
                    in_peak_hour = True
                    break
            
            if in_peak_hour:
                # More frequent errors during peak hours
                base *= 0.7
        
        # Add some randomness to avoid predictable patterns
        jitter = random.uniform(0.8, 1.2)
        return base * jitter
    
    def _select_weighted_service(self) -> Optional[str]:
        """
        Select a service based on configured error rates.
        
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
    
    def _trigger_service_operation(self, service_name: str, operation: str) -> Any:
        """
        Trigger a specific operation on a service.
        
        Args:
            service_name: Name of the service
            operation: Name of the operation to trigger
            
        Returns:
            Any: Result of the operation
            
        Raises:
            AttributeError: If the operation doesn't exist on the service
            Exception: Any exception raised by the operation
        """
        service = self.services[service_name]
        
        # Get the operation method
        operation_method = getattr(service, operation)
        
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
    
    def _update_error_stats(self, service_name: str, pattern: str) -> None:
        """
        Update error generation statistics.
        
        Args:
            service_name: Name of the service where error was generated
            pattern: Pattern used to generate the error
        """
        self.stats["total_errors_generated"] += 1
        self.stats["errors_by_service"][service_name] = self.stats["errors_by_service"].get(service_name, 0) + 1
        self.stats["errors_by_pattern"][pattern] = self.stats["errors_by_pattern"].get(pattern, 0) + 1
        self.stats["last_error_time"] = time.time()
        
        # Try to determine error type from the exception
        error_type = None
        try:
            # This will intentionally fail with an exception that we can capture
            service = self.services[service_name]
            operations = service.get_available_operations()
            if operations:
                operation = operations[0]
                result = getattr(service, operation)(*[], **{})
        except Exception as e:
            error_type = type(e).__name__
            if error_type in self.stats["errors_by_type"]:
                self.stats["errors_by_type"][error_type] += 1
    
    def get_stats(self) -> Dict[str, Any]:
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
        
        return {
            "total_errors_generated": self.stats["total_errors_generated"],
            "errors_by_service": self.stats["errors_by_service"],
            "errors_by_type": self.stats["errors_by_type"],
            "errors_by_pattern": self.stats["errors_by_pattern"],
            "last_error_time": self.stats["last_error_time"],
            "generation_start_time": self.stats["generation_start_time"],
            "runtime_seconds": runtime,
            "errors_per_minute": errors_per_minute,
            "is_running": self.running,
            "base_interval": self.base_interval,
            "pattern_type": self.pattern_type,
            "bursts_triggered": self.stats["bursts_triggered"],
            "total_burst_errors": self.stats["total_burst_errors"]
        }
    
    def set_pattern(self, pattern: str) -> bool:
        """
        Set the error generation pattern.
        
        Args:
            pattern: Pattern type ("random", "burst", "periodic", "wave")
            
        Returns:
            bool: True if pattern was set successfully
        """
        valid_patterns = ["random", "burst", "periodic", "wave"]
        if pattern not in valid_patterns:
            if self.logger:
                self.logger.log_warning(f"Invalid pattern type: {pattern}", {
                    "component": "ScheduledErrorGenerator",
                    "operation": "set_pattern",
                    "valid_patterns": valid_patterns
                })
            return False
        
        self.pattern_type = pattern
        
        if self.logger:
            self.logger.log_info(f"Set error generation pattern to {pattern}", {
                "component": "ScheduledErrorGenerator",
                "operation": "set_pattern"
            })
        
        return True
    
    def set_base_interval(self, interval: float) -> bool:
        """
        Set the base error generation interval.
        
        Args:
            interval: Base interval in seconds
            
        Returns:
            bool: True if interval was set successfully
        """
        if interval <= 0:
            if self.logger:
                self.logger.log_warning(f"Invalid interval: {interval}", {
                    "component": "ScheduledErrorGenerator",
                    "operation": "set_base_interval"
                })
            return False
        
        self.base_interval = interval
        
        if self.logger:
            self.logger.log_info(f"Set base error generation interval to {interval}", {
                "component": "ScheduledErrorGenerator",
                "operation": "set_base_interval"
            })
        
        return True
    
    def set_time_patterns(self, enabled: bool) -> None:
        """
        Enable or disable time-based error patterns.
        
        Args:
            enabled: Whether time-based patterns should be enabled
        """
        self.time_patterns_enabled = enabled
        
        if self.logger:
            self.logger.log_info(f"{'Enabled' if enabled else 'Disabled'} time-based error patterns", {
                "component": "ScheduledErrorGenerator",
                "operation": "set_time_patterns"
            })
    
    def configure_peak_hours(self, peak_hours: List[tuple]) -> None:
        """
        Configure peak hours for error generation.
        
        Args:
            peak_hours: List of (start_hour, end_hour) tuples in 24-hour format
        """
        # Validate peak hours
        valid_peak_hours = []
        for start, end in peak_hours:
            if 0 <= start < 24 and 0 <= end < 24 and start < end:
                valid_peak_hours.append((start, end))
        
        if valid_peak_hours:
            self.peak_hours = valid_peak_hours
            
            if self.logger:
                self.logger.log_info(f"Configured peak hours for error generation", {
                    "component": "ScheduledErrorGenerator",
                    "operation": "configure_peak_hours",
                    "peak_hours": valid_peak_hours
                })
        else:
            if self.logger:
                self.logger.log_warning(f"No valid peak hours provided", {
                    "component": "ScheduledErrorGenerator",
                    "operation": "configure_peak_hours"
                })
    
    def reset_stats(self) -> None:
        """Reset error generation statistics."""
        # Preserve start time
        start_time = self.stats["generation_start_time"]
        
        self.stats = {
            "total_errors_generated": 0,
            "errors_by_service": {service: 0 for service in self.services},
            "errors_by_type": {error_type: 0 for error_type in self.error_config.get_error_type_probabilities()},
            "errors_by_pattern": {
                "random": 0,
                "burst": 0,
                "periodic": 0,
                "wave": 0
            },
            "last_error_time": None,
            "generation_start_time": start_time,
            "bursts_triggered": 0,
            "total_burst_errors": 0
        }
        
        if self.logger:
            self.logger.log_info("Reset error generation statistics", {
                "component": "ScheduledErrorGenerator",
                "operation": "reset_stats"
            })