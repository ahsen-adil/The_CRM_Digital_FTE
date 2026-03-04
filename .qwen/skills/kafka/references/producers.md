# Producers

Building reliable Kafka producers with confluent-kafka-python.

---

## Basic Producer

```python
from confluent_kafka import Producer
import json

def delivery_callback(err, msg):
    if err:
        print(f"Delivery failed: {err}")
    else:
        print(f"Delivered to {msg.topic()}[{msg.partition()}]@{msg.offset()}")

producer = Producer({
    'bootstrap.servers': 'kafka:9092',
    'client.id': 'my-producer'
})

# Send message
producer.produce(
    topic='events',
    key='user-123',
    value=json.dumps({'action': 'login'}),
    callback=delivery_callback
)

# CRITICAL: flush to ensure delivery
producer.flush()
```

---

## Async Producer (AIOProducer)

For FastAPI and asyncio applications:

```python
from confluent_kafka import Producer
import asyncio

class AIOProducer:
    """Async wrapper for confluent-kafka Producer."""

    def __init__(self, config: dict):
        self._producer = Producer(config)
        self._loop = asyncio.get_event_loop()

    async def produce(self, topic: str, key: str, value: bytes) -> dict:
        """Async produce with delivery confirmation."""
        future = self._loop.create_future()

        def callback(err, msg):
            if err:
                self._loop.call_soon_threadsafe(
                    future.set_exception,
                    Exception(str(err))
                )
            else:
                self._loop.call_soon_threadsafe(
                    future.set_result,
                    {'partition': msg.partition(), 'offset': msg.offset()}
                )

        self._producer.produce(
            topic=topic,
            key=key.encode() if isinstance(key, str) else key,
            value=value,
            callback=callback
        )
        self._producer.poll(0)  # Trigger callback

        return await future

    async def flush(self, timeout: float = 10.0):
        """Flush with async-friendly polling."""
        while True:
            remaining = self._producer.flush(timeout=0.1)
            if remaining == 0:
                break
            await asyncio.sleep(0.01)

    def close(self):
        self._producer.flush()
```

---

## Production Configuration

```python
producer = Producer({
    # Connection
    'bootstrap.servers': 'kafka:9092',
    'client.id': 'order-service-producer',

    # Durability (CRITICAL)
    'acks': 'all',                    # Wait for all replicas
    'enable.idempotence': True,       # Prevent duplicates

    # Retries
    'retries': 2147483647,            # Infinite retries
    'retry.backoff.ms': 100,          # Backoff between retries
    'delivery.timeout.ms': 120000,    # 2 min total timeout

    # Batching (performance)
    'batch.size': 16384,              # 16KB batch
    'linger.ms': 5,                   # Wait 5ms for batch
    'compression.type': 'lz4',        # Compress batches

    # Memory
    'buffer.memory': 33554432,        # 32MB buffer
    'max.block.ms': 60000,            # Block if buffer full
})
```

### Configuration Explained

| Setting | Value | Why |
|---------|-------|-----|
| `acks=all` | Wait for ISR | Durability over speed |
| `enable.idempotence` | Exactly-once per partition | Prevents duplicates |
| `retries` | Very high | Network issues are transient |
| `linger.ms` | 5-100ms | Balance latency vs throughput |
| `compression.type` | lz4 | Fast, good ratio |

---

## Delivery Guarantees

### At-Most-Once (Fire and Forget)

```python
producer = Producer({
    'bootstrap.servers': 'kafka:9092',
    'acks': '0',  # Don't wait for ack
})

producer.produce(topic='metrics', value=data)
# No flush, no callback - may lose messages
```

### At-Least-Once (Default Recommended)

```python
producer = Producer({
    'bootstrap.servers': 'kafka:9092',
    'acks': 'all',
    'enable.idempotence': True,
    'retries': 2147483647,
})

producer.produce(topic='orders', value=data, callback=delivery_callback)
producer.flush()  # Wait for confirmation
```

### Exactly-Once (Transactions)

```python
producer = Producer({
    'bootstrap.servers': 'kafka:9092',
    'transactional.id': 'order-processor-1',  # Unique per instance
    'acks': 'all',
    'enable.idempotence': True,
})

producer.init_transactions()

try:
    producer.begin_transaction()

    producer.produce(topic='orders', value=order_data)
    producer.produce(topic='inventory', value=inventory_update)

    producer.commit_transaction()
except Exception as e:
    producer.abort_transaction()
    raise
```

---

## Error Handling

### Simple Pattern (Using retriable())

```python
from confluent_kafka import Producer

def delivery_callback(err, msg):
    if err is None:
        print(f"Delivered: {msg.topic()}[{msg.partition()}]@{msg.offset()}")
        return

    if err.retriable():
        # Transient error (network, broker restart) - will auto-retry
        print(f"Retriable error for {msg.key()}: {err}")
    else:
        # Fatal error (authorization, invalid topic) - needs intervention
        print(f"Fatal error for {msg.key()}: {err}")
        send_to_dlq(msg, err)
```

### Production Pattern (ReliableProducer with DLQ)

```python
from confluent_kafka import Producer
import json
import logging

logger = logging.getLogger(__name__)

class ReliableProducer:
    """Production producer with automatic DLQ handling."""

    def __init__(self, bootstrap_servers: str, client_id: str):
        config = {
            'bootstrap.servers': bootstrap_servers,
            'client.id': client_id,
            'acks': 'all',
            'enable.idempotence': True,
            'retries': 2147483647,
            'delivery.timeout.ms': 120000,
        }
        self.producer = Producer(config)
        self.dlq_producer = Producer(config)

    def _delivery_callback(self, err, msg):
        if err is None:
            logger.info(f"Delivered: {msg.topic()}[{msg.partition()}]@{msg.offset()}")
            return

        if err.retriable():
            logger.warning(f"Retriable error (auto-retry): {err}")
        else:
            logger.error(f"Fatal error, sending to DLQ: {err}")
            self._send_to_dlq(msg, err)

    def _send_to_dlq(self, msg, err):
        dlq_message = {
            'original_topic': msg.topic(),
            'original_key': msg.key().decode() if msg.key() else None,
            'original_value': msg.value().decode() if msg.value() else None,
            'error': str(err),
            'error_code': err.code(),
        }
        self.dlq_producer.produce(
            topic=f"{msg.topic()}.dlq",
            key=msg.key(),
            value=json.dumps(dlq_message),
        )

    def send(self, topic: str, key: str, value: dict):
        self.producer.produce(
            topic=topic,
            key=key.encode() if key else None,
            value=json.dumps(value).encode(),
            callback=self._delivery_callback,
        )
        self.producer.poll(0)

    def flush(self):
        self.producer.flush()
        self.dlq_producer.flush()

    def close(self):
        self.flush()

# Usage
producer = ReliableProducer(
    bootstrap_servers='localhost:30092',
    client_id='task-service'
)
producer.send('task-events', 'task-123', {'title': 'Buy groceries'})
producer.flush()
```

### Error Categories

| Error Type | `err.retriable()` | Action | Examples |
|------------|-------------------|--------|----------|
| Retriable | `True` | Auto-retry | Network timeout, broker restart |
| Fatal | `False` | Send to DLQ | Auth failure, topic doesn't exist |

### Buffer Full Handling

```python
def safe_produce(producer, topic, key, value, max_retries=3):
    for attempt in range(max_retries):
        try:
            producer.produce(topic=topic, key=key, value=value, callback=delivery_callback)
            producer.poll(0)
            return True
        except BufferError:
            logger.warning("Buffer full, backing off")
            producer.poll(1)  # Wait for some deliveries
            time.sleep(0.5 * (2 ** attempt))
    return False
```

---

## Message Key Design

Choose the right key based on ordering requirements and scalability:

| Use Case | Recommended Key | Ordering | Scalability |
|----------|-----------------|----------|-------------|
| Entity lifecycle | `entity_id` | ✅ Per entity | ✅ Scales with entities |
| User activity | `user_id` | ✅ Per user | ⚠️ Hot users = hot partitions |
| Multi-tenant | `tenant_id:entity_id` | ✅ Per entity | ✅ Good isolation |
| Max parallelism | `None` (round-robin) | ❌ None | ✅ Maximum |

### Example: Task Lifecycle Events

```python
# Task events: created → updated → completed
# Key by task_id ensures ordering within task

producer.produce(
    topic='task-events',
    key=f'task-{task_id}'.encode(),  # All events for this task → same partition
    value=json.dumps({
        'type': 'task.created',
        'task_id': task_id,
        'user_id': user_id,
    })
)

# Later...
producer.produce(
    topic='task-events',
    key=f'task-{task_id}'.encode(),  # Same key → same partition → ordered
    value=json.dumps({
        'type': 'task.completed',
        'task_id': task_id,
    })
)
```

### Trade-offs

| Key Choice | Pros | Cons |
|------------|------|------|
| `task_id` | Lifecycle ordering guaranteed | One busy task can't parallelize |
| `user_id` | User activity ordered | Power users create hot partitions |
| `project_id` | Project-level aggregation | Large projects = hot partitions |
| Compound `project:task` | Balanced | More complex key management |

---

## Partitioning Strategies

### Key-Based (Default)

```python
# Same key always goes to same partition
producer.produce(
    topic='user-events',
    key=f'user-{user_id}',  # Consistent hashing
    value=event_data
)
```

### Custom Partitioner

```python
from confluent_kafka import Producer

def region_partitioner(key, all_partitions, available_partitions):
    """Route by region prefix."""
    if key is None:
        return random.choice(available_partitions)

    region = key.decode().split('-')[0]  # "us-east-user-123"
    regions = {'us-east': 0, 'us-west': 1, 'eu': 2}
    return regions.get(region, 0)

# Note: confluent-kafka-python doesn't support custom partitioners directly
# Use key design instead:
key = f"{region}-{entity_id}"  # Partition by hash of full key
```

### Round-Robin

```python
# No key = round-robin
producer.produce(
    topic='logs',
    key=None,  # Distribute evenly
    value=log_entry
)
```

---

## Headers and Metadata

```python
from uuid import uuid4
import time

producer.produce(
    topic='events',
    key='order-123',
    value=order_data,
    headers=[
        ('correlation_id', str(uuid4()).encode()),
        ('trace_id', trace_id.encode()),
        ('source', 'order-service'.encode()),
        ('event_type', 'order.created'.encode()),
    ],
    timestamp=int(time.time() * 1000)  # Event time
)
```

---

## Batching for Throughput

```python
# High-throughput producer
producer = Producer({
    'bootstrap.servers': 'kafka:9092',
    'acks': 'all',

    # Aggressive batching
    'batch.size': 65536,        # 64KB batches
    'linger.ms': 50,            # Wait 50ms for batch
    'compression.type': 'lz4',

    # More in-flight
    'max.in.flight.requests.per.connection': 5,
})

# Produce many messages
for event in events:
    producer.produce(topic='events', value=event)
    producer.poll(0)  # Non-blocking poll

producer.flush()  # Final flush
```

---

## Latency vs Throughput Tuning Matrix

Use this table to configure producers based on use case:

| Scenario | linger.ms | batch.size | Compression | acks |
|----------|-----------|------------|-------------|------|
| **Real-time actions** (API responses) | 0-5 | 16KB | none/snappy | all |
| **Analytics events** (dashboards) | 10-50 | 64KB-256KB | lz4 | all |
| **Batch pipelines** (ETL) | 100-500 | 512KB-1MB | lz4/zstd | all |
| **Log aggregation** (high volume) | 500-1000 | 1MB | zstd | 1 |
| **Non-critical metrics** | 100 | 256KB | lz4 | 0 |

**Batching trigger:** Message sent when EITHER `linger.ms` expires OR `batch.size` reached.

---

## Stats Callback for Debugging

Monitor batching efficiency and diagnose throughput issues:

```python
from confluent_kafka import Producer
import json

def stats_callback(stats_json):
    """Called periodically with producer statistics."""
    stats = json.loads(stats_json)

    # Overall producer stats
    print(f"Messages in queue: {stats.get('msg_cnt', 0)}")
    print(f"Messages in flight: {stats.get('msg_size', 0)} bytes")

    # Per-topic stats
    for topic_name, topic_stats in stats.get('topics', {}).items():
        for partition_id, partition_stats in topic_stats.get('partitions', {}).items():
            batch_size = partition_stats.get('batchsize', {})
            print(f"{topic_name}[{partition_id}]:")
            print(f"  Avg batch size: {batch_size.get('avg', 0)} bytes")
            print(f"  Batch count: {batch_size.get('cnt', 0)}")

producer = Producer({
    'bootstrap.servers': 'localhost:30092',
    'linger.ms': 50,
    'batch.size': 65536,
    'stats_cb': stats_callback,
    'statistics.interval.ms': 5000,  # Stats every 5 seconds
})
```

**Use this to diagnose:**
- Batches too small → increase `linger.ms`
- Queue backing up → increase `batch.size` or producer count
- Messages not batching → check key distribution (same key = same partition)

---

## Metrics to Monitor

| Metric | Healthy | Action if Unhealthy |
|--------|---------|---------------------|
| `record-send-rate` | Stable | Check batching config |
| `record-error-rate` | ~0 | Check broker health |
| `request-latency-avg` | <100ms | Check `acks`, network |
| `buffer-available-bytes` | >50% | Increase buffer or slow down |
| `batch-size-avg` | Near `batch.size` | Increase `linger.ms` |
