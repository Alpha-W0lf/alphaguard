"""Eval debt note + golden stub loader."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_golden_cases() -> list[dict]:
    path = ROOT / "eval" / "golden_cases.jsonl"
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def test_golden_cases_present() -> None:
    cases = load_golden_cases()
    assert len(cases) >= 5
    # Remaining debt: grow to ≥20 before portfolio claim (schema/identity/as-of/gate).
