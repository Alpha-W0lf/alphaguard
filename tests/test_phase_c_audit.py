"""Phase C label/data audit. Injected defects fail the check; the fix clears them."""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from alphaguard.contracts.decisions import FEATURE_NAMES
from alphaguard.ml.audit_label import label_mismatch_rows
from alphaguard.ml.audit_leakage import asof_violations, construction_duplicate_count
from alphaguard.ml.audit_prevalence import classify_slice
from alphaguard.ml.audit_report import gate_summary, render_gates_markdown, run_phase_c_audit
from alphaguard.ml.train_option_b import dataset_hash, load_training_frame
from alphaguard.ml.audit_rules_align import audit_rules_alignment
from alphaguard.ml.dataset_asof import (
    _return_between,
    _session_list,
    _xnys_calendar,
    compute_features_and_label,
    default_yfinance_closes,
    feature_as_of_session,
    label_high_risk_from_fwd,
    session_offset,
)
from alphaguard.ml.study_schema import ModelHyperparams, RunConfig
from alphaguard.ml.study_walkforward import (
    apply_trading_day_embargo,
    evaluate_expanding4,
    expanding4_folds,
    horizon_overlap_count,
    split_for_walk_forward,
)

_GO_ASSIGN = re.compile(
    r"""(?i)(promotion_decision|decision)\s*=\s*['\"](?:go|model quality go)['\"]"""
)


def test_threshold_edges_are_exact() -> None:
    assert label_high_risk_from_fwd(-0.0299) == 0
    assert label_high_risk_from_fwd(-0.0301) == 1
    assert label_high_risk_from_fwd(-0.03) == 0


def test_synthetic_closes_hit_the_same_edges() -> None:
    """Closes are a fraction. 100→97.01 is above -3 percent; 100→96.99 is below.

    100→97.00 is one float ulp under -0.03, so the strict rule labels it 1.
    The exact literal -0.03 stays 0 (see ``test_threshold_edges_are_exact``).
    """
    start = date(2024, 3, 15)
    end = date(2024, 3, 22)

    def fwd(end_px: float) -> float:
        series = pd.Series([100.0, end_px], index=[start, end])
        return _return_between(series, start, end)

    above = fwd(97.01)
    below = fwd(96.99)
    assert abs(above - (-0.0299)) < 1e-6
    assert abs(below - (-0.0301)) < 1e-6
    assert label_high_risk_from_fwd(above) == 0
    assert label_high_risk_from_fwd(below) == 1
    assert label_high_risk_from_fwd(fwd(97.0)) == 1


def test_horizon_skips_weekend_and_holiday() -> None:
    sessions = _session_list(_xnys_calendar())
    assert session_offset(sessions, date(2024, 3, 15), 5) == date(2024, 3, 22)
    # 2024-07-04 is a Thursday holiday. The window steps to 2024-07-05.
    window_end = session_offset(sessions, date(2024, 7, 3), 5)
    assert window_end == date(2024, 7, 11)
    start_i = sessions.index(date(2024, 7, 3))
    assert date(2024, 7, 4) not in sessions[start_i : sessions.index(window_end)]


def test_missing_close_is_unlabeled_and_prices_are_auto_adjusted(monkeypatch) -> None:
    series = pd.Series({date(2024, 3, 15): 100.0})
    assert _return_between(series, date(2024, 3, 15), date(2024, 3, 22)) is None
    pub = datetime(2024, 3, 15, 15, 0, tzinfo=timezone.utc)

    def empty_fetch(ticker: str, start: date, end: date) -> pd.Series:
        return pd.Series(dtype=float)

    assert compute_features_and_label(ticker="AAPL", published_at=pub, fetch_closes=empty_fetch) is None
    captured: dict = {}

    def fake_download(*_args, **kwargs):
        captured.update(kwargs)
        idx = pd.to_datetime(["2024-03-15"])
        return pd.DataFrame({"Close": [100.0]}, index=idx)

    import yfinance as yf

    monkeypatch.setattr(yf, "download", fake_download)
    default_yfinance_closes("AAPL", date(2024, 3, 1), date(2024, 3, 20))
    assert captured["auto_adjust"] is True


def test_label_recompute_lists_every_mismatch() -> None:
    df = pd.DataFrame({"fwd_return_5d": [-0.04, -0.03, -0.02], "label_high_risk": [1, 1, 0]})
    assert label_mismatch_rows(df) == [1]
    df.loc[1, "label_high_risk"] = 0
    assert label_mismatch_rows(df) == []


def test_duplicate_headline_is_detected_then_cleared() -> None:
    pub = datetime(2020, 1, 2, 15, 0, tzinfo=timezone.utc)
    rows = pd.DataFrame(
        {
            "ticker": ["NVDA", "NVDA"],
            "published_at": [pub, pub],
            "headline": ["Nvidia rises", "  nvidia   rises "],
        }
    )
    assert construction_duplicate_count(rows) == 1
    assert construction_duplicate_count(rows.iloc[:1]) == 0


def test_future_news_is_detected_then_cleared() -> None:
    pub = datetime(2024, 3, 12, 15, 0, tzinfo=timezone.utc)
    feature_day = feature_as_of_session(pub)
    frame = pd.DataFrame(
        {
            "ticker": ["AAPL"],
            "published_at": [pub],
            "feature_as_of": [feature_day],
            "headline": ["Apple headline"],
            "news_available_at": [pub + timedelta(days=1)],
        }
    )
    found = asof_violations(frame)
    assert len(found) == 1
    assert "news_available_after_published" in found[0]["reasons"]
    frame["news_available_at"] = frame["published_at"]
    assert asof_violations(frame) == []


def test_row_embargo_overlaps_and_trading_day_purge_clears_it() -> None:
    folds, _n_dev, _source = expanding4_folds(80, embargo_rows=5)
    feature = np.arange(80, dtype=int)
    label_end = np.arange(80, dtype=int)
    fold = folds[0]
    label_end[fold.val_start - 8 : fold.val_start] = fold.val_start
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
    assert purged[0].val_start - purged[0].train_end > 5


def test_locked_test_split_drops_straddling_train_rows() -> None:
    n = 50
    boundary = int(n * 0.8)
    feature = np.arange(n, dtype=int)
    label_end = np.arange(n, dtype=int)
    label_end[boundary - 6 : boundary] = boundary
    df = pd.DataFrame(
        {
            "label_high_risk": [0, 1] * (n // 2),
            "published_at": pd.date_range("2020-01-01", periods=n, tz="UTC"),
            "_feature_session_idx": feature,
            "_label_end_session_idx": label_end,
            **{name: np.zeros(n) for name in FEATURE_NAMES},
        }
    )
    plain = split_for_walk_forward(df.drop(columns=["_feature_session_idx", "_label_end_session_idx"]), 0.8, "off")
    purged = split_for_walk_forward(df, 0.8, "expanding4")
    assert len(plain.y_train) == boundary
    assert len(purged.y_train) == boundary - 6
    assert len(purged.y_test) == n - boundary
    nested = split_for_walk_forward(df, 0.8, "off")  # frame WITH session columns
    assert len(nested.y_train) == boundary - 6
    assert len(nested.y_test) == n - boundary


def _both_class_frame(n: int = 180) -> pd.DataFrame:
    rng = np.random.default_rng(0)
    x = rng.normal(size=(n, len(FEATURE_NAMES)))
    y = (x[:, 0] > 0).astype(int)
    y[:20] = [0, 1] * 10
    data = {name: x[:, i] for i, name in enumerate(FEATURE_NAMES)}
    data["label_high_risk"] = y
    data["published_at"] = pd.date_range("2020-01-01", periods=n, tz="UTC")
    return pd.DataFrame(data)


def test_evaluate_expanding4_uses_trading_day_gap_when_sessions_exist() -> None:
    df = _both_class_frame()
    folds, _n_dev, _source = expanding4_folds(len(df), embargo_rows=5)
    feature = np.arange(len(df), dtype=int)
    label_end = feature.copy()
    for fold in folds:
        label_end[fold.val_start - 8 : fold.val_start] = fold.val_start
    df["_feature_session_idx"] = feature
    df["_label_end_session_idx"] = label_end
    config = RunConfig(
        study_id="phasec_audit",
        run_id="purge",
        seed=0,
        dataset_path="unused",
        dataset_hash="unused",
        model_params=ModelHyperparams(max_depth=2, eta=0.1, num_boost_round=2),
    )
    block, _scores = evaluate_expanding4(df, config, n_dev=int(len(df) * 0.8))
    assert block.embargo_source == "trading_day_horizon"
    for fold in block.folds:
        assert fold.val_start - fold.train_end > 5


def test_one_ticker_fold_is_artifact_and_spread_drawdown_is_regime() -> None:
    day = date(2020, 3, 16)
    artifact = pd.DataFrame(
        {
            "ticker": ["NVDA"] * 8,
            "feature_as_of": [day] * 8,
            "label_high_risk": [1] * 8,
            "published_at": pd.date_range("2020-03-16", periods=8, tz="UTC"),
            "headline": [f"headline {i}" for i in range(8)],
        }
    )
    market = pd.Series({day: -0.04})
    assert classify_slice(artifact, market_fwd_by_date=market)["verdict"] == "artifact"

    days = [date(2020, 3, d) for d in range(2, 7)]
    regime = pd.DataFrame(
        {
            "ticker": ["NVDA"] * 5 + ["QQQ"] * 5,
            "feature_as_of": days + days,
            "label_high_risk": [1] * 10,
            "published_at": pd.date_range("2020-03-02", periods=10, tz="UTC"),
            "headline": [f"h{i}" for i in range(10)],
        }
    )
    market = pd.Series({item: -0.02 for item in days})
    row = classify_slice(regime, market_fwd_by_date=market)
    assert row["verdict"] == "regime"
    assert "spread_and_market_drawdown" in row["reasons"]


def test_rules_alignment_needs_three_of_four_folds() -> None:
    n = 100
    folds, n_dev, _source = expanding4_folds(n, embargo_rows=5)
    y = np.zeros(n, dtype=int)
    prior = np.zeros(n, dtype=float)
    # Folds 2 and 3: veto set is the positive class. Folds 0 and 1: the opposite.
    higher_folds = {folds[2].val_start, folds[3].val_start}
    for fold in folds:
        sl = slice(fold.val_start, fold.val_end)
        width = fold.val_end - fold.val_start
        half = width // 2
        prior[sl][:half] = -0.05
        if fold.val_start in higher_folds:
            y[sl][:half] = 1
        else:
            y[sl][half:] = 1
    df = pd.DataFrame(
        {
            "label_high_risk": y,
            "return_5d_prior": prior,
            "published_at": pd.date_range("2020-01-01", periods=n, tz="UTC"),
        }
    )
    misaligned = audit_rules_alignment(df, folds, n_dev)
    assert misaligned["verdict"] == "misaligned"
    assert misaligned["folds_veto_higher"] == 2

    for fold in folds:
        sl = slice(fold.val_start, fold.val_end)
        width = fold.val_end - fold.val_start
        half = width // 2
        y[sl] = 0
        y[sl][:half] = 1
        prior[sl][:half] = -0.05
        prior[sl][half:] = 0.0
    df["label_high_risk"] = y
    df["return_5d_prior"] = prior
    aligned = audit_rules_alignment(df, folds, n_dev)
    assert aligned["verdict"] == "aligned"
    assert aligned["folds_veto_higher"] == 4


def test_gate_summary_and_report_do_not_claim_go() -> None:
    c1 = {"mismatch_count": 0}
    c2 = {"any_artifact": True}
    c3 = {
        "asof_violation_count": 0,
        "construction_duplicates": 0,
        "row_embargo_overlap_rows": 4,
        "row_embargo_short_boundaries": 1,
        "purged_overlap_rows": 0,
    }
    c4 = {"verdict": "misaligned", "folds_veto_higher": 2, "fold_count": 4, "slices": []}
    gates = gate_summary(c1, c2, c3, c4)
    assert gates["a_fired"] and gates["b_fired"] and gates["c_fired"] and gates["c5_fired"]
    assert gates["model_quality_go"] == "UNCLAIMED"
    text = render_gates_markdown({"gates": gates, "c2": {"slices": []}, "c4": c4})
    assert "UNCLAIMED" in text
    assert _GO_ASSIGN.search(text) is None


# Historical 5-feature freeze columns (pre Option B). Kept for backup hash checks.
_LEGACY_534A_FEATURE_NAMES = (
    "finbert_sentiment",
    "volatility_20d",
    "return_5d_prior",
    "return_20d_prior",
    "spy_return_5d",
)


@pytest.mark.skipif(
    not Path("data/derived/training_events_jh633_534a341a.parquet").exists(),
    reason="534a backup parquet is local and gitignored",
)
def test_local_freeze_534a341a_backup_gate_verdicts() -> None:
    """Historical Fail record: 534a backup still audits clean under legacy 5 features."""
    import pandas as pd

    path = Path("data/derived/training_events_jh633_534a341a.parquet")
    df = pd.read_parquet(path)
    digest = dataset_hash(
        df[list(_LEGACY_534A_FEATURE_NAMES)].to_numpy(dtype=float),
        df["label_high_risk"].to_numpy(dtype=int),
    )
    assert digest.startswith("534a341a")
    report = run_phase_c_audit(df)
    assert report["c1"]["mismatch_count"] == 0
    assert report["c3"]["asof_violation_count"] == 0
    assert report["c3"]["construction_duplicates"] == 0
    assert report["c3"]["purged_overlap_rows"] == 0
    assert report["c3"]["row_embargo_overlap_rows"] > 0
    fold1 = next(row for row in report["c2"]["slices"] if row["name"] == "fold_1")
    assert fold1["verdict"] == "regime"
    assert report["c4"]["verdict"] == "misaligned"
    gates = report["gates"]
    assert gates["a_fired"] and gates["b_fired"] and gates["c_fired"] and gates["c5_fired"]
    assert gates["model_quality_go"] == "UNCLAIMED"


@pytest.mark.skipif(
    not Path("data/derived/training_events.parquet").exists(),
    reason="freeze parquet is local and gitignored",
)
def test_local_freeze_current_has_option_b_features() -> None:
    """After Option B rebuild, live parquet must expose all FEATURE_NAMES."""
    path = Path("data/derived/training_events.parquet")
    try:
        df = load_training_frame(path)
    except Exception as exc:  # noqa: BLE001
        # Pre-rebuild (still 5-col) is expected during WP-B1; skip until WP-B2.
        if "missing columns" in str(exc):
            import pytest as _pytest

            _pytest.skip(f"live freeze not yet rebuilt for Option B: {exc}")
        raise
    for name in FEATURE_NAMES:
        assert name in df.columns
    digest = dataset_hash(
        df[list(FEATURE_NAMES)].to_numpy(dtype=float),
        df["label_high_risk"].to_numpy(dtype=int),
    )
    assert not digest.startswith("534a341a")
    assert len(df) == 8907


def test_clean_gate_does_not_fire_c5() -> None:
    c1 = {"mismatch_count": 0}
    c2 = {"any_artifact": False}
    c3 = {
        "asof_violation_count": 0,
        "construction_duplicates": 0,
        "row_embargo_overlap_rows": 0,
        "row_embargo_short_boundaries": 0,
        "purged_overlap_rows": 0,
    }
    c4 = {"verdict": "aligned"}
    gates = gate_summary(c1, c2, c3, c4)
    assert gates["c5_fired"] is False
