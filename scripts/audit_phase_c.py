#!/usr/bin/env python3
"""Read-only Phase C audit of a frozen training parquet.

Writes JSON reports and a gate summary. Does not fit a model and does not
claim a quality decision. Run artifacts stay under ``runs/`` and are not
source.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from alphaguard.contracts.decisions import FEATURE_NAMES
from alphaguard.ml.audit_common import FREEZE_HASH
from alphaguard.ml.audit_report import render_gates_markdown, run_phase_c_audit
from alphaguard.ml.train_option_b import dataset_hash, load_training_frame


def _write(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase C label and data audit")
    parser.add_argument(
        "--parquet",
        type=Path,
        default=Path("data/derived/training_events.parquet"),
    )
    parser.add_argument("--freeze", type=str, default=FREEZE_HASH[:8])
    parser.add_argument(
        "--phaseb-dir",
        type=Path,
        default=Path("runs/phaseb_2026-09-25"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("runs/phasec_2026-09-25/audit"),
    )
    args = parser.parse_args(argv)
    df = load_training_frame(args.parquet)
    x = df[list(FEATURE_NAMES)].to_numpy(dtype=float)
    y = df["label_high_risk"].to_numpy(dtype=int)
    digest = dataset_hash(x, y)
    if not digest.startswith(args.freeze):
        print(
            f"ERROR: freeze {args.freeze!r} is not a prefix of dataset hash {digest}",
            file=sys.stderr,
        )
        return 1
    report = run_phase_c_audit(df, phaseb_dir=args.phaseb_dir)
    report["dataset_hash"] = digest
    args.out.mkdir(parents=True, exist_ok=True)
    _write(args.out / "c1_labels.json", report["c1"])
    _write(args.out / "c2_folds.json", report["c2"])
    # As-of violation rows can be long; the count is the gate input.
    c3 = dict(report["c3"])
    c3["asof_violations"] = c3["asof_violations"][:50]
    _write(args.out / "c3_leakage.json", c3)
    _write(args.out / "c4_rules.json", report["c4"])
    _write(args.out / "gates.json", report["gates"])
    (args.out / "gates.md").write_text(render_gates_markdown(report), encoding="utf-8")
    gates = report["gates"]
    print(
        f"hash={digest} a={gates['a_fired']} b={gates['b_fired']} "
        f"c={gates['c_fired']} c5={gates['c5_fired']} "
        f"purged_overlaps={gates['purged_overlap_rows']}"
    )
    print("Model Quality Go remains UNCLAIMED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
