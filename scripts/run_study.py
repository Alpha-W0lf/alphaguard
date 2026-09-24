#!/usr/bin/env python3
"""CLI to execute an experiment study matrix in parallel (JH-63.2)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from alphaguard.ml.study_cli import run_study_cli  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(run_study_cli())
