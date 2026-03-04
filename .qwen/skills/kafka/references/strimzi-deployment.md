# Strimzi Deployment

Deploying Apache Kafka on Kubernetes with Strimzi in KRaft mode.

---

## Prerequisites

- Kubernetes 1.27+
- Helm 3.x
- `kubectl` configured

---

## Quick Start

```bash
# 1. Install Strimzi operator
helm repo add strimzi https://strimzi.io/charts
helm install strimzi-operator strimzi/strimzi-kafka-operator \
  -n kafka --create-namespace

# 2. Wait for operator
kubectl wait --for=condition=Ready pod -l name=strimzi-cluster-operator -n kafka --timeout=300s

# 3. Deploy Kafka cluster
kubectl apply -f kafka-cluster.yaml -n kafka

# 4. Wait for cluster
kubectl wait kafka/my-cluster --for=condition=Ready -n kafka --timeout=600s
```

---

## Kafka CRD (KRaft Mode)

```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: Kafka
metadata:
  name: my-cluster
  namespace: kafka
spec:
  kafka:
    version: 4.1.1
    # KRaft mode - no ZooKeeper
    metadataVersion: 4.1-IV0

    listeners:
      - name: plain
        port: 9092
        type: internal
        tls: false
      - name: tls
        port: 9093
        type: internal
        tls: true
        authentication:
          type: tls

    config:
      offsets.topic.replication.factor: 3
      transaction.state.log.replication.factor: 3
      transaction.state.log.min.isr: 2
      default.replication.factor: 3
      min.insync.replicas: 2

  # Node pools for role separation
  # See KafkaNodePool below

  entityOperator:
    topicOperator: {}
    userOperator: {}
```

---

## KafkaNodePool (Role Separation)

### Controllers (Metadata)

```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaNodePool
metadata:
  name: controllers
  labels:
    strimzi.io/cluster: my-cluster
spec:
  replicas: 3
  roles:
    - controller
  storage:
    type: jbod
    volumes:
      - id: 0
        type: persistent-claim
        size: 10Gi
        class: standard
  resources:
    requests:
      memory: 2Gi
      cpu: 500m
    limits:
      memory: 4Gi
      cpu: 1
```

### Brokers (Data)

```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaNodePool
metadata:
  name: brokers
  labels:
    strimzi.io/cluster: my-cluster
spec:
  replicas: 3
  roles:
    - broker
  storage:
    type: jbod
    volumes:
      - id: 0
        type: persistent-claim
        size: 100Gi
        class: fast-ssd
  resources:
    requests:
      memory: 4Gi
      cpu: 1
    limits:
      memory: 8Gi
      cpu: 2
```

### Combined (Dev/Small)

```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaNodePool
metadata:
  name: dual-role
  labels:
    strimzi.io/cluster: my-cluster
spec:
  replicas: 3
  roles:
    - controller
    - broker
  storage:
    type: jbod
    volumes:
      - id: 0
        type: persistent-claim
        size: 50Gi
```

---

## KafkaTopic CRD

```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaTopic
metadata:
  name: order-events
  labels:
    strimzi.io/cluster: my-cluster
spec:
  partitions: 12
  replicas: 3
  config:
    retention.ms: 604800000        # 7 days
    cleanup.policy: delete
    min.insync.replicas: 2
    segment.bytes: 1073741824      # 1GB segments
```

### Topic Naming

```yaml
# Pattern: <domain>.<entity>.<event>
metadata:
  name: orders.order.created
  name: payments.payment.completed
  name: agents.task.assigned
```

---

## KafkaUser CRD

### SCRAM Authentication

```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaUser
metadata:
  name: order-service
  labels:
    strimzi.io/cluster: my-cluster
spec:
  authentication:
    type: scram-sha-512
  authorization:
    type: simple
    acls:
      # Produce to order topics
      - resource:
          type: topic
          name: orders.
          patternType: prefix
        operations:
          - Write
          - Describe
      # Consume from order topics
      - resource:
          type: topic
          name: orders.
          patternType: prefix
        operations:
          - Read
          - Describe
      # Consumer group
      - resource:
          type: group
          name: order-service
          patternType: literal
        operations:
          - Read
```

### mTLS Authentication

```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaUser
metadata:
  name: payment-service
  labels:
    strimzi.io/cluster: my-cluster
spec:
  authentication:
    type: tls
  authorization:
    type: simple
    acls:
      - resource:
          type: topic
          name: payments.
          patternType: prefix
        operations:
          - All
```

---

## Environment Configurations

### Development

```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: Kafka
metadata:
  name: dev-cluster
spec:
  kafka:
    version: 4.1.1
    metadataVersion: 4.1-IV0
    listeners:
      - name: plain
        port: 9092
        type: internal
        tls: false  # No TLS for dev
    config:
      offsets.topic.replication.factor: 1
      transaction.state.log.replication.factor: 1
      default.replication.factor: 1
      min.insync.replicas: 1
---
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaNodePool
metadata:
  name: dev-pool
  labels:
    strimzi.io/cluster: dev-cluster
spec:
  replicas: 1  # Single node
  roles:
    - controller
    - broker
  storage:
    type: ephemeral  # No persistence
  resources:
    requests:
      memory: 1Gi
      cpu: 250m
```

### Production

```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: Kafka
metadata:
  name: prod-cluster
spec:
  kafka:
    version: 4.1.1
    metadataVersion: 4.1-IV0
    listeners:
      - name: tls
        port: 9093
        type: internal
        tls: true
        authentication:
          type: tls
      - name: external
        port: 9094
        type: loadbalancer
        tls: true
        authentication:
          type: scram-sha-512
    config:
      offsets.topic.replication.factor: 3
      transaction.state.log.replication.factor: 3
      default.replication.factor: 3
      min.insync.replicas: 2
      log.retention.hours: 168  # 7 days
      auto.create.topics.enable: false
---
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaNodePool
metadata:
  name: controllers
  labels:
    strimzi.io/cluster: prod-cluster
spec:
  replicas: 3
  roles:
    - controller
  storage:
    type: jbod
    volumes:
      - id: 0
        type: persistent-claim
        size: 20Gi
        class: fast-ssd
---
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaNodePool
metadata:
  name: brokers
  labels:
    strimzi.io/cluster: prod-cluster
spec:
  replicas: 5
  roles:
    - broker
  storage:
    type: jbod
    volumes:
      - id: 0
        type: persistent-claim
        size: 500Gi
        class: fast-ssd
  resources:
    requests:
      memory: 8Gi
      cpu: 2
    limits:
      memory: 16Gi
      cpu: 4
```

---

## Storage Sizing

### Formula

```
Storage per broker = (daily_bytes × retention_days × replication_factor) / num_brokers
```

### Example Calculation

| Parameter | Value |
|-----------|-------|
| Daily message volume | 100 GB/day |
| Retention period | 7 days |
| Replication factor | 3 |
| Number of brokers | 5 |

```
Storage = (100 GB × 7 days × 3) / 5 brokers = 420 GB per broker
```

**Add 20% buffer:**
```
Recommended: 420 GB × 1.2 = 504 GB → Round to 500 GB
```

### Storage Class Selection

| Workload | Storage Class | Why |
|----------|---------------|-----|
| Dev/Test | standard | Cost-effective, ephemeral OK |
| Production (low) | gp3 (AWS) / pd-balanced (GCP) | Balanced price/performance |
| Production (high) | io2 (AWS) / pd-ssd (GCP) | High IOPS for throughput |
| Edge/local | local-path | Direct disk, lowest latency |

### JBOD Configuration

For high-throughput clusters, use multiple disks:

```yaml
storage:
  type: jbod
  volumes:
    - id: 0
      type: persistent-claim
      size: 500Gi
      class: fast-ssd
    - id: 1
      type: persistent-claim
      size: 500Gi
      class: fast-ssd
```

**Benefit:** Kafka stripes partitions across volumes for parallel I/O.

---

## Schema Registry

Strimzi doesn't include Schema Registry. Deploy separately:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: schema-registry
  namespace: kafka
spec:
  replicas: 2
  selector:
    matchLabels:
      app: schema-registry
  template:
    metadata:
      labels:
        app: schema-registry
    spec:
      containers:
        - name: schema-registry
          image: confluentinc/cp-schema-registry:7.5.0
          ports:
            - containerPort: 8081
          env:
            - name: SCHEMA_REGISTRY_HOST_NAME
              valueFrom:
                fieldRef:
                  fieldPath: metadata.name
            - name: SCHEMA_REGISTRY_KAFKASTORE_BOOTSTRAP_SERVERS
              value: my-cluster-kafka-bootstrap:9092
            - name: SCHEMA_REGISTRY_LISTENERS
              value: http://0.0.0.0:8081
          resources:
            requests:
              memory: 512Mi
              cpu: 250m
            limits:
              memory: 1Gi
              cpu: 500m
---
apiVersion: v1
kind: Service
metadata:
  name: schema-registry
  namespace: kafka
spec:
  ports:
    - port: 8081
  selector:
    app: schema-registry
```

---

## Useful Commands

```bash
# Cluster status
kubectl get kafka -n kafka
kubectl get kafkanodepools -n kafka
kubectl describe kafka my-cluster -n kafka

# Topics
kubectl get kafkatopics -n kafka
kubectl describe kafkatopic order-events -n kafka

# Users
kubectl get kafkausers -n kafka
kubectl get secret order-service -n kafka -o jsonpath='{.data.password}' | base64 -d

# Logs
kubectl logs -n kafka -l strimzi.io/cluster=my-cluster -c kafka --tail=100

# Exec into broker
kubectl exec -n kafka my-cluster-kafka-0 -c kafka -- \
  bin/kafka-topics.sh --bootstrap-server localhost:9092 --list
```

---

## Troubleshooting

| Issue | Check | Fix |
|-------|-------|-----|
| Pods not starting | `kubectl describe pod` | Check resources, PVC |
| Cluster not ready | `kubectl get kafka -o yaml` | Check conditions |
| Topic creation fails | Topic operator logs | Check ACLs, config |
| Connection refused | Listener config | Verify listener type |
