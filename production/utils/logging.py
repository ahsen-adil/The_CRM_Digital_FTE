"""
Structured logging infrastructure for production monitoring and debugging.
Uses python-json-logger for machine-readable logs compatible with ELK stack.
"""
import logging
import sys
from typing import Optional
from pythonjsonlogger import jsonlogger
from datetime import datetime
import os


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields."""
    
    def add_fields(self, log_record, record, message_dict):
        """Add custom fields to log records."""
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        
        # Add timestamp in ISO format
        log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        
        # Add log level
        log_record['level'] = record.levelname
        
        # Add logger name
        log_record['logger'] = record.name
        
        # Add custom fields if present
        if hasattr(record, 'correlation_id'):
            log_record['correlation_id'] = record.correlation_id
        
        if hasattr(record, 'customer_id'):
            log_record['customer_id'] = record.customer_id
        
        if hasattr(record, 'ticket_id'):
            log_record['ticket_id'] = record.ticket_id


def setup_logging(
    level: str = "DEBUG",
    log_file: Optional[str] = None,
    environment: str = "development"
) -> logging.Logger:
    """
    Configure structured logging for the application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for log output
        environment: Environment name (development, production)
    
    Returns:
        Configured logger instance
    
    Usage:
        logger = setup_logging()
        logger.info("Application started", extra={"correlation_id": "abc123"})
    """
    # Create logger
    logger = logging.getLogger("crm_fte")
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    
    # Create file handler if specified
    if log_file:
        # Ensure log directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level.upper()))
        logger.addHandler(file_handler)
    
    # Set formatter based on environment
    if environment == "production":
        # JSON format for production (machine-readable)
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        )
    else:
        # Human-readable format for development
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Logger instance
    
    Usage:
        logger = get_logger(__name__)
        logger.info("Processing ticket", extra={"ticket_id": "TKT-2026-000001"})
    """
    return logging.getLogger(name)


# Example usage and initialization
def init_logging():
    """Initialize logging on application startup."""
    from production.config import settings
    
    logger = setup_logging(
        level=settings.LOG_LEVEL,
        log_file="logs/crm_fte.log" if settings.ENVIRONMENT == "development" else None,
        environment=settings.ENVIRONMENT
    )
    
    logger.info(
        "Logging initialized",
        extra={
            "environment": settings.ENVIRONMENT,
            "log_level": settings.LOG_LEVEL
        }
    )
    
    return logger
