# Transactional Outbox Pattern

Guaranteed event publishing without dual-write inconsistency.

---

## The Problem: Dual-Write Inconsistency

```python
# DANGEROUS: Two separate operations
def create_task(task_data):
    db.insert(task_data)           # 1. Database write
    kafka.produce(task_event)      # 2. Kafka write
    # What if app crashes between these two?
    # Database has task, but no event published
```

**Failure scenarios:**
- Crash after DB write, before Kafka → data exists, no event
- Kafka fails, DB succeeds → data exists, no event
- Both succeed but in wrong order → consumers see stale state

---

## The Solution: Transactional Outbox

Write events to an outbox table in the SAME database transaction as business data. A separate process (Debezium CDC) reads the outbox and publishes to Kafka.

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────┐
│   App       │────▶│  Database   │────▶│  Debezium   │────▶│  Kafka  │
│             │     │ (atomic)    │     │  (CDC)      │     │         │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────┘
                    tasks + outbox       reads WAL          publishes
                    in one transaction   publishes events   to topic
```

**Guarantee:** If the business data is committed, the event WILL be published.

---

## Outbox Table Schema

```sql
CREATE TABLE outbox (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    aggregate_type VARCHAR(255) NOT NULL,  -- e.g., "Task", "Order"
    aggregate_id VARCHAR(255) NOT NULL,    -- e.g., task_id, order_id
    event_type VARCHAR(255) NOT NULL,      -- e.g., "TaskCreated"
    payload JSONB NOT NULL,                -- Event data
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_outbox_created_at ON outbox(created_at);
```

---

## Python: Atomic Write Pattern

```python
from sqlalchemy import text
from sqlalchemy.orm import Session
import json
import uuid
from datetime import datetime, timezone

def create_task_with_event(session: Session, title: str, owner_id: str) -> dict:
    """Create task and event atomically - both succeed or both fail."""
    task_id = str(uuid.uuid4())

    event_payload = {
        "task_id": task_id,
        "title": title,
        "owner_id": owner_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    # Single transaction - atomic
    session.execute(
        text("""
            INSERT INTO tasks (id, title, owner_id, status)
            VALUES (:id, :title, :owner_id, 'pending')
        """),
        {"id": task_id, "title": title, "owner_id": owner_id}
    )

    session.execute(
        text("""
            INSERT INTO outbox (aggregate_type, aggregate_id, event_type, payload)
            VALUES (:agg_type, :agg_id, :event_type, :payload)
        """),
        {
            "agg_type": "Task",
            "agg_id": task_id,
            "event_type": "TaskCreated",
            "payload": json.dumps(event_payload)
        }
    )

    session.commit()  # Both writes atomic
    return {"id": task_id, "title": title}
```

---

## PostgreSQL Setup for Debezium

```sql
-- Enable logical replication (postgresql.conf)
-- wal_level = logical
-- max_replication_slots = 4
-- max_wal_senders = 4

-- Create replication user
CREATE ROLE debezium WITH LOGIN REPLICATION PASSWORD 'dbz-secret';
GRANT CONNECT ON DATABASE taskdb TO debezium;
GRANT USAGE ON SCHEMA public TO debezium;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO debezium;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO debezium;
```

---

## Kubernetes: KafkaConnect with Debezium

```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaConnect
metadata:
  name: task-connect
  namespace: kafka
  annotations:
    strimzi.io/use-connector-resources: "true"
spec:
  version: 4.1.1
  replicas: 1
  bootstrapServers: task-events-kafka-bootstrap:9092
  config:
    group.id: task-connect-cluster
    offset.storage.topic: connect-offsets
    config.storage.topic: connect-configs
    status.storage.topic: connect-status
    config.storage.replication.factor: 1
    offset.storage.replication.factor: 1
    status.storage.replication.factor: 1
  build:
    output:
      type: docker
      image: my-registry/kafka-connect-debezium:latest
    plugins:
      - name: debezium-postgres
        artifacts:
          - type: tgz
            url: https://repo1.maven.org/maven2/io/debezium/debezium-connector-postgres/3.0.0.Final/debezium-connector-postgres-3.0.0.Final-plugin.tar.gz
```

---

## Outbox Connector with Event Router

```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaConnector
metadata:
  name: task-outbox-connector
  namespace: kafka
  labels:
    strimzi.io/cluster: task-connect
spec:
  class: io.debezium.connector.postgresql.PostgresConnector
  tasksMax: 1
  config:
    # Database connection
    database.hostname: postgres-service
    database.port: "5432"
    database.user: debezium
    database.password: "${file:/opt/kafka/external-configuration/postgres-creds/password}"
    database.dbname: taskdb

    # Replication settings
    topic.prefix: taskdb
    plugin.name: pgoutput
    slot.name: debezium_outbox_slot
    publication.name: debezium_outbox_pub

    # Only capture outbox table
    table.include.list: public.outbox

    # Event Router transformation
    transforms: outbox
    transforms.outbox.type: io.debezium.transforms.outbox.EventRouter
    transforms.outbox.route.topic.replacement: ${routedByValue}.events
    transforms.outbox.table.field.event.type: event_type
    transforms.outbox.table.field.event.key: aggregate_id
    transforms.outbox.table.field.event.payload: payload
    transforms.outbox.table.expand.json.payload: true

    # Schema history
    schema.history.internal.kafka.bootstrap.servers: task-events-kafka-bootstrap:9092
    schema.history.internal.kafka.topic: schema-changes.outbox
```

**Event Router behavior:**
- Routes to topic based on `aggregate_type` → `Task.events`
- Uses `aggregate_id` as message key
- Expands JSON payload into event body

---

## Outbox Cleanup

Outbox grows indefinitely without cleanup:

```sql
-- Delete processed entries older than 7 days
DELETE FROM outbox WHERE created_at < NOW() - INTERVAL '7 days';
```

**Kubernetes CronJob:**
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: outbox-cleanup
spec:
  schedule: "0 3 * * *"  # Daily at 3 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: cleanup
            image: postgres:15
            command:
            - psql
            - -c
            - "DELETE FROM outbox WHERE created_at < NOW() - INTERVAL '7 days'"
            env:
            - name: PGHOST
              value: postgres-service
            - name: PGDATABASE
              value: taskdb
          restartPolicy: OnFailure
```

---

## When to Use Outbox Pattern

| Scenario | Use Outbox? | Why |
|----------|-------------|-----|
| DB + Kafka writes must be consistent | ✅ Yes | Eliminates dual-write |
| Event sourcing | ❌ No | Events ARE the source |
| Read-only consumers | ❌ No | No write consistency needed |
| Fire-and-forget events | ❌ No | Loss acceptable |
| Multi-database transactions | ✅ Yes | Saga coordination |

---

## Trade-offs

| Aspect | Benefit | Cost |
|--------|---------|------|
| Consistency | Guaranteed delivery | Added complexity |
| Latency | Slightly higher (CDC lag) | Usually < 1 second |
| Operations | Debezium to manage | More infrastructure |
| Debugging | Clear audit trail | More moving parts |

**Alternative:** If you only write to Kafka (event sourcing), you don't need outbox—Kafka IS your source of truth.
