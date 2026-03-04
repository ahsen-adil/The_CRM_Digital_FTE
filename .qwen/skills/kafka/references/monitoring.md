# Monitoring

Prometheus metrics, Grafana dashboards, and alerting for Kafka.

---

## Strimzi Metrics Configuration

### Enable Prometheus Metrics

```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: Kafka
metadata:
  name: my-cluster
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
```

### Metrics ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: kafka-metrics
data:
  kafka-metrics-config.yml: |
    lowercaseOutputName: true
    rules:
      # Broker metrics
      - pattern: kafka.server<type=(.+), name=(.+)><>Value
        name: kafka_server_$1_$2
        type: GAUGE
      - pattern: kafka.server<type=(.+), name=(.+)><>Count
        name: kafka_server_$1_$2_total
        type: COUNTER

      # Topic metrics
      - pattern: kafka.log<type=(.+), name=(.+), topic=(.+), partition=(.+)><>Value
        name: kafka_log_$1_$2
        labels:
          topic: $3
          partition: $4
        type: GAUGE

      # Consumer group metrics
      - pattern: kafka.coordinator.group<type=(.+), name=(.+)><>Value
        name: kafka_coordinator_$1_$2
        type: GAUGE
```

---

## Key Metrics

### Broker Health

| Metric | Query | Alert Threshold |
|--------|-------|-----------------|
| Under-replicated partitions | `kafka_server_ReplicaManager_UnderReplicatedPartitions` | > 0 |
| Offline partitions | `kafka_controller_KafkaController_OfflinePartitionsCount` | > 0 |
| Active controller | `kafka_controller_KafkaController_ActiveControllerCount` | != 1 |
| ISR shrinks/expands | `rate(kafka_server_ReplicaManager_IsrShrinksPerSec[5m])` | > 0 sustained |

### Throughput

| Metric | Query | Description |
|--------|-------|-------------|
| Messages in/sec | `sum(rate(kafka_server_BrokerTopicMetrics_MessagesInPerSec[5m]))` | Cluster throughput |
| Bytes in/sec | `sum(rate(kafka_server_BrokerTopicMetrics_BytesInPerSec[5m]))` | Network in |
| Bytes out/sec | `sum(rate(kafka_server_BrokerTopicMetrics_BytesOutPerSec[5m]))` | Network out |

### Consumer Lag

| Metric | Query | Alert Threshold |
|--------|-------|-----------------|
| Consumer lag | `kafka_consumergroup_lag` | > 10000 |
| Lag rate | `rate(kafka_consumergroup_lag[5m])` | Increasing |
| Lag by group | `sum by(consumergroup)(kafka_consumergroup_lag)` | Group-specific |

### Latency

| Metric | Query | Alert Threshold |
|--------|-------|-----------------|
| Produce latency | `kafka_network_RequestMetrics_TotalTimeMs{request="Produce"}` | p99 > 100ms |
| Fetch latency | `kafka_network_RequestMetrics_TotalTimeMs{request="Fetch"}` | p99 > 100ms |
| Request queue time | `kafka_network_RequestChannel_RequestQueueTimeMs` | > 10ms |

---

## Prometheus ServiceMonitor

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: kafka-metrics
  namespace: kafka
  labels:
    release: prometheus  # Match Prometheus selector
spec:
  selector:
    matchLabels:
      strimzi.io/cluster: my-cluster
      strimzi.io/kind: Kafka
  endpoints:
    - port: tcp-prometheus
      interval: 30s
      path: /metrics
```

---

## Grafana Dashboards

### Strimzi Dashboard

Import official Strimzi dashboards:
- Kafka: ID `11285`
- ZooKeeper: ID `11287` (not needed for KRaft)
- Kafka Exporter: ID `11288`

### Custom Consumer Lag Dashboard

```json
{
  "title": "Consumer Lag",
  "panels": [
    {
      "title": "Lag by Consumer Group",
      "type": "timeseries",
      "targets": [
        {
          "expr": "sum by(consumergroup)(kafka_consumergroup_lag)",
          "legendFormat": "{{consumergroup}}"
        }
      ]
    },
    {
      "title": "Lag by Topic",
      "type": "timeseries",
      "targets": [
        {
          "expr": "sum by(topic)(kafka_consumergroup_lag)",
          "legendFormat": "{{topic}}"
        }
      ]
    },
    {
      "title": "Lag Heatmap",
      "type": "heatmap",
      "targets": [
        {
          "expr": "sum by(consumergroup, topic)(kafka_consumergroup_lag)"
        }
      ]
    }
  ]
}
```

---

## Alerting Rules

### PrometheusRule

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: kafka-alerts
  namespace: kafka
spec:
  groups:
    - name: kafka.rules
      rules:
        # Broker alerts
        - alert: KafkaUnderReplicatedPartitions
          expr: kafka_server_ReplicaManager_UnderReplicatedPartitions > 0
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: Kafka under-replicated partitions
            description: "{{ $value }} partitions are under-replicated"

        - alert: KafkaOfflinePartitions
          expr: kafka_controller_KafkaController_OfflinePartitionsCount > 0
          for: 1m
          labels:
            severity: critical
          annotations:
            summary: Kafka offline partitions
            description: "{{ $value }} partitions are offline"

        - alert: KafkaNoActiveController
          expr: kafka_controller_KafkaController_ActiveControllerCount != 1
          for: 1m
          labels:
            severity: critical
          annotations:
            summary: No active Kafka controller

        # Consumer alerts
        - alert: KafkaConsumerLagHigh
          expr: sum by(consumergroup)(kafka_consumergroup_lag) > 10000
          for: 10m
          labels:
            severity: warning
          annotations:
            summary: "Consumer group {{ $labels.consumergroup }} lag is high"
            description: "Lag is {{ $value }} messages"

        - alert: KafkaConsumerLagIncreasing
          expr: |
            rate(kafka_consumergroup_lag[5m]) > 0
            and
            kafka_consumergroup_lag > 1000
          for: 15m
          labels:
            severity: warning
          annotations:
            summary: "Consumer lag increasing for {{ $labels.consumergroup }}"

        # Disk alerts
        - alert: KafkaDiskUsageHigh
          expr: |
            (kafka_log_Log_Size / kafka_log_Log_MaxSize) > 0.85
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: Kafka disk usage above 85%
```

---

## Kafka Exporter

Dedicated exporter for consumer group metrics.

```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: Kafka
metadata:
  name: my-cluster
spec:
  kafkaExporter:
    image: quay.io/strimzi/kafka:latest
    groupRegex: ".*"
    topicRegex: ".*"
    resources:
      requests:
        memory: 64Mi
        cpu: 50m
      limits:
        memory: 128Mi
        cpu: 100m
    logging: warn
    readinessProbe:
      initialDelaySeconds: 15
      timeoutSeconds: 5
    livenessProbe:
      initialDelaySeconds: 15
      timeoutSeconds: 5
```

---

## Application Metrics

### Producer Metrics

```python
from prometheus_client import Counter, Histogram, start_http_server

# Metrics
messages_produced = Counter(
    'kafka_messages_produced_total',
    'Total messages produced',
    ['topic']
)
produce_latency = Histogram(
    'kafka_produce_latency_seconds',
    'Produce latency',
    ['topic'],
    buckets=[.001, .005, .01, .025, .05, .1, .25, .5, 1]
)

# Usage
@produce_latency.labels(topic=topic).time()
async def produce_message(topic, value):
    result = await producer.produce(topic, value)
    messages_produced.labels(topic=topic).inc()
    return result

# Expose metrics
start_http_server(8000)
```

### Consumer Metrics

```python
from prometheus_client import Counter, Gauge

messages_consumed = Counter(
    'kafka_messages_consumed_total',
    'Total messages consumed',
    ['topic', 'group']
)
processing_time = Histogram(
    'kafka_message_processing_seconds',
    'Message processing time',
    ['topic']
)
consumer_lag = Gauge(
    'kafka_consumer_lag_messages',
    'Consumer lag in messages',
    ['topic', 'partition', 'group']
)
```

---

## Health Checks

### FastAPI Health Endpoint

```python
from fastapi import FastAPI, Response
from confluent_kafka.admin import AdminClient

app = FastAPI()

@app.get("/health")
async def health():
    try:
        admin = AdminClient({'bootstrap.servers': 'kafka:9092'})
        cluster_meta = admin.list_topics(timeout=5)
        return {
            "status": "healthy",
            "brokers": len(cluster_meta.brokers),
            "topics": len(cluster_meta.topics)
        }
    except Exception as e:
        return Response(
            content=f'{{"status": "unhealthy", "error": "{e}"}}',
            status_code=503,
            media_type="application/json"
        )
```

---

## Log Aggregation

### Fluent Bit Config

```yaml
[INPUT]
    Name              tail
    Path              /var/log/kafka/*.log
    Tag               kafka.*

[FILTER]
    Name              parser
    Match             kafka.*
    Key_Name          log
    Parser            kafka_log

[OUTPUT]
    Name              es
    Match             kafka.*
    Host              elasticsearch
    Port              9200
    Index             kafka-logs
```
