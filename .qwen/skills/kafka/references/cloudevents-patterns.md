# CloudEvents Patterns

CNCF CloudEvents specification for AI agent event architectures.

---

## What is CloudEvents?

A specification for describing events in a common way across services, platforms, and systems.

```
┌─────────────────────────────────────────────────────────────┐
│ CloudEvents Envelope                                        │
├─────────────────────────────────────────────────────────────┤
│ Required Attributes:                                        │
│   id: "evt-123"           (unique event ID)                 │
│   source: "agent/task-worker-1"  (event producer)           │
│   type: "task.completed"  (event type)                      │
│   specversion: "1.0"      (CloudEvents version)             │
├─────────────────────────────────────────────────────────────┤
│ Optional Attributes:                                        │
│   time: "2024-01-15T10:30:00Z"                              │
│   subject: "task-456"                                       │
│   datacontenttype: "application/avro"                       │
│   dataschema: "http://registry/schemas/task-result/1"       │
├─────────────────────────────────────────────────────────────┤
│ Data (Your Payload):                                        │
│   { "result": "success", "output": {...} }                  │
└─────────────────────────────────────────────────────────────┘
```

---

## CloudEvents + Kafka

### Message Structure

```python
# Kafka message with CloudEvents in headers
headers = [
    ('ce_specversion', b'1.0'),
    ('ce_id', event_id.encode()),
    ('ce_source', source.encode()),
    ('ce_type', event_type.encode()),
    ('ce_time', timestamp.encode()),
    ('ce_subject', subject.encode()),
    ('ce_datacontenttype', b'application/avro'),
]

producer.produce(
    topic='agent-events',
    key=subject,
    value=avro_payload,  # Avro-serialized data
    headers=headers
)
```

### Wrapper Class

```python
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4
from typing import Any, Optional

@dataclass
class CloudEvent:
    """CloudEvents 1.0 envelope."""

    # Required
    type: str
    source: str
    data: Any

    # Optional (with defaults)
    id: str = field(default_factory=lambda: str(uuid4()))
    specversion: str = "1.0"
    time: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    subject: Optional[str] = None
    datacontenttype: str = "application/json"
    dataschema: Optional[str] = None

    def to_headers(self) -> list[tuple[str, bytes]]:
        """Convert to Kafka headers."""
        headers = [
            ('ce_specversion', self.specversion.encode()),
            ('ce_id', self.id.encode()),
            ('ce_source', self.source.encode()),
            ('ce_type', self.type.encode()),
            ('ce_time', self.time.encode()),
            ('ce_datacontenttype', self.datacontenttype.encode()),
        ]
        if self.subject:
            headers.append(('ce_subject', self.subject.encode()))
        if self.dataschema:
            headers.append(('ce_dataschema', self.dataschema.encode()))
        return headers

    @classmethod
    def from_message(cls, msg) -> 'CloudEvent':
        """Parse from Kafka message."""
        headers = {k: v.decode() for k, v in msg.headers() or []}
        return cls(
            id=headers.get('ce_id'),
            specversion=headers.get('ce_specversion', '1.0'),
            type=headers.get('ce_type'),
            source=headers.get('ce_source'),
            time=headers.get('ce_time'),
            subject=headers.get('ce_subject'),
            datacontenttype=headers.get('ce_datacontenttype'),
            dataschema=headers.get('ce_dataschema'),
            data=msg.value()  # Deserialize separately
        )
```

---

## Agent Event Patterns

### Task Assignment

```python
# Orchestrator assigns task to worker
CloudEvent(
    type="agent.task.assigned",
    source="agent/orchestrator",
    subject="task-123",
    data={
        "task_id": "task-123",
        "task_type": "web_research",
        "parameters": {
            "query": "Latest AI news",
            "max_results": 10
        },
        "assigned_to": "worker-5",
        "deadline": "2024-01-15T12:00:00Z",
        "priority": "high"
    }
)
```

### Task Progress

```python
CloudEvent(
    type="agent.task.progress",
    source="agent/worker-5",
    subject="task-123",
    data={
        "task_id": "task-123",
        "status": "in_progress",
        "progress_percent": 50,
        "current_step": "Fetching results",
        "steps_completed": 3,
        "steps_total": 6
    }
)
```

### Task Completion

```python
CloudEvent(
    type="agent.task.completed",
    source="agent/worker-5",
    subject="task-123",
    data={
        "task_id": "task-123",
        "status": "success",
        "result": {
            "findings": [...],
            "summary": "..."
        },
        "duration_ms": 5432,
        "tokens_used": 1500
    }
)
```

### Task Failure

```python
CloudEvent(
    type="agent.task.failed",
    source="agent/worker-5",
    subject="task-123",
    data={
        "task_id": "task-123",
        "status": "failed",
        "error": {
            "code": "RATE_LIMIT",
            "message": "API rate limit exceeded",
            "retryable": True,
            "retry_after": 60
        },
        "attempts": 3
    }
)
```

---

## Event Type Taxonomy

```
agent.
├── task.
│   ├── created        # Task defined
│   ├── assigned       # Assigned to worker
│   ├── progress       # Progress update
│   ├── completed      # Success
│   ├── failed         # Error
│   └── cancelled      # User cancelled
│
├── worker.
│   ├── registered     # Worker came online
│   ├── heartbeat      # Health check
│   └── shutdown       # Worker going offline
│
├── conversation.
│   ├── started        # New conversation
│   ├── message        # User/agent message
│   └── ended          # Conversation closed
│
└── audit.
    ├── action         # Agent took action
    ├── decision       # Agent made decision
    └── access         # Resource accessed
```

---

## Notification Fanout

One event triggers multiple notifications:

```python
# Source event
CloudEvent(
    type="order.completed",
    source="orders/checkout",
    subject="order-789",
    data={"order_id": "789", "customer_email": "..."}
)

# Consumers produce derived events:

# Email service
CloudEvent(
    type="notification.email.queued",
    source="notifications/email",
    subject="order-789",
    data={"template": "order_confirmation", "to": "..."}
)

# SMS service
CloudEvent(
    type="notification.sms.queued",
    source="notifications/sms",
    subject="order-789",
    data={"template": "order_shipped", "phone": "..."}
)

# Push service
CloudEvent(
    type="notification.push.queued",
    source="notifications/push",
    subject="order-789",
    data={"title": "Order Confirmed", "body": "..."}
)
```

### Topic Structure

```
notifications.email.queued   → Email worker
notifications.sms.queued     → SMS worker
notifications.push.queued    → Push worker
notifications.*.sent         → Audit (wildcard consumer)
```

---

## Saga Orchestration

Multi-step workflow with compensation:

```python
# Step 1: Start saga
CloudEvent(
    type="saga.order.started",
    source="saga/order-saga",
    subject="saga-001",
    data={
        "saga_id": "saga-001",
        "order_id": "order-789",
        "steps": ["reserve_inventory", "charge_payment", "ship_order"]
    }
)

# Step 2: Reserve inventory
CloudEvent(
    type="saga.step.completed",
    source="inventory/service",
    subject="saga-001",
    data={
        "saga_id": "saga-001",
        "step": "reserve_inventory",
        "status": "success",
        "compensation": {
            "type": "inventory.release",
            "data": {"reservation_id": "res-123"}
        }
    }
)

# Step 3: Payment fails
CloudEvent(
    type="saga.step.failed",
    source="payment/service",
    subject="saga-001",
    data={
        "saga_id": "saga-001",
        "step": "charge_payment",
        "error": "Insufficient funds"
    }
)

# Step 4: Compensate (release inventory)
CloudEvent(
    type="inventory.release",
    source="saga/order-saga",
    subject="saga-001",
    data={"reservation_id": "res-123"}
)

# Step 5: Saga completed (failed)
CloudEvent(
    type="saga.order.completed",
    source="saga/order-saga",
    subject="saga-001",
    data={
        "saga_id": "saga-001",
        "status": "failed",
        "compensated_steps": ["reserve_inventory"]
    }
)
```

---

## Audit Logging

Track all agent actions:

```python
@dataclass
class AuditEvent:
    action: str
    actor: str
    resource: str
    result: str
    details: dict

    def to_cloudevent(self) -> CloudEvent:
        return CloudEvent(
            type=f"audit.{self.action}",
            source=f"agent/{self.actor}",
            subject=self.resource,
            data={
                "action": self.action,
                "actor": self.actor,
                "resource": self.resource,
                "result": self.result,
                "details": self.details,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

# Usage
audit = AuditEvent(
    action="file.read",
    actor="research-agent",
    resource="/data/sensitive.json",
    result="allowed",
    details={"bytes_read": 1024}
)
producer.produce('audit-events', value=audit.to_cloudevent())
```

---

## Avro Schema for CloudEvents

```json
{
  "type": "record",
  "name": "AgentTaskEvent",
  "namespace": "com.devraftel.events",
  "fields": [
    {"name": "task_id", "type": "string"},
    {"name": "status", "type": {
      "type": "enum",
      "name": "TaskStatus",
      "symbols": ["PENDING", "IN_PROGRESS", "COMPLETED", "FAILED", "CANCELLED"]
    }},
    {"name": "agent_id", "type": "string"},
    {"name": "progress_percent", "type": ["null", "int"], "default": null},
    {"name": "result", "type": ["null", "string"], "default": null},
    {"name": "error", "type": ["null", {
      "type": "record",
      "name": "TaskError",
      "fields": [
        {"name": "code", "type": "string"},
        {"name": "message", "type": "string"},
        {"name": "retryable", "type": "boolean"}
      ]
    }], "default": null},
    {"name": "metadata", "type": {"type": "map", "values": "string"}}
  ]
}
```

---

## Best Practices

| Practice | Why |
|----------|-----|
| Use namespaced types | `agent.task.completed` not `task_done` |
| Include correlation IDs | Link related events across services |
| Make events self-contained | Consumer shouldn't need external lookup |
| Use subject for routing | Partition key alignment |
| Timestamp events at source | Accurate event ordering |
| Schema all payloads | Evolution and validation |
