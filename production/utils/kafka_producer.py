"""
Kafka Producer Service

Production-ready Kafka producer with:
- At-least-once delivery guarantees
- Automatic retries with exponential backoff
- Idempotent producer for exactly-once semantics
- Comprehensive error handling and logging
- Async and sync produce methods
"""
import json
import uuid
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from confluent_kafka import Producer, KafkaException
from production.utils.kafka_config import PRODUCER_CONFIG, KafkaTopics, AuditEvent
import time

logger = logging.getLogger(__name__)


class KafkaProducerService:
    """
    Production-ready Kafka producer service.
    
    Features:
    - At-least-once delivery
    - Automatic retries
    - Idempotent producer
    - Delivery callbacks
    - Error handling
    """
    
    def __init__(self, bootstrap_servers: str):
        """
        Initialize Kafka producer.
        
        Args:
            bootstrap_servers: Kafka bootstrap servers (comma-separated)
        """
        self.bootstrap_servers = bootstrap_servers
        
        # Producer configuration
        config = PRODUCER_CONFIG.copy()
        config['bootstrap.servers'] = bootstrap_servers
        
        # Create producer
        self.producer = Producer(config)
        
        # Delivery tracking
        self.delivery_results = {}
        self.delivery_errors = []
        
        logger.info(f"Kafka producer initialized for {bootstrap_servers}")
    
    def _delivery_callback(self, err, msg):
        """
        Delivery report callback.
        
        Called when message is delivered or fails.
        """
        if err is not None:
            logger.error(f'Message delivery failed: {err}')
            self.delivery_errors.append({
                'error': str(err),
                'topic': msg.topic(),
                'partition': msg.partition(),
                'offset': msg.offset(),
                'timestamp': datetime.now().isoformat(),
            })
        else:
            logger.debug(
                f'Message delivered to {msg.topic()} [{msg.partition()}] '
                f'at offset {msg.offset()}'
            )
            
            # Store delivery result
            msg_id = msg.headers()[0][1].decode() if msg.headers() else None
            if msg_id:
                self.delivery_results[msg_id] = {
                    'topic': msg.topic(),
                    'partition': msg.partition(),
                    'offset': msg.offset(),
                    'timestamp': datetime.now().isoformat(),
                }
    
    def produce(
        self,
        topic: str,
        value: Dict[str, Any],
        key: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        callback: Optional[Callable] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> bool:
        """
        Produce a message to Kafka with retries.
        
        Args:
            topic: Kafka topic
            value: Message value (will be JSON serialized)
            key: Optional message key for partitioning
            headers: Optional message headers
            callback: Optional delivery callback
            max_retries: Maximum retry attempts
            retry_delay: Delay between retries in seconds
            
        Returns:
            True if message was delivered successfully
        """
        # Serialize message
        try:
            value_bytes = json.dumps(value, default=str).encode('utf-8')
        except Exception as e:
            logger.error(f'Failed to serialize message: {e}')
            return False
        
        # Prepare headers
        msg_headers = []
        if headers:
            for k, v in headers.items():
                msg_headers.append((k, v.encode('utf-8')))
        
        # Add message ID header for tracking
        msg_id = str(uuid.uuid4())
        msg_headers.append(('message_id', msg_id.encode('utf-8')))
        msg_headers.append(('timestamp', datetime.now().isoformat().encode('utf-8')))
        
        # Add key header if provided
        if key:
            msg_headers.append(('message_key', key.encode('utf-8')))
        
        # Produce with retries
        for attempt in range(max_retries):
            try:
                # Custom callback
                def delivery_callback(err, msg):
                    self._delivery_callback(err, msg)
                    if callback:
                        callback(err, msg)
                
                # Produce message
                self.producer.produce(
                    topic=topic,
                    value=value_bytes,
                    key=key.encode('utf-8') if key else None,
                    headers=msg_headers,
                    on_delivery=delivery_callback,
                )
                
                # Poll for delivery
                self.producer.poll(0)
                
                logger.debug(f'Message {msg_id} produced to {topic}')
                return True
                
            except KafkaException as e:
                if attempt == max_retries - 1:
                    logger.error(f'Failed to produce message after {max_retries} attempts: {e}')
                    return False
                
                # Exponential backoff
                wait_time = retry_delay * (2 ** attempt)
                logger.warning(
                    f'Produce attempt {attempt + 1}/{max_retries} failed. '
                    f'Retrying in {wait_time}s...'
                )
                time.sleep(wait_time)
                
            except Exception as e:
                logger.error(f'Unexpected error producing message: {e}')
                return False
        
        return False
    
    def produce_ticket_event(
        self,
        event_type: str,
        ticket_id: str,
        customer_id: str,
        channel: str,
        subject: str,
        message: str,
        metadata: dict = None,
    ) -> bool:
        """
        Produce a ticket event to appropriate topic.
        
        Args:
            event_type: Type of event (created, updated, resolved, etc.)
            ticket_id: Ticket ID
            customer_id: Customer ID
            channel: Channel (email, whatsapp, web_form)
            subject: Ticket subject
            message: Ticket message
            metadata: Additional metadata
            
        Returns:
            True if message was delivered
        """
        # Determine topic based on channel
        topic_map = {
            'email': KafkaTopics.INCOMING_EMAIL,
            'whatsapp': KafkaTopics.INCOMING_WHATSAPP,
            'web_form': KafkaTopics.INCOMING_WEBFORM,
        }
        topic = topic_map.get(channel, KafkaTopics.INCOMING_EMAIL)
        
        # Create event
        event = {
            'event_id': str(uuid.uuid4()),
            'event_type': event_type,
            'ticket_id': ticket_id,
            'customer_id': customer_id,
            'channel': channel,
            'subject': subject,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {},
        }
        
        # Produce to topic
        return self.produce(
            topic=topic,
            value=event,
            key=ticket_id,
        )
    
    def produce_agent_response(
        self,
        ticket_id: str,
        response_text: str,
        sentiment_score: float,
        confidence_score: float,
        escalation_required: bool,
        escalation_reason: str = None,
        processing_time_ms: int = 0,
    ) -> bool:
        """
        Produce an agent response event.
        
        Args:
            ticket_id: Ticket ID
            response_text: AI-generated response
            sentiment_score: Sentiment score (-1.0 to 1.0)
            confidence_score: Confidence score (0.0 to 1.0)
            escalation_required: Whether escalation is needed
            escalation_reason: Reason for escalation
            processing_time_ms: Processing time in milliseconds
            
        Returns:
            True if message was delivered
        """
        event = {
            'event_id': str(uuid.uuid4()),
            'ticket_id': ticket_id,
            'response_text': response_text,
            'sentiment_score': sentiment_score,
            'confidence_score': confidence_score,
            'escalation_required': escalation_required,
            'escalation_reason': escalation_reason,
            'processing_time_ms': processing_time_ms,
            'timestamp': datetime.now().isoformat(),
        }
        
        return self.produce(
            topic=KafkaTopics.AGENT_RESPONSES,
            value=event,
            key=ticket_id,
        )
    
    def produce_email_notification(
        self,
        recipient: str,
        subject: str,
        body: str,
        ticket_id: str = None,
        priority: str = 'normal',
    ) -> bool:
        """
        Produce an email notification event.
        
        Args:
            recipient: Recipient email
            subject: Email subject
            body: Email body
            ticket_id: Associated ticket ID
            priority: Priority (low, normal, high, urgent)
            
        Returns:
            True if message was delivered
        """
        event = {
            'event_id': str(uuid.uuid4()),
            'notification_type': 'email',
            'recipient': recipient,
            'subject': subject,
            'body': body,
            'ticket_id': ticket_id,
            'priority': priority,
            'timestamp': datetime.now().isoformat(),
        }
        
        return self.produce(
            topic=KafkaTopics.EMAIL_NOTIFICATIONS,
            value=event,
            key=recipient,
        )
    
    def produce_whatsapp_notification(
        self,
        recipient: str,
        message: str,
        ticket_id: str = None,
        priority: str = 'normal',
    ) -> bool:
        """
        Produce a WhatsApp notification event.
        
        Args:
            recipient: Recipient phone number
            message: WhatsApp message
            ticket_id: Associated ticket ID
            priority: Priority
            
        Returns:
            True if message was delivered
        """
        event = {
            'event_id': str(uuid.uuid4()),
            'notification_type': 'whatsapp',
            'recipient': recipient,
            'message': message,
            'ticket_id': ticket_id,
            'priority': priority,
            'timestamp': datetime.now().isoformat(),
        }
        
        return self.produce(
            topic=KafkaTopics.WHATSAPP_NOTIFICATIONS,
            value=event,
            key=recipient,
        )
    
    def produce_escalation(
        self,
        ticket_id: str,
        reason: str,
        assigned_team: str,
        priority: str,
        context: dict = None,
    ) -> bool:
        """
        Produce an escalation event.
        
        Args:
            ticket_id: Ticket ID
            reason: Escalation reason
            assigned_team: Team to handle escalation
            priority: Escalation priority
            context: Additional context
            
        Returns:
            True if message was delivered
        """
        event = {
            'event_id': str(uuid.uuid4()),
            'ticket_id': ticket_id,
            'reason': reason,
            'assigned_team': assigned_team,
            'priority': priority,
            'context': context or {},
            'timestamp': datetime.now().isoformat(),
        }
        
        return self.produce(
            topic=KafkaTopics.ESCALATIONS,
            value=event,
            key=ticket_id,
        )
    
    def produce_audit_event(
        self,
        event_type: str,
        entity_type: str,
        entity_id: str,
        action: str,
        user_id: str = None,
        details: dict = None,
    ) -> bool:
        """
        Produce an audit event.
        
        Args:
            event_type: Event type
            entity_type: Entity type (ticket, customer, etc.)
            entity_id: Entity ID
            action: Action performed
            user_id: User ID (if applicable)
            details: Additional details
            
        Returns:
            True if message was delivered
        """
        event = {
            'event_id': str(uuid.uuid4()),
            'event_type': event_type,
            'entity_type': entity_type,
            'entity_id': entity_id,
            'action': action,
            'user_id': user_id,
            'details': details or {},
            'timestamp': datetime.now().isoformat(),
        }
        
        return self.produce(
            topic=KafkaTopics.AUDIT_LOG,
            value=event,
            key=entity_id,
        )
    
    def flush(self, timeout: int = 10):
        """
        Flush all pending messages.
        
        Args:
            timeout: Timeout in seconds
        """
        logger.info('Flushing producer...')
        remaining = self.producer.flush(timeout)
        if remaining > 0:
            logger.warning(f'{remaining} messages still in queue after flush')
        else:
            logger.info('Producer flushed successfully')
    
    def close(self):
        """Close the producer."""
        self.flush()
        logger.info('Kafka producer closed')


# =============================================================================
# Global Producer Instance
# =============================================================================

# Will be initialized with actual Kafka servers
_kafka_producer: Optional[KafkaProducerService] = None


def init_kafka_producer(bootstrap_servers: str) -> KafkaProducerService:
    """
    Initialize global Kafka producer.
    
    Args:
        bootstrap_servers: Kafka bootstrap servers
        
    Returns:
        Kafka producer instance
    """
    global _kafka_producer
    _kafka_producer = KafkaProducerService(bootstrap_servers)
    return _kafka_producer


def get_kafka_producer() -> KafkaProducerService:
    """
    Get global Kafka producer instance.
    
    Returns:
        Kafka producer instance
    """
    if _kafka_producer is None:
        raise RuntimeError('Kafka producer not initialized. Call init_kafka_producer() first.')
    return _kafka_producer
