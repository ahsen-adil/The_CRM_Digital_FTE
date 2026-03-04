# Operator Comparison

Decision matrix for Kafka deployment options on Kubernetes.

---

## Quick Comparison

| Feature | Strimzi | Confluent for K8s | Redpanda |
|---------|---------|-------------------|----------|
| **License** | Apache 2.0 | Commercial | BSL 1.1 |
| **Cost** | Free | $$$$ | Free* |
| **KRaft** | Full support | Full support | Native (no ZK ever) |
| **Schema Registry** | Separate deploy | Included | Included |
| **Connect** | KafkaConnect CRD | Included | Separate |
| **Monitoring** | Prometheus export | Control Center | Console |
| **Support** | Community | Enterprise | Enterprise option |

*BSL converts to Apache 2.0 after 4 years

---

## Strimzi

**Best for:** K8s-native, GitOps, cost-conscious production

### Pros

- Fully open source (Apache 2.0)
- Deep Kubernetes integration (CRDs, operators)
- GitOps-friendly declarative configuration
- Active CNCF community
- Full KRaft support
- Flexible deployment options

### Cons

- Schema Registry separate deployment
- No built-in UI (use third-party)
- Learning curve for CRDs
- Community support only (unless Red Hat)

### When to Choose

- GitOps workflows (ArgoCD, Flux)
- Budget constraints
- Kubernetes-first architecture
- Open source preference
- Full control needed

### Deployment

```bash
helm repo add strimzi https://strimzi.io/charts
helm install strimzi strimzi/strimzi-kafka-operator -n kafka
kubectl apply -f kafka-cluster.yaml
```

---

## Confluent for Kubernetes

**Best for:** Enterprise, full platform, commercial support

### Pros

- Complete platform (Schema Registry, Connect, ksqlDB)
- Confluent Control Center (UI)
- Enterprise support with SLAs
- Tiered storage support
- Multi-datacenter replication
- Role-based access control

### Cons

- Commercial license required
- Higher complexity
- Opinionated configuration
- Vendor lock-in potential

### When to Choose

- Enterprise requirements
- Need commercial support
- Full Confluent Platform features
- Existing Confluent relationship
- Compliance requirements

### Deployment

```bash
helm repo add confluentinc https://packages.confluent.io/helm
helm install confluent confluentinc/confluent-for-kubernetes -n confluent
kubectl apply -f confluent-platform.yaml
```

---

## Redpanda

**Best for:** Simplicity, performance, Kafka-compatible

### Pros

- No ZooKeeper ever (C++ implementation)
- Lower latency, higher throughput
- Simpler operations (single binary)
- Kafka API compatible
- Built-in Schema Registry
- Console UI included
- Lower resource usage

### Cons

- BSL license (not pure open source)
- Newer, less battle-tested
- Some Kafka features missing
- Smaller ecosystem

### When to Choose

- Performance critical
- Operational simplicity priority
- New greenfield projects
- Smaller teams
- License acceptable

### Deployment

```bash
helm repo add redpanda https://charts.redpanda.com
helm install redpanda redpanda/redpanda -n redpanda
```

---

## Decision Matrix

| Requirement | Strimzi | Confluent | Redpanda |
|-------------|---------|-----------|----------|
| **Pure open source** | ★★★ | ★ | ★★ |
| **Enterprise support** | ★ | ★★★ | ★★ |
| **Ease of operation** | ★★ | ★★ | ★★★ |
| **K8s integration** | ★★★ | ★★ | ★★ |
| **Performance** | ★★ | ★★ | ★★★ |
| **Feature completeness** | ★★ | ★★★ | ★★ |
| **Cost (TCO)** | ★★★ | ★ | ★★★ |
| **Community size** | ★★★ | ★★ | ★★ |
| **Production proven** | ★★★ | ★★★ | ★★ |

---

## Feature Comparison

### CRD Support

| CRD | Strimzi | Confluent | Redpanda |
|-----|---------|-----------|----------|
| Kafka cluster | ✅ Kafka | ✅ Kafka | ✅ Cluster |
| Topics | ✅ KafkaTopic | ✅ KafkaTopic | ✅ Topic |
| Users | ✅ KafkaUser | ✅ | ✅ User |
| Connect | ✅ KafkaConnect | ✅ Connect | ❌ |
| Connectors | ✅ KafkaConnector | ✅ Connector | ❌ |
| Mirror | ✅ KafkaMirrorMaker2 | ✅ | ❌ |

### Security

| Feature | Strimzi | Confluent | Redpanda |
|---------|---------|-----------|----------|
| TLS | ✅ | ✅ | ✅ |
| SASL/SCRAM | ✅ | ✅ | ✅ |
| mTLS | ✅ | ✅ | ✅ |
| OAuth/OIDC | ✅ | ✅ | ✅ |
| RBAC | ❌ | ✅ | ✅ |
| Audit logs | ❌ | ✅ | ✅ |

### Monitoring

| Feature | Strimzi | Confluent | Redpanda |
|---------|---------|-----------|----------|
| Prometheus metrics | ✅ | ✅ | ✅ |
| Grafana dashboards | Community | Provided | Provided |
| Built-in UI | ❌ | Control Center | Console |
| Alerting rules | Community | Provided | Provided |

---

## Migration Considerations

### From Strimzi to Confluent

- Topic data preserved (same Kafka)
- Reconfigure client connections
- Deploy Confluent operator alongside
- Migrate topics gradually
- Update Schema Registry clients

### From Strimzi to Redpanda

- Topics need migration (different storage)
- Kafka clients compatible (protocol same)
- Schema Registry migration
- Test thoroughly (subtle differences)

### From Confluent to Strimzi

- Possible but loses Confluent features
- Deploy Schema Registry separately
- Connect configuration migration
- Client connection updates

---

## Cost Comparison (Rough)

| Item | Strimzi | Confluent Cloud | Redpanda |
|------|---------|-----------------|----------|
| **License** | $0 | $0.10-0.50/GB | $0 |
| **Support** | Community/$$ (Red Hat) | Included | Optional $$ |
| **Operations** | Your team | Managed | Your team |
| **Schema Registry** | Self-host | Included | Included |

### Self-Hosted (3 brokers, 1TB/month)

- **Strimzi:** Infrastructure only (~$300-500/mo cloud)
- **Confluent Platform:** License + infrastructure (~$2000+/mo)
- **Redpanda:** Infrastructure only (~$250-400/mo)

---

## Recommendation

```
START HERE:
    │
    ▼
Need enterprise support? ──YES──▶ Confluent
    │
    NO
    │
    ▼
Performance critical? ──YES──▶ Consider Redpanda
    │                          (test compatibility)
    NO
    │
    ▼
K8s-native / GitOps? ──YES──▶ Strimzi ✓
    │
    NO
    │
    ▼
Managed service OK? ──YES──▶ Confluent Cloud / AWS MSK
    │
    NO
    │
    ▼
Strimzi (default choice)
```

**Default recommendation:** Strimzi for most Kubernetes deployments.
