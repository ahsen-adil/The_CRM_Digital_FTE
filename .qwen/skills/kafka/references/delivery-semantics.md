# Delivery Semantics

Understanding and implementing message delivery guarantees.

---

## The Three Guarantees

| Guarantee | Definition | Messages Lost? | Messages Duplicated? |
|-----------|------------|----------------|---------------------|
| **At-most-once** | Fire and forget | Possible | No |
| **At-least-once** | Retry until ack | No | Possible |
| **Exactly-once** | Transactional | No | No |

---

## Decision Tree (Agent Guidance)

Use this flow to select the appropriate guarantee:

```
Q1: Can you lose messages?
├── YES → At-most-once
│         (metrics, logs, click tracking)
└── NO  → Continue to Q2

Q2: Can your consumer handle duplicates (is it idempotent)?
├── YES → At-least-once (RECOMMENDED)
│         (most applications - dedupe by ID)
└── NO  → Continue to Q3

Q3: Can you MAKE your consumer idempotent?
├── YES → At-least-once + idempotent consumer (BEST)
│         (add deduplication layer)
└── NO  → Exactly-once (LAST RESORT)
          (Kafka→Kafka only, higher latency)
```

**Critical:** Exactly-once only works when reading from Kafka AND writing to Kafka (or transactional external stores). Most consumers write to databases, call APIs, or send emails—operations outside Kafka transactions. **Idempotent consumers are almost always simpler.**

---

## At-Most-Once

**Use when:** Loss acceptable, duplicates not (rare in practice)

```python
# Producer: don't wait for acks
producer = Producer({
    'bootstrap.servers': 'kafka:9092',
    'acks': '0',  # No acknowledgment
})

producer.produce(topic='metrics', value=data)
# No flush - may lose messages

# Consumer: commit before processing
consumer = Consumer({
    'bootstrap.servers': 'kafka:9092',
    'group.id': 'metrics-reader',
    'enable.auto.commit': True,
    'auto.commit.interval.ms': 1000,
})

while True:
    msg = consumer.poll(1.0)
    if msg:
        # Offset committed before processing
        # If processing fails, message is lost
        process(msg.value())
```

**Use cases:**
- Metrics collection (occasional loss OK)
- Logging (gaps acceptable)
- Real-time analytics (latest matters, not all)

---

## At-Least-Once

**Use when:** No loss acceptable, duplicates can be handled (most common)

```python
# Producer: wait for all replicas
producer = Producer({
    'bootstrap.servers': 'kafka:9092',
    'acks': 'all',
    'enable.idempotence': True,
    'retries': 2147483647,
    'delivery.timeout.ms': 120000,
})

def delivery_callback(err, msg):
    if err:
        # Handle failure - retry or alert
        logger.error(f"Delivery failed: {err}")
        retry_or_alert(msg)

producer.produce(
    topic='orders',
    value=order_data,
    callback=delivery_callback
)
producer.flush()  # Wait for confirmation

# Consumer: commit after processing
consumer = Consumer({
    'bootstrap.servers': 'kafka:9092',
    'group.id': 'order-processor',
    'enable.auto.commit': False,
})

while True:
    msg = consumer.poll(1.0)
    if msg and not msg.error():
        try:
            process(msg.value())
            consumer.commit()  # Only after success
        except Exception as e:
            # Don't commit - will reprocess
            logger.error(f"Processing failed: {e}")
```

### Handling Duplicates (Idempotency)

```python
# Option 1: Database unique constraint
def process_order(order):
    try:
        db.execute(
            "INSERT INTO orders (order_id, ...) VALUES (%s, ...)",
            (order['id'], ...)
        )
    except UniqueViolation:
        logger.info(f"Duplicate order {order['id']}, skipping")

# Option 2: Idempotency key tracking
processed_ids = redis.Redis()

def process_order(order):
    key = f"processed:{order['id']}"
    if processed_ids.exists(key):
        return  # Already processed

    do_processing(order)
    processed_ids.setex(key, 86400, "1")  # 24h TTL

# Option 3: Version/timestamp check
def process_order(order):
    current = db.get_order(order['id'])
    if current and current.version >= order['version']:
        return  # Stale or duplicate

    db.upsert_order(order)
```

---

## Exactly-Once (Transactions)

**Use when:** Financial, critical data, no duplicates allowed

### Producer Transactions

```python
producer = Producer({
    'bootstrap.servers': 'kafka:9092',
    'transactional.id': 'order-processor-1',  # Must be unique per instance
    'acks': 'all',
    'enable.idempotence': True,
})

# Initialize once at startup
producer.init_transactions()

def process_and_produce(input_msg):
    try:
        producer.begin_transaction()

        # Process input
        result = transform(input_msg.value())

        # Produce outputs (all or nothing)
        producer.produce(topic='processed-orders', value=result)
        producer.produce(topic='audit-log', value=audit_entry)

        # Commit consumer offset as part of transaction
        producer.send_offsets_to_transaction(
            consumer.position(consumer.assignment()),
            consumer.consumer_group_metadata()
        )

        producer.commit_transaction()

    except Exception as e:
        producer.abort_transaction()
        raise
```

### Consumer with Transactions

```python
consumer = Consumer({
    'bootstrap.servers': 'kafka:9092',
    'group.id': 'exactly-once-processor',
    'isolation.level': 'read_committed',  # CRITICAL
    'enable.auto.commit': False,
})
```

### Transactional ID Strategy

```
<service>-<instance>

Examples:
order-processor-0
order-processor-1
payment-handler-pod-abc123
```

**Important:** Same transactional.id across restarts = zombie fencing works.

---

## Consume-Process-Produce Pattern

The most common exactly-once pattern:

```python
class ExactlyOnceProcessor:
    def __init__(self, consumer_config, producer_config, input_topic, output_topic):
        self.consumer = Consumer({
            **consumer_config,
            'isolation.level': 'read_committed',
            'enable.auto.commit': False,
        })
        self.producer = Producer({
            **producer_config,
            'transactional.id': f'{input_topic}-processor-{uuid.uuid4()}',
            'acks': 'all',
            'enable.idempotence': True,
        })
        self.input_topic = input_topic
        self.output_topic = output_topic

    def start(self):
        self.consumer.subscribe([self.input_topic])
        self.producer.init_transactions()

    def run(self):
        while True:
            msg = self.consumer.poll(1.0)
            if msg is None or msg.error():
                continue

            try:
                self.producer.begin_transaction()

                # Process
                result = self.process(msg.value())

                # Produce result
                self.producer.produce(self.output_topic, value=result)

                # Commit consumer offset in transaction
                self.producer.send_offsets_to_transaction(
                    self.consumer.position(self.consumer.assignment()),
                    self.consumer.consumer_group_metadata()
                )

                self.producer.commit_transaction()

            except Exception as e:
                self.producer.abort_transaction()
                logger.error(f"Transaction failed: {e}")

    def process(self, value):
        # Your processing logic
        return transform(value)
```

---

## Decision Matrix

| Scenario | Guarantee | Why |
|----------|-----------|-----|
| Metrics/logs | At-most-once | Loss acceptable |
| Event notifications | At-least-once | Idempotent handlers |
| Order processing | At-least-once | Dedupe by order ID |
| Financial transactions | Exactly-once | No tolerance for errors |
| Agent task dispatch | At-least-once | Idempotent task execution |
| Saga coordination | Exactly-once | Compensation complexity |

---

## Performance Comparison

| Guarantee | Latency | Throughput | Complexity |
|-----------|---------|------------|------------|
| At-most-once | Lowest | Highest | Lowest |
| At-least-once | Medium | Medium | Low |
| Exactly-once | Highest | Lowest | High |

### Exactly-Once Overhead

- ~2x latency (transaction commit)
- ~20-30% throughput reduction
- Additional broker coordination

---

## Gotchas

### Producer

| Gotcha | Symptom | Fix |
|--------|---------|-----|
| `acks=1` | Data loss on leader failure | Use `acks=all` |
| No idempotence | Duplicates on retry | `enable.idempotence=true` |
| Low `delivery.timeout.ms` | Premature failure | Increase to 2+ minutes |

### Consumer

| Gotcha | Symptom | Fix |
|--------|---------|-----|
| Auto-commit | Message loss on crash | Manual commit after processing |
| Commit before process | Message loss | Commit after success |
| No `read_committed` | See uncommitted (aborted) messages | Set isolation level |

### Transactions

| Gotcha | Symptom | Fix |
|--------|---------|-----|
| Same transactional.id | Producer fenced | Unique ID per instance |
| Long transactions | Timeout, abort | Keep transactions short |
| Missing `send_offsets_to_transaction` | Consumer reprocesses | Include offset commit |
