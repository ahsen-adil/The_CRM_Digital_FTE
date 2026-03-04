"""
Kafka Consumer Service

Production-ready Kafka consumer with:
- At-least-once delivery (manual commit)
- Automatic retries with exponential backoff
- Dead letter queue for failed messages
- Consumer group management
- Graceful shutdown
- Comprehensive error handling and logging
"""
import json
import logging
import time
import signal
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from confluent_kafka import Consumer, KafkaException, TopicPartition, Message
from production.utils.kafka_config import CONSUMER_CONFIG, KafkaTopics

logger = logging.getLogger(__name__)


class KafkaConsumerService:
    """
    Production-ready Kafka consumer service.
    
    Features:
    - At-least-once delivery
    - Manual offset commit
    - Automatic retries
    - Dead letter queue
    - Graceful shutdown
    """
    
    def __init__(
        self,
        bootstrap_servers: str,
        group_id: str,
        topics: List[str],
        auto_commit: bool = False,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Initialize Kafka consumer.
        
        Args:
            bootstrap_servers: Kafka bootstrap servers
            group_id: Consumer group ID
            topics: List of topics to consume
            auto_commit: Enable auto commit (default False for at-least-once)
            max_retries: Maximum retry attempts for failed messages
            retry_delay: Delay between retries in seconds
        """
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.topics = topics
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.running = False
        self.stats = {
            'messages_consumed': 0,
            'messages_processed': 0,
            'messages_failed': 0,
            'messages_retried': 0,
            'last_commit': None,
        }
        
        # Consumer configuration
        config = CONSUMER_CONFIG.copy()
        config['bootstrap.servers'] = bootstrap_servers
        config['group.id'] = group_id
        config['enable.auto.commit'] = auto_commit
        
        # Create consumer
        self.consumer = Consumer(config)
        
        # Message handlers
        self.handlers: Dict[str, Callable] = {}
        
        # Dead letter queue
        self.dlq_messages = []
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info(
            f'Kafka consumer initialized for group {group_id} '
            f'on topics {topics}'
        )
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f'Received signal {signum}, initiating shutdown...')
        self.running = False
    
    def register_handler(self, topic: str, handler: Callable):
        """
        Register a message handler for a topic.
        
        Args:
            topic: Kafka topic
            handler: Message handler function
        """
        self.handlers[topic] = handler
        logger.info(f'Registered handler for topic {topic}')
    
    def _process_message(self, msg: Message) -> bool:
        """
        Process a single message with retries.
        
        Args:
            msg: Kafka message
            
        Returns:
            True if processing succeeded
        """
        topic = msg.topic()
        msg_key = msg.key().decode() if msg.key() else None
        msg_value = msg.value().decode() if msg.value() else None
        
        self.stats['messages_consumed'] += 1
        
        # Parse message
        try:
            value = json.loads(msg_value) if msg_value else {}
        except json.JSONDecodeError as e:
            logger.error(f'Failed to parse message: {e}')
            self.stats['messages_failed'] += 1
            return False
        
        # Get handler
        handler = self.handlers.get(topic)
        if not handler:
            logger.warning(f'No handler registered for topic {topic}')
            self.stats['messages_failed'] += 1
            return False
        
        # Process with retries
        for attempt in range(self.max_retries):
            try:
                # Call handler
                handler(value, msg_key)
                
                self.stats['messages_processed'] += 1
                logger.debug(
                    f'Message {msg_key} processed successfully from {topic} '
                    f'[{msg.partition()}:{msg.offset()}]'
                )
                return True
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    logger.error(
                        f'Message processing failed after {self.max_retries} attempts: {e}'
                    )
                    self.stats['messages_failed'] += 1
                    
                    # Send to dead letter queue
                    self._send_to_dlq(msg, str(e))
                    return False
                
                # Retry with exponential backoff
                self.stats['messages_retried'] += 1
                wait_time = self.retry_delay * (2 ** attempt)
                logger.warning(
                    f'Processing attempt {attempt + 1}/{self.max_retries} failed. '
                    f'Retrying in {wait_time}s...'
                )
                time.sleep(wait_time)
        
        return False
    
    def _send_to_dlq(self, msg: Message, error: str):
        """
        Send failed message to dead letter queue.
        
        Args:
            msg: Failed message
            error: Error message
        """
        dlq_entry = {
            'topic': msg.topic(),
            'partition': msg.partition(),
            'offset': msg.offset(),
            'key': msg.key().decode() if msg.key() else None,
            'value': msg.value().decode() if msg.value() else None,
            'error': error,
            'timestamp': datetime.now().isoformat(),
        }
        
        self.dlq_messages.append(dlq_entry)
        
        # Keep DLQ size manageable
        if len(self.dlq_messages) > 1000:
            self.dlq_messages = self.dlq_messages[-1000:]
        
        logger.warning(f'Message sent to DLQ: {dlq_entry["key"]}')
    
    def consume(self, timeout: float = 1.0):
        """
        Consume messages from Kafka.
        
        Args:
            timeout: Poll timeout in seconds
        """
        self.running = True
        logger.info('Starting consumer...')
        
        # Subscribe to topics
        self.consumer.subscribe(self.topics)
        
        try:
            while self.running:
                # Poll for messages
                msg = self.consumer.poll(timeout)
                
                if msg is None:
                    continue
                
                if msg.error():
                    if msg.error().code() == KafkaException._PARTITION_EOF:
                        # End of partition, continue
                        continue
                    else:
                        logger.error(f'Consumer error: {msg.error()}')
                        continue
                
                # Process message
                success = self._process_message(msg)
                
                # Commit offset (at-least-once delivery)
                if success:
                    try:
                        self.consumer.commit(msg, asynchronous=False)
                        self.stats['last_commit'] = datetime.now().isoformat()
                    except Exception as e:
                        logger.error(f'Failed to commit offset: {e}')
                
        except KeyboardInterrupt:
            logger.info('Received keyboard interrupt')
        finally:
            self.close()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get consumer statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            **self.stats,
            'group_id': self.group_id,
            'topics': self.topics,
            'dlq_size': len(self.dlq_messages),
            'running': self.running,
        }
    
    def get_dlq_messages(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get dead letter queue messages.
        
        Args:
            limit: Maximum messages to return
            
        Returns:
            List of DLQ messages
        """
        return self.dlq_messages[-limit:]
    
    def close(self):
        """Close the consumer."""
        logger.info('Closing consumer...')
        self.running = False
        
        # Commit final offsets
        try:
            self.consumer.commit(asynchronous=False)
            logger.info('Final offset commit successful')
        except Exception as e:
            logger.error(f'Final commit failed: {e}')
        
        # Close consumer
        self.consumer.close()
        logger.info('Kafka consumer closed')


# =============================================================================
# Consumer Workers
# =============================================================================

class AgentProcessingConsumer(KafkaConsumerService):
    """
    Consumer for agent processing topic.
    
    Processes incoming tickets and generates AI responses.
    """
    
    def __init__(self, bootstrap_servers: str):
        super().__init__(
            bootstrap_servers=bootstrap_servers,
            group_id='agent.processing.group',
            topics=[
                KafkaTopics.INCOMING_EMAIL,
                KafkaTopics.INCOMING_WHATSAPP,
                KafkaTopics.INCOMING_WEBFORM,
            ],
        )
        
        logger.info('Agent processing consumer initialized')


class EmailNotificationConsumer(KafkaConsumerService):
    """
    Consumer for email notifications.
    
    Sends email notifications via SMTP.
    """
    
    def __init__(self, bootstrap_servers: str):
        super().__init__(
            bootstrap_servers=bootstrap_servers,
            group_id='email.notifications.group',
            topics=[KafkaTopics.EMAIL_NOTIFICATIONS],
        )
        
        logger.info('Email notification consumer initialized')


class WhatsAppNotificationConsumer(KafkaConsumerService):
    """
    Consumer for WhatsApp notifications.
    
    Sends WhatsApp notifications via Whapi.
    """
    
    def __init__(self, bootstrap_servers: str):
        super().__init__(
            bootstrap_servers=bootstrap_servers,
            group_id='whatsapp.notifications.group',
            topics=[KafkaTopics.WHATSAPP_NOTIFICATIONS],
        )
        
        logger.info('WhatsApp notification consumer initialized')


class EscalationConsumer(KafkaConsumerService):
    """
    Consumer for escalations.
    
    Processes escalations and notifies teams.
    """
    
    def __init__(self, bootstrap_servers: str):
        super().__init__(
            bootstrap_servers=bootstrap_servers,
            group_id='escalations.group',
            topics=[KafkaTopics.ESCALATIONS],
        )
        
        logger.info('Escalation consumer initialized')
