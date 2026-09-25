"""Option B pre-registered feature unit tests (JH-63 Option B)."""

from __future__ import annotations

from datetime import date, datetime, timezone

import numpy as np
import pandas as pd

from alphaguard.ml.dataset_asof import (
    _drawdown_window,
    _vol_20d,
    _vol_window,
    compute_features_and_label,
)


def _synthetic_sessions(n: int = 40, start: date = date(2020, 1, 2)) -> list[date]:
    """Weekday-only session list long enough for 20d windows."""
    out: list[date] = []
    d = start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d = date.fromordinal(d.toordinal() + 1)
    return out


def _closes_from_levels(sessions: list[date], levels: list[float]) -> pd.Series:
    assert len(sessions) == len(levels)
    return pd.Series(levels, index=sessions, dtype=float)


def test_vol_20d_wrapper_matches_vol_window() -> None:
    sessions = _synthetic_sessions(30)
    # Geometric random walk with fixed seed for determinism
    rng = np.random.default_rng(0)
    rets = rng.normal(0.001, 0.01, size=len(sessions) - 1)
    levels = [100.0]
    for r in rets:
        levels.append(levels[-1] * (1.0 + r))
    series = _closes_from_levels(sessions, levels)
    as_of = sessions[25]
    a = _vol_20d(series, as_of, sessions)
    b = _vol_window(series, as_of, sessions, 20)
    assert a is not None and b is not None
    assert a == b


def test_vol_window_hand_computed_5d() -> None:
    sessions = _synthetic_sessions(10)
    # 6 closes ending at sessions[5] → 5 daily returns
    levels = [100.0, 101.0, 99.0, 102.0, 100.0, 103.0, 104.0, 105.0, 106.0, 107.0]
    series = _closes_from_levels(sessions, levels)
    as_of = sessions[5]
    window = levels[0:6]
    rets = np.diff(window) / np.array(window[:-1])
    expected = float(np.std(rets, ddof=1) * np.sqrt(252))
    got = _vol_window(series, as_of, sessions, 5)
    assert got is not None
    assert got == expected


def test_drawdown_20d_hand_computed() -> None:
    sessions = _synthetic_sessions(25)
    levels = [100.0 + i for i in range(21)]  # rising → drawdown 0 at end
    levels[10] = 150.0  # peak mid-window
    # pad to 25
    while len(levels) < 25:
        levels.append(levels[-1] + 1.0)
    series = _closes_from_levels(sessions, levels)
    as_of = sessions[20]
    window = levels[0:21]
    expected = float(window[-1] / max(window) - 1.0)
    got = _drawdown_window(series, as_of, sessions, 20)
    assert got is not None
    assert got == expected
    assert expected < 0.0


def test_rs_20d_and_new_features_via_compute() -> None:
    """Drive compute_features_and_label with a fake calendar + close fetcher."""

    class FakeCal:
        def __init__(self, sessions: list[date]) -> None:
            idx = pd.DatetimeIndex([pd.Timestamp(d) for d in sessions])
            closes = pd.Series(
                [pd.Timestamp(d).tz_localize("America/New_York").replace(hour=16) for d in sessions],
                index=idx,
            )
            self.schedule = pd.DataFrame({"close": closes}, index=idx)

    sessions = _synthetic_sessions(80, start=date(2019, 6, 3))
    cal = FakeCal(sessions)

    # Build ticker and SPY closes covering the whole session list
    ticker_levels = [100.0]
    spy_levels = [200.0]
    for i in range(1, len(sessions)):
        ticker_levels.append(ticker_levels[-1] * (1.0 + (0.002 if i % 3 else -0.003)))
        spy_levels.append(spy_levels[-1] * (1.0 + (0.001 if i % 2 else -0.001)))
    ticker_s = _closes_from_levels(sessions, ticker_levels)
    spy_s = _closes_from_levels(sessions, spy_levels)

    def fetch(ticker: str, start: date, end: date) -> pd.Series:
        src = spy_s if ticker == "SPY" else ticker_s
        idx = [d for d in src.index if start <= d <= end]
        return src.loc[idx]

    # Pick a mid-list as_of: published just after that session's close
    as_of = sessions[40]
    published = datetime(
        as_of.year, as_of.month, as_of.day, 21, 0, tzinfo=timezone.utc
    )  # after US close
    out = compute_features_and_label(
        ticker="AAPL",
        published_at=published,
        fetch_closes=fetch,
        calendar=cal,
    )
    assert out is not None
    # Hand-check rs_20d
    prior20 = sessions[sessions.index(as_of) - 20]
    r20 = ticker_s.loc[as_of] / ticker_s.loc[prior20] - 1.0
    s20 = spy_s.loc[as_of] / spy_s.loc[prior20] - 1.0
    assert out["rs_20d"] == float(r20 - s20)
    assert "drawdown_20d" in out
    assert "volatility_5d" in out
    assert "spy_volatility_20d" in out
    # Existing five keys still present
    for k in (
        "volatility_20d",
        "return_5d_prior",
        "return_20d_prior",
        "spy_return_5d",
        "fwd_return_5d",
        "label_high_risk",
    ):
        assert k in out


def test_no_lookahead_perturb_future_close() -> None:
    class FakeCal:
        def __init__(self, sessions: list[date]) -> None:
            idx = pd.DatetimeIndex([pd.Timestamp(d) for d in sessions])
            closes = pd.Series(
                [pd.Timestamp(d).tz_localize("America/New_York").replace(hour=16) for d in sessions],
                index=idx,
            )
            self.schedule = pd.DataFrame({"close": closes}, index=idx)

    sessions = _synthetic_sessions(80, start=date(2019, 6, 3))
    cal = FakeCal(sessions)
    ticker_levels = [100.0 + 0.1 * i for i in range(len(sessions))]
    spy_levels = [200.0 + 0.05 * i for i in range(len(sessions))]
    ticker_s = _closes_from_levels(sessions, ticker_levels)
    spy_s = _closes_from_levels(sessions, spy_levels)

    def make_fetch(t_s: pd.Series, s_s: pd.Series):
        def fetch(ticker: str, start: date, end: date) -> pd.Series:
            src = s_s if ticker == "SPY" else t_s
            idx = [d for d in src.index if start <= d <= end]
            return src.loc[idx]

        return fetch

    as_of = sessions[40]
    published = datetime(as_of.year, as_of.month, as_of.day, 21, 0, tzinfo=timezone.utc)
    base = compute_features_and_label(
        ticker="AAPL",
        published_at=published,
        fetch_closes=make_fetch(ticker_s, spy_s),
        calendar=cal,
    )
    assert base is not None
    # Perturb every close strictly after feature_as_of (including label window)
    t2 = ticker_s.copy()
    for d in sessions:
        if d > as_of:
            t2.loc[d] = float(t2.loc[d]) * 1.5
    s2 = spy_s.copy()
    for d in sessions:
        if d > as_of:
            s2.loc[d] = float(s2.loc[d]) * 1.5
    # Recompute — feature columns must be unchanged; label may change
    alt = compute_features_and_label(
        ticker="AAPL",
        published_at=published,
        fetch_closes=make_fetch(t2, s2),
        calendar=cal,
    )
    assert alt is not None
    for k in (
        "volatility_20d",
        "return_5d_prior",
        "return_20d_prior",
        "spy_return_5d",
        "rs_20d",
        "drawdown_20d",
        "volatility_5d",
        "spy_volatility_20d",
    ):
        assert base[k] == alt[k], k


def test_incomplete_window_returns_none() -> None:
    sessions = _synthetic_sessions(10)
    # Only 3 closes present → 20d and 5d windows incomplete
    series = pd.Series([100.0, 101.0, 102.0], index=sessions[:3], dtype=float)
    assert _vol_window(series, sessions[2], sessions, 5) is None
    assert _vol_20d(series, sessions[2], sessions) is None
    assert _drawdown_window(series, sessions[2], sessions, 20) is None
