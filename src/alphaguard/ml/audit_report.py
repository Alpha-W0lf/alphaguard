"""Phase C gate summary. Tooling records evidence and never claims quality Go."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from alphaguard.ml.audit_common import FREEZE_HASH, recorded_folds
from alphaguard.ml.audit_label import audit_labels
from alphaguard.ml.audit_leakage import audit_leakage
from alphaguard.ml.audit_prevalence import audit_prevalence, load_phaseb_fold_metrics
from alphaguard.ml.audit_rules_align import audit_rules_alignment
from alphaguard.ml.dataset_asof import _session_list, _xnys_calendar, frame_session_indices


def gate_summary(c1: dict[str, Any], c2: dict[str, Any], c3: dict[str, Any], c4: dict[str, Any]) -> dict[str, Any]:
    """Gates (a), (b), and (c). Any one fires WP-C5."""
    reasons: list[str] = []
    if c1["mismatch_count"]:
        reasons.append(f"C1 label mismatches={c1['mismatch_count']}")
    if c3["asof_violation_count"]:
        reasons.append(f"C3 as-of violations={c3['asof_violation_count']}")
    if c3["construction_duplicates"]:
        reasons.append(f"C3 construction duplicates={c3['construction_duplicates']}")
    if c3["row_embargo_overlap_rows"]:
        reasons.append(
            f"C3 horizon overlaps on the 5-row embargo={c3['row_embargo_overlap_rows']}"
        )
    if c3["row_embargo_short_boundaries"]:
        reasons.append(
            "C3 5-row embargo is shorter than 5 feature sessions on "
            f"{c3['row_embargo_short_boundaries']} boundaries"
        )
    fired_a = bool(reasons)
    fired_b = bool(c2["any_artifact"])
    fired_c = c4["verdict"] == "misaligned"
    return {
        "freeze": FREEZE_HASH,
        "a_fired": fired_a,
        "a_reasons": reasons,
        "b_fired": fired_b,
        "c_fired": fired_c,
        "c_verdict": c4["verdict"],
        "c5_fired": fired_a or fired_b or fired_c,
        "purged_overlap_rows": c3["purged_overlap_rows"],
        "model_quality_go": "UNCLAIMED",
    }


def run_phase_c_audit(
    df: pd.DataFrame,
    *,
    phaseb_dir: Path | None = None,
) -> dict[str, Any]:
    folds, n_dev = recorded_folds(len(df))
    feature_idx, label_end_idx = frame_session_indices(df)
    sessions = _session_list(_xnys_calendar())
    session_index = {day: i for i, day in enumerate(sessions)}
    phaseb = load_phaseb_fold_metrics(phaseb_dir) if phaseb_dir else []
    c1 = audit_labels(df, folds, n_dev)
    c2 = audit_prevalence(
        df, folds, n_dev, session_index=session_index, phaseb_metrics=phaseb
    )
    c3 = audit_leakage(
        df, folds, n_dev, feature_idx=feature_idx, label_end_idx=label_end_idx
    )
    c4 = audit_rules_alignment(df, folds, n_dev)
    gates = gate_summary(c1, c2, c3, c4)
    return {"c1": c1, "c2": c2, "c3": c3, "c4": c4, "gates": gates}


def render_gates_markdown(report: dict[str, Any]) -> str:
    gates = report["gates"]
    c2 = report["c2"]
    c4 = report["c4"]
    lines = [
        "# Phase C gates",
        "",
        "Model Quality Go remains UNCLAIMED. This audit does not propose a candidate.",
        "",
        f"- Freeze: `{gates['freeze']}`",
        f"- Gate (a) fired: {gates['a_fired']}",
        f"- Gate (b) fired: {gates['b_fired']}",
        f"- Gate (c) fired: {gates['c_fired']} ({gates['c_verdict']})",
        f"- WP-C5 fired: {gates['c5_fired']}",
        f"- Overlap rows after trading-day purge: {gates['purged_overlap_rows']}",
        "",
        "## Gate (a) reasons",
        "",
    ]
    if gates["a_reasons"]:
        lines.extend(f"- {reason}" for reason in gates["a_reasons"])
    else:
        lines.append("- none")
    lines.extend(["", "## Fold verdicts", ""])
    for row in c2["slices"]:
        lines.append(
            f"- {row['name']}: **{row['verdict']}** prevalence={row['prevalence']} "
            f"reasons={', '.join(row['reasons'])}"
        )
    lines.extend(
        [
            "",
            "## Rules alignment",
            "",
            f"Verdict: **{c4['verdict']}** "
            f"({c4['folds_veto_higher']}/{c4['fold_count']} folds, veto rate higher).",
            "",
            "| slice | veto positive rate | non-veto positive rate | veto higher |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in c4["slices"]:
        lines.append(
            f"| {row['name']} | {row['veto_positive_rate']} | "
            f"{row['non_veto_positive_rate']} | {row['veto_higher']} |"
        )
    lines.append("")
    return "\n".join(lines)
