# Production Configuration

Optimized settings for brokers, topics, producers, and consumers.

---

## Broker Configuration

### Strimzi Kafka CR

```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: Kafka
metadata:
  name: prod-cluster
spec:
  kafka:
    version: 4.1.1
    metadataVersion: 3.9-IV0

    config:
      # Replication
      offsets.topic.replication.factor: 3
      transaction.state.log.replication.factor: 3
      transaction.state.log.min.isr: 2
      default.replication.factor: 3
      min.insync.replicas: 2

      # Topics
      auto.create.topics.enable: false  # Explicit topic creation
      delete.topic.enable: true
      num.partitions: 12  # Default for new topics

      # Retention
      log.retention.hours: 168  # 7 days
      log.retention.bytes: -1  # No size limit
      log.segment.bytes: 1073741824  # 1GB segments

      # Performance
      num.network.threads: 8
      num.io.threads: 16
      socket.send.buffer.bytes: 102400
      socket.receive.buffer.bytes: 102400
      socket.request.max.bytes: 104857600  # 100MB

      # Compression
      compression.type: producer  # Let producer decide
      log.message.timestamp.type: CreateTime

      # Security
      auto.leader.rebalance.enable: true
      leader.imbalance.check.interval.seconds: 300
```

### Resource Allocation

| Role | Memory | CPU | Storage |
|------|--------|-----|---------|
| Controller | 4-8 Gi | 1-2 | 20 Gi |
| Broker (small) | 8 Gi | 2 | 100 Gi |
| Broker (medium) | 16 Gi | 4 | 500 Gi |
| Broker (large) | 32 Gi | 8 | 1 Ti |

```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaNodePool
metadata:
  name: brokers
spec:
  replicas: 5
  roles:
    - broker
  resources:
    requests:
      memory: 16Gi
      cpu: 4
    limits:
      memory: 24Gi
      cpu: 8
  jvmOptions:
    -Xms: 8g
    -Xmx: 8g
  storage:
    type: jbod
    volumes:
      - id: 0
        type: persistent-claim
        size: 500Gi
        class: fast-ssd
        deleteClaim: false
```

---

## Topic Configuration

### Event Topics (Standard)

```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaTopic
metadata:
  name: orders-order-created
spec:
  partitions: 12
  replicas: 3
  config:
    retention.ms: "604800000"        # 7 days
    min.insync.replicas: "2"
    cleanup.policy: "delete"
    segment.bytes: "1073741824"      # 1GB
    max.message.bytes: "1048576"     # 1MB
```

### Compacted Topics (State)

```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaTopic
metadata:
  name: user-profiles
spec:
  partitions: 12
  replicas: 3
  config:
    cleanup.policy: "compact"
    min.cleanable.dirty.ratio: "0.5"
    segment.ms: "604800000"          # 7 days
    delete.retention.ms: "86400000"  # 1 day tombstone retention
    min.insync.replicas: "2"
```

### High-Throughput Topics

```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaTopic
metadata:
  name: clickstream
spec:
  partitions: 50  # High parallelism
  replicas: 3
  config:
    retention.ms: "86400000"         # 1 day
    min.insync.replicas: "1"         # Trade safety for speed
    compression.type: "lz4"
    segment.bytes: "536870912"       # 512MB
```

### Partition Count Guidelines

| Throughput | Messages/sec | Partitions |
|------------|--------------|------------|
| Low | < 1,000 | 6 |
| Medium | 1,000 - 10,000 | 12-24 |
| High | 10,000 - 100,000 | 50-100 |
| Very High | > 100,000 | 100-200 |

**Formula:** `partitions >= max(expected_throughput / per_partition_throughput, max_consumers)`

---

## Producer Configuration

### Reliable Producer

```python
producer = Producer({
    # Connection
    'bootstrap.servers': 'kafka:9092',
    'client.id': 'order-service-prod',

    # Durability (CRITICAL)
    'acks': 'all',
    'enable.idempotence': True,
    'max.in.flight.requests.per.connection': 5,  # OK with idempotence

    # Retries
    'retries': 2147483647,
    'retry.backoff.ms': 100,
    'retry.backoff.max.ms': 1000,
    'delivery.timeout.ms': 120000,  # 2 min total

    # Batching
    'batch.size': 65536,            # 64KB
    'linger.ms': 10,                # 10ms wait
    'buffer.memory': 67108864,      # 64MB

    # Compression
    'compression.type': 'lz4',

    # Timeouts
    'request.timeout.ms': 30000,
    'socket.timeout.ms': 60000,
})
```

### High-Throughput Producer

```python
producer = Producer({
    'bootstrap.servers': 'kafka:9092',
    'acks': 'all',
    'enable.idempotence': True,

    # Aggressive batching
    'batch.size': 131072,           # 128KB
    'linger.ms': 50,                # 50ms wait
    'buffer.memory': 134217728,     # 128MB

    # Compression
    'compression.type': 'lz4',
    'compression.level': 6,

    # Parallelism
    'max.in.flight.requests.per.connection': 5,
})
```

---

## Consumer Configuration

### Reliable Consumer

```python
consumer = Consumer({
    # Connection
    'bootstrap.servers': 'kafka:9092',
    'group.id': 'order-processor-prod',
    'client.id': 'order-processor-1',

    # Offset management
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': False,    # Manual commit

    # Session management
    'session.timeout.ms': 45000,
    'heartbeat.interval.ms': 15000,
    'max.poll.interval.ms': 300000,  # 5 min processing time

    # Fetching
    'fetch.min.bytes': 1,
    'fetch.max.wait.ms': 500,
    'max.partition.fetch.bytes': 1048576,  # 1MB

    # Assignment
    'partition.assignment.strategy': 'cooperative-sticky',

    # Transactions (if using exactly-once)
    'isolation.level': 'read_committed',
})
```

### High-Throughput Consumer

```python
consumer = Consumer({
    'bootstrap.servers': 'kafka:9092',
    'group.id': 'analytics-consumer',

    # Batch fetching
    'fetch.min.bytes': 50000,        # Wait for 50KB
    'fetch.max.wait.ms': 500,
    'max.partition.fetch.bytes': 10485760,  # 10MB

    # Large batches
    'max.poll.records': 1000,

    # Quick session
    'session.timeout.ms': 30000,
    'max.poll.interval.ms': 120000,
})
```

---

## Schema Registry Configuration

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: schema-registry
spec:
  replicas: 2  # HA
  template:
    spec:
      containers:
        - name: schema-registry
          image: confluentinc/cp-schema-registry:7.5.0
          env:
            - name: SCHEMA_REGISTRY_HOST_NAME
              valueFrom:
                fieldRef:
                  fieldPath: status.podIP
            - name: SCHEMA_REGISTRY_KAFKASTORE_BOOTSTRAP_SERVERS
              value: "prod-cluster-kafka-bootstrap:9092"
            - name: SCHEMA_REGISTRY_LISTENERS
              value: "http://0.0.0.0:8081"
            # Performance
            - name: SCHEMA_REGISTRY_KAFKASTORE_TOPIC_REPLICATION_FACTOR
              value: "3"
            - name: SCHEMA_REGISTRY_MASTER_ELIGIBILITY
              value: "true"
            # Caching
            - name: SCHEMA_REGISTRY_SCHEMA_CACHE_SIZE
              value: "1000"
            - name: SCHEMA_REGISTRY_SCHEMA_CACHE_EXPIRY_SECS
              value: "300"
          resources:
            requests:
              memory: 1Gi
              cpu: 500m
            limits:
              memory: 2Gi
              cpu: 1
```

---

## Monitoring Configuration

### Strimzi Metrics

```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: Kafka
spec:
  kafka:
    metricsConfig:
      type: jmxPrometheusExporter
      valueFrom:
        configMapKeyRef:
          name: kafka-metrics
          key: kafka-metrics-config.yml
  kafkaExporter:
    topicRegex: ".*"
    groupRegex: ".*"
    resources:
      requests:
        memory: 256Mi
        cpu: 100m
```

---

## Security Configuration Summary

| Environment | Protocol | Auth | Encryption |
|-------------|----------|------|------------|
| Dev | PLAINTEXT | None | None |
| Staging | SASL_SSL | SCRAM-SHA-512 | TLS |
| Prod | SSL | mTLS | TLS |

---

## Performance Tuning Checklist

### Broker
- [ ] SSD storage (not HDD)
- [ ] Adequate heap (50% of available RAM, max 6GB)
- [ ] Separate disks for logs and data
- [ ] Network threads = cores
- [ ] I/O threads = 2x cores

### Producer
- [ ] `acks=all` for durability
- [ ] Compression enabled (lz4)
- [ ] Appropriate batch size (16-128KB)
- [ ] Linger time based on latency requirements

### Consumer
- [ ] Manual offset commits
- [ ] Cooperative-sticky assignment
- [ ] Appropriate poll interval
- [ ] Parallel consumers = partitions

### Topics
- [ ] Replication factor >= 3
- [ ] min.insync.replicas >= 2
- [ ] Partition count based on throughput
- [ ] Retention based on use case
