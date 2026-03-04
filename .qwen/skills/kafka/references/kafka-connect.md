# Kafka Connect

Data integration framework for streaming data in and out of Kafka.

---

## Architecture

```
┌─────────────┐    ┌─────────────────┐    ┌─────────────┐
│ Source      │───▶│ Kafka Connect   │───▶│ Kafka       │
│ (Database)  │    │ (Source Conn.)  │    │ Topics      │
└─────────────┘    └─────────────────┘    └─────────────┘
                                                │
                   ┌─────────────────┐          │
                   │ Kafka Connect   │◀─────────┘
                   │ (Sink Conn.)    │
                   └────────┬────────┘
                            │
                            ▼
                   ┌─────────────┐
                   │ Sink        │
                   │ (ES, S3...) │
                   └─────────────┘
```

---

## Strimzi KafkaConnect

### Deploy Connect Cluster

```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaConnect
metadata:
  name: my-connect
  annotations:
    strimzi.io/use-connector-resources: "true"  # Enable KafkaConnector CRDs
spec:
  version: 4.1.1
  replicas: 3
  bootstrapServers: my-cluster-kafka-bootstrap:9092
  config:
    group.id: connect-cluster
    offset.storage.topic: connect-offsets
    config.storage.topic: connect-configs
    status.storage.topic: connect-status
    key.converter: org.apache.kafka.connect.json.JsonConverter
    value.converter: org.apache.kafka.connect.json.JsonConverter
    key.converter.schemas.enable: true
    value.converter.schemas.enable: true
  build:
    output:
      type: docker
      image: my-registry/my-connect:latest
    plugins:
      - name: debezium-postgres
        artifacts:
          - type: tgz
            url: https://repo1.maven.org/maven2/io/debezium/debezium-connector-postgres/2.4.0.Final/debezium-connector-postgres-2.4.0.Final-plugin.tar.gz
      - name: elasticsearch-sink
        artifacts:
          - type: zip
            url: https://d1i4a15mxbxib1.cloudfront.net/api/plugins/confluentinc/kafka-connect-elasticsearch/versions/14.0.3/confluentinc-kafka-connect-elasticsearch-14.0.3.zip
  resources:
    requests:
      memory: 2Gi
      cpu: 500m
    limits:
      memory: 4Gi
      cpu: 1
```

---

## Debezium CDC

Change Data Capture from PostgreSQL to Kafka.

### PostgreSQL Source Connector

```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaConnector
metadata:
  name: postgres-source
  labels:
    strimzi.io/cluster: my-connect
spec:
  class: io.debezium.connector.postgresql.PostgresConnector
  tasksMax: 1
  config:
    # Database connection
    database.hostname: postgres
    database.port: "5432"
    database.user: debezium
    database.password: ${secrets:postgres:password}
    database.dbname: orders

    # Topic configuration
    topic.prefix: cdc.orders
    # Creates topics: cdc.orders.public.orders, cdc.orders.public.customers

    # Tables to capture
    table.include.list: public.orders,public.customers

    # Slot configuration (PostgreSQL replication)
    plugin.name: pgoutput
    slot.name: debezium_orders
    publication.name: dbz_publication

    # Snapshot mode
    snapshot.mode: initial  # or: never, always, schema_only

    # Transforms (optional)
    transforms: unwrap
    transforms.unwrap.type: io.debezium.transforms.ExtractNewRecordState
    transforms.unwrap.drop.tombstones: true

    # Schema Registry
    key.converter: io.confluent.connect.avro.AvroConverter
    key.converter.schema.registry.url: http://schema-registry:8081
    value.converter: io.confluent.connect.avro.AvroConverter
    value.converter.schema.registry.url: http://schema-registry:8081
```

### PostgreSQL Setup

```sql
-- Enable logical replication
ALTER SYSTEM SET wal_level = logical;

-- Create replication user
CREATE USER debezium WITH REPLICATION PASSWORD 'secret';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO debezium;

-- Create publication
CREATE PUBLICATION dbz_publication FOR TABLE orders, customers;
```

---

## Outbox Pattern

Reliable event publishing from database transactions.

### Table Structure

```sql
CREATE TABLE outbox (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    aggregate_type VARCHAR(255) NOT NULL,
    aggregate_id VARCHAR(255) NOT NULL,
    event_type VARCHAR(255) NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Application writes in same transaction:
BEGIN;
  INSERT INTO orders (id, customer_id, total) VALUES (...);
  INSERT INTO outbox (aggregate_type, aggregate_id, event_type, payload)
    VALUES ('order', 'order-123', 'OrderCreated', '{"order_id": "123", ...}');
COMMIT;
```

### Outbox Connector

```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaConnector
metadata:
  name: outbox-connector
  labels:
    strimzi.io/cluster: my-connect
spec:
  class: io.debezium.connector.postgresql.PostgresConnector
  tasksMax: 1
  config:
    database.hostname: postgres
    database.port: "5432"
    database.user: debezium
    database.password: ${secrets:postgres:password}
    database.dbname: orders
    topic.prefix: outbox

    # Only capture outbox table
    table.include.list: public.outbox

    # Outbox event router transform
    transforms: outbox
    transforms.outbox.type: io.debezium.transforms.outbox.EventRouter
    transforms.outbox.table.field.event.type: event_type
    transforms.outbox.table.field.event.key: aggregate_id
    transforms.outbox.table.field.event.payload: payload
    transforms.outbox.route.topic.replacement: events.${routedByValue}
    # Routes to: events.OrderCreated, events.OrderShipped, etc.

    # Delete processed rows (optional)
    transforms.outbox.table.expand.json.payload: true
```

---

## Common Connectors

### Elasticsearch Sink

```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaConnector
metadata:
  name: elasticsearch-sink
  labels:
    strimzi.io/cluster: my-connect
spec:
  class: io.confluent.connect.elasticsearch.ElasticsearchSinkConnector
  tasksMax: 3
  config:
    topics: orders,products
    connection.url: http://elasticsearch:9200
    type.name: _doc
    key.ignore: false
    schema.ignore: true
    behavior.on.null.values: delete
    write.method: upsert

    # Error handling
    errors.tolerance: all
    errors.deadletterqueue.topic.name: dlq.elasticsearch
    errors.log.enable: true
```

### S3 Sink

```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaConnector
metadata:
  name: s3-sink
  labels:
    strimzi.io/cluster: my-connect
spec:
  class: io.confluent.connect.s3.S3SinkConnector
  tasksMax: 3
  config:
    topics: events
    s3.bucket.name: my-events-bucket
    s3.region: us-east-1
    flush.size: 1000
    rotate.interval.ms: 60000
    storage.class: io.confluent.connect.s3.storage.S3Storage
    format.class: io.confluent.connect.s3.format.parquet.ParquetFormat
    partitioner.class: io.confluent.connect.storage.partitioner.TimeBasedPartitioner
    path.format: "'year'=YYYY/'month'=MM/'day'=dd/'hour'=HH"
    locale: en-US
    timezone: UTC
```

---

## Transforms

### Single Message Transforms (SMT)

```yaml
config:
  # Extract nested field
  transforms: extractField
  transforms.extractField.type: org.apache.kafka.connect.transforms.ExtractField$Value
  transforms.extractField.field: payload

  # Add timestamp
  transforms: insertTime
  transforms.insertTime.type: org.apache.kafka.connect.transforms.InsertField$Value
  transforms.insertTime.timestamp.field: processed_at

  # Route to different topics
  transforms: route
  transforms.route.type: org.apache.kafka.connect.transforms.RegexRouter
  transforms.route.regex: (.*)
  transforms.route.replacement: prod-$1

  # Filter messages
  transforms: filter
  transforms.filter.type: org.apache.kafka.connect.transforms.Filter
  transforms.filter.predicate: isOrder
  transforms.filter.negate: true
  predicates: isOrder
  predicates.isOrder.type: org.apache.kafka.connect.transforms.predicates.RecordIsTombstone
```

---

## Error Handling

### Dead Letter Queue

```yaml
config:
  # Enable DLQ
  errors.tolerance: all  # 'none' to fail on error
  errors.deadletterqueue.topic.name: dlq.my-connector
  errors.deadletterqueue.topic.replication.factor: 3

  # Log errors
  errors.log.enable: true
  errors.log.include.messages: true

  # Retry configuration
  errors.retry.delay.max.ms: 60000
  errors.retry.timeout: 300000  # 5 minutes
```

### Monitor DLQ

```python
# Consumer for DLQ monitoring
consumer = Consumer({
    'bootstrap.servers': 'kafka:9092',
    'group.id': 'dlq-monitor',
})
consumer.subscribe(['dlq.my-connector'])

while True:
    msg = consumer.poll(1.0)
    if msg:
        headers = dict(msg.headers() or [])
        logger.error(
            f"DLQ message: topic={headers.get('__connect.errors.topic')}, "
            f"error={headers.get('__connect.errors.exception.message')}"
        )
        alert_team(msg)
```

---

## Monitoring

### Connector Status

```bash
# List connectors
kubectl exec -n kafka my-connect-connect-0 -- \
  curl -s http://localhost:8083/connectors

# Connector status
kubectl exec -n kafka my-connect-connect-0 -- \
  curl -s http://localhost:8083/connectors/postgres-source/status

# Task status
kubectl exec -n kafka my-connect-connect-0 -- \
  curl -s http://localhost:8083/connectors/postgres-source/tasks/0/status
```

### Metrics

Key JMX metrics to monitor:

| Metric | Description |
|--------|-------------|
| `source-record-poll-rate` | Records/sec from source |
| `source-record-write-rate` | Records/sec to Kafka |
| `sink-record-read-rate` | Records/sec from Kafka |
| `sink-record-send-rate` | Records/sec to sink |
| `offset-commit-success-rate` | Commit success rate |
| `task-count` | Running tasks |

---

## Troubleshooting

| Issue | Check | Fix |
|-------|-------|-----|
| Connector not starting | `GET /connectors/{name}/status` | Check config, credentials |
| Tasks failing | Task logs | Fix source/sink issues |
| Slow throughput | `tasksMax`, batch settings | Increase parallelism |
| Rebalancing loops | Worker logs | Check worker health |
| Offset lag | Consumer lag metrics | Increase tasks |
