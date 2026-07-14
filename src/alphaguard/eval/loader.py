"""Fail-closed golden-case loader (Guide 03)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ALLOWED_CHECKS = frozenset({"schema", "identity", "asof", "gate", "oou"})

REQUIRED_BY_CHECK: dict[str, frozenset[str]] = {
    "schema": frozenset({"action", "confidence"}),
    "identity": frozenset(
        {"llm_ticker", "input_ticker", "llm_event_id", "input_event_id"}
    ),
    "asof": frozenset({"published_at", "hits"}),
    "gate": frozenset({"action", "force_score"}),
    "oou": frozenset({"ticker"}),
}


class GoldenCaseLoadError(ValueError):
    """Fail-closed golden JSONL load / shape error."""


def default_golden_path() -> Path:
    """Repo-root ``eval/golden_cases.jsonl`` relative to this package file."""
    return Path(__file__).resolve().parents[3] / "eval" / "golden_cases.jsonl"


def load_golden_cases(path: Path | None = None) -> list[dict[str, Any]]:
    """Load and validate golden cases. Hard-fails on shape / duplicate / unknown check."""
    golden_path = path if path is not None else default_golden_path()
    if not golden_path.exists():
        raise GoldenCaseLoadError(f"golden cases file missing: {golden_path}")

    rows: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for line_no, line in enumerate(
        golden_path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise GoldenCaseLoadError(
                f"invalid JSON at {golden_path}:{line_no}: {exc}"
            ) from exc
        if not isinstance(raw, dict):
            raise GoldenCaseLoadError(
                f"{golden_path}:{line_no}: row must be a JSON object"
            )
        _validate_row(raw, golden_path, line_no, seen_ids)
        rows.append(raw)
    if not rows:
        raise GoldenCaseLoadError(f"golden cases file empty: {golden_path}")
    return rows


def _validate_row(
    row: dict[str, Any],
    path: Path,
    line_no: int,
    seen_ids: set[str],
) -> None:
    for key in ("case_id", "check", "expect"):
        if key not in row or row[key] in (None, ""):
            raise GoldenCaseLoadError(
                f"{path}:{line_no}: missing required universal key {key!r}"
            )
    case_id = str(row["case_id"])
    if case_id in seen_ids:
        raise GoldenCaseLoadError(f"{path}:{line_no}: duplicate case_id={case_id!r}")
    seen_ids.add(case_id)

    check = str(row["check"])
    if check not in ALLOWED_CHECKS:
        raise GoldenCaseLoadError(
            f"{path}:{line_no}: unknown check={check!r}; "
            f"allowed={sorted(ALLOWED_CHECKS)}"
        )
    missing = REQUIRED_BY_CHECK[check] - set(row.keys())
    if missing:
        raise GoldenCaseLoadError(
            f"{path}:{line_no}: case_id={case_id!r} check={check!r} "
            f"missing required keys: {sorted(missing)}"
        )
