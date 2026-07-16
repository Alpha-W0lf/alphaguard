"""NYSE as-of features + forward downside labels for Option B rows."""

from __future__ import annotations

from datetime import date, datetime, time, timezone
from typing import Any, Callable
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

ET = ZoneInfo("America/New_York")
LABEL_THRESHOLD = -0.03


def published_at_from_calendar_date(calendar_date: date) -> datetime:
    """Date-only headlines → 09:30 America/New_York → UTC (ARCHITECTURE §8 / soft pin)."""
    local = datetime.combine(calendar_date, time(9, 30), tzinfo=ET)
    return local.astimezone(timezone.utc)


def _xnys_calendar() -> Any:
    import exchange_calendars as xcals

    return xcals.get_calendar("XNYS")


def feature_as_of_session(published_at: datetime, calendar: Any | None = None) -> date:
    """Last fully completed NYSE regular session at or before published_at."""
    cal = calendar or _xnys_calendar()
    if published_at.tzinfo is None:
        raise ValueError("published_at must be timezone-aware UTC")
    pub = published_at.astimezone(timezone.utc)
    # Sessions whose close is <= published_at are completed for feature use.
    # exchange_calendars: schedule indexed by session date; market_close is tz-aware.
    schedule = cal.schedule
    closes = schedule["close"]
    eligible = closes[closes <= pub]
    if eligible.empty:
        raise ValueError(f"no completed NYSE session at/before {pub.isoformat()}")
    session_ts = eligible.index[-1]
    return session_ts.date() if hasattr(session_ts, "date") else pd.Timestamp(session_ts).date()


def label_start_session(published_at: datetime, calendar: Any | None = None) -> date:
    """First completed session close at or after the event's calendar session."""
    cal = calendar or _xnys_calendar()
    pub = published_at.astimezone(timezone.utc)
    schedule = cal.schedule
    closes = schedule["close"]
    eligible = closes[closes >= pub]
    # Also include session that contains published_at if close is still after (same day open stamp).
    if eligible.empty:
        # If published during a session, first completed close at/after event is that session's close.
        eligible = closes[closes >= pub]
    if eligible.empty:
        raise ValueError(f"no label-start session at/after {pub.isoformat()}")
    session_ts = eligible.index[0]
    return session_ts.date() if hasattr(session_ts, "date") else pd.Timestamp(session_ts).date()


def _session_list(calendar: Any) -> list[date]:
    idx = calendar.schedule.index
    return [pd.Timestamp(ts).date() for ts in idx]


def session_offset(sessions: list[date], start: date, n: int) -> date | None:
    try:
        i = sessions.index(start)
    except ValueError:
        return None
    j = i + n
    if j < 0 or j >= len(sessions):
        return None
    return sessions[j]


CloseFetcher = Callable[[str, date, date], pd.Series]


def default_yfinance_closes(ticker: str, start: date, end: date) -> pd.Series:
    import yfinance as yf

    # yfinance end is exclusive-ish; pad one day.
    hist = yf.download(
        ticker,
        start=start.isoformat(),
        end=(pd.Timestamp(end) + pd.Timedelta(days=7)).date().isoformat(),
        auto_adjust=True,
        progress=False,
    )
    if hist is None or hist.empty:
        return pd.Series(dtype=float)
    closes = hist["Close"]
    if isinstance(closes, pd.DataFrame):
        closes = closes.iloc[:, 0]
    closes.index = pd.to_datetime(closes.index).tz_localize(None).date
    return closes.astype(float)


def make_cached_close_fetcher(
    *,
    history_start: date = date(2008, 1, 1),
    history_end: date = date(2021, 6, 1),
) -> CloseFetcher:
    """Download each ticker once over the archive window (e2e performance)."""
    cache: dict[str, pd.Series] = {}

    def fetch(ticker: str, start: date, end: date) -> pd.Series:
        if ticker not in cache:
            print(f"yfinance cache miss: downloading {ticker} …")
            cache[ticker] = default_yfinance_closes(ticker, history_start, history_end)
        series = cache[ticker]
        if series.empty:
            return series
        idx = [d for d in series.index if start <= d <= end]
        return series.loc[idx] if idx else pd.Series(dtype=float)

    return fetch


def _close_on(series: pd.Series, d: date) -> float | None:
    if d not in series.index:
        # try Timestamp key
        for key in series.index:
            kd = key.date() if hasattr(key, "date") else key
            if kd == d:
                val = float(series.loc[key])
                return val if np.isfinite(val) else None
        return None
    val = float(series.loc[d])
    return val if np.isfinite(val) else None


def _return_between(series: pd.Series, start: date, end: date) -> float | None:
    a = _close_on(series, start)
    b = _close_on(series, end)
    if a is None or b is None or a == 0:
        return None
    return (b / a) - 1.0


def _vol_20d(series: pd.Series, as_of: date, sessions: list[date]) -> float | None:
    end_i = None
    try:
        end_i = sessions.index(as_of)
    except ValueError:
        return None
    start_i = end_i - 20
    if start_i < 0:
        return None
    window_dates = sessions[start_i : end_i + 1]
    vals = []
    for d in window_dates:
        c = _close_on(series, d)
        if c is None:
            return None
        vals.append(c)
    rets = np.diff(vals) / np.array(vals[:-1])
    if len(rets) < 5:
        return None
    return float(np.std(rets, ddof=1) * np.sqrt(252))


def compute_features_and_label(
    *,
    ticker: str,
    published_at: datetime,
    fetch_closes: CloseFetcher | None = None,
    calendar: Any | None = None,
) -> dict[str, Any] | None:
    """Return feature/label dict or None if row cannot be labeled honestly."""
    cal = calendar or _xnys_calendar()
    sessions = _session_list(cal)
    fetch = fetch_closes or default_yfinance_closes

    feature_as_of = feature_as_of_session(published_at, cal)
    label_start = label_start_session(published_at, cal)
    label_end = session_offset(sessions, label_start, 5)
    if label_end is None:
        return None

    prior5 = session_offset(sessions, feature_as_of, -5)
    prior20 = session_offset(sessions, feature_as_of, -20)
    if prior5 is None or prior20 is None:
        return None

    # Need price history spanning prior20 → label_end.
    ticker_closes = fetch(ticker, prior20, label_end)
    spy_closes = fetch("SPY", prior20, feature_as_of)
    if ticker_closes.empty or spy_closes.empty:
        return None

    return_5d_prior = _return_between(ticker_closes, prior5, feature_as_of)
    return_20d_prior = _return_between(ticker_closes, prior20, feature_as_of)
    spy_return_5d = _return_between(spy_closes, prior5, feature_as_of)
    volatility_20d = _vol_20d(ticker_closes, feature_as_of, sessions)
    fwd_return_5d = _return_between(ticker_closes, label_start, label_end)

    if None in (
        return_5d_prior,
        return_20d_prior,
        spy_return_5d,
        volatility_20d,
        fwd_return_5d,
    ):
        return None

    label_high_risk = 1 if fwd_return_5d < LABEL_THRESHOLD else 0
    return {
        "feature_as_of": feature_as_of,
        "volatility_20d": float(volatility_20d),
        "return_5d_prior": float(return_5d_prior),
        "return_20d_prior": float(return_20d_prior),
        "spy_return_5d": float(spy_return_5d),
        "fwd_return_5d": float(fwd_return_5d),
        "label_high_risk": int(label_high_risk),
    }


def label_high_risk_from_fwd(fwd_return_5d: float) -> int:
    return 1 if fwd_return_5d < LABEL_THRESHOLD else 0
