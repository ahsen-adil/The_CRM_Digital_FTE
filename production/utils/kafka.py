"""
Kafka configuration and connection management.
Uses confluent-kafka for high-performance async message processing.
"""
from typing import Optional, Dict, Any, Callable
from confluent_kafka import Producer, Consumer, KafkaError, KafkaException
from confluent_kafka.admin import AdminClient, NewTopic
import json
import logging
from production.config import settings

logger = logging.getLogger(__name__)


class KafkaConfig:
    """Kafka configuration manager."""
    
    @staticmethod
    def get_producer_config() -> Dict[str, Any]:
        """
        Get producer configuration with production best practices.
        
        Returns:
            Dict[str, Any]: Producer configuration
        """
        return {
            'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS,
            'acks': 'all',  # Wait for all replicas to acknowledge
            'enable.idempotence': True,  # Prevent duplicate messages
            'retries': 5,
            'retry.backoff.ms': 100,
            'message.timeout.ms': 30000,
            'compression.type': 'snappy',  # Compress messages
            'batch.num.messages': 1000,  # Batch messages
            'linger.ms': 10,  # Wait up to 10ms to batch messages
        }
    
    @staticmethod
    def get_consumer_config(group_id: str) -> Dict[str, Any]:
        """
        Get consumer configuration for a specific consumer group.
        
        Args:
            group_id: Consumer group ID
            
        Returns:
            Dict[str, Any]: Consumer configuration
        """
        return {
            'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS,
            'group.id': group_id,
            'auto.offset.reset': 'earliest',  # Start from earliest message
            'enable.auto.commit': False,  # Manual commit for at-least-once delivery
            'auto.commit.interval.ms': 5000,
            'session.timeout.ms': 30000,
            'max.poll.interval.ms': 300000,  # 5 minutes max processing time
        }


class KafkaProducer:
    """Kafka producer with delivery callbacks."""
    
    def __init__(self):
        self._producer: Optional[Producer] = None
    
    def create_producer(self) -> Producer:
        """Create and configure Kafka producer."""
        config = KafkaConfig.get_producer_config()
        self._producer = Producer(config)
        logger.info("✅ Kafka producer initialized")
        return self._producer
    
    def delivery_callback(self, err: Optional[KafkaError], msg):
        """
        Callback for message delivery confirmation.
        
        Args:
            err: Error if delivery failed
            msg: Message that was delivered (or failed)
        """
        if err is not None:
            logger.error(f"❌ Message delivery failed: {err}", extra={
                "topic": msg.topic(),
                "partition": msg.partition(),
                "offset": msg.offset()
            })
        else:
            logger.debug(f"✅ Message delivered", extra={
                "topic": msg.topic(),
                "partition": msg.partition(),
                "offset": msg.offset()
            })
    
    async def produce(
        self,
        topic: str,
        value: Dict[str, Any],
        key: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        """
        Produce a message to Kafka topic.
        
        Args:
            topic: Topic name
            value: Message value (will be JSON-encoded)
            key: Optional message key for partitioning
            headers: Optional message headers
        
        Raises:
            KafkaException: If producer not initialized or message fails
        """
        if self._producer is None:
            self.create_producer()
        
        # Serialize message
        value_bytes = json.dumps(value).encode('utf-8')
        key_bytes = key.encode('utf-8') if key else None
        
        # Convert headers to Kafka format
        kafka_headers = None
        if headers:
            kafka_headers = [(k, v.encode('utf-8')) for k, v in headers.items()]
        
        # Produce message
        self._producer.produce(
            topic=topic,
            value=value_bytes,
            key=key_bytes,
            headers=kafka_headers,
            on_delivery=self.delivery_callback
        )
        
        # Flush to ensure message is sent
        self._producer.flush(timeout=10)
        
        logger.info(f"📤 Message produced to {topic}", extra={
            "topic": topic,
            "key": key
        })


class KafkaConsumer:
    """Kafka consumer with manual commit for at-least-once delivery."""
    
    def __init__(self, group_id: str, topics: list[str]):
        self.group_id = group_id
        self.topics = topics
        self._consumer: Optional[Consumer] = None
    
    def create_consumer(self) -> Consumer:
        """Create and configure Kafka consumer."""
        config = KafkaConfig.get_consumer_config(self.group_id)
        self._consumer = Consumer(config)
        self._consumer.subscribe(self.topics)
        logger.info(f"✅ Kafka consumer initialized for group '{self.group_id}'", extra={
            "topics": self.topics
        })
        return self._consumer
    
    async def consume(self, timeout: float = 1.0):
        """
        Consume a single message from Kafka.
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            Message or None if timeout
        """
        if self._consumer is None:
            self.create_consumer()
        
        msg = self._consumer.poll(timeout)
        
        if msg is None:
            return None
        
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                # End of partition, no more messages
                return None
            else:
                logger.error(f"❌ Consumer error: {msg.error()}")
                raise KafkaException(msg.error())
        
        # Parse message value
        try:
            value = json.loads(msg.value().decode('utf-8'))
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message: {e}")
            raise
        
        logger.debug(f"📥 Message consumed", extra={
            "topic": msg.topic(),
            "partition": msg.partition(),
            "offset": msg.offset(),
            "key": msg.key()
        })
        
        return {
            "topic": msg.topic(),
            "partition": msg.partition(),
            "offset": msg.offset(),
            "key": msg.key().decode('utf-8') if msg.key() else None,
            "value": value,
            "headers": {h.key: h.value.decode('utf-8') for h in msg.headers()} if msg.headers() else None,
            "timestamp": msg.timestamp()[1] if msg.timestamp() else None
        }
    
    def commit(self):
        """Commit offsets for processed messages."""
        if self._consumer:
            self._consumer.commit(asynchronous=False)
            logger.debug("✅ Offsets committed")
    
    def close(self):
        """Close consumer and commit final offsets."""
        if self._consumer:
            self._consumer.close()
            logger.info("🔒 Kafka consumer closed")


class KafkaAdmin:
    """Kafka admin client for topic management."""
    
    def __init__(self):
        self._admin_client: Optional[AdminClient] = None
    
    def create_admin_client(self) -> AdminClient:
        """Create admin client."""
        config = {
            'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS
        }
        self._admin_client = AdminClient(config)
        return self._admin_client
    
    async def create_topic(
        self,
        topic_name: str,
        num_partitions: int = 3,
        replication_factor: int = 1
    ):
        """
        Create a Kafka topic.
        
        Args:
            topic_name: Topic name
            num_partitions: Number of partitions
            replication_factor: Replication factor
        """
        if self._admin_client is None:
            self.create_admin_client()
        
        topic = NewTopic(
            topic=topic_name,
            num_partitions=num_partitions,
            replication_factor=replication_factor
        )
        
        fs = self._admin_client.create_topics([topic])
        
        # Wait for operation to complete
        for topic, f in fs.items():
            try:
                f.result()  # Raises exception if failed
                logger.info(f"✅ Topic '{topic}' created successfully")
            except KafkaException as e:
                if e.args[0].code() == KafkaError.TOPIC_ALREADY_EXISTS:
                    logger.warning(f"⚠️ Topic '{topic}' already exists")
                else:
                    logger.error(f"❌ Failed to create topic '{topic}': {e}")
                    raise


# Global instances
kafka_producer = KafkaProducer()


def get_kafka_producer() -> KafkaProducer:
    """Get Kafka producer instance."""
    return kafka_producer
