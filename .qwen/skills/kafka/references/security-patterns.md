# Security Patterns

Authentication and encryption configurations per environment.

---

## Security Progression

```
Development         Staging             Production
    │                  │                    │
    ▼                  ▼                    ▼
No Auth (plain) → SASL/SCRAM-512 → mTLS (certificates)
No TLS          → TLS (one-way)  → TLS (mutual)
```

---

## Development (No Auth)

Simple setup for local development.

### Strimzi Kafka

```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: Kafka
metadata:
  name: dev-cluster
spec:
  kafka:
    listeners:
      - name: plain
        port: 9092
        type: internal
        tls: false  # No encryption
        # No authentication
```

### Client Config

```python
producer = Producer({
    'bootstrap.servers': 'kafka:9092',
})
```

---

## Staging (SASL/SCRAM)

Username/password authentication with TLS encryption.

### Strimzi Kafka

```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: Kafka
metadata:
  name: staging-cluster
spec:
  kafka:
    listeners:
      - name: tls
        port: 9093
        type: internal
        tls: true
        authentication:
          type: scram-sha-512
```

### Create User

```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaUser
metadata:
  name: order-service
  labels:
    strimzi.io/cluster: staging-cluster
spec:
  authentication:
    type: scram-sha-512
  authorization:
    type: simple
    acls:
      - resource:
          type: topic
          name: orders
          patternType: prefix
        operations:
          - Read
          - Write
          - Describe
      - resource:
          type: group
          name: order-service
          patternType: literal
        operations:
          - Read
```

### Get Credentials

```bash
# Get password from secret
kubectl get secret order-service -n kafka \
  -o jsonpath='{.data.password}' | base64 -d

# Get JAAS config
kubectl get secret order-service -n kafka \
  -o jsonpath='{.data.sasl\.jaas\.config}' | base64 -d
```

### Client Config

```python
producer = Producer({
    'bootstrap.servers': 'kafka:9093',
    'security.protocol': 'SASL_SSL',
    'sasl.mechanism': 'SCRAM-SHA-512',
    'sasl.username': 'order-service',
    'sasl.password': os.environ['KAFKA_PASSWORD'],
    'ssl.ca.location': '/certs/ca.crt',
})
```

### Environment Variables

```yaml
# Kubernetes Deployment
env:
  - name: KAFKA_PASSWORD
    valueFrom:
      secretKeyRef:
        name: order-service
        key: password
  - name: KAFKA_BOOTSTRAP_SERVERS
    value: staging-cluster-kafka-bootstrap:9093
```

---

## Production (mTLS)

Mutual TLS with client certificates.

### Strimzi Kafka

```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: Kafka
metadata:
  name: prod-cluster
spec:
  kafka:
    listeners:
      - name: tls
        port: 9093
        type: internal
        tls: true
        authentication:
          type: tls  # Client certificate auth
```

### Create User (TLS)

```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaUser
metadata:
  name: payment-service
  labels:
    strimzi.io/cluster: prod-cluster
spec:
  authentication:
    type: tls  # Certificate-based
  authorization:
    type: simple
    acls:
      - resource:
          type: topic
          name: payments
          patternType: prefix
        operations:
          - All
```

### Get Certificates

```bash
# Strimzi creates secrets automatically:
# - payment-service (user cert + key)
# - prod-cluster-cluster-ca-cert (CA cert)

# Extract to files
kubectl get secret payment-service -n kafka \
  -o jsonpath='{.data.user\.crt}' | base64 -d > user.crt
kubectl get secret payment-service -n kafka \
  -o jsonpath='{.data.user\.key}' | base64 -d > user.key
kubectl get secret prod-cluster-cluster-ca-cert -n kafka \
  -o jsonpath='{.data.ca\.crt}' | base64 -d > ca.crt
```

### Client Config

```python
producer = Producer({
    'bootstrap.servers': 'prod-cluster-kafka-bootstrap:9093',
    'security.protocol': 'SSL',
    'ssl.ca.location': '/certs/ca.crt',
    'ssl.certificate.location': '/certs/user.crt',
    'ssl.key.location': '/certs/user.key',
    # Optional: key password
    'ssl.key.password': os.environ.get('SSL_KEY_PASSWORD'),
})
```

### Mount Certificates

```yaml
# Kubernetes Deployment
spec:
  containers:
    - name: app
      volumeMounts:
        - name: kafka-certs
          mountPath: /certs
          readOnly: true
  volumes:
    - name: kafka-certs
      projected:
        sources:
          - secret:
              name: payment-service
              items:
                - key: user.crt
                  path: user.crt
                - key: user.key
                  path: user.key
          - secret:
              name: prod-cluster-cluster-ca-cert
              items:
                - key: ca.crt
                  path: ca.crt
```

---

## ACL Patterns

### Service Account Pattern

```yaml
# One user per service, scoped permissions
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaUser
metadata:
  name: order-service
spec:
  authorization:
    type: simple
    acls:
      # Produce to own topics
      - resource:
          type: topic
          name: orders.
          patternType: prefix
        operations: [Write, Describe]

      # Consume from own + shared topics
      - resource:
          type: topic
          name: orders.
          patternType: prefix
        operations: [Read, Describe]
      - resource:
          type: topic
          name: shared.notifications
          patternType: literal
        operations: [Read, Describe]

      # Own consumer group
      - resource:
          type: group
          name: order-service
          patternType: prefix
        operations: [Read]
```

### Producer-Only

```yaml
acls:
  - resource:
      type: topic
      name: events
      patternType: literal
    operations: [Write, Describe]
  - resource:
      type: topic
      name: events
      patternType: literal
    operations: [Create]  # For auto-topic creation
```

### Consumer-Only

```yaml
acls:
  - resource:
      type: topic
      name: events
      patternType: literal
    operations: [Read, Describe]
  - resource:
      type: group
      name: my-consumer-group
      patternType: literal
    operations: [Read]
```

### Admin

```yaml
acls:
  - resource:
      type: topic
      name: "*"
      patternType: literal
    operations: [All]
  - resource:
      type: group
      name: "*"
      patternType: literal
    operations: [All]
  - resource:
      type: cluster
      patternType: literal
    operations: [All]
```

---

## Secrets Management

### External Secrets Operator

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: kafka-credentials
spec:
  secretStoreRef:
    name: vault-backend
    kind: ClusterSecretStore
  target:
    name: kafka-credentials
    template:
      data:
        username: "{{ .username }}"
        password: "{{ .password }}"
  data:
    - secretKey: username
      remoteRef:
        key: kafka/order-service
        property: username
    - secretKey: password
      remoteRef:
        key: kafka/order-service
        property: password
```

### Sealed Secrets

```yaml
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: kafka-credentials
spec:
  encryptedData:
    password: AgBy8hC...encrypted...
```

---

## Configuration Matrix

| Setting | Dev | Staging | Prod |
|---------|-----|---------|------|
| `security.protocol` | `PLAINTEXT` | `SASL_SSL` | `SSL` |
| `sasl.mechanism` | - | `SCRAM-SHA-512` | - |
| `ssl.ca.location` | - | `/certs/ca.crt` | `/certs/ca.crt` |
| `ssl.certificate.location` | - | - | `/certs/user.crt` |
| `ssl.key.location` | - | - | `/certs/user.key` |

---

## Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: kafka-access
  namespace: kafka
spec:
  podSelector:
    matchLabels:
      strimzi.io/cluster: prod-cluster
  policyTypes:
    - Ingress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              kafka-access: "true"
        - podSelector:
            matchLabels:
              kafka-client: "true"
      ports:
        - port: 9093
          protocol: TCP
```

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `SASL authentication failed` | Wrong credentials | Check secret values |
| `SSL handshake failed` | Certificate mismatch | Verify CA cert |
| `Not authorized` | Missing ACL | Add required permissions |
| `Connection refused` | Wrong port/protocol | Match listener config |
| `Certificate expired` | Strimzi cert rotation | Restart clients |
