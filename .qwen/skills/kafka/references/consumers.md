# Consumers

Building reliable Kafka consumers with confluent-kafka-python.

---

## Bootstrap Server Selection (CRITICAL)

**Where is your code running?**

| Location | Bootstrap Server | When |
|----------|------------------|------|
| Local Mac/Windows | `localhost:30092` | NodePort for development |
| Same K8s namespace | `dev-cluster-kafka-bootstrap:9092` | Short name |
| Different K8s namespace | `dev-cluster-kafka-bootstrap.kafka.svc.cluster.local:9092` | FQDN |

### Environment-Aware Pattern (Recommended)

```python
import os

consumer = Consumer({
    'bootstrap.servers': os.environ.get(
        'KAFKA_BOOTSTRAP_SERVERS',
        'localhost:30092'  # Default for local development
    ),
    'group.id': 'my-service',
    # ... other config
})
```

**Usage:**

```bash
# Local development (uses default localhost:30092)
python consumer.py

# Kubernetes deployment (set in Pod spec)
KAFKA_BOOTSTRAP_SERVERS=dev-cluster-kafka-bootstrap:9092 python consumer.py
```

### Kubernetes ConfigMap Pattern

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: kafka-config
data:
  KAFKA_BOOTSTRAP_SERVERS: "dev-cluster-kafka-bootstrap.kafka.svc.cluster.local:9092"
---
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      containers:
      - name: consumer
        envFrom:
        - configMapRef:
            name: kafka-config
```

### Common Mistakes

| Mistake | Symptom | Fix |
|---------|---------|-----|
| K8s DNS from local Mac | `Failed to resolve` | Use `localhost:30092` |
| `localhost:9092` in K8s | Connection refused | Use K8s service name |
| Port 9092 from local | Connection timeout | Use NodePort (30092) |

---

## Basic Consumer

```python
from confluent_kafka import Consumer, KafkaError

consumer = Consumer({
    'bootstrap.servers': 'kafka:9092',
    'group.id': 'order-processor',
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': False,  # Manual commit
})

consumer.subscribe(['order-events'])

try:
    while True:
        msg = consumer.poll(timeout=1.0)

        if msg is None:
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                continue  # End of partition
            raise KafkaException(msg.error())

        # Process message
        process(msg.value())

        # Commit after successful processing
        consumer.commit(asynchronous=False)

finally:
    consumer.close()  # Leave group cleanly
```

---

## Async Consumer (AIOConsumer)

For FastAPI and asyncio applications:

```python
from confluent_kafka import Consumer
import asyncio
from typing import Callable, Awaitable

class AIOConsumer:
    """Async wrapper for confluent-kafka Consumer."""

    def __init__(self, config: dict, topics: list[str]):
        self._consumer = Consumer(config)
        self._consumer.subscribe(topics)
        self._running = False

    async def consume(
        self,
        handler: Callable[[bytes], Awaitable[None]],
        poll_timeout: float = 1.0
    ):
        """Consume messages with async handler."""
        self._running = True
        loop = asyncio.get_event_loop()

        while self._running:
            # Poll in thread pool (blocking call)
            msg = await loop.run_in_executor(
                None,
                self._consumer.poll,
                poll_timeout
            )

            if msg is None:
                continue
            if msg.error():
                await self._handle_error(msg.error())
                continue

            try:
                await handler(msg.value())
                self._consumer.commit(asynchronous=False)
            except Exception as e:
                await self._handle_processing_error(msg, e)

    async def _handle_error(self, error):
        if error.code() != KafkaError._PARTITION_EOF:
            logger.error(f"Consumer error: {error}")

    async def _handle_processing_error(self, msg, error):
        logger.error(f"Processing failed: {error}")
        # Send to dead letter queue
        await self.send_to_dlq(msg)
        self._consumer.commit()  # Move past failed message

    def stop(self):
        self._running = False

    def close(self):
        self._consumer.close()
```

---

## Production Configuration

```python
consumer = Consumer({
    # Connection
    'bootstrap.servers': 'kafka:9092',
    'group.id': 'order-processor',
    'client.id': 'order-processor-1',

    # Offset management
    'auto.offset.reset': 'earliest',     # Start from beginning
    'enable.auto.commit': False,         # Manual commit

    # Session management
    'session.timeout.ms': 45000,         # 45s heartbeat timeout
    'heartbeat.interval.ms': 15000,      # Heartbeat every 15s
    'max.poll.interval.ms': 300000,      # 5min max processing time

    # Fetching
    'fetch.min.bytes': 1,                # Don't wait for data
    'fetch.max.wait.ms': 500,            # Max wait time
    'max.partition.fetch.bytes': 1048576, # 1MB per partition

    # Partition assignment
    'partition.assignment.strategy': 'cooperative-sticky',
})
```

### Configuration Explained

| Setting | Value | Why |
|---------|-------|-----|
| `enable.auto.commit=False` | Manual | Control when message is "done" |
| `max.poll.interval.ms` | 5 min | Time for processing before rebalance |
| `session.timeout.ms` | 45s | Detect dead consumers |
| `cooperative-sticky` | Assignment | Minimize rebalances |

---

## Consumer Groups

```
Topic: orders (4 partitions)

Group: order-processor
┌──────────────┬──────────────┬──────────────┐
│ Consumer 1   │ Consumer 2   │ Consumer 3   │
│ Partition 0  │ Partition 2  │ Partition 3  │
│ Partition 1  │              │              │
└──────────────┴──────────────┴──────────────┘

Add Consumer 4:
┌──────────────┬──────────────┬──────────────┬──────────────┐
│ Consumer 1   │ Consumer 2   │ Consumer 3   │ Consumer 4   │
│ Partition 0  │ Partition 1  │ Partition 2  │ Partition 3  │
└──────────────┴──────────────┴──────────────┴──────────────┘

Add Consumer 5 and 6 (MORE CONSUMERS THAN PARTITIONS):
┌──────────────┬──────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
│ Consumer 1   │ Consumer 2   │ Consumer 3   │ Consumer 4   │ Consumer 5   │ Consumer 6   │
│ Partition 0  │ Partition 1  │ Partition 2  │ Partition 3  │ IDLE         │ IDLE         │
└──────────────┴──────────────┴──────────────┴──────────────┴──────────────┴──────────────┘
```

### Scaling Rule

**`consumers <= partitions` for efficiency**

| Partitions | Consumers | Result |
|------------|-----------|--------|
| 4 | 2 | Each consumer handles 2 partitions |
| 4 | 4 | Each consumer handles 1 partition (optimal) |
| 4 | 6 | 4 consumers active, **2 IDLE** (wasted resources) |
| 4 | 10 | 4 consumers active, **6 IDLE** (very wasteful) |

**When to increase partitions vs consumers:**
- High lag + consumers at partition limit → increase partitions
- Low CPU per consumer → add more consumers (up to partition count)
- Need more parallelism → increase partitions first

### Group ID Best Practices

```
<service-name>-<function>

Examples:
order-service-processor     # Main processing
order-service-analytics     # Different group, same topic
notification-sender
agent-task-worker
```

---

## Offset Commit Patterns

### After Each Message (Safest)

```python
while True:
    msg = consumer.poll(1.0)
    if msg and not msg.error():
        process(msg.value())
        consumer.commit(asynchronous=False)  # Sync commit
```

### Batch Commit (Balanced)

```python
batch_size = 100
processed = 0

while True:
    msg = consumer.poll(1.0)
    if msg and not msg.error():
        process(msg.value())
        processed += 1

        if processed >= batch_size:
            consumer.commit(asynchronous=False)
            processed = 0
```

### Async Commit (Fast, Less Safe)

```python
while True:
    msg = consumer.poll(1.0)
    if msg and not msg.error():
        process(msg.value())
        consumer.commit(asynchronous=True)  # Fire and forget
```

### Manual Offset Tracking

```python
from confluent_kafka import TopicPartition

while True:
    msg = consumer.poll(1.0)
    if msg and not msg.error():
        process(msg.value())

        # Commit specific offset
        tp = TopicPartition(msg.topic(), msg.partition(), msg.offset() + 1)
        consumer.commit(offsets=[tp], asynchronous=False)
```

---

## Rebalancing

When consumers join/leave, partitions are reassigned.

### Rebalance Callback

```python
def on_assign(consumer, partitions):
    """Called when partitions assigned."""
    logger.info(f"Assigned: {partitions}")
    # Optional: seek to specific offsets

def on_revoke(consumer, partitions):
    """Called before partitions revoked."""
    logger.info(f"Revoking: {partitions}")
    # CRITICAL: commit offsets before losing partitions
    consumer.commit(asynchronous=False)

def on_lost(consumer, partitions):
    """Called when partitions lost (crash)."""
    logger.warning(f"Lost: {partitions}")
    # Cannot commit - partitions already reassigned

consumer.subscribe(
    ['orders'],
    on_assign=on_assign,
    on_revoke=on_revoke,
    on_lost=on_lost
)
```

### Cooperative Sticky Assignment

Minimizes partition movement during rebalance:

```python
consumer = Consumer({
    'partition.assignment.strategy': 'cooperative-sticky',
    # Other config...
})
```

---

## Error Handling

```python
from confluent_kafka import KafkaError, KafkaException

def consume_with_retry():
    while True:
        try:
            msg = consumer.poll(1.0)

            if msg is None:
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                elif msg.error().code() == KafkaError.UNKNOWN_TOPIC_OR_PART:
                    logger.error("Topic doesn't exist")
                    time.sleep(5)  # Wait for topic creation
                    continue
                else:
                    raise KafkaException(msg.error())

            # Process with retry
            for attempt in range(3):
                try:
                    process(msg.value())
                    break
                except TransientError:
                    time.sleep(0.5 * (2 ** attempt))
            else:
                # All retries failed - send to DLQ
                send_to_dlq(msg)

            consumer.commit()

        except KafkaException as e:
            logger.error(f"Kafka error: {e}")
            time.sleep(1)
```

---

## Dead Letter Queue (DLQ)

```python
dlq_producer = Producer({'bootstrap.servers': 'kafka:9092'})

def send_to_dlq(original_msg, error: Exception):
    """Send failed message to dead letter queue."""
    dlq_producer.produce(
        topic=f"{original_msg.topic()}.dlq",
        key=original_msg.key(),
        value=original_msg.value(),
        headers=[
            ('original_topic', original_msg.topic().encode()),
            ('original_partition', str(original_msg.partition()).encode()),
            ('original_offset', str(original_msg.offset()).encode()),
            ('error_type', type(error).__name__.encode()),
            ('error_message', str(error).encode()),
            ('failed_at', datetime.utcnow().isoformat().encode()),
        ]
    )
    dlq_producer.flush()
```

---

## Consumer Lag

Difference between latest offset and consumer position.

### Check Lag Programmatically

```python
from confluent_kafka import TopicPartition

def get_consumer_lag(consumer, topic):
    """Get lag for all partitions."""
    # Get assigned partitions
    assignment = consumer.assignment()

    # Get committed offsets
    committed = consumer.committed(assignment)

    # Get high watermarks (latest offsets)
    lag_info = []
    for tp in assignment:
        _, high = consumer.get_watermark_offsets(tp)
        committed_offset = next(
            (c.offset for c in committed if c.partition == tp.partition),
            0
        )
        lag = high - committed_offset
        lag_info.append({
            'partition': tp.partition,
            'committed': committed_offset,
            'latest': high,
            'lag': lag
        })

    return lag_info
```

### CLI Lag Check

```bash
kafka-consumer-groups.sh \
  --bootstrap-server kafka:9092 \
  --describe \
  --group order-processor
```

---

## Parallel Processing

### Multi-Threaded

```python
from concurrent.futures import ThreadPoolExecutor
import threading

class ParallelConsumer:
    def __init__(self, config, topics, workers=4):
        self._consumer = Consumer(config)
        self._consumer.subscribe(topics)
        self._executor = ThreadPoolExecutor(max_workers=workers)
        self._pending = {}
        self._lock = threading.Lock()

    def consume(self):
        while True:
            msg = self._consumer.poll(0.1)

            if msg and not msg.error():
                # Submit to thread pool
                future = self._executor.submit(self._process, msg)
                with self._lock:
                    self._pending[msg.offset()] = future

            # Commit completed
            self._commit_completed()

    def _process(self, msg):
        process(msg.value())
        return msg.offset()

    def _commit_completed(self):
        with self._lock:
            completed = [
                offset for offset, future in self._pending.items()
                if future.done()
            ]
            if completed:
                # Commit up to highest completed
                # (simplified - real impl needs partition tracking)
                self._consumer.commit()
                for offset in completed:
                    del self._pending[offset]
```

---

## Metrics to Monitor

| Metric | Healthy | Action if Unhealthy |
|--------|---------|---------------------|
| Consumer lag | Low/stable | Add consumers, check processing time |
| Rebalance rate | ~0 | Check `max.poll.interval.ms` |
| Commit rate | Matches consume rate | Check commit logic |
| Poll latency | <100ms | Check broker connectivity |
| Processing time | < `max.poll.interval.ms` | Optimize or increase timeout |
