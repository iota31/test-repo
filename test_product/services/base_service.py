"""
Base service class with common error handling patterns.
"""

import random
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ..logging_system import StructuredLogger
from ..config import TestConfig, ErrorConfig


class BaseService(ABC):
    """
    Abstract base class for all buggy services.
    
    Provides common error handling patterns, probability management,
    and logging methods for realistic error generation.
    """
    
    def __init__(self, service_name: str, logger: StructuredLogger, 
                 error_probability: float = 0.05, config: Optional[TestConfig] = None):
        """
        Initialize the base service.
        
        Args:
            service_name: Name of the service for logging
            logger: Structured logger instance
            error_probability: Base probability of triggering errors (0.0-1.0)
            config: Optional test configuration
        """
        self.service_name = service_name
        self.logger = logger
        self.error_probability = error_probability
        self.config = config or TestConfig()
        
        # Track operation statistics
        self.operation_count = 0
        self.error_count = 0
        self.success_count = 0
        
        # Initialize error configuration
        self.error_config = ErrorConfig()
    
    def _should_trigger_error(self) -> bool:
        """
        Determine if an error should be triggered based on probability.
        
        Returns:
            bool: True if an error should be triggered
        """
        return random.random() < self.error_probability
    
    def _get_operation_context(self, operation: str, **kwargs) -> Dict[str, Any]:
        """
        Create context dictionary for logging operations.
        
        Args:
            operation: Name of the operation being performed
            **kwargs: Additional context data
            
        Returns:
            Dict containing operation context
        """
        context = {
            "operation": operation,
            "service": self.service_name,
            "operation_count": self.operation_count,
            "timestamp": time.time()
        }
        
        # Add any additional context provided
        context.update(kwargs)
        
        return context
    
    def _log_error(self, error: Exception, operation: str, **context_data) -> None:
        """
        Log an error with proper context and formatting.
        
        Args:
            error: The exception that occurred
            operation: Name of the operation that failed
            **context_data: Additional context information
        """
        context = self._get_operation_context(operation, **context_data)
        context["error_type"] = type(error).__name__
        context["error_message"] = str(error)
        
        # Determine log level based on error type
        if isinstance(error, (MemoryError, RecursionError, ConnectionError)):
            self.logger.log_critical(error, context)
        else:
            self.logger.log_error(error, context)
        
        self.error_count += 1
    
    def _log_success(self, operation: str, **context_data) -> None:
        """
        Log a successful operation.
        
        Args:
            operation: Name of the operation that succeeded
            **context_data: Additional context information
        """
        context = self._get_operation_context(operation, **context_data)
        message = f"Successfully completed {operation} in {self.service_name}"
        
        self.logger.log_info(message, context)
        self.success_count += 1
    
    def _log_warning(self, message: str, operation: str, **context_data) -> None:
        """
        Log a warning message.
        
        Args:
            message: Warning message
            operation: Name of the operation
            **context_data: Additional context information
        """
        context = self._get_operation_context(operation, **context_data)
        self.logger.log_warning(message, context)
    
    def _execute_with_error_handling(self, operation_name: str, 
                                   operation_func: Callable, 
                                   error_func: Optional[Callable] = None,
                                   **context_data) -> Any:
        """
        Execute an operation with error handling and logging.
        
        Args:
            operation_name: Name of the operation for logging
            operation_func: Function to execute for normal operation
            error_func: Optional function to execute when error should be triggered
            **context_data: Additional context for logging
            
        Returns:
            Result of the operation
            
        Raises:
            Exception: If an error occurs during execution
        """
        self.operation_count += 1
        
        try:
            # Check if we should trigger an error
            if self._should_trigger_error() and error_func:
                # Execute the error-generating function
                result = error_func()
                # If error function doesn't raise, log success
                self._log_success(operation_name, **context_data)
                return result
            else:
                # Execute normal operation
                result = operation_func()
                self._log_success(operation_name, **context_data)
                return result
                
        except Exception as e:
            # Log the error and re-raise
            self._log_error(e, operation_name, **context_data)
            raise
    
    def get_service_stats(self) -> Dict[str, Any]:
        """
        Get service operation statistics.
        
        Returns:
            Dict containing service statistics
        """
        return {
            "service_name": self.service_name,
            "total_operations": self.operation_count,
            "successful_operations": self.success_count,
            "failed_operations": self.error_count,
            "error_rate": self.error_count / max(self.operation_count, 1),
            "success_rate": self.success_count / max(self.operation_count, 1)
        }
    
    def reset_stats(self) -> None:
        """Reset operation statistics."""
        self.operation_count = 0
        self.error_count = 0
        self.success_count = 0
    
    def update_error_probability(self, new_probability: float) -> None:
        """
        Update the error probability for this service.
        
        Args:
            new_probability: New error probability (0.0-1.0)
        """
        if not 0.0 <= new_probability <= 1.0:
            raise ValueError("Error probability must be between 0.0 and 1.0")
        
        old_probability = self.error_probability
        self.error_probability = new_probability
        
        self._log_warning(
            f"Error probability updated from {old_probability} to {new_probability}",
            "config_update",
            old_probability=old_probability,
            new_probability=new_probability
        )
    
    @abstractmethod
    def get_service_name(self) -> str:
        """
        Get the service name.
        
        Returns:
            str: Service name
        """
        pass
    
    @abstractmethod
    def get_available_operations(self) -> list:
        """
        Get list of available operations for this service.
        
        Returns:
            list: List of operation names
        """
        pass
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check for this service.
        
        Returns:
            Dict containing health status
        """
        stats = self.get_service_stats()
        
        # Determine health status based on error rate
        error_rate = stats["error_rate"]
        if error_rate > 0.5:
            status = "unhealthy"
        elif error_rate > 0.2:
            status = "degraded"
        else:
            status = "healthy"
        
        return {
            "service": self.service_name,
            "status": status,
            "error_rate": error_rate,
            "total_operations": stats["total_operations"],
            "last_check": time.time()
        }