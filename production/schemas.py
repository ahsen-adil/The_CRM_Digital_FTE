"""
Pydantic schemas for request/response validation.
Uses Pydantic v2 with Field validators and model config.
"""
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


# Enums

class ChannelEnum(str, Enum):
    """Supported communication channels."""
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    WEB_FORM = "web_form"


class TicketStatusEnum(str, Enum):
    """Ticket lifecycle statuses."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING_CUSTOMER = "pending_customer"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    CLOSED = "closed"


class PriorityEnum(str, Enum):
    """Ticket priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class EscalationReasonEnum(str, Enum):
    """Reasons for escalation."""
    NEGATIVE_SENTIMENT = "negative_sentiment"
    PRICING_REQUEST = "pricing_request"
    REFUND_REQUEST = "refund_request"
    LEGAL_COMPLIANCE = "legal_compliance"
    COMPLEX_ISSUE = "complex_issue"
    KNOWLEDGE_GAP = "knowledge_gap"
    CUSTOMER_REQUEST = "customer_request"


class ConversationStatusEnum(str, Enum):
    """Conversation statuses."""
    OPEN = "open"
    PENDING = "pending"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    CLOSED = "closed"


class MessageDirectionEnum(str, Enum):
    """Message direction."""
    INBOUND = "inbound"
    OUTBOUND = "outbound"


# Customer Schemas

class CustomerBase(BaseModel):
    """Base customer schema."""
    email: EmailStr = Field(..., description="Customer email address")
    phone_number: Optional[str] = Field(None, max_length=20, description="WhatsApp phone number in E.164 format")
    name: Optional[str] = Field(None, max_length=255, description="Customer name")


class CustomerCreate(CustomerBase):
    """Schema for creating a customer."""
    pass


class CustomerResponse(CustomerBase):
    """Schema for customer response."""
    id: str
    total_tickets: int = 0
    average_sentiment: Optional[float] = Field(None, ge=-1.0, le=1.0)
    preferred_channel: ChannelEnum = ChannelEnum.EMAIL
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Ticket Schemas

class TicketBase(BaseModel):
    """Base ticket schema."""
    channel: ChannelEnum = Field(..., description="Origin channel")
    subject: Optional[str] = Field(None, max_length=500)
    description: str = Field(..., min_length=1, description="Ticket description")
    priority: PriorityEnum = PriorityEnum.NORMAL


class TicketCreate(TicketBase):
    """Schema for creating a ticket."""
    customer_id: str = Field(..., description="Customer ID")
    conversation_id: Optional[str] = Field(None, description="Related conversation ID")


class TicketUpdate(BaseModel):
    """Schema for updating a ticket."""
    subject: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    priority: Optional[PriorityEnum] = None
    status: Optional[TicketStatusEnum] = None
    assigned_to: Optional[str] = None
    escalation_reason: Optional[str] = Field(None, max_length=500)


class TicketResponse(TicketBase):
    """Schema for ticket response."""
    id: str
    ticket_number: str
    customer_id: str
    conversation_id: Optional[str]
    status: TicketStatusEnum
    sentiment_score: Optional[float] = Field(None, ge=-1.0, le=1.0)
    assigned_to: Optional[str]
    escalation_reason: Optional[str]
    created_at: datetime
    first_response_at: Optional[datetime]
    resolved_at: Optional[datetime]
    closed_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)


# Conversation Schemas

class ConversationBase(BaseModel):
    """Base conversation schema."""
    topic: Optional[str] = Field(None, max_length=500)
    status: ConversationStatusEnum = ConversationStatusEnum.OPEN


class ConversationCreate(ConversationBase):
    """Schema for creating a conversation."""
    customer_id: str = Field(..., description="Customer ID")


class ConversationResponse(ConversationBase):
    """Schema for conversation response."""
    id: str
    customer_id: str
    channel_history: List[str] = []
    resolution_status: str = "unresolved"
    sentiment_trend: Optional[Dict[str, Any]] = None
    opened_at: datetime
    resolved_at: Optional[datetime]
    last_activity_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Message Schemas

class MessageBase(BaseModel):
    """Base message schema."""
    channel: ChannelEnum
    direction: MessageDirectionEnum
    content: str = Field(..., min_length=1, description="Message content")
    content_html: Optional[str] = None


class MessageCreate(MessageBase):
    """Schema for creating a message."""
    conversation_id: str = Field(..., description="Conversation ID")
    ticket_id: Optional[str] = Field(None, description="Related ticket ID")
    message_id: str = Field(..., description="Unique message ID from channel")


class MessageResponse(MessageBase):
    """Schema for message response."""
    id: str
    message_id: str
    conversation_id: str
    ticket_id: Optional[str]
    sentiment_score: Optional[float] = Field(None, ge=-1.0, le=1.0)
    sentiment_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    topics: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    in_reply_to: Optional[str] = None
    references: Optional[List[str]] = None
    sent_at: datetime
    delivered_at: Optional[datetime]
    read_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)


# Escalation Schemas

class EscalationBase(BaseModel):
    """Base escalation schema."""
    reason_code: EscalationReasonEnum
    reason_details: Optional[str] = None
    assigned_team: Optional[str] = Field(None, max_length=100)
    priority: PriorityEnum = PriorityEnum.NORMAL


class EscalationCreate(EscalationBase):
    """Schema for creating an escalation."""
    ticket_id: str = Field(..., description="Ticket ID")


class EscalationResponse(EscalationBase):
    """Schema for escalation response."""
    id: str
    escalation_number: str
    ticket_id: str
    assigned_to: Optional[str]
    status: str = "pending"
    conversation_context: Optional[Dict[str, Any]] = None
    sentiment_trend: Optional[Dict[str, Any]] = None
    attempted_resolutions: Optional[List[str]] = None
    created_at: datetime
    assigned_at: Optional[datetime]
    resolved_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)


# Web Form Schemas

class WebFormRequest(BaseModel):
    """Schema for web form submission."""
    email: EmailStr = Field(..., description="Customer email")
    name: Optional[str] = Field(None, max_length=255)
    subject: Optional[str] = Field(None, max_length=500)
    message: str = Field(..., min_length=1, max_length=2000, description="Support message")
    priority: PriorityEnum = PriorityEnum.NORMAL
    category: Optional[str] = Field(None, description="Support category")


class WebFormResponse(BaseModel):
    """Schema for web form response."""
    success: bool = True
    ticket_number: str
    message: str = "Your support request has been submitted successfully"
    estimated_response_time: str = "30 seconds"


# Metrics Schemas

class MetricsResponse(BaseModel):
    """Schema for system metrics."""
    total_tickets: int
    open_tickets: int
    avg_response_time_seconds: float
    ai_resolution_rate: float = Field(..., ge=0.0, le=1.0)
    escalation_rate: float = Field(..., ge=0.0, le=1.0)
    avg_sentiment: Optional[float] = Field(None, ge=-1.0, le=1.0)
    channel_breakdown: Dict[str, int] = {}


# Error Schemas

class ErrorResponse(BaseModel):
    """Schema for error responses."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None


# List Response Schemas

class TicketListResponse(BaseModel):
    """Schema for list of tickets."""
    tickets: List[TicketResponse]
    total: int
    limit: int
    offset: int


class CustomerHistoryResponse(BaseModel):
    """Schema for customer history."""
    customer: CustomerResponse
    conversations: List[ConversationResponse] = []
    tickets: List[TicketResponse] = []
    total_tickets: int
    average_sentiment: Optional[float] = None
