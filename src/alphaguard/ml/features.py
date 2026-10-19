"""Fixture feature rows for smoke (FinBERT precomputed — never load FinBERT here)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from alphaguard.contracts.decisions import FEATURE_NAMES
from alphaguard.contracts.events import NewsEvent


@dataclass(frozen=True)
class FeatureRow:
    event_id: str
    ticker: str
    values: dict[str, float]
    feature_as_of: date

    def ordered_vector(self, feature_names: list[str]) -> list[float]:
        missing = [n for n in feature_names if n not in self.values]
        if missing:
            raise KeyError(f"feature row missing columns: {missing}")
        return [float(self.values[n]) for n in feature_names]


def load_feature_row(event: NewsEvent, path: Path) -> FeatureRow:
    if not path.exists():
        raise FileNotFoundError(f"feature fixture missing: {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    row = raw.get(event.event_id)
    if row is None:
        raise KeyError(f"no feature row for event_id={event.event_id}")
    as_of_raw = row["feature_as_of"]
    if isinstance(as_of_raw, str):
        feature_as_of = date.fromisoformat(as_of_raw)
    else:
        feature_as_of = as_of_raw
    values = {name: float(row[name]) for name in FEATURE_NAMES}
    return FeatureRow(
        event_id=event.event_id,
        ticker=event.ticker,
        values=values,
        feature_as_of=feature_as_of,
    )


def parse_iso_date(value: str | date | datetime) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    return date.fromisoformat(value)
