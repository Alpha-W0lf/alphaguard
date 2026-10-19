"""Unit tests for Option B dataset builder helpers (mocked yfinance/FinBERT)."""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import pytest

from alphaguard.ml.dataset_asof import (
    default_yfinance_closes,
    feature_as_of_session,
    label_high_risk_from_fwd,
    make_cached_close_fetcher,
    published_at_from_calendar_date,
)
from alphaguard.ml.dataset_build import build_training_events
from alphaguard.ml.dataset_finbert import sentiment_from_probs
from alphaguard.contracts.events import TICKER_UNIVERSE
from alphaguard.ml.dataset_ingest import (
    BUILDER_VERSION,
    event_id_for,
    load_filter_dedup_sample,
    normalize_headline,
    reject_oou_tickers,
    source_row_hash,
)
from alphaguard.ml.study_walkforward import (
    LOCKED_TEST_ASOF_ANCHOR_001856A6,
    SPLIT_POLICY_NESTED_V1_DATE_ANCHOR,
    apply_trading_day_embargo,
    expanding4_folds,
    horizon_overlap_count,
    resolve_locked_test_boundary,
    split_for_walk_forward,
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


def test_ingest_alias_on_fb_meta_and_goog_googl(tmp_path: Path) -> None:
    csv = tmp_path / "news.csv"
    csv.write_text(
        "date,stock,headline\n"
        "2020-03-01,AAPL,Apple news\n"
        "2020-03-02,FB,Facebook news\n"
        "2020-03-03,GOOG,Alphabet class C\n",
        encoding="utf-8",
    )
    df, stats = load_filter_dedup_sample(csv, target_rows=10, random_seed=42)
    assert stats.alias_rule_version == "fb_meta_v1+goog_googl_v1"
    assert stats.alias_applied_counts.get("FB→META") == 1
    assert stats.alias_applied_counts.get("GOOG→GOOGL") == 1
    assert stats.alias_candidates_oou == {}
    assert set(df["ticker"]) == {"AAPL", "META", "GOOGL"}
    assert "FB" not in set(df["ticker"])
    assert "GOOG" not in set(df["ticker"])
    assert "META" not in stats.universe_tickers_absent
    assert BUILDER_VERSION == "0.1.1"
    assert all(df["builder_version"] == "0.1.1")
    fb_row = df.loc[df["ticker"] == "META"].iloc[0]
    assert fb_row["source_row_hash"] == source_row_hash(
        "2020-03-02", "FB", "Facebook news"
    )
    assert fb_row["event_id"] == event_id_for(
        "META", date(2020, 3, 2), normalize_headline("Facebook news")
    )


def test_ingest_alias_off_honesty(tmp_path: Path) -> None:
    csv = tmp_path / "news.csv"
    csv.write_text(
        "date,stock,headline\n"
        "2020-03-01,AAPL,Apple news\n"
        "2020-03-02,FB,Facebook news\n"
        "2020-03-03,GOOG,Alphabet class C\n",
        encoding="utf-8",
    )
    df, stats = load_filter_dedup_sample(
        csv, target_rows=10, random_seed=42, apply_archive_aliases=False
    )
    assert stats.rows_universe == 1
    assert set(df["ticker"]) == {"AAPL"}
    assert "META" in stats.universe_tickers_absent
    assert stats.alias_rule_version == "off"
    assert stats.alias_applied_counts == {}
    assert stats.alias_candidates_oou.get("FB") == 1
    assert stats.alias_candidates_oou.get("GOOG") == 1


def test_price_fetcher_rejects_fb_and_goog() -> None:
    with pytest.raises(ValueError, match="fb_meta_v1"):
        default_yfinance_closes("FB", date(2020, 1, 1), date(2020, 6, 1))
    with pytest.raises(ValueError, match="goog_googl_v1"):
        default_yfinance_closes("GOOG", date(2020, 1, 1), date(2020, 6, 1))
    closer = make_cached_close_fetcher()
    with pytest.raises(ValueError, match="fb_meta_v1"):
        closer("FB", date(2020, 1, 1), date(2020, 2, 1))
    with pytest.raises(ValueError, match="goog_googl_v1"):
        closer("GOOG", date(2020, 1, 1), date(2020, 2, 1))


def test_build_alias_on_never_fetches_archive_sources(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    csv = raw / "analyst_ratings_processed.csv"
    csv.write_text(
        "date,stock,headline\n"
        "2020-03-02 10:00:00,FB,Facebook news\n"
        "2020-03-03 10:00:00,AAPL,Apple news\n"
        "2020-03-04 10:00:00,GOOG,Alphabet class C\n",
        encoding="utf-8",
    )
    fetched: list[str] = []
    sessions = pd.bdate_range("2019-12-02", "2020-04-30").date.tolist()

    def fetch(ticker: str, start: date, end: date) -> pd.Series:
        fetched.append(ticker)
        assert ticker not in {"FB", "GOOG"}
        idx = [d for d in sessions if start <= d <= end]
        base = 200.0 if ticker == "SPY" else 100.0
        return pd.Series({d: base + i * 0.01 for i, d in enumerate(idx)})

    out = tmp_path / "dev_nofinbert.parquet"
    df = build_training_events(
        raw_dir=raw,
        out_path=out,
        target_rows=10,
        random_seed=42,
        allow_shortfall=True,
        skip_download=True,
        skip_finbert=True,
        fetch_closes=fetch,
    )
    assert "FB" not in fetched
    assert "GOOG" not in fetched
    assert "META" in set(df["ticker"])
    assert "GOOGL" in set(df["ticker"])
    assert set(df["ticker"]).isdisjoint({"FB", "GOOG"})


def test_build_empty_meta_series_fail_closed(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    csv = raw / "analyst_ratings_processed.csv"
    csv.write_text(
        "date,stock,headline\n"
        "2020-03-02 10:00:00,FB,Facebook only\n",
        encoding="utf-8",
    )

    def fetch_empty(ticker: str, start: date, end: date) -> pd.Series:
        assert ticker != "FB"
        return pd.Series(dtype=float)

    out = tmp_path / "dev_nofinbert.parquet"
    with pytest.raises(RuntimeError, match="fb_meta_v1|META"):
        build_training_events(
            raw_dir=raw,
            out_path=out,
            target_rows=10,
            random_seed=42,
            allow_shortfall=True,
            skip_download=True,
            skip_finbert=True,
            fetch_closes=fetch_empty,
        )


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


def test_training_universe_none_matches_explicit_served(tmp_path: Path) -> None:
    """Default training_universe=None is byte-identical to explicit TICKER_UNIVERSE."""
    csv = tmp_path / "news.csv"
    csv.write_text(
        "date,stock,headline\n"
        "2020-03-01,AAPL,Apple news\n"
        "2020-03-02,NVDA,Nvidia news\n"
        "2020-03-03,TSLA,Tesla oou\n"
        "2020-03-04,MSFT,Microsoft news\n",
        encoding="utf-8",
    )
    df_default, stats_default = load_filter_dedup_sample(csv, target_rows=10, random_seed=42)
    df_explicit, stats_explicit = load_filter_dedup_sample(
        csv, target_rows=10, random_seed=42, training_universe=TICKER_UNIVERSE
    )
    assert list(df_default["event_id"]) == list(df_explicit["event_id"])
    assert list(df_default["ticker"]) == list(df_explicit["ticker"])
    assert list(df_default["source_row_hash"]) == list(df_explicit["source_row_hash"])
    assert stats_default.rows_universe == stats_explicit.rows_universe
    assert stats_default.oou_dropped == stats_explicit.oou_dropped == 1
    assert set(df_default["ticker"]).isdisjoint({"TSLA"})


def test_training_universe_expand_keeps_aliases(tmp_path: Path) -> None:
    csv = tmp_path / "news.csv"
    csv.write_text(
        "date,stock,headline\n"
        "2020-03-01,FB,Facebook news\n"
        "2020-03-02,GOOG,Alphabet class C\n"
        "2020-03-03,MU,Micron news\n"
        "2020-03-04,TSLA,Still oou for this universe\n",
        encoding="utf-8",
    )
    universe = frozenset({"META", "GOOGL", "MU"})
    df, stats = load_filter_dedup_sample(
        csv, target_rows=10, random_seed=42, training_universe=universe
    )
    assert stats.alias_applied_counts.get("FB→META") == 1
    assert stats.alias_applied_counts.get("GOOG→GOOGL") == 1
    assert set(df["ticker"]) == {"META", "GOOGL", "MU"}
    assert "TSLA" not in set(df["ticker"])
    assert "FB" not in set(df["ticker"])
    assert "GOOG" not in set(df["ticker"])


def test_build_writes_served_universe_column(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    csv = raw / "analyst_ratings_processed.csv"
    csv.write_text(
        "date,stock,headline\n"
        "2020-03-02 10:00:00,AAPL,Apple news\n"
        "2020-03-03 10:00:00,MU,Micron news\n",
        encoding="utf-8",
    )
    sessions = pd.bdate_range("2019-12-02", "2020-04-30").date.tolist()

    def fetch(ticker: str, start: date, end: date) -> pd.Series:
        assert ticker not in {"FB", "GOOG"}
        idx = [d for d in sessions if start <= d <= end]
        base = 200.0 if ticker == "SPY" else 100.0
        return pd.Series({d: base + i * 0.01 for i, d in enumerate(idx)})

    out = tmp_path / "dev_nofinbert.parquet"
    df = build_training_events(
        raw_dir=raw,
        out_path=out,
        target_rows=10,
        random_seed=42,
        allow_shortfall=True,
        skip_download=True,
        skip_finbert=True,
        fetch_closes=fetch,
        training_universe=frozenset({"AAPL", "MU"}),
    )
    assert "served_universe" in df.columns
    assert bool(df.loc[df["ticker"] == "AAPL", "served_universe"].iloc[0]) is True
    assert bool(df.loc[df["ticker"] == "MU", "served_universe"].iloc[0]) is False


def test_date_anchor_excludes_asof_ge_anchor_from_train() -> None:
    n = 40
    asof_dates = [date(2020, 2, 20) + __import__("datetime").timedelta(days=i) for i in range(n)]
    # Ensure some rows land on/after the locked anchor.
    asof_dates = [
        date(2020, 2, 20) if i < 20 else date(2020, 2, 25) if i < 25 else date(2020, 2, 26)
        for i in range(n)
    ]
    df = pd.DataFrame(
        {
            "label_high_risk": [0, 1] * (n // 2),
            "published_at": pd.date_range("2020-01-01", periods=n, tz="UTC"),
            "feature_as_of": asof_dates,
            **{name: np.zeros(n) for name in (
                "finbert_sentiment",
                "volatility_20d",
                "return_5d_prior",
                "return_20d_prior",
                "spy_return_5d",
                "rs_20d",
                "drawdown_20d",
                "volatility_5d",
                "spy_volatility_20d",
            )},
        }
    )
    from alphaguard.contracts.decisions import FEATURE_NAMES as _FN

    for name in _FN:
        if name not in df.columns:
            df[name] = 0.0
    boundary = resolve_locked_test_boundary(
        df, train_frac=0.8, split_policy=SPLIT_POLICY_NESTED_V1_DATE_ANCHOR
    )
    assert boundary == 20
    split = split_for_walk_forward(
        df, 0.8, "off", split_policy=SPLIT_POLICY_NESTED_V1_DATE_ANCHOR
    )
    train_asof = df.iloc[: len(split.y_train)]["feature_as_of"]
    assert (train_asof >= LOCKED_TEST_ASOF_ANCHOR_001856A6).sum() == 0
    test_asof = df.iloc[boundary:]["feature_as_of"]
    assert (test_asof >= LOCKED_TEST_ASOF_ANCHOR_001856A6).all()


def test_purge_holds_across_tickers_same_session() -> None:
    """Trading-day purge uses shared session indices across tickers."""
    n = 60
    # Two tickers interleaved on the same session calendar.
    feature = np.array([i // 2 for i in range(n)], dtype=int)
    label_end = feature + 5
    folds, _n_dev, _source = expanding4_folds(n, embargo_rows=5)
    # Force label windows from late train to overlap early val sessions.
    fold = folds[0]
    label_end = label_end.copy()
    label_end[fold.val_start - 10 : fold.val_start] = feature[fold.val_start]
    before = horizon_overlap_count(
        label_end, feature, fold.train_end, fold.val_start, fold.val_end
    )
    assert before > 0
    purged, changed = apply_trading_day_embargo(folds, label_end, feature)
    assert changed
    after = horizon_overlap_count(
        label_end, feature, purged[0].train_end, purged[0].val_start, purged[0].val_end
    )
    assert after == 0
