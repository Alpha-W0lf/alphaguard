#!/usr/bin/env python3
"""Thin CLI for Option B training_events.parquet builder (Guide 05a)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from alphaguard.ml.dataset_build import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
