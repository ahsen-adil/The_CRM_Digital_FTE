# Architecture Patterns: When and Why Kafka

## The Coupling Problem

### Synchronous (Direct Call) Architecture

```
┌─────────┐     ┌──────────────┐
│ Task    │────▶│ Notification │  500ms
│ API     │     └──────────────┘
│         │     ┌──────────────┐
│         │────▶│ Audit        │  500ms
│         │     └──────────────┘
│         │     ┌──────────────┐
│         │────▶│ Reminder     │  500ms
└─────────┘     └──────────────┘

Total latency: 1500ms (sequential)
Or: 500ms (parallel) but still coupled
```

### Three Types of Coupling

| Coupling | Problem | Example |
|----------|---------|---------|
| **Temporal** | Caller waits for response | Task API blocks 1500ms total |
| **Availability** | If callee down, caller fails | Notification down = Task fails |
| **Behavioral** | Caller knows callee details | Task API imports all 3 clients |

### Analysis Questions

When analyzing a synchronous architecture, ask:

1. **Temporal**: "What happens if Service B takes 30 seconds?"
   - Caller times out
   - User sees error
   - Retry storm begins

2. **Availability**: "What happens if Service B is down?"
   - Caller fails entirely
   - Or: Caller must implement circuit breaker
   - Cascading failures possible

3. **Behavioral**: "What happens if we add Service D?"
   - Caller code must change
   - New dependency added
   - Deployment coupling

---

## Event-Driven Architecture (Kafka Solution)

```
┌─────────┐     ┌───────┐     ┌──────────────┐
│ Task    │────▶│ Kafka │────▶│ Notification │
│ API     │     │       │────▶│ Audit        │
│         │     │       │────▶│ Reminder     │
└─────────┘     └───────┘     └──────────────┘

Task API latency: ~10ms (just publish)
Services process asynchronously
```

### Coupling Comparison

| Coupling | Synchronous | Event-Driven |
|----------|-------------|--------------|
| **Temporal** | Waits 1500ms | Returns in 10ms |
| **Availability** | Fails if any down | Succeeds, events queued |
| **Behavioral** | Knows all services | Knows only event schema |

---

## Pattern: Publish Domain Events

### Before (Synchronous)

```python
# task_api.py - COUPLED
from notification_client import NotificationClient
from audit_client import AuditClient
from reminder_client import ReminderClient

async def create_task(task: Task):
    # Save task
    saved = await db.save(task)

    # Direct calls - TEMPORAL COUPLING
    await notification_client.notify(task.assignee, "New task")  # 500ms
    await audit_client.log("task_created", task.id)              # 500ms
    await reminder_client.schedule(task.due_date, task.id)       # 500ms

    return saved  # Total: 1500ms+
```

### After (Event-Driven)

```python
# task_api.py - DECOUPLED
from kafka_producer import producer

async def create_task(task: Task):
    # Save task
    saved = await db.save(task)

    # Publish event - NO COUPLING
    await producer.send("task.events", {
        "type": "task.created",
        "data": {"task_id": task.id, "assignee": task.assignee, "due": task.due_date}
    })

    return saved  # Total: ~10ms

# notification_service.py - INDEPENDENT
async def handle_event(event):
    if event["type"] == "task.created":
        await notify(event["data"]["assignee"], "New task")

# audit_service.py - INDEPENDENT
async def handle_event(event):
    if event["type"] == "task.created":
        await log("task_created", event["data"]["task_id"])

# reminder_service.py - INDEPENDENT
async def handle_event(event):
    if event["type"] == "task.created":
        await schedule(event["data"]["due"], event["data"]["task_id"])
```

---

## When to Use Each Pattern

### Use Synchronous When:

- Response needed immediately (user waiting)
- Transaction must be atomic
- Simple, few dependencies
- Low latency requirement (<100ms)

### Use Event-Driven When:

- Response can be eventual
- Multiple consumers need same data
- Services should be independent
- Failure of one shouldn't fail all
- Adding new consumers shouldn't change producer

---

## Eventual Consistency

**The tradeoff:** Event-driven systems are eventually consistent, not immediately consistent.

```
Strong Consistency          Eventual Consistency
─────────────────          ────────────────────
Write → Read = latest      Write → Read = maybe stale
Slower (waits for acks)    Faster (async processing)
Simpler mental model       Requires handling lag
```

### Consistency Windows by Domain

| Domain | Acceptable Window | Example |
|--------|------------------|---------|
| E-commerce checkout | 200-500ms | Order placed → confirmation email |
| Inventory display | 1-5 seconds | Stock reserved → UI updated |
| Search indexing | 5-30 seconds | Product created → searchable |
| Analytics dashboard | 1-5 minutes | Event → metric updated |
| Reporting | Hours | Daily aggregation jobs |

### Read-Your-Writes Pattern

When users must see their own changes immediately:

```python
# Pattern 1: Return entity directly (optimistic UI)
@app.post("/orders")
async def create_order(order: Order):
    saved = await db.save(order)
    await producer.send("order.created", saved)
    return saved  # User sees order immediately, processing async

# Pattern 2: Local cache for consistency gap
@app.get("/orders/{id}")
async def get_order(id: str, user_id: str):
    order = await db.get(id)
    if not order:
        # Check user's pending orders (covers consistency gap)
        order = await pending_cache.get(f"pending:{user_id}:{id}")
    return order

# Pattern 3: Include status indicating eventual state
@app.post("/orders")
async def create_order(order: Order):
    saved = await db.save(order)
    await producer.send("order.created", saved)
    return {"order": saved, "status": "processing"}  # Explicit async status
```

### Handling "Where's My Order?" Scenarios

| User Action | System State | Solution |
|-------------|--------------|----------|
| Just placed order, refreshes page | Event not yet processed | Return from write path, show "processing" |
| Checks order after 1 min | Should be consistent | Normal read path |
| Order confirmation email delayed | Email consumer lagging | Show status in UI, email is secondary |

---

## Anti-Patterns to Identify

### 1. Fan-Out Synchronous Calls

```python
# BAD: N services = N * latency
for service in [svc1, svc2, svc3, svc4]:
    await service.call(data)  # 500ms each = 2000ms
```

**Fix:** Publish one event, N consumers process independently.

### 2. Request-Reply Over Events

```python
# BAD: Using Kafka like HTTP
await producer.send("request-topic", request)
response = await consumer.wait_for_response()  # Defeats the purpose
```

**Fix:** If you need sync response, use HTTP. Events are for async.

### 3. Distributed Monolith

```python
# BAD: Events but still coupled
await producer.send("notification-service.notify", {...})
await producer.send("audit-service.log", {...})
```

**Fix:** Publish domain events, not commands to specific services.

---

## Scenario Analysis Template

When analyzing architecture for coupling:

```markdown
## Current State
- Service A calls: [list services]
- Call pattern: [sync/async]
- Latency per call: [Xms]
- Total latency: [Xms]

## Coupling Analysis
- Temporal: [Yes/No] - [explanation]
- Availability: [Yes/No] - [explanation]
- Behavioral: [Yes/No] - [explanation]

## Event-Driven Solution
- Event type: [domain.event.name]
- Producer: [which service]
- Consumers: [list services]
- Expected latency: [Xms]

## Trade-offs
- Gains: [decoupling benefits]
- Costs: [complexity, eventual consistency]
```

---

## Real Scenario: Task API → 3 Services

### Input
> Task API calls Notification, Audit, Reminder directly. Each takes 500ms.

### Analysis

**Temporal Coupling: YES**
- Task API waits 1500ms (sequential) or 500ms (parallel)
- User experiences slow response
- If any call slow, entire request slow

**Availability Coupling: YES**
- If Notification service down → Task creation fails
- If Audit service down → Task creation fails
- Single point of failure × 3

**Behavioral Coupling: YES**
- Task API imports NotificationClient, AuditClient, ReminderClient
- Adding LoggingService requires Task API code change
- Removing a service requires Task API code change

### Recommendation

Publish `task.created` event to Kafka:

```python
# Task API (producer)
await producer.send("task.events", {
    "type": "task.created",
    "task_id": task.id,
    "assignee": task.assignee,
    "due_date": task.due_date
})
# Returns in ~10ms

# Each service subscribes independently
# consumer_group: notification-service → topic: task.events
# consumer_group: audit-service → topic: task.events
# consumer_group: reminder-service → topic: task.events
```

**Result:**
- Temporal: Task API returns in ~10ms
- Availability: Task succeeds even if services down (events queued)
- Behavioral: Adding new consumer = zero changes to Task API
