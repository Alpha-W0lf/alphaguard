"""Unit tests for RSS fetch retries (Guide 06 Phase B) — mocked httpx only."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from alphaguard.ingest.rss_fetch import (
    FEED_URL_TEMPLATE,
    MAX_ATTEMPTS,
    RssFetchError,
    feed_url,
    fetch_feed,
)

REPO = Path(__file__).resolve().parents[1]
FIXTURE = REPO / "data" / "fixtures" / "rss" / "yahoo_aapl_sample.xml"


class _FakeResponse:
    def __init__(self, status_code: int, content: bytes) -> None:
        self.status_code = status_code
        self.content = content


class _ScriptedClient:
    """Minimal httpx.Client stand-in with scripted get() results."""

    def __init__(self, script: list[object]) -> None:
        self._script = list(script)
        self.calls = 0

    def get(self, url: str, headers: dict[str, str] | None = None) -> _FakeResponse:
        self.calls += 1
        if not self._script:
            raise AssertionError("unexpected extra get()")
        item = self._script.pop(0)
        if isinstance(item, Exception):
            raise item
        assert isinstance(item, _FakeResponse)
        return item

    def close(self) -> None:
        return None


def test_feed_url_template() -> None:
    assert feed_url("AAPL") == FEED_URL_TEMPLATE.format(TICKER="AAPL")


def test_fetch_200_ok() -> None:
    xml = FIXTURE.read_bytes()
    client = _ScriptedClient([_FakeResponse(200, xml)])
    slept: list[float] = []
    body = fetch_feed("AAPL", client=client, sleep_fn=slept.append)  # type: ignore[arg-type]
    assert body == xml
    assert client.calls == 1
    assert slept == []


def test_fetch_retries_500_then_ok() -> None:
    xml = FIXTURE.read_bytes()
    client = _ScriptedClient(
        [_FakeResponse(500, b"err"), _FakeResponse(200, xml)]
    )
    slept: list[float] = []
    body = fetch_feed("AAPL", client=client, sleep_fn=slept.append)  # type: ignore[arg-type]
    assert body == xml
    assert client.calls == 2
    assert len(slept) == 1


def test_fetch_hard_fail_after_max_attempts() -> None:
    client = _ScriptedClient(
        [_FakeResponse(503, b"x") for _ in range(MAX_ATTEMPTS)]
    )
    slept: list[float] = []
    with pytest.raises(RssFetchError, match="exhausted"):
        fetch_feed("AAPL", client=client, sleep_fn=slept.append)  # type: ignore[arg-type]
    assert client.calls == MAX_ATTEMPTS
    assert len(slept) == MAX_ATTEMPTS - 1


def test_fetch_timeout_retries() -> None:
    xml = FIXTURE.read_bytes()
    client = _ScriptedClient(
        [
            httpx.ReadTimeout("slow"),
            _FakeResponse(200, xml),
        ]
    )
    slept: list[float] = []
    body = fetch_feed("MSFT", client=client, sleep_fn=slept.append)  # type: ignore[arg-type]
    assert body.startswith(b"<?xml") or body == xml
    assert client.calls == 2


@pytest.mark.rss_live
def test_live_yahoo_aapl_optional() -> None:
    """Opt-in live probe — skipped by default addopts."""
    import os

    if os.environ.get("ALPHAGUARD_RUN_RSS_LIVE") != "1":
        pytest.skip("set ALPHAGUARD_RUN_RSS_LIVE=1 to run")
    body = fetch_feed("AAPL")
    assert b"<rss" in body.lower() or b"<channel" in body.lower()
