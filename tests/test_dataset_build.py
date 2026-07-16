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


def test_stratified_sample_unique_event_ids(tmp_path: Path) -> None:
    rows = []
    for i in range(40):
        for ticker in ("AAPL", "MSFT", "NVDA", "GOOGL"):
            rows.append(f"2024-03-{(i % 20) + 1:02d},{ticker},Headline {ticker} {i}\n")
    csv = tmp_path / "news.csv"
    csv.write_text("date,stock,headline\n" + "".join(rows), encoding="utf-8")
    df, _stats = load_filter_dedup_sample(csv, target_rows=100, random_seed=42)
    assert len(df) == 100
    assert df["event_id"].nunique() == 100


def test_compute_features_and_label_bounds() -> None:
    from alphaguard.ml.dataset_asof import compute_features_and_label

    sessions = pd.bdate_range("2024-01-02", "2024-03-22").date.tolist()
    prices = {d: 100.0 + i for i, d in enumerate(sessions)}

    class FakeCal:
        def __init__(self) -> None:
            idx = pd.DatetimeIndex([pd.Timestamp(d) for d in sessions])
            closes = [
                pd.Timestamp(d, tz="America/New_York") + pd.Timedelta(hours=16)
                for d in sessions
            ]
            self.schedule = pd.DataFrame({"close": closes}, index=idx)

    def fetch(ticker: str, start: date, end: date) -> pd.Series:
        idx = [d for d in sessions if start <= d <= end]
        base = 200.0 if ticker == "SPY" else 100.0
        data = {d: base + (prices[d] - 100.0) for d in idx}
        return pd.Series(data)

    # Tuesday 2024-03-12 10:00 ET = 14:00 UTC — features must use Mon 03-11
    pub = datetime(2024, 3, 12, 14, 0, tzinfo=timezone.utc)
    out = compute_features_and_label(
        ticker="AAPL",
        published_at=pub,
        fetch_closes=fetch,
        calendar=FakeCal(),
    )
    assert out is not None
    assert out["feature_as_of"] == date(2024, 3, 11)
    assert out["label_high_risk"] in (0, 1)
    assert isinstance(out["fwd_return_5d"], float)


def test_title_column_alias(tmp_path: Path) -> None:
    csv = tmp_path / "analyst_ratings_processed.csv"
    csv.write_text(
        "title,date,stock\n"
        "Apple rises,2020-06-05 17:00:00,AAPL\n",
        encoding="utf-8",
    )
    df, _ = load_filter_dedup_sample(csv, target_rows=10)
    assert len(df) == 1
    assert df.iloc[0]["published_at_parsed"] is not None
    # 17:00 ET should not collapse to 09:30
    pub = df.iloc[0]["published_at_parsed"]
    assert pub.astimezone(ZoneInfo("America/New_York")).hour == 17
