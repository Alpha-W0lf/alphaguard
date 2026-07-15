"""Kafka consumer for news.raw — durable handle via PipelineService.ingest_event."""

from __future__ import annotations

import logging
from typing import Any

from kafka import KafkaConsumer, KafkaProducer, TopicPartition
from kafka.errors import KafkaError
from kafka.structs import OffsetAndMetadata

from alphaguard.config import Settings
from alphaguard.ingest.codec import CodecError, deserialize_bytes
from alphaguard.ingest.producer import TOPIC_DLQ, TOPIC_NEWS_RAW, create_producer, produce_bytes
from alphaguard.pipeline.service import PipelineService

logger = logging.getLogger(__name__)

CONSUMER_GROUP = "alphaguard-news-raw"
# Failed durable-handle attempts before DLQ (DLQ on Nth failure). Soft pin: 3.
MAX_ATTEMPTS = 3
MAX_RETRIES = MAX_ATTEMPTS  # alias — name means attempts, not "retries after first"


class NewsRawConsumer:
    def __init__(
        self,
        settings: Settings,
        pipeline: PipelineService,
        *,
        bootstrap_servers: str | None = None,
        group_id: str | None = None,
        consumer_timeout_ms: int = 1000,
        auto_offset_reset: str = "earliest",
    ) -> None:
        self.settings = settings
        self.pipeline = pipeline
        self.bootstrap_servers = bootstrap_servers or settings.kafka_bootstrap_servers
        self.group_id = group_id or CONSUMER_GROUP
        self.consumer_timeout_ms = consumer_timeout_ms
        self.auto_offset_reset = auto_offset_reset
        self._failure_counts: dict[tuple[str, int, int], int] = {}
        self._consumer: KafkaConsumer | None = None
        self._producer: KafkaProducer | None = None

    def _get_consumer(self) -> KafkaConsumer:
        if self._consumer is None:
            self._consumer = KafkaConsumer(
                TOPIC_NEWS_RAW,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                enable_auto_commit=False,
                auto_offset_reset=self.auto_offset_reset,
                consumer_timeout_ms=self.consumer_timeout_ms,
            )
        return self._consumer

    def _get_producer(self) -> KafkaProducer:
        if self._producer is None:
            self._producer = create_producer(self.bootstrap_servers)
        return self._producer

    def close(self) -> None:
        if self._consumer is not None:
            self._consumer.close()
            self._consumer = None
        if self._producer is not None:
            self._producer.close()
            self._producer = None

    def _failure_key(self, message: Any) -> tuple[str, int, int]:
        return (message.topic, message.partition, message.offset)

    def _record_failure(self, message: Any) -> int:
        key = self._failure_key(message)
        count = self._failure_counts.get(key, 0) + 1
        self._failure_counts[key] = count
        return count

    def _clear_failure(self, message: Any) -> None:
        self._failure_counts.pop(self._failure_key(message), None)

    def _send_to_dlq(self, message: Any, *, reason: str) -> None:
        key = message.key.decode("utf-8") if message.key else None
        produce_bytes(
            self._get_producer(),
            topic=TOPIC_DLQ,
            key=key,
            value=message.value,
        )
        logger.warning(
            "dlq_sent topic=%s partition=%s offset=%s reason=%s",
            message.topic,
            message.partition,
            message.offset,
            reason,
        )

    def _topic_partition(self, message: Any) -> TopicPartition:
        return TopicPartition(message.topic, message.partition)

    def _commit_message(self, consumer: Any, message: Any) -> None:
        """Commit only the handled offset (next offset = message.offset + 1)."""
        tp = self._topic_partition(message)
        consumer.commit({tp: OffsetAndMetadata(message.offset + 1, "")})

    def _seek_for_retry(self, consumer: Any, message: Any) -> None:
        """Rewind fetch position so the same record is retried; do not commit."""
        tp = self._topic_partition(message)
        consumer.seek(tp, message.offset)
        logger.warning(
            "seek_retry topic=%s partition=%s offset=%s",
            message.topic,
            message.partition,
            message.offset,
        )

    def process_message(self, message: Any) -> bool:
        """Process one record. Returns True when offset may be committed."""
        try:
            event = deserialize_bytes(message.value)
            self.pipeline.ingest_event(event)
            self._clear_failure(message)
            return True
        except (CodecError, Exception) as exc:  # noqa: BLE001 — bounded retry + DLQ
            attempts = self._record_failure(message)
            logger.warning(
                "ingest_failed topic=%s partition=%s offset=%s attempts=%s error=%s",
                message.topic,
                message.partition,
                message.offset,
                attempts,
                exc,
            )
            if attempts < MAX_ATTEMPTS:
                return False
            try:
                self._send_to_dlq(message, reason=str(exc))
            except KafkaError as dlq_exc:
                logger.error("dlq_produce_failed: %s", dlq_exc)
                return False
            self._clear_failure(message)
            return True

    def run_once(self) -> int:
        """Poll and process available records; returns count committed.

        On durable-handle failure: seek back to the failed offset and stop this
        poll batch so a later success cannot commit past an unhandled record.
        """
        consumer = self._get_consumer()
        processed = 0
        for message in consumer:
            if self.process_message(message):
                self._commit_message(consumer, message)
                processed += 1
            else:
                self._seek_for_retry(consumer, message)
                break
        return processed

    def run_forever(self) -> None:
        logger.info(
            "consumer_start topic=%s group=%s bootstrap=%s",
            TOPIC_NEWS_RAW,
            CONSUMER_GROUP,
            self.bootstrap_servers,
        )
        try:
            while True:
                self.run_once()
        except KeyboardInterrupt:
            logger.info("consumer_stopped")
        finally:
            self.close()
