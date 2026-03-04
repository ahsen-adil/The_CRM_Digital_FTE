"""
Kafka Configuration and Topics for Customer Success Digital FTE

Production-ready Kafka setup with:
- Topic definitions
- Consumer group configurations
- Producer configurations
- Retry policies
- At-least-once delivery guarantees
"""
from typing import Dict, Any


# =============================================================================
# Kafka Topics
# =============================================================================

class KafkaTopics:
    """Kafka topic definitions"""
    
    # Incoming messages from all channels
    INCOMING_EMAIL = "tickets.incoming.email"
    INCOMING_WHATSAPP = "tickets.incoming.whatsapp"
    INCOMING_WEBFORM = "tickets.incoming.webform"
    
    # Agent processing
    AGENT_PROCESSING = "tickets.agent.processing"
    AGENT_RESPONSES = "tickets.agent.responses"
    
    # Escalations
    ESCALATIONS = "tickets.escalations"
    
    # Outbound notifications
    EMAIL_NOTIFICATIONS = "notifications.email"
    WHATSAPP_NOTIFICATIONS = "notifications.whatsapp"
    
    # Audit and logging
    AUDIT_LOG = "audit.log"
    METRICS = "metrics.events"


# =============================================================================
# Producer Configuration
# =============================================================================

PRODUCER_CONFIG = {
    # Reliability
    'acks': 'all',  # Wait for all replicas to acknowledge
    'retries': 5,  # Retry up to 5 times
    'retry.backoff.ms': 1000,  # Wait 1s between retries
    
    # Performance
    'batch.size': 16384,  # 16KB batch size
    'linger.ms': 5,  # Wait up to 5ms for batch to fill
    'compression.type': 'snappy',  # Compress messages
    
    # Reliability
    'enable.idempotence': True,  # Exactly-once semantics
    'max.in.flight.requests.per.connection': 5,
    
    # Timeout
    'request.timeout.ms': 30000,
    'delivery.timeout.ms': 120000,
}


# =============================================================================
# Consumer Configuration
# =============================================================================

CONSUMER_CONFIG = {
    # Consumer group
    'auto.offset.reset': 'earliest',  # Start from earliest if no offset
    
    # At-least-once delivery
    'enable.auto.commit': False,  # Manual commit for at-least-once
    
    # Session management
    'session.timeout.ms': 30000,
    'heartbeat.interval.ms': 10000,
}


# =============================================================================
# Topic Configurations
# =============================================================================

TOPIC_CONFIGS: Dict[str, Dict[str, Any]] = {
    # High-priority topics (agent processing)
    KafkaTopics.AGENT_PROCESSING: {
        'num_partitions': 6,
        'replication_factor': 3,
        'retention.ms': 604800000,  # 7 days
        'cleanup.policy': 'delete',
    },
    
    # Response topics
    KafkaTopics.AGENT_RESPONSES: {
        'num_partitions': 3,
        'replication_factor': 3,
        'retention.ms': 259200000,  # 3 days
        'cleanup.policy': 'delete',
    },
    
    # Escalations (keep longer for audit)
    KafkaTopics.ESCALATIONS: {
        'num_partitions': 3,
        'replication_factor': 3,
        'retention.ms': 2592000000,  # 30 days
        'cleanup.policy': 'delete',
    },
    
    # Notification queues
    KafkaTopics.EMAIL_NOTIFICATIONS: {
        'num_partitions': 3,
        'replication_factor': 3,
        'retention.ms': 86400000,  # 1 day
        'cleanup.policy': 'delete',
    },
    
    KafkaTopics.WHATSAPP_NOTIFICATIONS: {
        'num_partitions': 3,
        'replication_factor': 3,
        'retention.ms': 86400000,  # 1 day
        'cleanup.policy': 'delete',
    },
    
    # Audit log (keep forever)
    KafkaTopics.AUDIT_LOG: {
        'num_partitions': 6,
        'replication_factor': 3,
        'retention.ms': -1,  # Forever
        'cleanup.policy': 'compact',
    },
    
    # Metrics
    KafkaTopics.METRICS: {
        'num_partitions': 3,
        'replication_factor': 3,
        'retention.ms': 604800000,  # 7 days
        'cleanup.policy': 'delete',
    },
}


# =============================================================================
# Message Schemas
# =============================================================================

class TicketEvent:
    """Schema for ticket events"""
    def __init__(
        self,
        event_id: str,
        event_type: str,
        ticket_id: str,
        customer_id: str,
        channel: str,
        subject: str,
        message: str,
        timestamp: str,
        metadata: dict = None
    ):
        self.event_id = event_id
        self.event_type = event_type
        self.ticket_id = ticket_id
        self.customer_id = customer_id
        self.channel = channel
        self.subject = subject
        self.message = message
        self.timestamp = timestamp
        self.metadata = metadata or {}
    
    def to_dict(self) -> dict:
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'ticket_id': self.ticket_id,
            'customer_id': self.customer_id,
            'channel': self.channel,
            'subject': self.subject,
            'message': self.message,
            'timestamp': self.timestamp,
            'metadata': self.metadata,
        }


class AgentResponse:
    """Schema for agent responses"""
    def __init__(
        self,
        event_id: str,
        ticket_id: str,
        response_text: str,
        sentiment_score: float,
        confidence_score: float,
        escalation_required: bool,
        escalation_reason: str = None,
        processing_time_ms: int = 0,
        metadata: dict = None
    ):
        self.event_id = event_id
        self.ticket_id = ticket_id
        self.response_text = response_text
        self.sentiment_score = sentiment_score
        self.confidence_score = confidence_score
        self.escalation_required = escalation_required
        self.escalation_reason = escalation_reason
        self.processing_time_ms = processing_time_ms
        self.metadata = metadata or {}
    
    def to_dict(self) -> dict:
        return {
            'event_id': self.event_id,
            'ticket_id': self.ticket_id,
            'response_text': self.response_text,
            'sentiment_score': self.sentiment_score,
            'confidence_score': self.confidence_score,
            'escalation_required': self.escalation_required,
            'escalation_reason': self.escalation_reason,
            'processing_time_ms': self.processing_time_ms,
            'metadata': self.metadata,
        }


class NotificationEvent:
    """Schema for notification events"""
    def __init__(
        self,
        event_id: str,
        notification_type: str,
        recipient: str,
        subject: str,
        body: str,
        ticket_id: str = None,
        priority: str = 'normal',
        metadata: dict = None
    ):
        self.event_id = event_id
        self.notification_type = notification_type
        self.recipient = recipient
        self.subject = subject
        self.body = body
        self.ticket_id = ticket_id
        self.priority = priority
        self.metadata = metadata or {}
    
    def to_dict(self) -> dict:
        return {
            'event_id': self.event_id,
            'notification_type': self.notification_type,
            'recipient': self.recipient,
            'subject': self.subject,
            'body': self.body,
            'ticket_id': self.ticket_id,
            'priority': self.priority,
            'metadata': self.metadata,
        }


class AuditEvent:
    """Schema for audit events"""
    def __init__(
        self,
        event_id: str,
        event_type: str,
        entity_type: str,
        entity_id: str,
        action: str,
        user_id: str = None,
        details: dict = None,
        timestamp: str = None
    ):
        self.event_id = event_id
        self.event_type = event_type
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.action = action
        self.user_id = user_id
        self.details = details or {}
        self.timestamp = timestamp
    
    def to_dict(self) -> dict:
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'action': self.action,
            'user_id': self.user_id,
            'details': self.details,
            'timestamp': self.timestamp,
        }
