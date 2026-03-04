# Agent Event Patterns

Event-driven patterns for AI agent coordination and task dispatch.

---

## Event Naming Convention

Use `domain.action` pattern in **past tense** (immutable facts):

```
task.created      ✅ (fact: task was created)
task.create       ❌ (command: create a task)

agent.assigned    ✅
agent.completed   ✅
notification.sent ✅
```

**Past tense indicates immutable history, not imperative commands.**

---

## Standard Event Schema

```python
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
import uuid

@dataclass
class EventMetadata:
    """Metadata for distributed tracing and compliance."""
    correlation_id: str    # Traces request across services
    causation_id: str      # What event caused this event
    source: str            # Service that produced the event

@dataclass
class DomainEvent:
    """Base structure for all domain events."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = ""
    occurred_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    data: dict = field(default_factory=dict)
    metadata: Optional[EventMetadata] = None

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "occurred_at": self.occurred_at,
            "data": self.data,
            "metadata": {
                "correlation_id": self.metadata.correlation_id,
                "causation_id": self.metadata.causation_id,
                "source": self.metadata.source
            } if self.metadata else {}
        }
```

**Example output:**
```json
{
  "event_id": "e7c5a8f2-3b4d-4e6a-9f1c-2d8e7a6b5c4d",
  "event_type": "task.created",
  "occurred_at": "2025-01-15T14:30:22.456Z",
  "data": {
    "task_id": "task-123",
    "title": "Review quarterly report",
    "owner_id": "user-456",
    "priority": 2
  },
  "metadata": {
    "correlation_id": "req-abc-123",
    "causation_id": "api-call-789",
    "source": "task-api"
  }
}
```

---

## Correlation ID vs Causation ID

| Field | Purpose | Scope |
|-------|---------|-------|
| **correlation_id** | Traces single user request across ALL services | Entire workflow |
| **causation_id** | Links event to what directly caused it | Parent-child |

**Example chain:**
```
User Request (correlation_id: req-123)
  └── API creates task (causation_id: api-call-1)
        └── task.created event
              └── Notification service (causation_id: evt-task-created-1)
                    └── notification.sent event
```

All events share `correlation_id: req-123` for end-to-end tracing.

---

## Agent Fanout Architecture

Multiple specialized agents consume the same events independently:

```
                    ┌──────────────────────┐
                    │   task.created       │
                    │   (single topic)     │
                    └──────────┬───────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ Email Agent   │    │ Slack Agent   │    │ Audit Agent   │
│ group.id:     │    │ group.id:     │    │ group.id:     │
│ notif-email   │    │ notif-slack   │    │ audit-log     │
└───────────────┘    └───────────────┘    └───────────────┘
        │                      │                      │
        ▼                      ▼                      ▼
   Send email            Post message           Write to log
```

**Key:** Different `group.id` = each agent gets ALL messages independently.

---

## Producer: FastAPI with Correlation ID

```python
import json
import uuid
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from confluent_kafka import Producer
from fastapi import FastAPI, Request
from pydantic import BaseModel

producer: Producer = None

def delivery_callback(err, msg):
    if err:
        print(f"Delivery failed: {err}")
    else:
        print(f"Delivered to {msg.topic()}[{msg.partition()}]")

@asynccontextmanager
async def lifespan(app: FastAPI):
    global producer
    producer = Producer({
        'bootstrap.servers': os.environ.get(
            'KAFKA_BOOTSTRAP_SERVERS', 'localhost:30092'
        ),
        'client.id': 'task-api',
        'acks': 'all',
        'enable.idempotence': True
    })
    yield
    producer.flush()

app = FastAPI(lifespan=lifespan)

class TaskCreate(BaseModel):
    title: str
    owner_id: str
    priority: int = 1

def publish_event(
    event_type: str,
    data: dict,
    correlation_id: str,
    causation_id: str
):
    """Publish domain event with tracing metadata."""
    event = {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "data": data,
        "metadata": {
            "correlation_id": correlation_id,
            "causation_id": causation_id,
            "source": "task-api"
        }
    }
    producer.produce(
        topic='task-events',
        key=data.get('task_id', str(uuid.uuid4())),
        value=json.dumps(event),
        callback=delivery_callback
    )
    producer.poll(0)

@app.post("/tasks")
async def create_task(task: TaskCreate, request: Request):
    # Extract or generate correlation ID
    correlation_id = request.headers.get(
        'X-Correlation-ID', str(uuid.uuid4())
    )
    task_id = str(uuid.uuid4())

    task_data = {
        "task_id": task_id,
        "title": task.title,
        "owner_id": task.owner_id,
        "priority": task.priority
    }

    publish_event(
        event_type="task.created",
        data=task_data,
        correlation_id=correlation_id,
        causation_id=f"api-create-{task_id}"
    )

    return {"id": task_id, "status": "created"}
```

---

## Consumer: Notification Agent

```python
import json
import os
from confluent_kafka import Consumer, KafkaError

def create_notification_consumer(notification_type: str):
    """Create consumer for a specific notification channel."""
    return Consumer({
        'bootstrap.servers': os.environ.get(
            'KAFKA_BOOTSTRAP_SERVERS', 'localhost:30092'
        ),
        'group.id': f'notification-{notification_type}',
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': False
    })

def send_email(to: str, subject: str, body: str):
    print(f"EMAIL to {to}: {subject}")

def process_email_notifications():
    consumer = create_notification_consumer('email')
    consumer.subscribe(['task-events'])

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                print(f"Error: {msg.error()}")
                continue

            event = json.loads(msg.value().decode())

            if event.get('event_type') == 'task.created':
                data = event.get('data', {})
                metadata = event.get('metadata', {})

                send_email(
                    to=f"{data.get('owner_id')}@company.com",
                    subject=f"New task: {data.get('title')}",
                    body=f"Task ID: {data.get('task_id')}\n"
                         f"Correlation: {metadata.get('correlation_id')}"
                )

            consumer.commit(message=msg)
    finally:
        consumer.close()
```

---

## Consumer: Audit Agent

```python
import json
import os
from datetime import datetime
from confluent_kafka import Consumer, KafkaError

class AuditLogger:
    """Append-only audit log for compliance."""

    def __init__(self, log_dir: str = "/var/log/audit"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)

    def append(self, event: dict):
        """Append event to immutable log."""
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        log_file = os.path.join(self.log_dir, f"audit-{date_str}.jsonl")

        log_entry = {
            "logged_at": datetime.utcnow().isoformat() + "Z",
            "event": event
        }

        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

def run_audit_agent():
    consumer = Consumer({
        'bootstrap.servers': os.environ.get(
            'KAFKA_BOOTSTRAP_SERVERS', 'localhost:30092'
        ),
        'group.id': 'audit-log',
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': False
    })
    consumer.subscribe(['task-events'])
    audit = AuditLogger()

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                continue

            event = json.loads(msg.value().decode())
            audit.append(event)
            consumer.commit(message=msg)
    finally:
        consumer.close()
```

---

## Agent Coordination Topics

| Topic | Purpose | Consumers |
|-------|---------|-----------|
| `task-events` | Task lifecycle events | All task-aware agents |
| `agent-tasks` | Work dispatch to agents | Worker agents |
| `agent-results` | Agent completion reports | Orchestrator |
| `audit-events` | All events for compliance | Audit service |

---

## Event Types for Agent Workflows

```
# Task lifecycle
task.created
task.assigned
task.started
task.completed
task.failed

# Agent lifecycle
agent.registered
agent.heartbeat
agent.task.accepted
agent.task.completed
agent.task.failed

# Orchestration
workflow.started
workflow.step.completed
workflow.completed
workflow.failed
```

---

## Best Practices

| Practice | Why |
|----------|-----|
| Always include `correlation_id` | End-to-end request tracing |
| Use past tense event names | Events are facts, not commands |
| Separate consumer groups per agent | Independent scaling and replay |
| Include `source` in metadata | Know which service produced event |
| Make consumers idempotent | Handle redelivery safely |
