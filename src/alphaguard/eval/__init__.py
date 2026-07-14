"""Eval harness — fail-closed golden loader + thin façade executors."""

from alphaguard.eval.harness import execute_golden, resolve_force_score
from alphaguard.eval.loader import (
    GoldenCaseLoadError,
    default_golden_path,
    load_golden_cases,
)

__all__ = [
    "GoldenCaseLoadError",
    "default_golden_path",
    "execute_golden",
    "load_golden_cases",
    "resolve_force_score",
]
