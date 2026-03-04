"""
Custom exception classes for the Customer Success Digital FTE application.
Provides structured error handling with proper HTTP status code mapping.
"""
from typing import Optional, Dict, Any
from http import HTTPStatus


class AppException(Exception):
    """Base exception for all application exceptions."""
    
    def __init__(
        self,
        message: str,
        status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON response."""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details,
            "status_code": self.status_code
        }


# Channel-specific exceptions

class ChannelException(AppException):
    """Base exception for channel-related errors."""
    pass


class EmailDeliveryError(ChannelException):
    """Raised when email delivery fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=HTTPStatus.BAD_GATEWAY,
            error_code="EMAIL_DELIVERY_ERROR",
            details=details
        )


class EmailReadError(ChannelException):
    """Raised when email reading fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=HTTPStatus.BAD_GATEWAY,
            error_code="EMAIL_READ_ERROR",
            details=details
        )


class WhatsAppDeliveryError(ChannelException):
    """Raised when WhatsApp message delivery fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=HTTPStatus.BAD_GATEWAY,
            error_code="WHATSAPP_DELIVERY_ERROR",
            details=details
        )


class WhatsAppWebhookError(ChannelException):
    """Raised when WhatsApp webhook processing fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=HTTPStatus.BAD_REQUEST,
            error_code="WHATSAPP_WEBHOOK_ERROR",
            details=details
        )


# Database exceptions

class DatabaseException(AppException):
    """Base exception for database-related errors."""
    pass


class DatabaseConnectionError(DatabaseException):
    """Raised when database connection fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            error_code="DATABASE_CONNECTION_ERROR",
            details=details
        )


class DatabaseQueryError(DatabaseException):
    """Raised when database query fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            error_code="DATABASE_QUERY_ERROR",
            details=details
        )


class RecordNotFoundError(DatabaseException):
    """Raised when a database record is not found."""
    
    def __init__(self, entity: str, identifier: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"{entity} with identifier '{identifier}' not found",
            status_code=HTTPStatus.NOT_FOUND,
            error_code="RECORD_NOT_FOUND",
            details={"entity": entity, "identifier": identifier, **(details or {})}
        )


# Agent exceptions

class AgentException(AppException):
    """Base exception for AI agent-related errors."""
    pass


class KnowledgeBaseSearchError(AgentException):
    """Raised when knowledge base search fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            error_code="KNOWLEDGE_BASE_SEARCH_ERROR",
            details=details
        )


class SentimentAnalysisError(AgentException):
    """Raised when sentiment analysis fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            error_code="SENTIMENT_ANALYSIS_ERROR",
            details=details
        )


class ResponseGenerationError(AgentException):
    """Raised when AI response generation fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            error_code="RESPONSE_GENERATION_ERROR",
            details=details
        )


# Escalation exceptions

class EscalationException(AppException):
    """Base exception for escalation-related errors."""
    pass


class EscalationCreationError(EscalationException):
    """Raised when escalation creation fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            error_code="ESCALATION_CREATION_ERROR",
            details=details
        )


class EscalationNotFoundError(EscalationException):
    """Raised when an escalation is not found."""
    
    def __init__(self, escalation_id: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Escalation with identifier '{escalation_id}' not found",
            status_code=HTTPStatus.NOT_FOUND,
            error_code="ESCALATION_NOT_FOUND",
            details={"escalation_id": escalation_id, **(details or {})}
        )


# Validation exceptions

class ValidationException(AppException):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            details={"field": field, **(details or {})}
        )


class ConfigurationError(AppException):
    """Raised when configuration is invalid or missing."""
    
    def __init__(self, message: str, setting: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            error_code="CONFIGURATION_ERROR",
            details={"setting": setting, **(details or {})}
        )
