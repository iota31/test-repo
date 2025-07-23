"""
FastAPI application for the test product.

This module provides the FastAPI application that serves as the main interface
for the test product, including health check endpoints and error trigger endpoints.
"""

import asyncio
import os
import socket
import sys
from typing import Dict, Any, List, Optional
import time

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Query, Path, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .config import TestConfig
from .logging_system import StructuredLogger
from .error_engine import ErrorGenerationEngine


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Overall application status")
    version: str = Field(..., description="Application version")
    uptime_seconds: float = Field(..., description="Application uptime in seconds")
    services: Dict[str, Any] = Field(..., description="Status of individual services")
    error_generation: Dict[str, Any] = Field(..., description="Error generation statistics")


class ErrorTriggerRequest(BaseModel):
    """Request model for triggering specific errors."""
    service: str = Field(..., description="Service name to trigger error in")
    operation: str = Field(..., description="Operation name to trigger")
    error_type: Optional[str] = Field(None, description="Specific error type to trigger (if supported)")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Optional parameters for the operation")


class ErrorTriggerResponse(BaseModel):
    """Response model for error trigger requests."""
    success: bool = Field(..., description="Whether the error was triggered successfully")
    service: str = Field(..., description="Service name")
    operation: str = Field(..., description="Operation name")
    error_type: Optional[str] = Field(None, description="Type of error triggered")
    message: str = Field(..., description="Status message")
    stack_trace: Optional[str] = Field(None, description="Stack trace if error was triggered")
    timestamp: float = Field(..., description="Timestamp when the error was triggered")
    request_id: Optional[str] = Field(None, description="Unique identifier for this request")


class ConfigUpdateRequest(BaseModel):
    """Request model for updating configuration."""
    error_probability: Optional[float] = Field(None, description="New error probability (0-1)")
    warning_probability: Optional[float] = Field(None, description="New warning probability (0-1)")
    critical_probability: Optional[float] = Field(None, description="New critical probability (0-1)")
    generation_interval: Optional[float] = Field(None, description="New error generation interval in seconds")
    error_pattern: Optional[str] = Field(None, description="Error generation pattern (random, burst, periodic, wave)")
    services_enabled: Optional[List[str]] = Field(None, description="List of services to enable")


class ConfigUpdateResponse(BaseModel):
    """Response model for configuration updates."""
    success: bool = Field(..., description="Whether the update was successful")
    message: str = Field(..., description="Status message")
    updated_config: Dict[str, Any] = Field(..., description="Updated configuration values")


class TestProductAPI:
    """
    FastAPI application for the test product.
    
    This class manages the FastAPI application instance, routes, and
    background tasks for the test product.
    """
    
    def __init__(self, config: TestConfig, logger: StructuredLogger, error_engine: ErrorGenerationEngine = None):
        """
        Initialize the FastAPI application.
        
        Args:
            config: Test product configuration
            logger: Structured logger instance
            error_engine: Optional error generation engine instance
        """
        self.config = config
        self.logger = logger
        self.error_engine = error_engine
        self.start_time = time.time()
        self.version = "1.0.0"
        
        # Create FastAPI application
        self.app = FastAPI(
            title="Test Product API",
            description="API for controlling the test product error generation",
            version=self.version,
            docs_url="/docs",
            redoc_url="/redoc"
        )
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Register routes
        self._register_routes()
        
        # Register startup and shutdown handlers
        self._register_lifecycle_handlers()
        
        # Background tasks
        self.background_tasks = []
    
    def _register_routes(self):
        """Register API routes."""
        # Health check endpoints
        self.app.get("/health", response_model=dict, tags=["Health"])(self.health_check)
        self.app.get("/status", response_model=HealthResponse, tags=["Health"])(self.detailed_status)
        
        # Error trigger endpoints
        self.app.post("/trigger", response_model=ErrorTriggerResponse, tags=["Errors"])(self.trigger_error)
        self.app.get("/trigger/{service}/{operation}", response_model=ErrorTriggerResponse, tags=["Errors"])(self.trigger_error_get)
        self.app.get("/trigger/services", response_model=Dict[str, List[str]], tags=["Errors"])(self.list_services_and_operations)
        self.app.get("/trigger/services/{service}", response_model=Dict[str, Any], tags=["Errors"])(self.get_service_details)
        self.app.get("/trigger/error-types", response_model=List[str], tags=["Errors"])(self.list_error_types)
        
        # Configuration endpoints
        self.app.post("/config", response_model=ConfigUpdateResponse, tags=["Configuration"])(self.update_config)
        self.app.get("/config", response_model=Dict[str, Any], tags=["Configuration"])(self.get_config)
        
        # Statistics endpoints
        self.app.get("/stats", response_model=Dict[str, Any], tags=["Statistics"])(self.get_statistics)
        self.app.post("/stats/reset", response_model=Dict[str, str], tags=["Statistics"])(self.reset_statistics)
        
        # Metrics endpoints
        self.app.get("/metrics", response_model=Dict[str, Any], tags=["Metrics"])(self.get_metrics)
        self.app.get("/metrics/errors", response_model=Dict[str, Any], tags=["Metrics"])(self.get_error_metrics)
        self.app.get("/metrics/services", response_model=Dict[str, Any], tags=["Metrics"])(self.get_service_metrics)
        self.app.get("/metrics/patterns", response_model=Dict[str, Any], tags=["Metrics"])(self.get_pattern_metrics)
    
    def _register_lifecycle_handlers(self):
        """Register application startup and shutdown handlers."""
        # Startup handler
        @self.app.on_event("startup")
        async def startup_event():
            self.logger.log_info("FastAPI application starting", {
                "component": "TestProductAPI",
                "version": self.version,
                "host": self.config.host,
                "port": self.config.port
            })
            
            # Start background tasks
            self._start_background_tasks()
        
        # Shutdown handler
        @self.app.on_event("shutdown")
        async def shutdown_event():
            self.logger.log_info("FastAPI application shutting down", {
                "component": "TestProductAPI",
                "uptime_seconds": time.time() - self.start_time
            })
            
            # Stop background tasks
            self._stop_background_tasks()
    
    def _start_background_tasks(self):
        """Start background tasks for the application."""
        if not self.error_engine:
            self.logger.log_warning("No error engine available for background tasks", {
                "component": "TestProductAPI",
                "operation": "start_background_tasks"
            })
            return
        
        # Start error generation if not already running
        if not self.error_engine.running:
            self.error_engine.start_scheduled_generation()
            self.logger.log_info("Started error generation engine from API", {
                "component": "TestProductAPI",
                "operation": "start_background_tasks"
            })
        
        # Start statistics logging task
        self.background_tasks.append(asyncio.create_task(self._log_statistics_periodically()))
    
    def _stop_background_tasks(self):
        """Stop all background tasks."""
        # Stop error generation engine
        if self.error_engine and self.error_engine.running:
            self.error_engine.stop_scheduled_generation()
            self.logger.log_info("Stopped error generation engine", {
                "component": "TestProductAPI",
                "operation": "stop_background_tasks"
            })
        
        # Cancel all background tasks
        for task in self.background_tasks:
            if not task.done():
                task.cancel()
        
        self.background_tasks = []
    
    async def _log_statistics_periodically(self):
        """Background task to periodically log statistics."""
        try:
            while True:
                # Wait for the next interval
                await asyncio.sleep(60)  # Log stats every minute
                
                if self.error_engine:
                    stats = self.error_engine.get_error_generation_stats()
                    self.logger.log_info("Error generation statistics", {
                        "component": "TestProductAPI",
                        "operation": "log_statistics",
                        "total_errors": stats["total_errors_generated"],
                        "errors_per_minute": stats["errors_per_minute"],
                        "uptime_seconds": time.time() - self.start_time
                    })
        except asyncio.CancelledError:
            # Task was cancelled, clean up
            self.logger.log_info("Statistics logging task cancelled", {
                "component": "TestProductAPI",
                "operation": "log_statistics_periodically"
            })
        except Exception as e:
            self.logger.log_error(e, {
                "component": "TestProductAPI",
                "operation": "log_statistics_periodically"
            })
    
    async def health_check(self):
        """
        Basic health check endpoint.
        
        Returns:
            dict: Basic health status
        """
        # Check if error engine is running
        error_engine_status = "running" if self.error_engine and self.error_engine.running else "stopped"
        
        # Calculate uptime
        uptime_seconds = time.time() - self.start_time
        
        # Format uptime in a human-readable format
        days, remainder = divmod(uptime_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_formatted = f"{int(days)}d {int(hours)}h {int(minutes)}m {int(seconds)}s"
        
        return {
            "status": "ok",
            "version": self.version,
            "timestamp": time.time(),
            "error_engine": error_engine_status,
            "uptime_seconds": uptime_seconds,
            "uptime": uptime_formatted,
            "hostname": socket.gethostname()
        }
    
    async def detailed_status(self):
        """
        Detailed application status endpoint.
        
        Returns:
            HealthResponse: Detailed health status
        """
        services_status = {}
        error_generation_stats = {}
        
        # Get service status if error engine is available
        if self.error_engine:
            # Get service health checks
            for service_name, service in self.error_engine.services.items():
                services_status[service_name] = service.health_check()
            
            # Get error generation stats
            error_generation_stats = self.error_engine.get_error_generation_stats()
            
            # Add additional metrics
            if "runtime_seconds" in error_generation_stats:
                # Format runtime in a human-readable format
                runtime = error_generation_stats["runtime_seconds"]
                days, remainder = divmod(runtime, 86400)
                hours, remainder = divmod(remainder, 3600)
                minutes, seconds = divmod(remainder, 60)
                error_generation_stats["runtime_formatted"] = f"{int(days)}d {int(hours)}h {int(minutes)}m {int(seconds)}s"
            
            # Add error rate per service
            if "errors_by_service" in error_generation_stats and "runtime_seconds" in error_generation_stats:
                runtime = error_generation_stats["runtime_seconds"]
                if runtime > 0:
                    error_generation_stats["error_rates_per_minute"] = {
                        service: (count * 60) / runtime 
                        for service, count in error_generation_stats["errors_by_service"].items()
                    }
        
        # Get system information
        system_info = {
            "hostname": socket.gethostname(),
            "python_version": sys.version,
            "platform": sys.platform,
            "cpu_count": os.cpu_count(),
            "process_id": os.getpid()
        }
        
        # Get memory usage
        try:
            import psutil
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            system_info["memory_usage_mb"] = memory_info.rss / (1024 * 1024)
            system_info["cpu_percent"] = process.cpu_percent(interval=0.1)
        except (ImportError, Exception):
            # psutil might not be available, ignore if it fails
            pass
        
        # Add system info to services status
        services_status["system"] = system_info
        
        return HealthResponse(
            status="healthy",
            version=self.version,
            uptime_seconds=time.time() - self.start_time,
            services=services_status,
            error_generation=error_generation_stats
        )
    
    async def trigger_error(self, request: ErrorTriggerRequest):
        """
        Trigger a specific error in a service.
        
        Args:
            request: Error trigger request
            
        Returns:
            ErrorTriggerResponse: Result of the error trigger
        """
        import uuid
        import traceback
        
        # Generate a unique request ID for tracking
        request_id = str(uuid.uuid4())
        
        if not self.error_engine:
            raise HTTPException(status_code=503, detail="Error generation engine not available")
        
        service = request.service
        operation = request.operation
        error_type = request.error_type
        parameters = request.parameters or {}
        
        # Check if service exists
        if service not in self.error_engine.services:
            available_services = list(self.error_engine.services.keys())
            raise HTTPException(
                status_code=404, 
                detail=f"Service '{service}' not found. Available services: {available_services}"
            )
        
        # Check if operation exists
        service_instance = self.error_engine.services[service]
        available_operations = service_instance.get_available_operations()
        if operation not in available_operations:
            raise HTTPException(
                status_code=404,
                detail=f"Operation '{operation}' not found in service '{service}'. Available operations: {available_operations}"
            )
        
        # Log the trigger attempt
        self.logger.log_info(f"Attempting to trigger error in {service}.{operation}", {
            "component": "TestProductAPI",
            "operation": "trigger_error",
            "service": service,
            "triggered_operation": operation,
            "requested_error_type": error_type,
            "request_id": request_id,
            "parameters": parameters
        })
        
        # Capture the stack trace if an error occurs
        stack_trace = None
        actual_error_type = None
        
        try:
            # Trigger the error with the enhanced method that supports error_type and parameters
            success = self.error_engine.trigger_specific_error(
                service, 
                operation,
                error_type=error_type,
                parameters=parameters
            )
            
            # Determine error type (best effort)
            try:
                # This will intentionally fail with an exception that we can capture
                if parameters:
                    result = getattr(service_instance, operation)(**parameters)
                else:
                    result = getattr(service_instance, operation)(*[], **{})
            except Exception as e:
                actual_error_type = type(e).__name__
                stack_trace = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        except Exception as e:
            # Handle any exceptions during the error triggering process
            success = False
            actual_error_type = type(e).__name__
            stack_trace = "".join(traceback.format_exception(type(e), e, e.__traceback__))
            self.logger.log_error(e, {
                "component": "TestProductAPI",
                "operation": "trigger_error",
                "service": service,
                "triggered_operation": operation,
                "request_id": request_id
            })
        
        # Check if the requested error type matches the actual error type
        if error_type and actual_error_type and error_type != actual_error_type:
            message = f"Warning: Requested error type '{error_type}' but got '{actual_error_type}' in {service}.{operation}"
            self.logger.log_warning(message, {
                "component": "TestProductAPI",
                "operation": "trigger_error",
                "service": service,
                "triggered_operation": operation,
                "requested_error_type": error_type,
                "actual_error_type": actual_error_type,
                "request_id": request_id
            })
        elif success:
            message = f"Successfully triggered {actual_error_type or 'error'} in {service}.{operation}"
            self.logger.log_info(message, {
                "component": "TestProductAPI",
                "operation": "trigger_error",
                "service": service,
                "triggered_operation": operation,
                "error_type": actual_error_type,
                "request_id": request_id
            })
        else:
            message = f"Failed to trigger error in {service}.{operation}"
            self.logger.log_warning(message, {
                "component": "TestProductAPI",
                "operation": "trigger_error",
                "service": service,
                "triggered_operation": operation,
                "request_id": request_id
            })
        
        # Create the response
        return ErrorTriggerResponse(
            success=success,
            service=service,
            operation=operation,
            error_type=actual_error_type,
            message=message,
            stack_trace=stack_trace,
            timestamp=time.time(),
            request_id=request_id
        )
    
    async def trigger_error_get(self, 
                           service: str = Path(..., description="Service name to trigger error in"),
                           operation: str = Path(..., description="Operation name to trigger"),
                           error_type: Optional[str] = Query(None, description="Specific error type to trigger"),
                           param_name: Optional[str] = Query(None, description="Parameter name for the operation"),
                           param_value: Optional[str] = Query(None, description="Parameter value for the operation")):
        """
        GET endpoint for triggering a specific error in a service.
        
        Args:
            service: Service name
            operation: Operation name
            error_type: Optional specific error type to trigger
            param_name: Optional parameter name for the operation
            param_value: Optional parameter value for the operation
            
        Returns:
            ErrorTriggerResponse: Result of the error trigger
        """
        # Build parameters dictionary if provided
        parameters = None
        if param_name and param_value:
            parameters = {param_name: param_value}
            
            # Try to convert parameter value to appropriate type
            try:
                # Try as int
                parameters[param_name] = int(param_value)
            except ValueError:
                try:
                    # Try as float
                    parameters[param_name] = float(param_value)
                except ValueError:
                    # Try as boolean
                    if param_value.lower() == "true":
                        parameters[param_name] = True
                    elif param_value.lower() == "false":
                        parameters[param_name] = False
                    # Otherwise keep as string
        
        # Create a request object and delegate to the POST handler
        request = ErrorTriggerRequest(
            service=service, 
            operation=operation,
            error_type=error_type,
            parameters=parameters
        )
        return await self.trigger_error(request)
    
    async def update_config(self, request: ConfigUpdateRequest):
        """
        Update application configuration.
        
        Args:
            request: Configuration update request
            
        Returns:
            ConfigUpdateResponse: Result of the configuration update
        """
        updated_values = {}
        
        # Update error probability
        if request.error_probability is not None:
            if not 0 <= request.error_probability <= 1:
                raise HTTPException(status_code=400, detail="Error probability must be between 0 and 1")
            self.config.error_probability = request.error_probability
            updated_values["error_probability"] = request.error_probability
        
        # Update warning probability
        if request.warning_probability is not None:
            if not 0 <= request.warning_probability <= 1:
                raise HTTPException(status_code=400, detail="Warning probability must be between 0 and 1")
            self.config.warning_probability = request.warning_probability
            updated_values["warning_probability"] = request.warning_probability
        
        # Update critical probability
        if request.critical_probability is not None:
            if not 0 <= request.critical_probability <= 1:
                raise HTTPException(status_code=400, detail="Critical probability must be between 0 and 1")
            self.config.critical_probability = request.critical_probability
            updated_values["critical_probability"] = request.critical_probability
        
        # Update generation interval
        if request.generation_interval is not None:
            if request.generation_interval <= 0:
                raise HTTPException(status_code=400, detail="Generation interval must be positive")
            self.config.generation_interval = request.generation_interval
            updated_values["generation_interval"] = request.generation_interval
            
            # Update error engine interval if available
            if self.error_engine:
                self.error_engine.update_generation_interval(request.generation_interval)
        
        # Update error pattern
        if request.error_pattern is not None:
            valid_patterns = ["random", "burst", "periodic", "wave"]
            if request.error_pattern not in valid_patterns:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid error pattern. Must be one of: {valid_patterns}"
                )
            
            # Update error engine pattern if available
            if self.error_engine:
                success = self.error_engine.set_error_pattern(request.error_pattern)
                if success:
                    updated_values["error_pattern"] = request.error_pattern
        
        # Update enabled services
        if request.services_enabled is not None:
            # Validate services
            if self.error_engine:
                available_services = list(self.error_engine.services.keys())
                invalid_services = [s for s in request.services_enabled if s not in available_services]
                if invalid_services:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid services: {invalid_services}. Available services: {available_services}"
                    )
            
            self.config.services_enabled = request.services_enabled
            updated_values["services_enabled"] = request.services_enabled
        
        # Log the configuration update
        self.logger.log_info("Configuration updated", {
            "component": "TestProductAPI",
            "operation": "update_config",
            "updated_values": updated_values
        })
        
        return ConfigUpdateResponse(
            success=True,
            message=f"Successfully updated {len(updated_values)} configuration values",
            updated_config=updated_values
        )
    
    async def get_config(self):
        """
        Get current application configuration.
        
        Returns:
            Dict: Current configuration values
        """
        # Get error engine configuration if available
        error_engine_config = {}
        if self.error_engine:
            stats = self.error_engine.get_error_generation_stats()
            error_engine_config = {
                "running": self.error_engine.running,
                "generation_interval": self.error_engine.generation_interval,
                "pattern_type": stats.get("scheduled_generator", {}).get("pattern_type", "unknown")
            }
        
        # Return configuration
        return {
            "application": {
                "version": self.version,
                "host": self.config.host,
                "port": self.config.port,
                "environment": self.config.environment,
                "debug": self.config.debug
            },
            "logging": {
                "log_file": self.config.log_file,
                "log_level": self.config.log_level
            },
            "error_generation": {
                "error_probability": self.config.error_probability,
                "warning_probability": self.config.warning_probability,
                "critical_probability": self.config.critical_probability,
                "services_enabled": self.config.services_enabled,
                **error_engine_config
            }
        }
    
    async def get_statistics(self):
        """
        Get error generation statistics.
        
        Returns:
            Dict: Error generation statistics
        """
        if not self.error_engine:
            return {
                "error": "Error generation engine not available",
                "uptime_seconds": time.time() - self.start_time
            }
        
        # Get error generation statistics
        stats = self.error_engine.get_error_generation_stats()
        
        # Add application uptime
        stats["application_uptime_seconds"] = time.time() - self.start_time
        
        return stats
    
    async def reset_statistics(self):
        """
        Reset error generation statistics.
        
        Returns:
            Dict: Status message
        """
        if not self.error_engine:
            raise HTTPException(status_code=503, detail="Error generation engine not available")
        
        # Reset statistics
        self.error_engine.reset_stats()
        
        self.logger.log_info("Reset error generation statistics", {
            "component": "TestProductAPI",
            "operation": "reset_statistics"
        })
        
        return {"status": "success", "message": "Statistics reset successfully"}
    
    async def get_metrics(self):
        """
        Get all metrics in Prometheus-compatible format.
        
        Returns:
            Dict: All metrics in a structured format
        """
        if not self.error_engine:
            raise HTTPException(status_code=503, detail="Error generation engine not available")
        
        # Get error generation statistics
        stats = self.error_engine.get_error_generation_stats()
        
        # Format metrics in a structured way
        metrics = {
            "application": {
                "version": self.version,
                "uptime_seconds": time.time() - self.start_time
            },
            "errors": {
                "total": stats["total_errors_generated"],
                "per_minute": stats.get("errors_per_minute", 0),
                "by_service": stats.get("errors_by_service", {}),
                "by_type": stats.get("errors_by_type", {}),
                "by_pattern": stats.get("errors_by_pattern", {})
            },
            "patterns": {
                "current": stats.get("scheduled_generator", {}).get("pattern_type", "unknown"),
                "bursts_triggered": stats.get("scheduled_generator", {}).get("bursts_triggered", 0),
                "total_burst_errors": stats.get("scheduled_generator", {}).get("total_burst_errors", 0)
            },
            "runtime": {
                "seconds": stats.get("runtime_seconds", 0),
                "is_running": stats.get("is_running", False),
                "generation_interval": stats.get("generation_interval", self.config.generation_interval)
            }
        }
        
        return metrics
    
    async def get_error_metrics(self):
        """
        Get detailed error metrics.
        
        Returns:
            Dict: Error metrics by type and service
        """
        if not self.error_engine:
            raise HTTPException(status_code=503, detail="Error generation engine not available")
        
        # Get error generation statistics
        stats = self.error_engine.get_error_generation_stats()
        
        # Calculate error rates per minute for each error type
        error_rates_by_type = {}
        runtime = stats.get("runtime_seconds", 0)
        if runtime > 0:
            for error_type, count in stats.get("errors_by_type", {}).items():
                error_rates_by_type[error_type] = (count * 60) / runtime
        
        # Format metrics
        metrics = {
            "total_errors": stats["total_errors_generated"],
            "errors_per_minute": stats.get("errors_per_minute", 0),
            "errors_by_type": stats.get("errors_by_type", {}),
            "error_rates_by_type": error_rates_by_type,
            "last_error_time": stats.get("last_error_time"),
            "time_since_last_error": time.time() - stats.get("last_error_time", time.time()) if stats.get("last_error_time") else None
        }
        
        return metrics
    
    async def get_service_metrics(self):
        """
        Get service-specific metrics.
        
        Returns:
            Dict: Metrics for each service
        """
        if not self.error_engine:
            raise HTTPException(status_code=503, detail="Error generation engine not available")
        
        # Get error generation statistics
        stats = self.error_engine.get_error_generation_stats()
        
        # Get service health checks
        services_status = {}
        for service_name, service in self.error_engine.services.items():
            services_status[service_name] = service.health_check()
        
        # Calculate error rates per minute for each service
        error_rates_by_service = {}
        runtime = stats.get("runtime_seconds", 0)
        if runtime > 0:
            for service, count in stats.get("errors_by_service", {}).items():
                error_rates_by_service[service] = (count * 60) / runtime
        
        # Format metrics
        metrics = {
            "services_enabled": list(self.error_engine.services.keys()),
            "errors_by_service": stats.get("errors_by_service", {}),
            "error_rates_by_service": error_rates_by_service,
            "services_status": services_status,
            "service_error_probabilities": {
                service_name: service.error_probability 
                for service_name, service in self.error_engine.services.items()
            }
        }
        
        return metrics
    
    async def get_pattern_metrics(self):
        """
        Get error pattern metrics.
        
        Returns:
            Dict: Metrics related to error generation patterns
        """
        if not self.error_engine:
            raise HTTPException(status_code=503, detail="Error generation engine not available")
        
        # Get error generation statistics
        stats = self.error_engine.get_error_generation_stats()
        scheduled_stats = stats.get("scheduled_generator", {})
        
        # Format metrics
        metrics = {
            "current_pattern": scheduled_stats.get("pattern_type", "unknown"),
            "errors_by_pattern": stats.get("errors_by_pattern", {}),
            "bursts_triggered": scheduled_stats.get("bursts_triggered", 0),
            "total_burst_errors": scheduled_stats.get("total_burst_errors", 0),
            "average_errors_per_burst": (
                scheduled_stats.get("total_burst_errors", 0) / scheduled_stats.get("bursts_triggered", 1)
                if scheduled_stats.get("bursts_triggered", 0) > 0 else 0
            ),
            "generation_interval": stats.get("generation_interval", self.config.generation_interval),
            "time_patterns_enabled": getattr(self.error_engine.scheduled_generator, "time_patterns_enabled", False)
                if hasattr(self.error_engine, "scheduled_generator") else False
        }
        
        return metrics
    
    async def list_services_and_operations(self):
        """
        List all available services and their operations.
        
        Returns:
            Dict: Mapping of service names to lists of available operations
        """
        if not self.error_engine:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
                detail="Error generation engine not available"
            )
        
        result = {}
        for service_name, service in self.error_engine.services.items():
            result[service_name] = service.get_available_operations()
        
        return result
    
    async def get_service_details(self, service: str = Path(..., description="Service name")):
        """
        Get detailed information about a specific service.
        
        Args:
            service: Service name
            
        Returns:
            Dict: Service details including operations and error types
        """
        if not self.error_engine:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
                detail="Error generation engine not available"
            )
        
        if service not in self.error_engine.services:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Service '{service}' not found. Available services: {list(self.error_engine.services.keys())}"
            )
        
        service_instance = self.error_engine.services[service]
        operations = service_instance.get_available_operations()
        
        # Get error types for each operation (best effort)
        operation_error_types = {}
        for operation in operations:
            try:
                # Try to determine error type by calling the operation
                getattr(service_instance, operation)(*[], **{})
                # If no exception, record as "None"
                operation_error_types[operation] = None
            except Exception as e:
                # Record the error type
                operation_error_types[operation] = type(e).__name__
        
        # Get service health and stats
        health = service_instance.health_check()
        stats = service_instance.get_service_stats()
        
        return {
            "service_name": service,
            "operations": operations,
            "operation_error_types": operation_error_types,
            "error_probability": service_instance.error_probability,
            "health_status": health,
            "statistics": stats
        }
    
    async def list_error_types(self):
        """
        List all possible error types that can be triggered.
        
        Returns:
            List: List of error type names
        """
        # Common Python error types that might be triggered
        common_error_types = [
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
        
        # If error engine is available, get actual error types from statistics
        if self.error_engine:
            stats = self.error_engine.get_error_generation_stats()
            actual_error_types = list(stats.get("errors_by_type", {}).keys())
            
            # Combine with common types, removing duplicates
            all_types = list(set(common_error_types + actual_error_types))
            all_types.sort()
            return all_types
        
        return common_error_types
    
    def get_app(self):
        """Get the FastAPI application instance."""
        return self.app