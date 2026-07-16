"""Unit tests for Option B dataset builder helpers (mocked yfinance/FinBERT)."""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from alphaguard.ml.dataset_asof import (
    feature_as_of_session,
    label_high_risk_from_fwd,
    published_at_from_calendar_date,
)
from alphaguard.ml.dataset_finbert import sentiment_from_probs
from alphaguard.ml.dataset_ingest import (
    event_id_for,
    load_filter_dedup_sample,
    normalize_headline,
    reject_oou_tickers,
)

ET = ZoneInfo("America/New_York")


def test_reject_oou() -> None:
    assert reject_oou_tickers(["AAPL", "TSLA", "MSFT"]) == ["TSLA"]


def test_dedup_and_normalize(tmp_path: Path) -> None:
    csv = tmp_path / "news.csv"
    csv.write_text(
        "date,stock,headline\n"
        "2024-03-12,AAPL,Apple rises\n"
        "2024-03-12,AAPL,  apple   rises \n"
        "2024-03-12,TSLA,Ignore me\n"
        "2024-03-13,MSFT,Microsoft news\n",
        encoding="utf-8",
    )
    df, stats = load_filter_dedup_sample(csv, target_rows=10, random_seed=42)
    assert stats.oou_dropped == 1
    assert stats.rows_after_dedup == 2
    assert set(df["ticker"]) <= {"AAPL", "MSFT"}
    assert normalize_headline("  Apple   rises ") == "apple rises"


def test_published_at_open_stamp() -> None:
    pub = published_at_from_calendar_date(date(2024, 3, 12))
    assert pub.tzinfo is not None
    local = pub.astimezone(ET)
    assert local.hour == 9 and local.minute == 30
    assert local.date() == date(2024, 3, 12)


def test_tuesday_morning_feature_as_of_is_prior_session() -> None:
    # Tuesday 2024-03-12 10:00 ET → open-stamp path uses 09:30; still prior close Mon.
    pub = datetime(2024, 3, 12, 14, 0, tzinfo=timezone.utc)  # 10:00 ET
    as_of = feature_as_of_session(pub)
    assert as_of < date(2024, 3, 12)
    assert as_of == date(2024, 3, 11)  # Monday


def test_label_rule() -> None:
    assert label_high_risk_from_fwd(-0.04) == 1
    assert label_high_risk_from_fwd(-0.03) == 0
    assert label_high_risk_from_fwd(0.01) == 0


def test_finbert_score_mapping() -> None:
    assert sentiment_from_probs(0.7, 0.2) == pytest.approx(0.5)


def test_empty_csv_fail_closed(tmp_path: Path) -> None:
    csv = tmp_path / "empty.csv"
    csv.write_text("date,stock,headline\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_filter_dedup_sample(csv, target_rows=10)


def test_event_id_stable() -> None:
    a = event_id_for("AAPL", date(2024, 3, 12), "apple rises")
    b = event_id_for("AAPL", date(2024, 3, 12), "apple rises")
    assert a == b
