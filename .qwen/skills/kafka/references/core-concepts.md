# Core Concepts

Fundamental Kafka architecture and terminology.

---

## The Log Abstraction

Kafka is a **distributed commit log**. Everything flows from this:

```
Partition 0: [msg0][msg1][msg2][msg3][msg4]  ← append-only
                                      ↑
                                   offset 4

Partition 1: [msg0][msg1][msg2]
                          ↑
                       offset 2
```

- Messages are **immutable** once written
- Order guaranteed **within partition only**
- Offsets are sequential integers per partition

---

## Topics

Named stream of records (like a database table for events).

```yaml
# Topic properties
name: order-events
partitions: 12          # Parallelism units
replication-factor: 3   # Copies across brokers
retention.ms: 604800000 # 7 days
cleanup.policy: delete  # or "compact"
```

### Naming Conventions

```
<domain>.<entity>.<event-type>

Examples:
orders.order.created
payments.payment.completed
agents.task.assigned
notifications.email.sent
```

### Partition Count Guidelines

| Use Case | Partitions | Rationale |
|----------|------------|-----------|
| Low volume | 3-6 | Match replication factor |
| Medium | 12-24 | Standard parallelism |
| High throughput | 50-100 | Match consumer instances |
| Event sourcing | 1 per aggregate | Ordering guarantee |

**Rule of thumb:** partitions ≥ max consumer instances you'll ever need.

---

## Producers

Write messages to topics.

```python
from confluent_kafka import Producer

producer = Producer({
    'bootstrap.servers': 'kafka:9092',
    'acks': 'all',
    'enable.idempotence': True
})

# Async send with callback
producer.produce(
    topic='order-events',
    key=order_id.encode(),     # Determines partition
    value=json.dumps(event),
    callback=delivery_report
)
producer.flush()  # Wait for delivery
```

### Key Concepts

| Concept | Purpose |
|---------|---------|
| **Key** | Partition routing (same key → same partition) |
| **Value** | Message payload |
| **Headers** | Metadata (correlation ID, trace ID) |
| **Timestamp** | Event time or ingestion time |

### Partitioning Strategy

```
key = None     → Round-robin across partitions
key = "user-1" → hash(key) % num_partitions → consistent partition
key = custom   → Implement partitioner class
```

---

## Consumers

Read messages from topics.

```python
from confluent_kafka import Consumer

consumer = Consumer({
    'bootstrap.servers': 'kafka:9092',
    'group.id': 'order-processor',
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': False  # Manual commit
})

consumer.subscribe(['order-events'])

while True:
    msg = consumer.poll(timeout=1.0)
    if msg is None:
        continue
    if msg.error():
        handle_error(msg.error())
        continue

    process(msg.value())
    consumer.commit(asynchronous=False)  # After processing
```

### Consumer Groups

```
Topic: order-events (4 partitions)

Consumer Group: order-processor
├── Consumer 1 → Partition 0, 1
├── Consumer 2 → Partition 2
└── Consumer 3 → Partition 3

Key rules:
- Each partition → exactly one consumer in group
- Consumer count > partitions → some idle
- Consumer dies → partitions reassigned (rebalance)
```

---

## Offsets

Consumer's position in a partition.

```
Partition: [0][1][2][3][4][5][6][7][8][9]
                      ↑           ↑
                   committed   current
                   offset=3    position=7
```

### Offset Management

| Strategy | When | Risk |
|----------|------|------|
| Auto-commit | Simple cases | May lose messages on crash |
| Commit after process | Reliability | May reprocess on crash |
| Commit before process | Speed | May lose on crash |
| Transactional | Exactly-once | Complexity, latency |

### Offset Reset Policies

```python
'auto.offset.reset': 'earliest'  # Start from beginning
'auto.offset.reset': 'latest'    # Start from now
'auto.offset.reset': 'none'      # Error if no offset
```

---

## Brokers

Kafka server instances.

```
Cluster (3 brokers)
├── Broker 0 (controller)
│   ├── topic-a/partition-0 (leader)
│   ├── topic-a/partition-1 (follower)
│   └── topic-b/partition-0 (follower)
├── Broker 1
│   ├── topic-a/partition-0 (follower)
│   ├── topic-a/partition-1 (leader)
│   └── topic-b/partition-0 (follower)
└── Broker 2
    ├── topic-a/partition-0 (follower)
    ├── topic-a/partition-1 (follower)
    └── topic-b/partition-0 (leader)
```

### Replication

- **Leader**: Handles all reads/writes for partition
- **Followers**: Replicate from leader
- **ISR (In-Sync Replicas)**: Followers caught up with leader
- **Replication factor 3**: Survives 2 broker failures

---

## KRaft Mode

Kafka's built-in consensus (replaces ZooKeeper).

```
Before (ZooKeeper):
┌─────────────┐     ┌─────────────┐
│   Kafka     │────▶│  ZooKeeper  │
│  Brokers    │     │  (metadata) │
└─────────────┘     └─────────────┘

After (KRaft):
┌─────────────────────────────────┐
│            Kafka                │
│  ┌──────────┐  ┌─────────────┐  │
│  │Controllers│  │   Brokers   │  │
│  │(metadata) │  │  (data)     │  │
│  └──────────┘  └─────────────┘  │
└─────────────────────────────────┘
```

### Benefits

- Simpler architecture (no ZK cluster to manage)
- Faster metadata operations
- Better scalability (millions of partitions)
- Single security model

### Node Roles

| Role | Function |
|------|----------|
| Controller | Metadata management, leader election |
| Broker | Message storage, client serving |
| Combined | Both roles (dev/small clusters) |

---

## Message Anatomy

```
┌────────────────────────────────────────┐
│ Record                                 │
├────────────────────────────────────────┤
│ Key: bytes (optional)                  │
│ Value: bytes                           │
│ Headers: [(name, bytes), ...]          │
│ Timestamp: milliseconds                │
│ Partition: int (assigned)              │
│ Offset: long (assigned)                │
└────────────────────────────────────────┘
```

### Serialization

```python
# String (simple)
key = "user-123".encode('utf-8')
value = json.dumps(event).encode('utf-8')

# Avro (recommended for production)
from confluent_kafka.schema_registry.avro import AvroSerializer
serializer = AvroSerializer(schema_registry_client, schema_str)
value = serializer(event, SerializationContext(topic, MessageField.VALUE))
```

---

## Guarantees Summary

| Guarantee | Kafka Provides | You Must Handle |
|-----------|----------------|-----------------|
| Ordering | Within partition | Partition assignment |
| Durability | After acks=all | Verify acks config |
| Delivery | At-least-once (default) | Idempotent consumers |
| Exactly-once | With transactions | Transaction boundaries |
