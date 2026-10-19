"""Replay ingest — load fixtures and call PipelineService (no Kafka)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import ValidationError

from alphaguard.contracts.events import TICKER_UNIVERSE, NewsEvent

if TYPE_CHECKING:
    from alphaguard.contracts.envelope import PipelineRunEnvelope
    from alphaguard.pipeline.service import PipelineService


class FixtureLoadError(RuntimeError):
    pass


def load_replay_events(path: Path) -> list[NewsEvent]:
    if not path.exists():
        raise FixtureLoadError(f"fixture file missing: {path}")
    events: list[NewsEvent] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise FixtureLoadError(f"invalid JSON at {path}:{line_no}: {exc}") from exc
        ticker = str(raw.get("ticker", "")).strip().upper()
        if ticker and ticker not in TICKER_UNIVERSE:
            raise FixtureLoadError(
                f"OOU ticker rejected in {path}:{line_no}: ticker {ticker!r} "
                f"not in universe {sorted(TICKER_UNIVERSE)} (ARCHITECTURE §7.1 — no silent remap)"
            )
        try:
            events.append(NewsEvent.model_validate(raw))
        except ValidationError as exc:
            raise FixtureLoadError(f"invalid fixture at {path}:{line_no}: {exc}") from exc
    if not events:
        raise FixtureLoadError(f"fixture file empty: {path}")
    return events


def get_event_by_id(path: Path, event_id: str) -> NewsEvent:
    for event in load_replay_events(path):
        if event.event_id == event_id:
            return event
    raise FixtureLoadError(f"unknown event_id={event_id!r} in {path}")


def run_replay(
    service: "PipelineService",
    fixtures_path: Path,
    event_id: str | None = None,
) -> "PipelineRunEnvelope":
    if event_id:
        event = get_event_by_id(fixtures_path, event_id)
    else:
        event = load_replay_events(fixtures_path)[0]
    return service.run(event)
