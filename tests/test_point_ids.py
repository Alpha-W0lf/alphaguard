"""Unit tests for stable UUID5 Qdrant point ids (Guide 04 D1)."""

from __future__ import annotations

from alphaguard.rag.service import event_point_id


def test_uuid5_stable_for_same_event_id() -> None:
    event_id = "evt-aapl-001"
    assert event_point_id(event_id) == event_point_id(event_id)


def test_uuid5_different_ids_different_points() -> None:
    a = event_point_id("evt-aapl-001")
    b = event_point_id("evt-msft-001")
    assert a != b
