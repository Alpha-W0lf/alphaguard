"""Kafka wire codec for versioned flat NewsEvent payloads."""

from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

from alphaguard.contracts.events import NewsEvent

PAYLOAD_VERSION = "1"


class CodecError(ValueError):
    """Raised when wire payload cannot be decoded into a NewsEvent."""


def serialize_event(event: NewsEvent, *, payload_version: str = PAYLOAD_VERSION) -> bytes:
    payload: dict[str, Any] = {
        "payload_version": payload_version,
        "event_id": event.event_id,
        "headline": event.headline,
        "ticker": event.ticker,
        "source": event.source,
        "published_at": event.published_at.isoformat(),
    }
    if event.url is not None:
        payload["url"] = event.url
    return json.dumps(payload, separators=(",", ":")).encode("utf-8")


def deserialize_payload(data: dict[str, Any]) -> NewsEvent:
    version = data.get("payload_version")
    if version != PAYLOAD_VERSION:
        raise CodecError(f"unknown payload_version: {version!r}")
    fields = {k: v for k, v in data.items() if k != "payload_version"}
    try:
        return NewsEvent.model_validate(fields)
    except ValidationError as exc:
        raise CodecError(str(exc)) from exc


def deserialize_bytes(raw: bytes) -> NewsEvent:
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CodecError(f"invalid JSON payload: {exc}") from exc
    if not isinstance(data, dict):
        raise CodecError("payload must be a JSON object")
    return deserialize_payload(data)
