#!/usr/bin/env python3
"""Tiny FinBERT MPS smoke: score ~32 headlines → mps_smoke.json."""

from __future__ import annotations

import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
import sys

sys.path.insert(0, str(ROOT / "src"))

from alphaguard.ml.dataset_finbert import _prefer_device, score_headlines  # noqa: E402


def main() -> int:
    import torch

    headlines = [
        f"Company {i} beats earnings estimates amid market rally"
        if i % 2 == 0
        else f"Firm {i} faces regulatory probe after sharp selloff"
        for i in range(32)
    ]
    preferred = _prefer_device(torch)
    t0 = time.perf_counter()
    scores = score_headlines(headlines, batch_size=16)
    elapsed = time.perf_counter() - t0
    # Device actually used is logged by score_headlines; record preferred + elapsed.
    out = {
        "preferred_device": preferred,
        "n_headlines": len(headlines),
        "batch_size": 16,
        "seconds": round(elapsed, 4),
        "headlines_per_sec": round(len(headlines) / elapsed, 3) if elapsed > 0 else None,
        "n_scores": len(scores),
        "score_min": float(min(scores)),
        "score_max": float(max(scores)),
        "score_mean": float(sum(scores) / len(scores)),
        "mps_available": bool(torch.backends.mps.is_available()),
    }
    dest = Path(__file__).resolve().parent / "mps_smoke.json"
    dest.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
