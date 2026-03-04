"""
Kafka Producer/Consumer Template for FastAPI

Usage:
    1. Copy relevant classes to your project
    2. Configure with your settings
    3. Use with FastAPI lifespan
"""

import asyncio
import json
import logging
from typing import Any, Callable, Awaitable, Optional
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4

from confluent_kafka import Producer, Consumer, KafkaError

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class KafkaConfig:
    """Kafka connection configuration."""
    bootstrap_servers: str = "kafka:9092"
    security_protocol: str = "PLAINTEXT"  # PLAINTEXT, SASL_SSL, SSL
    sasl_mechanism: Optional[str] = None  # SCRAM-SHA-512
    sasl_username: Optional[str] = None
    sasl_password: Optional[str] = None
    ssl_ca_location: Optional[str] = None
    ssl_certificate_location: Optional[str] = None
    ssl_key_location: Optional[str] = None

    def to_dict(self) -> dict:
        config = {"bootstrap.servers": self.bootstrap_servers}

        if self.security_protocol != "PLAINTEXT":
            config["security.protocol"] = self.security_protocol

        if self.sasl_mechanism:
            config["sasl.mechanism"] = self.sasl_mechanism
            config["sasl.username"] = self.sasl_username
            config["sasl.password"] = self.sasl_password

        if self.ssl_ca_location:
            config["ssl.ca.location"] = self.ssl_ca_location
        if self.ssl_certificate_location:
            config["ssl.certificate.location"] = self.ssl_certificate_location
        if self.ssl_key_location:
            config["ssl.key.location"] = self.ssl_key_location

        return config


# =============================================================================
# CloudEvents Envelope
# =============================================================================

@dataclass
class CloudEvent:
    """CloudEvents 1.0 envelope."""
    type: str
    source: str
    data: Any

    id: str = field(default_factory=lambda: str(uuid4()))
    specversion: str = "1.0"
    time: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    subject: Optional[str] = None
    datacontenttype: str = "application/json"

    def to_headers(self) -> list[tuple[str, bytes]]:
        headers = [
            ("ce_specversion", self.specversion.encode()),
            ("ce_id", self.id.encode()),
            ("ce_source", self.source.encode()),
            ("ce_type", self.type.encode()),
            ("ce_time", self.time.encode()),
            ("ce_datacontenttype", self.datacontenttype.encode()),
        ]
        if self.subject:
            headers.append(("ce_subject", self.subject.encode()))
        return headers

    def to_value(self) -> bytes:
        return json.dumps(self.data).encode()


# =============================================================================
# Async Producer
# =============================================================================

class AIOProducer:
    """Async Kafka producer for FastAPI."""

    def __init__(self, config: KafkaConfig):
        producer_config = config.to_dict()
        producer_config.update({
            "acks": "all",
            "enable.idempotence": True,
            "retries": 2147483647,
            "delivery.timeout.ms": 120000,
        })
        self._producer = Producer(producer_config)
        self._loop = asyncio.get_event_loop()

    async def produce(
        self,
        topic: str,
        value: bytes,
        key: Optional[str] = None,
        headers: Optional[list] = None,
    ) -> dict:
        """Produce message with async delivery confirmation."""
        future = self._loop.create_future()

        def callback(err, msg):
            if err:
                self._loop.call_soon_threadsafe(
                    future.set_exception,
                    Exception(f"Delivery failed: {err}")
                )
            else:
                self._loop.call_soon_threadsafe(
                    future.set_result,
                    {
                        "topic": msg.topic(),
                        "partition": msg.partition(),
                        "offset": msg.offset(),
                    }
                )

        self._producer.produce(
            topic=topic,
            value=value,
            key=key.encode() if key else None,
            headers=headers,
            callback=callback,
        )
        self._producer.poll(0)

        return await future

    async def produce_event(self, topic: str, event: CloudEvent) -> dict:
        """Produce CloudEvents-formatted message."""
        return await self.produce(
            topic=topic,
            value=event.to_value(),
            key=event.subject,
            headers=event.to_headers(),
        )

    async def flush(self, timeout: float = 10.0):
        """Async-friendly flush."""
        while True:
            remaining = self._producer.flush(timeout=0.1)
            if remaining == 0:
                break
            await asyncio.sleep(0.01)

    def close(self):
        self._producer.flush()


# =============================================================================
# Async Consumer
# =============================================================================

class AIOConsumer:
    """Async Kafka consumer for FastAPI."""

    def __init__(
        self,
        config: KafkaConfig,
        group_id: str,
        topics: list[str],
    ):
        consumer_config = config.to_dict()
        consumer_config.update({
            "group.id": group_id,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
            "session.timeout.ms": 45000,
            "max.poll.interval.ms": 300000,
            "partition.assignment.strategy": "cooperative-sticky",
        })
        self._consumer = Consumer(consumer_config)
        self._consumer.subscribe(topics)
        self._running = False

    async def consume(
        self,
        handler: Callable[[dict, dict], Awaitable[None]],
        poll_timeout: float = 1.0,
    ):
        """Consume messages with async handler."""
        self._running = True
        loop = asyncio.get_event_loop()

        while self._running:
            msg = await loop.run_in_executor(
                None,
                self._consumer.poll,
                poll_timeout,
            )

            if msg is None:
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                logger.error(f"Consumer error: {msg.error()}")
                continue

            try:
                # Parse headers
                headers = {
                    k: v.decode() if v else None
                    for k, v in (msg.headers() or [])
                }

                # Parse value
                value = json.loads(msg.value().decode())

                # Call handler
                await handler(value, headers)

                # Commit after success
                self._consumer.commit(asynchronous=False)

            except Exception as e:
                logger.exception(f"Handler error: {e}")
                # TODO: Send to DLQ

    def stop(self):
        self._running = False

    def close(self):
        self._consumer.close()


# =============================================================================
# FastAPI Integration Example
# =============================================================================

"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
import asyncio

producer: AIOProducer | None = None
consumer_task: asyncio.Task | None = None

async def handle_event(value: dict, headers: dict):
    print(f"Received: {value}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    global producer, consumer_task

    config = KafkaConfig(bootstrap_servers="kafka:9092")

    producer = AIOProducer(config)

    consumer = AIOConsumer(
        config=config,
        group_id="my-service",
        topics=["events"],
    )
    consumer_task = asyncio.create_task(consumer.consume(handle_event))

    yield

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

@app.post("/events")
async def create_event(data: dict):
    event = CloudEvent(
        type="my.event.created",
        source="my-service",
        subject=data.get("id"),
        data=data,
    )
    result = await producer.produce_event("events", event)
    return {"status": "accepted", "kafka": result}
"""
