"""
Structured logging system that matches log_generator.py format.
"""

import json
import logging
import random
import socket
import threading
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Any


class StructuredLogger:
    """
    Logger that produces JSON-formatted logs matching log_generator.py format.
    """
    
    def __init__(self, service_name: str, log_file: str, log_level: str = "INFO"):
        self.service_name = service_name
        self.log_file = log_file
        self.hostname = socket.gethostname()
        
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Set up Python logger
        self.logger = logging.getLogger(f"test_product.{service_name}")
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Create file handler
        handler = logging.FileHandler(log_file)
        handler.setLevel(getattr(logging, log_level.upper()))
        
        # Create formatter (we'll handle JSON formatting ourselves)
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        
        # Add handler to logger
        if not self.logger.handlers:
            self.logger.addHandler(handler)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format with Z suffix."""
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    def _get_thread_name(self) -> str:
        """Get current thread name."""
        return threading.current_thread().name
    
    def _create_log_entry(self, level: str, message: str, context: Optional[Dict[str, Any]] = None, 
                         exception: Optional[Exception] = None) -> Dict[str, Any]:
        """Create a structured log entry matching log_generator.py format."""
        log_entry = {
            "timestamp": self._get_timestamp(),
            "level": level,
            "service": self.service_name,
            "message": message,
            "hostname": self.hostname,
            "thread": self._get_thread_name(),
        }
        
        # Add context information if provided
        if context:
            log_entry.update(context)
        
        # Add exception information for errors
        if exception and level in ("ERROR", "CRITICAL"):
            log_entry["stack_trace"] = self._generate_python_stack_trace(exception)
            log_entry["error_type"] = type(exception).__name__
            
            # Try to get function name and line number from traceback
            tb = traceback.extract_tb(exception.__traceback__)
            if tb:
                frame = tb[-1]  # Get the last frame (where error occurred)
                log_entry["function_name"] = frame.name
                log_entry["line_number"] = frame.lineno
        
        return log_entry
    
    def _generate_python_stack_trace(self, exception: Exception) -> str:
        """Generate a Python stack trace string."""
        return ''.join(traceback.format_exception(type(exception), exception, exception.__traceback__)).strip()
    
    def _write_log(self, log_entry: Dict[str, Any]) -> None:
        """Write log entry to file."""
        json_log = json.dumps(log_entry)
        self.logger.info(json_log)
    
    def log_info(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log an INFO level message."""
        log_entry = self._create_log_entry("INFO", message, context)
        self._write_log(log_entry)
    
    def log_warning(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log a WARNING level message."""
        log_entry = self._create_log_entry("WARNING", message, context)
        self._write_log(log_entry)
    
    def log_error(self, exception: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """Log an ERROR level message with exception details."""
        message = f"{type(exception).__name__} occurred in {self.service_name}"
        log_entry = self._create_log_entry("ERROR", message, context, exception)
        self._write_log(log_entry)
    
    def log_critical(self, exception: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """Log a CRITICAL level message with exception details."""
        message = f"CRITICAL {type(exception).__name__} occurred in {self.service_name}"
        log_entry = self._create_log_entry("CRITICAL", message, context, exception)
        self._write_log(log_entry)


class LogLevelManager:
    """
    Manages log level distribution to maintain realistic ratios.
    Default: 80% INFO, 15% WARNING, 4% ERROR, 1% CRITICAL
    """
    
    def __init__(self, info_ratio: float = 0.8, warning_ratio: float = 0.15, 
                 error_ratio: float = 0.04, critical_ratio: float = 0.01):
        self.info_ratio = info_ratio
        self.warning_ratio = warning_ratio
        self.error_ratio = error_ratio
        self.critical_ratio = critical_ratio
        
        # Validate ratios sum to 1.0
        total = info_ratio + warning_ratio + error_ratio + critical_ratio
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Log level ratios must sum to 1.0, got {total}")
    
    def get_random_log_level(self) -> str:
        """Get a random log level based on configured probabilities."""
        rand = random.random()
        
        if rand < self.critical_ratio:
            return "CRITICAL"
        elif rand < self.critical_ratio + self.error_ratio:
            return "ERROR"
        elif rand < self.critical_ratio + self.error_ratio + self.warning_ratio:
            return "WARNING"
        else:
            return "INFO"
    
    def should_log_at_level(self, level: str) -> bool:
        """Determine if we should log at the given level based on probabilities."""
        rand = random.random()
        
        if level == "CRITICAL":
            return rand < self.critical_ratio
        elif level == "ERROR":
            return rand < self.error_ratio
        elif level == "WARNING":
            return rand < self.warning_ratio
        else:  # INFO
            return rand < self.info_ratio


def create_logger(service_name: str, log_file: str, log_level: str = "INFO") -> StructuredLogger:
    """Factory function to create a structured logger."""
    return StructuredLogger(service_name, log_file, log_level)