"""Kafka integration tests — require Compose (Guide 04 D3)."""

from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError

from alphaguard.config import Settings
from alphaguard.ingest.codec import serialize_event
from alphaguard.ingest.consumer import NewsRawConsumer, TOPIC_DLQ
from alphaguard.ingest.producer import (
    TOPIC_NEWS_RAW,
    create_producer,
    probe_kafka,
    produce_bytes,
    produce_event,
)
from alphaguard.pipeline.service import PipelineService
from alphaguard.rag.service import event_point_id

pytestmark = pytest.mark.kafka_integration


def _kafka_tests_enabled() -> bool:
    if os.environ.get("ALPHAGUARD_RUN_KAFKA_TESTS") == "1":
        return True
    settings = Settings()
    status, _ = probe_kafka(settings.kafka_bootstrap_servers)
    return status == "ok"


def _ensure_topics(bootstrap: str) -> None:
    """Create news.raw + DLQ if missing (auto-create races are flaky under kafka-python)."""
    admin = KafkaAdminClient(bootstrap_servers=bootstrap, request_timeout_ms=10000)
    try:
        existing = set(admin.list_topics())
        needed = [
            NewTopic(name, num_partitions=1, replication_factor=1)
            for name in (TOPIC_NEWS_RAW, TOPIC_DLQ)
            if name not in existing
        ]
        if not needed:
            return
        try:
            admin.create_topics(needed, validate_only=False)
        except TopicAlreadyExistsError:
            pass
        # Allow metadata to propagate
        deadline = time.time() + 10
        while time.time() < deadline:
            have = set(admin.list_topics())
            if TOPIC_NEWS_RAW in have and TOPIC_DLQ in have:
                return
            time.sleep(0.25)
        raise RuntimeError(f"topics not visible after create: {admin.list_topics()}")
    finally:
        admin.close()


@pytest.fixture
def kafka_settings() -> Settings:
    return Settings(
        alphaguard_mode="live",
        alphaguard_rag_mode="qdrant",
        kafka_bootstrap_servers=os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        qdrant_url=os.environ.get("QDRANT_URL", "http://localhost:6333"),
        qdrant_collection=f"alphaguard_test_{uuid.uuid4().hex[:8]}",
    )


@pytest.fixture
def skip_without_kafka(kafka_settings: Settings) -> None:
    if not _kafka_tests_enabled():
        pytest.skip("Kafka not reachable; start docker compose or set ALPHAGUARD_RUN_KAFKA_TESTS=1")
    _ensure_topics(kafka_settings.kafka_bootstrap_servers)


def _happy_event(event_id: str | None = None):
    from alphaguard.contracts.events import NewsEvent

    return NewsEvent(
        event_id=event_id or f"evt-test-{uuid.uuid4().hex[:8]}",
        headline="Integration test headline",
        ticker="AAPL",
        source="fixture",
        published_at=datetime(2024, 3, 12, 14, 30, tzinfo=timezone.utc),
    )


def _new_consumer(settings: Settings, service: PipelineService) -> NewsRawConsumer:
    """Isolated group + latest offset so tests do not replay topic backlog."""
    return NewsRawConsumer(
        settings,
        service,
        group_id=f"alphaguard-itest-{uuid.uuid4().hex[:8]}",
        consumer_timeout_ms=8000,
        auto_offset_reset="latest",
    )


def _warmup_assignment(consumer: NewsRawConsumer) -> None:
    """Join group / assign partitions before producing (latest → empty poll)."""
    consumer.run_once()


@pytest.mark.usefixtures("skip_without_kafka")
def test_happy_produce_consume_upsert(kafka_settings: Settings) -> None:
    from qdrant_client import QdrantClient

    event = _happy_event()
    service = PipelineService(kafka_settings, skip_ollama_preflight=True)
    consumer = _new_consumer(kafka_settings, service)
    try:
        _warmup_assignment(consumer)
        producer = create_producer(kafka_settings.kafka_bootstrap_servers)
        try:
            produce_event(producer, event)
        finally:
            producer.close()

        found = False
        for _ in range(15):
            consumer.run_once()
            client = QdrantClient(url=kafka_settings.qdrant_url, timeout=5.0)
            try:
                points = client.retrieve(
                    collection_name=kafka_settings.qdrant_collection,
                    ids=[event_point_id(event.event_id)],
                    with_payload=True,
                )
            except Exception:  # noqa: BLE001 — collection may not exist until first upsert
                points = []
            if points:
                found = True
                break
        assert found, "expected Qdrant point after consume"
    finally:
        consumer.close()


@pytest.mark.usefixtures("skip_without_kafka")
def test_redelivery_idempotent(kafka_settings: Settings) -> None:
    event = _happy_event()
    service = PipelineService(kafka_settings, skip_ollama_preflight=True)
    consumer = _new_consumer(kafka_settings, service)

    message = SimpleNamespace(
        topic=TOPIC_NEWS_RAW,
        partition=0,
        offset=42,
        key=event.event_id.encode(),
        value=serialize_event(event),
    )
    try:
        assert consumer.process_message(message) is True
        assert consumer.process_message(message) is True
    finally:
        consumer.close()


@pytest.mark.usefixtures("skip_without_kafka")
def test_poison_dlq_after_attempts_live(kafka_settings: Settings) -> None:
    """Guide D3: poison → MAX_ATTEMPTS → DLQ + commit via real broker + seek loop."""
    from kafka import KafkaConsumer

    from alphaguard.ingest.consumer import MAX_ATTEMPTS

    poison_id = f"poison-live-{uuid.uuid4().hex[:8]}"
    poison_value = json.dumps(
        {
            "payload_version": "2",  # frozen codec poison
            "event_id": poison_id,
            "headline": "x",
            "ticker": "AAPL",
            "source": "fixture",
            "published_at": "2024-03-12T14:30:00+00:00",
        }
    ).encode()

    service = PipelineService(kafka_settings, skip_ollama_preflight=True)
    consumer = _new_consumer(kafka_settings, service)
    try:
        _warmup_assignment(consumer)
        producer = create_producer(kafka_settings.kafka_bootstrap_servers)
        try:
            produce_bytes(producer, topic=TOPIC_NEWS_RAW, key=poison_id, value=poison_value)
        finally:
            producer.close()

        committed = 0
        for _ in range(MAX_ATTEMPTS + 3):
            committed += consumer.run_once()
            if committed >= 1:
                break
        assert committed >= 1, "expected poison offset committed after DLQ"
    finally:
        consumer.close()

    # Verify DLQ after producer/consumer closed (avoids metadata cancellation races).
    time.sleep(0.5)
    dlq = KafkaConsumer(
        TOPIC_DLQ,
        bootstrap_servers=kafka_settings.kafka_bootstrap_servers,
        group_id=f"alphaguard-dlq-verify-{uuid.uuid4().hex[:8]}",
        enable_auto_commit=False,
        auto_offset_reset="earliest",
        consumer_timeout_ms=10000,
    )
    try:
        keys = {
            (msg.key.decode("utf-8") if msg.key else None) for msg in dlq
        }
    finally:
        dlq.close()
    assert poison_id in keys, f"expected poison key on {TOPIC_DLQ}"
