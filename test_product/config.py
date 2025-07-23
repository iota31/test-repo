"""
Configuration management for the test product application.
"""

import os
from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path


@dataclass
class TestConfig:
    """Configuration class for the test product application."""
    
    # Logging configuration
    log_file: str = "logs/test_product.log"
    log_level: str = "INFO"
    
    # Error generation probabilities
    error_probability: float = 0.05
    warning_probability: float = 0.15
    critical_probability: float = 0.01
    
    # Generation timing
    generation_interval: float = 2.0
    
    # Service configuration
    services_enabled: List[str] = field(default_factory=lambda: [
        "UserService",
        "PaymentService", 
        "DataProcessingService",
        "AuthService"
    ])
    
    # Application configuration
    port: int = 8000
    host: str = "0.0.0.0"
    
    # Environment-specific settings
    environment: str = "development"
    debug: bool = True
    
    @classmethod
    def from_env(cls) -> 'TestConfig':
        """Create configuration from environment variables."""
        return cls(
            log_file=os.getenv("TEST_PRODUCT_LOG_FILE", "logs/test_product.log"),
            log_level=os.getenv("TEST_PRODUCT_LOG_LEVEL", "INFO"),
            error_probability=float(os.getenv("TEST_PRODUCT_ERROR_RATE", "0.05")),
            warning_probability=float(os.getenv("TEST_PRODUCT_WARNING_RATE", "0.15")),
            critical_probability=float(os.getenv("TEST_PRODUCT_CRITICAL_RATE", "0.01")),
            generation_interval=float(os.getenv("TEST_PRODUCT_INTERVAL", "2.0")),
            port=int(os.getenv("TEST_PRODUCT_PORT", "8000")),
            host=os.getenv("TEST_PRODUCT_HOST", "0.0.0.0"),
            environment=os.getenv("TEST_PRODUCT_ENV", "development"),
            debug=os.getenv("TEST_PRODUCT_DEBUG", "true").lower() == "true",
            services_enabled=os.getenv("TEST_PRODUCT_SERVICES", "UserService,PaymentService,DataProcessingService,AuthService").split(",")
        )
    
    def ensure_log_directory(self) -> None:
        """Ensure the log directory exists."""
        log_path = Path(self.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)


@dataclass 
class ErrorConfig:
    """Configuration for error generation engine."""
    
    # Error type probabilities
    name_error_probability: float = 0.2
    key_error_probability: float = 0.15
    attribute_error_probability: float = 0.15
    zero_division_error_probability: float = 0.1
    type_error_probability: float = 0.1
    index_error_probability: float = 0.1
    file_not_found_error_probability: float = 0.05
    value_error_probability: float = 0.05
    memory_error_probability: float = 0.02
    import_error_probability: float = 0.03
    recursion_error_probability: float = 0.02
    connection_error_probability: float = 0.03
    
    # Service-specific error rates
    user_service_error_rate: float = 0.08
    payment_service_error_rate: float = 0.06
    data_processing_service_error_rate: float = 0.07
    auth_service_error_rate: float = 0.05
    
    def get_error_type_probabilities(self) -> dict:
        """Get normalized error type probabilities."""
        return {
            "NameError": self.name_error_probability,
            "KeyError": self.key_error_probability,
            "AttributeError": self.attribute_error_probability,
            "ZeroDivisionError": self.zero_division_error_probability,
            "TypeError": self.type_error_probability,
            "IndexError": self.index_error_probability,
            "FileNotFoundError": self.file_not_found_error_probability,
            "ValueError": self.value_error_probability,
            "MemoryError": self.memory_error_probability,
            "ImportError": self.import_error_probability,
            "RecursionError": self.recursion_error_probability,
            "ConnectionError": self.connection_error_probability,
        }
    
    def get_service_error_rates(self) -> dict:
        """Get service-specific error rates."""
        return {
            "UserService": self.user_service_error_rate,
            "PaymentService": self.payment_service_error_rate,
            "DataProcessingService": self.data_processing_service_error_rate,
            "AuthService": self.auth_service_error_rate,
        }