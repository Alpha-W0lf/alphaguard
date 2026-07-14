"""Executable golden harness (Guide 03) — presence floor + parametrized façades."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest

from alphaguard.eval import execute_golden, load_golden_cases
from alphaguard.ml.gate import DownsideRiskGate

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "data" / "fixtures" / "model_bundle_fixture"
CASES = load_golden_cases()


@pytest.fixture(scope="module")
def gate() -> DownsideRiskGate:
    if not (BUNDLE / "manifest.json").exists():
        pytest.skip("fixture bundle missing — run `make bundle`")
    return DownsideRiskGate(BUNDLE)


def test_golden_cases_presence_and_themes() -> None:
    assert len(CASES) >= 21
    ids = [c["case_id"] for c in CASES]
    assert len(ids) == len(set(ids))
    counts = Counter(c["check"] for c in CASES)
    assert counts["schema"] >= 3
    assert counts["identity"] >= 2
    assert counts["asof"] >= 3
    assert counts["gate"] >= 4
    assert counts["oou"] >= 3
    assert any(c["case_id"] == "oou_fixture_path_reject" for c in CASES)
    assert any(
        c.get("tmp_vol_veto") or "vol_veto" in c["case_id"] for c in CASES
    )
    assert any(c.get("via") == "fixture" for c in CASES)
    # Committed fixture must remain vol-veto off (tmp-manifest golden only).
    import json

    manifest = json.loads((BUNDLE / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["vol_veto_enabled"] is False
    assert manifest["vol_veto_threshold"] is None


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["case_id"])
def test_golden_case_executes(
    case: dict, gate: DownsideRiskGate, tmp_path: Path
) -> None:
    execute_golden(case, gate=gate, fixture_bundle=BUNDLE, tmp_path=tmp_path)
