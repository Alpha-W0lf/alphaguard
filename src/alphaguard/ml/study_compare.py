"""Compare table generator for experiment harness studies (JH-63.2).

Generates markdown and CSV tables comparing child runs in a study.
"""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Any

from alphaguard.ml.study_registry import StudyRegistry
from alphaguard.ml.study_schema import ParentStudyRecord, RunRecord


def generate_compare_data(
    study: ParentStudyRecord,
    runs: list[RunRecord],
    sort_by: str = "test_f1",
) -> list[dict[str, Any]]:
    """Produce structured rows for all runs in a study."""
    rows: list[dict[str, Any]] = []

    for r in runs:
        test_m = r.metrics.get("test")

        test_f1 = test_m.f1 if test_m else 0.0
        test_p = test_m.precision if test_m else 0.0
        test_r = test_m.recall if test_m else 0.0
        test_fbeta = test_m.fbeta if test_m else 0.0
        test_auprc = test_m.auprc if test_m else 0.0
        test_brier = test_m.brier if test_m else 0.0

        if r.confusion:
            confusion_str = (
                f"{r.confusion.tp}/{r.confusion.fp}/{r.confusion.tn}/{r.confusion.fn}"
            )
        else:
            confusion_str = "n/a"

        row = {
            "run_id": r.run_id,
            "git_sha": r.git_sha[:8] if len(r.git_sha) >= 8 else r.git_sha,
            "dataset_hash": r.dataset_hash[:12] if len(r.dataset_hash) >= 12 else r.dataset_hash,
            "config_hash": r.config_hash[:8] if len(r.config_hash) >= 8 else r.config_hash,
            "seed": r.seed,
            "method": r.threshold_method,
            "calib": r.calibration_method,
            "threshold": round(r.score_threshold, 3),
            "test_f1": round(test_f1, 4),
            "test_p": round(test_p, 4),
            "test_r": round(test_r, 4),
            "test_fbeta": round(test_fbeta, 4),
            "test_auprc": round(test_auprc, 4),
            "test_brier": round(test_brier, 4),
            "confusion_tp_fp_tn_fn": confusion_str,
            "n_pos_test": r.n_positive_test,
            "wall_time_s": r.wall_time_s,
            "stage": r.stage,
            "aborted": r.aborted,
            "abort_reason": r.abort_reason or "",
        }
        rows.append(row)

    # Sort rows
    reverse = True
    if sort_by in ("wall_time_s", "test_brier"):
        reverse = False
    rows.sort(key=lambda x: (not x["aborted"], x.get(sort_by, 0.0)), reverse=reverse)
    return rows


def format_markdown_table(
    study: ParentStudyRecord,
    rows: list[dict[str, Any]],
) -> str:
    """Format compare rows into a clean Markdown table."""
    buf = io.StringIO()
    buf.write(f"# Study Comparison: {study.study_id}\n\n")
    if study.description:
        buf.write(f"**Description:** {study.description}\n\n")
    buf.write(
        f"- **Launch Git SHA:** `{study.git_sha}`\n"
        f"- **Dataset Hash:** `{study.dataset_hash}`\n"
        f"- **Total Runs:** {study.total_runs} "
        f"(Completed: {study.completed_runs}, Aborted: {study.aborted_runs})\n"
        f"- **Promotion Decision:** `{study.promotion_decision}`\n\n"
    )

    headers = [
        "Run ID",
        "Config",
        "Seed",
        "Method",
        "Calib",
        "Threshold",
        "Test F1",
        "Test P",
        "Test R",
        "Test Fβ",
        "AUPRC",
        "Brier",
        "Confusion (TP/FP/TN/FN)",
        "N+ Test",
        "Wall (s)",
        "Status",
    ]
    buf.write("| " + " | ".join(headers) + " |\n")
    buf.write("| " + " | ".join(["---"] * len(headers)) + " |\n")

    for r in rows:
        status = "Aborted" if r["aborted"] else "OK"
        line = [
            f"`{r['run_id']}`",
            f"`{r['config_hash']}`",
            str(r["seed"]),
            r["method"],
            r["calib"],
            f"{r['threshold']:.3f}",
            f"{r['test_f1']:.4f}",
            f"{r['test_p']:.4f}",
            f"{r['test_r']:.4f}",
            f"{r['test_fbeta']:.4f}",
            f"{r['test_auprc']:.4f}",
            f"{r['test_brier']:.4f}",
            r["confusion_tp_fp_tn_fn"],
            str(r["n_pos_test"]),
            f"{r['wall_time_s']:.2f}",
            status,
        ]
        buf.write("| " + " | ".join(line) + " |\n")

    # Render Promotion Gate section if promotion rollup or decision exists
    buf.write("\n## Promotion Gate (JH-AG-93.1)\n\n")
    if study.promotion_rollup:
        p_info = study.promotion_rollup
        floors = p_info.get("floors", {})
        f1_floor = floors.get("f1", 0.30)
        p_floor = floors.get("precision", 0.25)
        auprc_floor = floors.get("auprc", 0.18)
        extra_seeds = p_info.get("extra_seeds", [])

        buf.write(
            f"- **Gate Decision:** `{study.promotion_decision}` "
            f"(Harness proposal only; Model Quality Go requires human review)\n"
            f"- **Target Floors:** F1 ≥ {f1_floor:.2f}, Precision ≥ {p_floor:.2f}, "
            f"AUPRC ≥ {auprc_floor:.2f} (All must clear)\n"
            f"- **Required Extra Seeds:** `{extra_seeds}`\n"
            f"- **Seeds Cleared:** `{study.seeds_cleared}`\n"
            f"- **Seeds Failed:** `{study.seeds_failed}`\n\n"
        )

        candidates = p_info.get("candidates", [])
        if candidates:
            buf.write("### Shortlisted Candidates & Multi-Seed Rollup\n\n")
            c_headers = [
                "Rank",
                "Primary Run",
                "Config",
                "Seed",
                "Test F1",
                "Test P",
                "AUPRC",
                "Confusion (TP/FP/TN/FN)",
                "N+ Test",
                "Floor Status",
            ]
            buf.write("| " + " | ".join(c_headers) + " |\n")
            buf.write("| " + " | ".join(["---"] * len(c_headers)) + " |\n")

            for c in candidates:
                seed_evals = c.get("seed_evaluations", {})
                for _seed_key, se in seed_evals.items():
                    fails = ", ".join(se.get("failed_floors", []))
                    pass_str = "PASS" if se.get("passed") else f"FAIL ({fails})"
                    conf = se.get("confusion")
                    conf_str = (
                        f"{conf['tp']}/{conf['fp']}/{conf['tn']}/{conf['fn']}"
                        if conf
                        else "n/a"
                    )
                    c_line = [
                        str(c.get("candidate_rank", 1)),
                        f"`{se.get('run_id', 'n/a')}`",
                        f"`{c.get('config_hash', 'n/a')[:8]}`",
                        str(se.get("seed")),
                        f"{se.get('test_f1', 0.0):.4f}" if "test_f1" in se else "n/a",
                        f"{se.get('test_precision', 0.0):.4f}" if "test_precision" in se else "n/a",
                        f"{se.get('test_auprc', 0.0):.4f}" if "test_auprc" in se else "n/a",
                        conf_str,
                        str(se.get("n_pos_test", "n/a")),
                        pass_str,
                    ]
                    buf.write("| " + " | ".join(c_line) + " |\n")
            buf.write("\n")
        if study.notes:
            buf.write(f"**Gate Notes:** {study.notes}\n\n")
    else:
        buf.write(
            f"- **Promotion Decision:** `{study.promotion_decision}`\n"
            "- **Status:** No promotion gate configured for this study.\n\n"
        )

    buf.write(
        "> **Notice:** Harness proposal (`candidate` / `rejected` / `none`) is an automated\n"
        "> multi-seed stability check. It does NOT constitute a `Model Quality Go` or an\n"
        "> economic trading claim.\n"
    )

    return buf.getvalue()


def format_csv_table(rows: list[dict[str, Any]]) -> str:
    """Format compare rows into CSV format."""
    if not rows:
        return ""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def write_study_compare(
    study_dir: Path | str,
    sort_by: str = "test_f1",
) -> tuple[Path, Path]:
    """Read a study directory, generate compare.md and compare.csv inside it."""
    s_dir = Path(study_dir)
    study_path = s_dir / "study.json"
    if not study_path.exists():
        raise FileNotFoundError(f"Study record not found at {study_path}")

    study = ParentStudyRecord.model_validate_json(study_path.read_text(encoding="utf-8"))
    registry = StudyRegistry(s_dir.parent.parent)
    runs = registry.list_runs(study.study_id)

    rows = generate_compare_data(study, runs, sort_by=sort_by)

    md_content = format_markdown_table(study, rows)
    csv_content = format_csv_table(rows)

    md_path = s_dir / "compare.md"
    csv_path = s_dir / "compare.csv"

    md_path.write_text(md_content, encoding="utf-8")
    csv_path.write_text(csv_content, encoding="utf-8")

    return md_path, csv_path
