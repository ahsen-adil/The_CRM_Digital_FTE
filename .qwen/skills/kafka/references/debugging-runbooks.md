# Debugging Runbooks

Step-by-step guides for common Kafka issues.

---

## Consumer Lag Diagnosis

### Symptoms
- Messages piling up in topic
- Processing delays increasing
- Lag metrics climbing

### Runbook

```bash
# 1. Check consumer group status
kubectl exec -n kafka kafka-cluster-kafka-0 -c kafka -- \
  bin/kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --describe --group order-processor

# Output shows:
# GROUP           TOPIC           PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG
# order-processor orders          0          1000            5000            4000
# order-processor orders          1          2000            3000            1000
```

```bash
# 2. Check consumer members
kubectl exec -n kafka kafka-cluster-kafka-0 -c kafka -- \
  bin/kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --describe --group order-processor --members

# Look for: active consumers, assigned partitions
```

```bash
# 3. Check consumer app logs
kubectl logs -n app -l app=order-processor --tail=100 | grep -i "error\|exception\|slow"
```

```bash
# 4. Check processing time
# If using Prometheus:
# avg(rate(kafka_message_processing_seconds_sum[5m]) / rate(kafka_message_processing_seconds_count[5m]))
```

### Resolution Decision Tree

```
Is consumer connected?
├── No → Check network, auth, bootstrap servers
└── Yes → Check partition assignment
    ├── No partitions → Consumer not in group (check group.id)
    └── Partitions assigned → Check processing
        ├── Processing slow → Optimize code, add consumers
        ├── Processing errors → Check DLQ, fix bugs
        └── Poll interval exceeded → Increase max.poll.interval.ms
```

### Fixes

| Cause | Fix |
|-------|-----|
| Too few consumers | Scale up consumer pods |
| Slow processing | Optimize code, batch processing |
| Errors causing retries | Fix bugs, use DLQ |
| Poll timeout | Increase `max.poll.interval.ms` |
| Network issues | Check connectivity, DNS |

---

## Rebalancing Storm

### Symptoms
- Frequent "Rebalance triggered" logs
- Consumers joining/leaving constantly
- Processing throughput drops

### Runbook

```bash
# 1. Check rebalance frequency
kubectl logs -n app -l app=order-processor | grep -i "rebalance" | tail -20

# 2. Check consumer session timeouts
kubectl logs -n app -l app=order-processor | grep -i "heartbeat\|session"

# 3. Check consumer poll intervals
# If poll() not called within max.poll.interval.ms, consumer kicked out
```

### Common Causes

| Cause | Evidence | Fix |
|-------|----------|-----|
| Long processing | "member timed out" | Increase `max.poll.interval.ms` |
| Frequent restarts | Pod restart count high | Fix crash bugs |
| Network issues | Connection timeouts | Check network policies |
| GC pauses | Long GC logs | Tune JVM / Python GC |
| Too many partitions | Many consumers | Reduce partitions or use sticky |

### Prevention

```python
consumer = Consumer({
    'bootstrap.servers': 'kafka:9092',
    'group.id': 'order-processor',

    # Prevent rebalancing storms
    'session.timeout.ms': 45000,           # 45s (default 10s too short)
    'heartbeat.interval.ms': 15000,        # 15s (1/3 of session timeout)
    'max.poll.interval.ms': 300000,        # 5min for long processing

    # Use cooperative rebalancing
    'partition.assignment.strategy': 'cooperative-sticky',
})
```

---

## Under-Replicated Partitions

### Symptoms
- `kafka_server_ReplicaManager_UnderReplicatedPartitions > 0`
- Alerts firing
- Potential data loss risk

### Runbook

```bash
# 1. Identify under-replicated partitions
kubectl exec -n kafka kafka-cluster-kafka-0 -c kafka -- \
  bin/kafka-topics.sh --bootstrap-server localhost:9092 \
  --describe --under-replicated-partitions

# 2. Check broker status
kubectl get pods -n kafka -l strimzi.io/kind=Kafka
kubectl describe pod kafka-cluster-kafka-1 -n kafka

# 3. Check broker logs
kubectl logs -n kafka kafka-cluster-kafka-1 -c kafka --tail=100 | grep -i "error\|exception"

# 4. Check disk usage
kubectl exec -n kafka kafka-cluster-kafka-1 -c kafka -- df -h /var/lib/kafka

# 5. Check network between brokers
kubectl exec -n kafka kafka-cluster-kafka-0 -c kafka -- \
  nc -zv kafka-cluster-kafka-1.kafka-cluster-kafka-brokers 9091
```

### Resolution

| Cause | Fix |
|-------|-----|
| Broker down | Restart pod, check PVC |
| Disk full | Increase PVC, reduce retention |
| Network partition | Check NetworkPolicies |
| Slow followers | Check network, disk I/O |
| Leader election | Wait, check controller logs |

### Recovery

```bash
# Force leader election (if stuck)
kubectl exec -n kafka kafka-cluster-kafka-0 -c kafka -- \
  bin/kafka-leader-election.sh \
  --bootstrap-server localhost:9092 \
  --election-type PREFERRED \
  --all-topic-partitions

# Reassign partitions (if broker permanently lost)
# Create reassignment.json, then:
kubectl exec -n kafka kafka-cluster-kafka-0 -c kafka -- \
  bin/kafka-reassign-partitions.sh \
  --bootstrap-server localhost:9092 \
  --reassignment-json-file /tmp/reassignment.json \
  --execute
```

---

## Connection/Auth Issues

### Symptoms
- "Connection refused"
- "SASL authentication failed"
- "SSL handshake failed"

### Runbook

```bash
# 1. Test basic connectivity
kubectl run test-conn --rm -it --image=busybox -n app -- \
  nc -zv kafka-cluster-kafka-bootstrap.kafka 9092

# 2. Check DNS resolution
kubectl run test-dns --rm -it --image=busybox -n app -- \
  nslookup kafka-cluster-kafka-bootstrap.kafka

# 3. Check listener configuration
kubectl get kafka kafka-cluster -n kafka -o jsonpath='{.spec.kafka.listeners}'

# 4. Verify credentials
kubectl get secret order-service -n kafka -o yaml
kubectl get secret kafka-cluster-cluster-ca-cert -n kafka -o yaml

# 5. Test with kafkacat
kubectl run kafkacat --rm -it --image=confluentinc/cp-kafkacat -n app -- \
  kafkacat -b kafka-cluster-kafka-bootstrap:9092 -L
```

### Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Connection refused` | Wrong port, service down | Check listener, port |
| `SASL authentication failed` | Wrong credentials | Verify secret |
| `SSL handshake failed` | Wrong CA, expired cert | Check certificates |
| `Unknown topic` | Topic doesn't exist | Create topic |
| `Not authorized` | Missing ACL | Add ACL permissions |

### Debug SSL

```bash
# Check certificate
openssl s_client -connect kafka-cluster-kafka-bootstrap:9093 \
  -CAfile /certs/ca.crt

# Verify client cert
openssl x509 -in /certs/user.crt -text -noout
```

---

## Message Loss Investigation

### Symptoms
- Messages sent but not received
- Gaps in sequence numbers
- "Fire and forget" without confirmation

### Runbook

```bash
# 1. Check producer acks configuration
# acks=0 or acks=1 can lose messages

# 2. Check topic replication
kubectl exec -n kafka kafka-cluster-kafka-0 -c kafka -- \
  bin/kafka-topics.sh --bootstrap-server localhost:9092 \
  --describe --topic orders

# Look for: ReplicationFactor, Isr

# 3. Check min.insync.replicas
# If ISR < min.insync.replicas, writes fail

# 4. Check producer errors
kubectl logs -n app -l app=order-producer | grep -i "error\|failed\|timeout"

# 5. Verify messages in topic
kubectl exec -n kafka kafka-cluster-kafka-0 -c kafka -- \
  bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic orders \
  --from-beginning \
  --max-messages 10
```

### Prevention Checklist

```python
# Safe producer config
producer = Producer({
    'bootstrap.servers': 'kafka:9092',
    'acks': 'all',                    # Wait for all replicas
    'enable.idempotence': True,       # Prevent duplicates
    'retries': 2147483647,            # Infinite retries
    'delivery.timeout.ms': 120000,    # 2 min timeout
})

# Always use callback
def delivery_callback(err, msg):
    if err:
        logger.error(f"DELIVERY FAILED: {err}")
        # Alert, retry, or dead letter

producer.produce(topic, value, callback=delivery_callback)
producer.flush()  # Never skip
```

---

## Performance Degradation

### Symptoms
- High latency
- Throughput drop
- Timeouts

### Runbook

```bash
# 1. Check broker CPU/memory
kubectl top pods -n kafka -l strimzi.io/kind=Kafka

# 2. Check disk I/O
kubectl exec -n kafka kafka-cluster-kafka-0 -c kafka -- iostat -x 1 3

# 3. Check network
kubectl exec -n kafka kafka-cluster-kafka-0 -c kafka -- \
  netstat -an | grep -c ESTABLISHED

# 4. Check request queue
# Metric: kafka.network:type=RequestChannel,name=RequestQueueSize

# 5. Check log flush latency
# Metric: kafka.log:type=LogFlushStats,name=LogFlushRateAndTimeMs
```

### Tuning

| Issue | Tune |
|-------|------|
| High produce latency | Increase `linger.ms`, use compression |
| High fetch latency | Increase `fetch.min.bytes` |
| Disk bottleneck | Use faster storage, spread partitions |
| Network bottleneck | Compress, use rack awareness |
| Memory pressure | Increase heap, tune buffer sizes |

---

## Quick Reference

```bash
# All topics
kafka-topics.sh --bootstrap-server localhost:9092 --list

# Topic details
kafka-topics.sh --bootstrap-server localhost:9092 --describe --topic TOPIC

# Consumer groups
kafka-consumer-groups.sh --bootstrap-server localhost:9092 --list

# Group lag
kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group GROUP

# Read from beginning
kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic TOPIC --from-beginning

# Read latest
kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic TOPIC

# Produce test message
echo "test" | kafka-console-producer.sh --bootstrap-server localhost:9092 --topic TOPIC
```
