# Gotchas

Common Kafka mistakes and how to prevent them.

---

## Producer Gotchas

### 1. Fire and Forget (Data Loss)

**Problem:**
```python
producer.produce(topic, value)
# No callback, no flush
# App exits → messages lost
```

**Fix:**
```python
producer.produce(topic, value, callback=delivery_callback)
producer.flush()  # ALWAYS flush before exit
```

**Prevention:** Set `acks=all`, use callbacks, flush on shutdown.

---

### 2. Wrong acks Setting

**Problem:**
```python
# acks=0: No acknowledgment (fastest, loses messages)
# acks=1: Leader only (loses on leader failure)
producer = Producer({'acks': '1'})
```

**Fix:**
```python
producer = Producer({
    'acks': 'all',                # Wait for all ISR
    'enable.idempotence': True,   # Prevent duplicates
})
```

---

### 3. Blocking the Event Loop

**Problem:**
```python
# In FastAPI async endpoint
producer.flush(timeout=30)  # BLOCKS event loop for 30s
```

**Fix:**
```python
# Use thread pool for blocking calls
await asyncio.get_event_loop().run_in_executor(
    None, producer.flush, 10
)

# Or use proper async wrapper
await aio_producer.flush()
```

---

### 4. No Error Handling

**Problem:**
```python
producer.produce(topic, value)  # Silently fails on buffer full
```

**Fix:**
```python
try:
    producer.produce(topic, value, callback=on_delivery)
except BufferError:
    # Buffer full - back off and retry
    time.sleep(0.5)
    producer.poll(0)  # Process callbacks
    producer.produce(topic, value, callback=on_delivery)
```

---

## Consumer Gotchas

### 5. Auto-Commit with At-Least-Once

**Problem:**
```python
consumer = Consumer({
    'enable.auto.commit': True,  # DEFAULT IS TRUE!
})

msg = consumer.poll()
process(msg)  # Crash here → message committed but not processed
```

**Fix:**
```python
consumer = Consumer({
    'enable.auto.commit': False,  # Manual commit
})

msg = consumer.poll()
try:
    process(msg)
    consumer.commit()  # Only after successful processing
except Exception:
    pass  # Don't commit - will reprocess
```

---

### 6. Blocking Poll Too Long

**Problem:**
```python
consumer = Consumer({
    'max.poll.interval.ms': 300000,  # 5 min
})

while True:
    msg = consumer.poll(1.0)
    heavy_processing(msg)  # Takes 10 minutes → kicked from group
```

**Fix:**
```python
# Option 1: Increase timeout
'max.poll.interval.ms': 900000  # 15 min

# Option 2: Process in background
async def process_batch():
    while True:
        msg = await loop.run_in_executor(None, consumer.poll, 1.0)
        asyncio.create_task(process_async(msg))
```

---

### 7. Not Handling Rebalance

**Problem:**
```python
consumer.subscribe(['orders'])
# No rebalance callback
# Partitions revoked → uncommitted offsets lost → duplicates
```

**Fix:**
```python
def on_revoke(consumer, partitions):
    consumer.commit()  # Commit before losing partitions

consumer.subscribe(['orders'], on_revoke=on_revoke)
```

---

### 8. Single Consumer for Many Partitions

**Problem:**
```python
# Topic has 100 partitions
# Only 1 consumer → can't keep up
```

**Fix:**
```python
# Scale consumers to match partitions
# Or at least: consumers <= partitions
```

---

## Schema Gotchas

### 9. Breaking Schema Changes

**Problem:**
```json
// Version 1
{"name": "order_id", "type": "string"}

// Version 2 - BREAKS CONSUMERS
{"name": "orderId", "type": "string"}  // Renamed field
```

**Fix:**
```json
// Add new field, keep old
{"name": "order_id", "type": "string"}
{"name": "orderId", "type": ["null", "string"], "default": null}
// Migrate consumers, then deprecate old field
```

---

### 10. No Default Values

**Problem:**
```json
// Add required field
{"name": "new_field", "type": "string"}  // No default
// Old messages can't be read → consumer crashes
```

**Fix:**
```json
{"name": "new_field", "type": "string", "default": ""}
// Or make optional
{"name": "new_field", "type": ["null", "string"], "default": null}
```

---

### 11. Wrong Compatibility Level

**Problem:**
```bash
# BACKWARD compatibility
# Add field without default → rejected
# But you want producers to add field freely
```

**Fix:**
```bash
# Use FORWARD for producer flexibility
# Use FULL for maximum safety
curl -X PUT -H "Content-Type: application/json" \
  --data '{"compatibility": "FULL"}' \
  http://localhost:8081/config/orders-value
```

---

## Configuration Gotchas

### 12. Wrong Partition Count

**Problem:**
```yaml
# Too few partitions
partitions: 3  # Only 3 consumers max
# Can't increase parallelism
```

**Fix:**
```yaml
# Start with more partitions than you need
partitions: 12  # Or more based on expected throughput

# Note: Can't reduce partitions, only increase
```

---

### 13. Short Retention

**Problem:**
```yaml
retention.ms: 3600000  # 1 hour
# Consumer down for 2 hours → misses messages
```

**Fix:**
```yaml
retention.ms: 604800000  # 7 days (default)
# Or use compaction for state topics
cleanup.policy: compact
```

---

### 14. Low Replication Factor

**Problem:**
```yaml
replication-factor: 1  # Single copy
# Broker dies → data lost
```

**Fix:**
```yaml
replication-factor: 3  # Survives 2 failures
min.insync.replicas: 2  # Require 2 replicas for writes
```

---

## Strimzi/K8s Gotchas

### 15. Wrong Bootstrap Server

**Problem:**
```python
'bootstrap.servers': 'kafka:9092'  # Wrong!
# Should use Strimzi service name
```

**Fix:**
```python
'bootstrap.servers': 'my-cluster-kafka-bootstrap.kafka:9092'
# Or from same namespace:
'bootstrap.servers': 'my-cluster-kafka-bootstrap:9092'
```

---

### 16. Hardcoded Bootstrap Servers

**Problem:**
```python
# Code only works in one environment
consumer = Consumer({
    'bootstrap.servers': 'dev-cluster-kafka-bootstrap.kafka.svc.cluster.local:9092',
})
# Run on Mac → "Failed to resolve"
# Run in K8s → works
```

**Fix:** Use environment variable with sensible default:
```python
import os

consumer = Consumer({
    'bootstrap.servers': os.environ.get(
        'KAFKA_BOOTSTRAP_SERVERS',
        'localhost:30092'  # Default for local dev
    ),
})
```

**Deployment:**
```bash
# Local (uses default)
python consumer.py

# Kubernetes (set in ConfigMap or Pod env)
KAFKA_BOOTSTRAP_SERVERS=dev-cluster-kafka-bootstrap:9092 python consumer.py
```

---

### 17. Port-Forward Doesn't Work for Local Development

**Problem:**
```bash
# Try to connect from local machine
kubectl port-forward svc/dev-cluster-kafka-bootstrap 9092:9092 -n kafka

# Then in Python
producer = Producer({'bootstrap.servers': 'localhost:9092'})
# FAILS! Broker advertises internal K8s DNS, client can't resolve
```

**Why:** Kafka clients fetch broker addresses from the cluster. Even with port-forward, the broker advertises `dev-cluster-kafka-0.dev-cluster-kafka-brokers.kafka.svc:9092` which your local machine can't resolve.

**Fix:** Use NodePort listener with `advertisedHost` on brokers (NOT on bootstrap):
```yaml
listeners:
  - name: external
    port: 9094
    type: nodeport
    tls: false
    configuration:
      bootstrap:
        nodePort: 30092
        # NOTE: advertisedHost NOT supported on bootstrap level
      brokers:
        - broker: 0
          nodePort: 30093
          advertisedHost: localhost    # CRITICAL for Docker Desktop
          advertisedPort: 30093
```

Then connect with:
```python
'bootstrap.servers': 'localhost:30092'  # Works!
```

| Location | Port | Why |
|----------|------|-----|
| Local machine | `30092` | NodePort + advertisedHost |
| Inside K8s pod | `9092` | Internal service works |

---

### 17b. Docker Desktop VM IP Unreachable

**Problem:**
```
Connect to ipv4#192.168.65.3:30093 failed: Network is unreachable
```

**Why:** Without `advertisedHost: localhost`, the broker advertises Docker Desktop's internal VM IP (`192.168.65.3`). Your Mac can't reach this IP directly.

**Fix:** Add `advertisedHost: localhost` and `advertisedPort` to broker configs (see above). Note: Strimzi only supports these on brokers, not on bootstrap.

**Verify fix:**
```bash
kubectl exec -n kafka <pod-name> -- cat /tmp/strimzi.properties | grep advertised
# Should show localhost, not 192.168.65.3
```

---

### 18. Missing Network Policy

**Problem:**
```yaml
# No network policy
# Any pod can access Kafka → security risk
```

**Fix:**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: kafka-access
spec:
  podSelector:
    matchLabels:
      strimzi.io/cluster: my-cluster
  ingress:
    - from:
        - podSelector:
            matchLabels:
              kafka-access: "true"
```

---

### 19. Ignoring Resource Limits

**Problem:**
```yaml
# No limits → OOM kills, resource starvation
resources: {}
```

**Fix:**
```yaml
resources:
  requests:
    memory: 4Gi
    cpu: 1
  limits:
    memory: 8Gi
    cpu: 2
```

---

## Async/FastAPI Gotchas

### 20. Not Closing Consumer on Shutdown

**Problem:**
```python
# App shutdown → consumer still in group
# Group rebalances slowly
```

**Fix:**
```python
@asynccontextmanager
async def lifespan(app):
    yield
    consumer.close()  # Leave group cleanly
```

---

### 21. Shared Consumer Across Requests

**Problem:**
```python
# Global consumer used by multiple requests
# poll() not thread-safe → corruption
```

**Fix:**
```python
# One consumer per background task
# Or use async consumer wrapper with proper locking
```

---

## Prevention Checklist

```markdown
## Producer
- [ ] acks=all
- [ ] enable.idempotence=true
- [ ] Delivery callbacks
- [ ] flush() before shutdown
- [ ] Error handling for BufferError

## Consumer
- [ ] enable.auto.commit=false
- [ ] Commit after processing
- [ ] Rebalance callback
- [ ] Appropriate max.poll.interval.ms
- [ ] close() on shutdown

## Schema
- [ ] Default values on new fields
- [ ] Compatibility level set
- [ ] Schema validated before deploy

## Operations
- [ ] replication-factor >= 3
- [ ] min.insync.replicas >= 2
- [ ] Retention appropriate
- [ ] Resource limits set
- [ ] Monitoring enabled
```
