"""Resource mode and ingest_event unit tests (always on)."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

from alphaguard.config import Settings
from alphaguard.contracts.events import NewsEvent
from alphaguard.pipeline.service import PipelineService


def test_resource_mode_kafka_integration() -> None:
    settings = Settings(alphaguard_mode="live", alphaguard_rag_mode="qdrant")
    assert settings.resource_mode == "kafka_integration"


def test_resource_mode_replay_fixture() -> None:
    settings = Settings(alphaguard_mode="replay", alphaguard_rag_mode="fixture")
    assert settings.resource_mode == "replay_fixture"


def test_ingest_event_calls_rag_upsert() -> None:
    settings = Settings(alphaguard_mode="live", alphaguard_rag_mode="qdrant")
    rag = MagicMock()
    service = PipelineService(settings=settings, rag=rag, skip_ollama_preflight=True)
    event = NewsEvent(
        event_id="evt-aapl-001",
        headline="Apple rises",
        ticker="AAPL",
        source="fixture",
        published_at=datetime(2024, 3, 12, 14, 30, tzinfo=timezone.utc),
    )
    service.ingest_event(event)
    rag.upsert_event.assert_called_once_with(event)


def _poison_bytes(event_id: str = "poison-1") -> bytes:
    import json

    return json.dumps(
        {
            "payload_version": "1",
            "event_id": event_id,
            "headline": "x",
            "ticker": "AAPL",
            "source": "fixture",
            "published_at": "2024-03-12T14:30:00+00:00",
        }
    ).encode()


def _msg(*, offset: int, key: bytes, value: bytes, partition: int = 0) -> SimpleNamespace:
    from alphaguard.ingest.producer import TOPIC_NEWS_RAW

    return SimpleNamespace(
        topic=TOPIC_NEWS_RAW,
        partition=partition,
        offset=offset,
        key=key,
        value=value,
    )


class _FakeKafkaConsumer:
    """Iterator that advances like kafka-python; seek rewinds; commit records."""

    def __init__(self, messages: list[SimpleNamespace]) -> None:
        self._messages = list(messages)
        self._pos = 0
        self.commits: list[dict] = []
        self.seeks: list[tuple] = []

    def __iter__(self) -> _FakeKafkaConsumer:
        return self

    def __next__(self) -> SimpleNamespace:
        if self._pos >= len(self._messages):
            raise StopIteration
        message = self._messages[self._pos]
        self._pos += 1
        return message

    def seek(self, tp: object, offset: int) -> None:
        self.seeks.append((tp, offset))
        for index, message in enumerate(self._messages):
            if message.partition == tp.partition and message.offset == offset:  # type: ignore[attr-defined]
                self._pos = index
                return
        raise ValueError(f"seek miss partition={tp} offset={offset}")

    def commit(self, offsets: dict | None = None) -> None:
        self.commits.append(offsets or {})


def test_poison_dlq_after_retries() -> None:
    """Poison commit policy — DLQ after MAX_ATTEMPTS without live Kafka."""
    from alphaguard.ingest.consumer import MAX_ATTEMPTS, NewsRawConsumer, TOPIC_DLQ

    settings = Settings(alphaguard_mode="live", alphaguard_rag_mode="qdrant")
    pipeline = MagicMock()
    pipeline.ingest_event.side_effect = ValueError("bad event")
    consumer = NewsRawConsumer(settings, pipeline)

    message = _msg(offset=99, key=b"poison-1", value=_poison_bytes())

    mock_producer = MagicMock()
    mock_future = MagicMock()
    mock_producer.send.return_value = mock_future
    consumer._producer = mock_producer  # noqa: SLF001 — test seam

    assert consumer.process_message(message) is False
    assert consumer.process_message(message) is False
    assert consumer.process_message(message) is True
    assert MAX_ATTEMPTS == 3
    assert consumer._failure_counts.get(("news.raw", 0, 99)) is None  # noqa: SLF001
    mock_producer.send.assert_called_once()
    assert mock_producer.send.call_args[0][0] == TOPIC_DLQ


def test_run_once_seeks_and_does_not_commit_past_failure() -> None:
    """Failing offset must seek+break; later success in same batch must not commit past it."""
    from kafka import TopicPartition
    from kafka.structs import OffsetAndMetadata

    from alphaguard.ingest.consumer import NewsRawConsumer, TOPIC_DLQ
    from alphaguard.ingest.producer import TOPIC_NEWS_RAW

    settings = Settings(alphaguard_mode="live", alphaguard_rag_mode="qdrant")
    pipeline = MagicMock()
    pipeline.ingest_event.side_effect = ValueError("bad event")
    consumer = NewsRawConsumer(settings, pipeline)

    poison = _msg(offset=10, key=b"poison-1", value=_poison_bytes("poison-1"))
    good = _msg(
        offset=11,
        key=b"good-1",
        value=_poison_bytes("good-1"),  # valid JSON; pipeline mock controls success
    )
    fake = _FakeKafkaConsumer([poison, good])
    consumer._consumer = fake  # noqa: SLF001
    mock_producer = MagicMock()
    mock_producer.send.return_value = MagicMock()
    consumer._producer = mock_producer  # noqa: SLF001

    # Attempt 1–2: fail → seek → break (no commit); good message never reached
    assert consumer.run_once() == 0
    assert consumer.run_once() == 0
    assert fake.commits == []
    assert len(fake.seeks) == 2
    assert fake.seeks[-1][1] == 10

    # Attempt 3: DLQ → commit only offset 10 (+1)
    assert consumer.run_once() == 1
    assert mock_producer.send.call_args[0][0] == TOPIC_DLQ
    assert len(fake.commits) == 1
    tp = TopicPartition(TOPIC_NEWS_RAW, 0)
    assert fake.commits[0] == {tp: OffsetAndMetadata(11, "")}

    # Now succeed on the following record
    pipeline.ingest_event.side_effect = None
    assert consumer.run_once() == 1
    assert fake.commits[-1] == {tp: OffsetAndMetadata(12, "")}


def test_run_once_retries_same_offset_until_success() -> None:
    """Transient failure: seek rewinds; later success commits that offset only."""
    from kafka import TopicPartition
    from kafka.structs import OffsetAndMetadata

    from alphaguard.ingest.consumer import NewsRawConsumer
    from alphaguard.ingest.producer import TOPIC_NEWS_RAW

    settings = Settings(alphaguard_mode="live", alphaguard_rag_mode="qdrant")
    pipeline = MagicMock()
    pipeline.ingest_event.side_effect = [ValueError("transient"), None]
    consumer = NewsRawConsumer(settings, pipeline)

    message = _msg(offset=42, key=b"evt-1", value=_poison_bytes("evt-1"))
    fake = _FakeKafkaConsumer([message])
    consumer._consumer = fake  # noqa: SLF001

    assert consumer.run_once() == 0
    assert fake.commits == []
    assert fake.seeks[-1][1] == 42

    assert consumer.run_once() == 1
    tp = TopicPartition(TOPIC_NEWS_RAW, 0)
    assert fake.commits == [{tp: OffsetAndMetadata(43, "")}]
