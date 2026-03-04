"""
Application configuration management.
Loads environment variables and provides typed configuration access.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    ENVIRONMENT: str = Field(default="development", description="Environment: development, staging, production")
    LOG_LEVEL: str = Field(default="DEBUG", description="Logging level")
    API_HOST: str = Field(default="0.0.0.0", description="API host")
    API_PORT: int = Field(default=8000, description="API port")
    API_RELOAD: bool = Field(default=True, description="Enable auto-reload in development")
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql://user:password@localhost:5432/crm_fte_db",
        description="PostgreSQL connection URL"
    )
    POSTGRES_USER: str = Field(default="user", description="PostgreSQL username")
    POSTGRES_PASSWORD: str = Field(default="password", description="PostgreSQL password")
    POSTGRES_HOST: str = Field(default="localhost", description="PostgreSQL host")
    POSTGRES_PORT: str = Field(default="5432", description="PostgreSQL port")
    POSTGRES_DB: str = Field(default="crm_fte_db", description="PostgreSQL database name")
    
    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = Field(
        default="localhost:9092",
        description="Kafka bootstrap servers (comma-separated)"
    )
    KAFKA_TOPIC_INCOMING: str = Field(default="tickets.incoming", description="Kafka topic for incoming tickets")
    KAFKA_TOPIC_RESPONSES: str = Field(default="tickets.responses", description="Kafka topic for responses")
    KAFKA_TOPIC_ESCALATIONS: str = Field(default="tickets.escalations", description="Kafka topic for escalations")
    
    # Email (SMTP/IMAP)
    EMAIL_ADDRESS: str = Field(default="", description="Email address for sending/receiving")
    EMAIL_PASSWORD: str = Field(default="", description="Email password or App Password")
    SMTP_HOST: str = Field(default="smtp.gmail.com", description="SMTP server host")
    SMTP_PORT: int = Field(default=587, description="SMTP server port")
    IMAP_HOST: str = Field(default="imap.gmail.com", description="IMAP server host")
    IMAP_PORT: int = Field(default=993, description="IMAP server port")
    POLL_INTERVAL: int = Field(default=60, description="Email polling interval in seconds")
    
    # WhatsApp (Whapi)
    WHAPI_API_KEY: str = Field(default="", description="Whapi.Cloud API key")
    WHAPI_PHONE_ID: str = Field(default="", description="WhatsApp phone ID")
    WHAPI_BASE_URL: str = Field(default="https://gate.whapi.cloud", description="Whapi API base URL")
    
    # OpenAI
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API key")
    OPENAI_MODEL: str = Field(default="gpt-4o", description="OpenAI model to use")
    OPENAI_EMBEDDING_MODEL: str = Field(default="text-embedding-3-small", description="Embedding model")
    
    # Sentiment Analysis
    SENTIMENT_MODEL: str = Field(
        default="distilbert-base-uncased-finetuned-sst-2-english",
        description="Hugging Face sentiment analysis model"
    )
    SENTIMENT_THRESHOLD: float = Field(default=0.3, description="Sentiment threshold for escalation")
    
    # Security
    SECRET_KEY: str = Field(
        default="change-me-in-production",
        description="Secret key for JWT tokens and session management"
    )
    API_KEY_HEADER: str = Field(default="X-API-Key", description="Header name for API key authentication")
    
    # CORS
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins"
    )
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, description="API rate limit per minute")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields not defined in the model


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings


def validate_settings() -> bool:
    """
    Validate that required settings are configured.
    
    Returns:
        bool: True if all required settings are present
        
    Raises:
        ValueError: If required settings are missing
    """
    required_settings = {
        "DATABASE_URL": settings.DATABASE_URL,
        "OPENAI_API_KEY": settings.OPENAI_API_KEY,
        "KAFKA_BOOTSTRAP_SERVERS": settings.KAFKA_BOOTSTRAP_SERVERS,
    }
    
    missing = [key for key, value in required_settings.items() if not value]
    
    if missing:
        raise ValueError(f"Missing required settings: {', '.join(missing)}")
    
    # Warn about development settings
    if settings.ENVIRONMENT == "production":
        if settings.SECRET_KEY == "change-me-in-production":
            raise ValueError("SECRET_KEY must be set in production!")
    
    return True
