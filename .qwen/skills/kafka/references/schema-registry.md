# Schema Registry

Avro schemas, evolution strategies, and Confluent Schema Registry.

---

## Why Schemas?

| Without Schema | With Schema |
|----------------|-------------|
| `{"user": "123"}` or `{"userId": 123}` | Enforced structure |
| Silent failures on type mismatch | Validation at produce time |
| No versioning | Evolution with compatibility |
| Large JSON payloads | Compact binary (Avro) |

---

## Avro Basics

### Schema Definition

```json
{
  "type": "record",
  "name": "OrderCreated",
  "namespace": "com.devraftel.orders",
  "fields": [
    {"name": "order_id", "type": "string"},
    {"name": "customer_id", "type": "string"},
    {"name": "total_amount", "type": "double"},
    {"name": "currency", "type": "string", "default": "USD"},
    {"name": "created_at", "type": "long", "logicalType": "timestamp-millis"},
    {
      "name": "items",
      "type": {
        "type": "array",
        "items": {
          "type": "record",
          "name": "OrderItem",
          "fields": [
            {"name": "product_id", "type": "string"},
            {"name": "quantity", "type": "int"},
            {"name": "unit_price", "type": "double"}
          ]
        }
      }
    },
    {"name": "metadata", "type": ["null", {"type": "map", "values": "string"}], "default": null}
  ]
}
```

### Type Reference

| Avro Type | Python Mapping | Notes |
|-----------|----------------|-------|
| null | None | Use in unions for optional |
| boolean | bool | |
| int | int | 32-bit signed |
| long | int | 64-bit signed |
| float | float | 32-bit IEEE 754 |
| double | float | 64-bit IEEE 754 |
| bytes | bytes | |
| string | str | UTF-8 |
| record | dict | Named complex type |
| array | list | |
| map | dict | Keys must be strings |
| union | value | `["null", "string"]` for optional |
| enum | str | |
| fixed | bytes | Fixed-size bytes |

### Logical Types

```json
{"name": "created_at", "type": "long", "logicalType": "timestamp-millis"}
{"name": "date", "type": "int", "logicalType": "date"}
{"name": "amount", "type": "bytes", "logicalType": "decimal", "precision": 10, "scale": 2}
{"name": "id", "type": "string", "logicalType": "uuid"}
```

---

## Schema Registry API

### Register Schema

```bash
curl -X POST -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  --data '{"schema": "{\"type\":\"record\",\"name\":\"Order\",\"fields\":[{\"name\":\"id\",\"type\":\"string\"}]}"}' \
  http://localhost:8081/subjects/orders-value/versions
```

### Get Schema

```bash
# Latest version
curl http://localhost:8081/subjects/orders-value/versions/latest

# Specific version
curl http://localhost:8081/subjects/orders-value/versions/1
```

### Check Compatibility

```bash
curl -X POST -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  --data '{"schema": "{...new schema...}"}' \
  http://localhost:8081/compatibility/subjects/orders-value/versions/latest
```

---

## Python Integration

### Producer with Avro

```python
from confluent_kafka import Producer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.serialization import SerializationContext, MessageField

# Schema Registry client
schema_registry_conf = {'url': 'http://localhost:8081'}
schema_registry = SchemaRegistryClient(schema_registry_conf)

# Define schema
schema_str = """
{
  "type": "record",
  "name": "Order",
  "namespace": "com.devraftel.orders",
  "fields": [
    {"name": "order_id", "type": "string"},
    {"name": "customer_id", "type": "string"},
    {"name": "total", "type": "double"}
  ]
}
"""

# Create serializer
avro_serializer = AvroSerializer(
    schema_registry,
    schema_str,
    lambda obj, ctx: obj  # to_dict function
)

# Producer
producer = Producer({'bootstrap.servers': 'localhost:9092'})

def produce_order(order: dict):
    producer.produce(
        topic='orders',
        key=order['order_id'],
        value=avro_serializer(
            order,
            SerializationContext('orders', MessageField.VALUE)
        )
    )
    producer.flush()

# Usage
produce_order({
    'order_id': 'ORD-123',
    'customer_id': 'CUST-456',
    'total': 99.99
})
```

### Consumer with Avro

```python
from confluent_kafka import Consumer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka.serialization import SerializationContext, MessageField

schema_registry = SchemaRegistryClient({'url': 'http://localhost:8081'})

avro_deserializer = AvroDeserializer(
    schema_registry,
    schema_str,
    lambda obj, ctx: obj  # from_dict function
)

consumer = Consumer({
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'order-processor',
    'auto.offset.reset': 'earliest'
})
consumer.subscribe(['orders'])

while True:
    msg = consumer.poll(1.0)
    if msg is None:
        continue
    if msg.error():
        continue

    order = avro_deserializer(
        msg.value(),
        SerializationContext('orders', MessageField.VALUE)
    )
    print(f"Received: {order}")
```

---

## Schema Evolution

### Compatibility Levels

| Level | Add Field | Remove Field | Change Type |
|-------|-----------|--------------|-------------|
| **BACKWARD** | With default | Yes | No |
| **FORWARD** | Yes | With default | No |
| **FULL** | With default | With default | No |
| **NONE** | Yes | Yes | Yes |

### Set Compatibility

```bash
# Global default
curl -X PUT -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  --data '{"compatibility": "BACKWARD"}' \
  http://localhost:8081/config

# Per subject
curl -X PUT -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  --data '{"compatibility": "FULL"}' \
  http://localhost:8081/config/orders-value
```

### Evolution Examples

#### Adding Optional Field (BACKWARD Compatible)

```json
// Version 1
{"name": "order_id", "type": "string"}
{"name": "total", "type": "double"}

// Version 2 - New field with default
{"name": "order_id", "type": "string"}
{"name": "total", "type": "double"}
{"name": "discount", "type": "double", "default": 0.0}  // OK
```

#### Adding Required Field (BREAKS BACKWARD)

```json
// Version 2 - New field without default
{"name": "currency", "type": "string"}  // FAILS - old consumers can't read
```

#### Removing Field (FORWARD Compatible)

```json
// Version 1
{"name": "order_id", "type": "string"}
{"name": "legacy_field", "type": "string"}

// Version 2 - Remove field (if it had default)
{"name": "order_id", "type": "string"}
// legacy_field removed - new consumers ignore it in old messages
```

---

## Compatibility Decision Matrix

| Scenario | Recommended | Why |
|----------|-------------|-----|
| Adding new events | BACKWARD | New consumers read old messages |
| Deprecating fields | FORWARD | Old consumers read new messages |
| Critical data | FULL | Maximum safety |
| Rapid iteration (dev) | NONE | Flexibility (dangerous) |

---

## Subject Naming

### TopicNameStrategy (Default)

```
Topic: orders
Key subject: orders-key
Value subject: orders-value
```

### RecordNameStrategy

```
Topic: orders
Key subject: com.devraftel.orders.OrderKey
Value subject: com.devraftel.orders.Order
```

### TopicRecordNameStrategy

```
Topic: orders
Value subject: orders-com.devraftel.orders.Order
```

Configure in producer:

```python
avro_serializer = AvroSerializer(
    schema_registry,
    schema_str,
    conf={'subject.name.strategy': 'io.confluent.kafka.serializers.subject.RecordNameStrategy'}
)
```

---

## JSON Schema Alternative

```python
from confluent_kafka.schema_registry.json_schema import JSONSerializer

schema_str = """
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "order_id": {"type": "string"},
    "total": {"type": "number"}
  },
  "required": ["order_id", "total"]
}
"""

json_serializer = JSONSerializer(schema_registry, schema_str)
```

### When to Use JSON Schema

| Use Avro | Use JSON Schema |
|----------|-----------------|
| High throughput (smaller size) | Debugging (human readable) |
| Strict schemas | Flexible/nested structures |
| Long-term storage | Rapid prototyping |
| Production | Development |

---

## Best Practices

### Schema Design

```
1. Use namespaces: com.company.domain.EntityName
2. Add doc fields: {"doc": "Customer order event"}
3. Use logical types for dates, decimals
4. Make new fields optional with defaults
5. Use enums for fixed sets
```

### Versioning

```
1. Never break compatibility in production
2. Test compatibility before deploying
3. Keep all schema versions in version control
4. Document breaking changes
5. Use compatibility checks in CI/CD
```

### CI/CD Integration

```yaml
# .github/workflows/schema-check.yaml
- name: Check Schema Compatibility
  run: |
    for schema in schemas/*.avsc; do
      subject=$(basename $schema .avsc)-value
      curl -X POST \
        -H "Content-Type: application/vnd.schemaregistry.v1+json" \
        --data "{\"schema\": $(cat $schema | jq -c . | jq -Rs .)}" \
        $SCHEMA_REGISTRY_URL/compatibility/subjects/$subject/versions/latest \
        | jq -e '.is_compatible == true'
    done
```
