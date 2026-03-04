# FastAPI Integration

Async Kafka producers and consumers with FastAPI.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│ FastAPI Application                                         │
├─────────────────────────────────────────────────────────────┤
│ Lifespan                                                    │
│   ├── startup: Initialize producer, start consumer task    │
│   └── shutdown: Flush producer, stop consumer              │
├─────────────────────────────────────────────────────────────┤
│ Endpoints                                                   │
│   ├── POST /orders → Produce to Kafka (async)               │
│   ├── GET /orders/{id} → Query state (updated by consumer) │
│   └── WebSocket → Stream consumer events                   │
├─────────────────────────────────────────────────────────────┤
│ Background Consumer                                         │
│   └── asyncio.create_task(consume_loop)                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Lifespan Pattern

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
import asyncio

from .kafka import AIOProducer, AIOConsumer

# Global instances
producer: AIOProducer | None = None
consumer_task: asyncio.Task | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global producer, consumer_task

    # Startup
    producer = AIOProducer({
        'bootstrap.servers': 'kafka:9092',
        'acks': 'all',
        'enable.idempotence': True,
    })

    consumer = AIOConsumer({
        'bootstrap.servers': 'kafka:9092',
        'group.id': 'order-service',
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': False,
    }, topics=['order-events'])

    consumer_task = asyncio.create_task(
        consumer.consume(handle_event)
    )

    yield  # Application runs

    # Shutdown
    consumer.stop()
    if consumer_task:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
    await producer.flush()
    consumer.close()

app = FastAPI(lifespan=lifespan)
```

---

## AIOProducer Implementation

```python
from confluent_kafka import Producer
import asyncio
from typing import Optional

class AIOProducer:
    """Async-friendly Kafka producer."""

    def __init__(self, config: dict):
        self._producer = Producer(config)
        self._loop = asyncio.get_event_loop()
        self._poll_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start background polling."""
        self._poll_task = asyncio.create_task(self._poll_loop())

    async def _poll_loop(self):
        """Poll for callbacks without blocking event loop."""
        while True:
            self._producer.poll(0)
            await asyncio.sleep(0.01)

    async def produce(
        self,
        topic: str,
        value: bytes,
        key: Optional[str] = None,
        headers: Optional[list] = None
    ) -> dict:
        """Async produce with delivery confirmation."""
        future = self._loop.create_future()

        def delivery_callback(err, msg):
            if err:
                self._loop.call_soon_threadsafe(
                    future.set_exception,
                    Exception(f"Delivery failed: {err}")
                )
            else:
                self._loop.call_soon_threadsafe(
                    future.set_result,
                    {
                        'topic': msg.topic(),
                        'partition': msg.partition(),
                        'offset': msg.offset()
                    }
                )

        self._producer.produce(
            topic=topic,
            value=value,
            key=key.encode() if key else None,
            headers=headers,
            callback=delivery_callback
        )
        self._producer.poll(0)

        return await future

    async def flush(self, timeout: float = 10.0):
        """Async flush."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self._producer.flush,
            timeout
        )

    def close(self):
        """Clean shutdown."""
        if self._poll_task:
            self._poll_task.cancel()
        self._producer.flush()
```

---

## AIOConsumer Implementation

```python
from confluent_kafka import Consumer, KafkaError
import asyncio
from typing import Callable, Awaitable, Optional

class AIOConsumer:
    """Async-friendly Kafka consumer."""

    def __init__(self, config: dict, topics: list[str]):
        self._consumer = Consumer(config)
        self._consumer.subscribe(topics)
        self._running = False

    async def consume(
        self,
        handler: Callable[[bytes, dict], Awaitable[None]],
        poll_timeout: float = 1.0
    ):
        """Consume with async handler."""
        self._running = True
        loop = asyncio.get_event_loop()

        while self._running:
            # Run blocking poll in thread pool
            msg = await loop.run_in_executor(
                None,
                self._consumer.poll,
                poll_timeout
            )

            if msg is None:
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    logger.error(f"Consumer error: {msg.error()}")
                    continue

            try:
                # Parse headers
                headers = {
                    k: v.decode() if v else None
                    for k, v in (msg.headers() or [])
                }

                # Call async handler
                await handler(msg.value(), headers)

                # Commit after successful processing
                self._consumer.commit(asynchronous=False)

            except Exception as e:
                logger.error(f"Handler error: {e}")
                # Optionally: send to DLQ, skip, or raise

    def stop(self):
        """Signal consumer to stop."""
        self._running = False

    def close(self):
        """Clean shutdown."""
        self._consumer.close()
```

---

## Endpoint Integration

### Produce from Endpoint

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json

class OrderCreate(BaseModel):
    customer_id: str
    items: list[dict]
    total: float

@app.post("/orders")
async def create_order(order: OrderCreate):
    order_id = str(uuid4())

    event = {
        "order_id": order_id,
        "customer_id": order.customer_id,
        "items": order.items,
        "total": order.total,
        "status": "pending"
    }

    try:
        result = await producer.produce(
            topic="orders.order.created",
            key=order_id,
            value=json.dumps(event).encode()
        )
        return {
            "order_id": order_id,
            "status": "accepted",
            "kafka": result
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to queue order: {e}")
```

### Request-Response Pattern

```python
from asyncio import Future
import asyncio

# Pending responses (correlation_id -> future)
pending_responses: dict[str, Future] = {}

async def handle_response(value: bytes, headers: dict):
    """Handle response events."""
    correlation_id = headers.get('correlation_id')
    if correlation_id and correlation_id in pending_responses:
        pending_responses[correlation_id].set_result(
            json.loads(value)
        )

@app.post("/process")
async def process_request(data: dict):
    correlation_id = str(uuid4())

    # Create future for response
    future = asyncio.get_event_loop().create_future()
    pending_responses[correlation_id] = future

    # Send request
    await producer.produce(
        topic="requests",
        key=correlation_id,
        value=json.dumps(data).encode(),
        headers=[('correlation_id', correlation_id.encode())]
    )

    try:
        # Wait for response (with timeout)
        result = await asyncio.wait_for(future, timeout=30.0)
        return result
    except asyncio.TimeoutError:
        raise HTTPException(504, "Request timeout")
    finally:
        pending_responses.pop(correlation_id, None)
```

---

## Background Task Pattern

```python
from fastapi import BackgroundTasks

async def process_async(order_id: str, data: dict):
    """Background processing that produces events."""
    # Do heavy processing
    result = await heavy_computation(data)

    # Produce result event
    await producer.produce(
        topic="orders.order.processed",
        key=order_id,
        value=json.dumps(result).encode()
    )

@app.post("/orders/async")
async def create_order_async(
    order: OrderCreate,
    background_tasks: BackgroundTasks
):
    order_id = str(uuid4())

    # Queue for background processing
    background_tasks.add_task(
        process_async,
        order_id,
        order.model_dump()
    )

    return {"order_id": order_id, "status": "processing"}
```

---

## WebSocket Streaming

```python
from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

@app.websocket("/events/{topic}")
async def websocket_events(websocket: WebSocket, topic: str):
    await websocket.accept()

    # Create dedicated consumer for this connection
    consumer = Consumer({
        'bootstrap.servers': 'kafka:9092',
        'group.id': f'ws-{uuid4()}',  # Unique group
        'auto.offset.reset': 'latest',
    })
    consumer.subscribe([topic])

    try:
        while True:
            msg = await asyncio.get_event_loop().run_in_executor(
                None,
                consumer.poll,
                1.0
            )
            if msg and not msg.error():
                await websocket.send_json({
                    'topic': msg.topic(),
                    'partition': msg.partition(),
                    'offset': msg.offset(),
                    'value': json.loads(msg.value())
                })
    except WebSocketDisconnect:
        pass
    finally:
        consumer.close()
```

---

## Testing

### Mock Producer

```python
import pytest
from unittest.mock import AsyncMock

@pytest.fixture
def mock_producer(monkeypatch):
    mock = AsyncMock()
    mock.produce.return_value = {
        'topic': 'test',
        'partition': 0,
        'offset': 1
    }
    monkeypatch.setattr('app.main.producer', mock)
    return mock

@pytest.mark.asyncio
async def test_create_order(mock_producer, client):
    response = await client.post("/orders", json={
        "customer_id": "cust-1",
        "items": [{"id": "prod-1", "qty": 2}],
        "total": 99.99
    })

    assert response.status_code == 200
    assert mock_producer.produce.called
```

### Integration Test with Testcontainers

```python
import pytest
from testcontainers.kafka import KafkaContainer

@pytest.fixture(scope="module")
def kafka():
    with KafkaContainer() as kafka:
        yield kafka.get_bootstrap_server()

@pytest.fixture
async def producer(kafka):
    p = AIOProducer({'bootstrap.servers': kafka})
    yield p
    await p.flush()

@pytest.mark.asyncio
async def test_produce_consume(kafka, producer):
    # Produce
    result = await producer.produce(
        topic='test-topic',
        value=b'{"test": "data"}'
    )
    assert result['offset'] >= 0

    # Consume
    consumer = Consumer({
        'bootstrap.servers': kafka,
        'group.id': 'test-group',
        'auto.offset.reset': 'earliest'
    })
    consumer.subscribe(['test-topic'])

    msg = consumer.poll(timeout=10.0)
    assert msg is not None
    assert json.loads(msg.value()) == {"test": "data"}
```

---

## Error Handling

```python
from fastapi import HTTPException
from confluent_kafka import KafkaException

async def safe_produce(topic: str, key: str, value: bytes):
    """Produce with retry and error handling."""
    max_retries = 3

    for attempt in range(max_retries):
        try:
            return await producer.produce(topic, value, key)
        except BufferError:
            # Buffer full - wait and retry
            await asyncio.sleep(0.5 * (2 ** attempt))
        except KafkaException as e:
            if attempt == max_retries - 1:
                raise HTTPException(503, f"Kafka unavailable: {e}")
            await asyncio.sleep(1.0)

    raise HTTPException(503, "Failed to produce after retries")
```

---

## Configuration

```python
from pydantic_settings import BaseSettings

class KafkaSettings(BaseSettings):
    bootstrap_servers: str = "localhost:9092"
    producer_acks: str = "all"
    consumer_group: str = "my-service"
    consumer_auto_offset: str = "earliest"

    class Config:
        env_prefix = "KAFKA_"

settings = KafkaSettings()

producer_config = {
    'bootstrap.servers': settings.bootstrap_servers,
    'acks': settings.producer_acks,
    'enable.idempotence': True,
}

consumer_config = {
    'bootstrap.servers': settings.bootstrap_servers,
    'group.id': settings.consumer_group,
    'auto.offset.reset': settings.consumer_auto_offset,
    'enable.auto.commit': False,
}
```
