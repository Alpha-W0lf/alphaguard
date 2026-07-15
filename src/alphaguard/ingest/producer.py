"""Kafka producer helpers for news.raw."""

from __future__ import annotations

import logging
from typing import Any

from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError

from alphaguard.contracts.events import NewsEvent
from alphaguard.ingest.codec import serialize_event

logger = logging.getLogger(__name__)

TOPIC_NEWS_RAW = "news.raw"
TOPIC_DLQ = "news.raw.dlq"


class KafkaProduceError(RuntimeError):
    """Raised when a record cannot be produced to Kafka."""


def probe_kafka(bootstrap_servers: str, *, timeout_ms: int = 2000) -> tuple[str, str]:
    """Bootstrap probe for /health — never hangs beyond consumer_timeout_ms."""
    consumer: KafkaConsumer | None = None
    try:
        consumer = KafkaConsumer(
            bootstrap_servers=bootstrap_servers,
            consumer_timeout_ms=timeout_ms,
        )
        # topics() forces metadata fetch; treat success as connected.
        # Do not rely solely on bootstrap_connected() — kafka-python can report
        # False after a successful metadata fetch on some brokers/clients.
        consumer.topics()
        return "ok", bootstrap_servers
    except KafkaError as exc:
        return "error", str(exc)
    except Exception as exc:  # noqa: BLE001 — health must not hang smoke
        return "error", str(exc)
    finally:
        if consumer is not None:
            consumer.close()


def create_producer(bootstrap_servers: str) -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        acks="all",
        retries=3,
        key_serializer=lambda k: k.encode("utf-8") if k else None,
        value_serializer=lambda v: v,
    )


def produce_event(
    producer: KafkaProducer,
    event: NewsEvent,
    *,
    topic: str = TOPIC_NEWS_RAW,
) -> dict[str, Any]:
    """Produce one NewsEvent; return pinned /trigger metadata fields."""
    future = producer.send(
        topic,
        key=event.event_id,
        value=serialize_event(event),
    )
    try:
        metadata = future.get(timeout=10)
    except KafkaError as exc:
        raise KafkaProduceError(str(exc)) from exc
    return {
        "ok": True,
        "topic": topic,
        "event_id": event.event_id,
        "partition": metadata.partition,
        "offset": metadata.offset,
    }


def produce_bytes(
    producer: KafkaProducer,
    *,
    topic: str,
    key: str | None,
    value: bytes,
) -> None:
    future = producer.send(topic, key=key, value=value)
    future.get(timeout=10)
    producer.flush()
