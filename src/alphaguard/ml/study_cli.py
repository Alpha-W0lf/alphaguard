"""CLI tools for running studies and comparing experiment matrices (JH-63.2)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from alphaguard.ml.study_compare import write_study_compare
from alphaguard.ml.study_runner import run_study
from alphaguard.ml.study_schema import StudyMatrixConfig


def load_matrix_yaml(yaml_path: Path) -> StudyMatrixConfig:
    """Parse YAML study definition into StudyMatrixConfig."""
    raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Expected dict in YAML, got {type(raw)}")
    return StudyMatrixConfig.model_validate(raw)


def run_study_cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run an experiment study matrix with parallel workers (JH-63.2)"
    )
    parser.add_argument(
        "--study",
        type=Path,
        required=True,
        help="Path to study YAML config",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of parallel worker processes (default: 4)",
    )
    parser.add_argument(
        "--artifacts",
        type=Path,
        default=Path("artifacts/runs"),
        help="Root directory for study and run artifacts (default: artifacts/runs)",
    )
    parser.add_argument(
        "--dataset-path",
        type=Path,
        default=None,
        help="Override dataset parquet path in config",
    )
    parser.add_argument(
        "--dataset-hash",
        type=str,
        default=None,
        help="Override expected dataset hash in config",
    )
    args = parser.parse_args(argv)

    if not args.study.exists():
        print(f"ERROR: study config not found: {args.study}", file=sys.stderr)
        return 1

    try:
        matrix = load_matrix_yaml(args.study)
    except Exception as exc:
        print(f"ERROR: failed parsing study YAML: {exc}", file=sys.stderr)
        return 1

    if args.dataset_path:
        matrix.dataset_path = str(args.dataset_path)
    if args.dataset_hash:
        matrix.dataset_hash = args.dataset_hash

    print(
        f"Starting study '{matrix.study_id}' with {args.workers} workers "
        f"across registry '{args.artifacts}'..."
    )
    parent, runs = run_study(
        matrix=matrix,
        registry_root=args.artifacts,
        max_workers=args.workers,
        matrix_source_path=str(args.study),
    )

    study_dir = args.artifacts / "studies" / matrix.study_id
    md_path, csv_path = write_study_compare(study_dir)

    print(
        f"Completed study '{matrix.study_id}': total={parent.total_runs}, "
        f"completed={parent.completed_runs}, aborted={parent.aborted_runs}"
    )
    print(f"Compare table generated at:\n  {md_path}\n  {csv_path}")

    # Exit non-zero if any runs aborted
    if parent.aborted_runs > 0:
        print(
            f"WARNING: {parent.aborted_runs} run(s) aborted during study execution.",
            file=sys.stderr,
        )
        return 2

    return 0


def compare_study_cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate comparison markdown and CSV tables for a study (JH-63.2)"
    )
    parser.add_argument(
        "--study-dir",
        type=Path,
        required=True,
        help="Path to study directory (e.g. artifacts/runs/studies/<study_id>)",
    )
    parser.add_argument(
        "--sort-by",
        type=str,
        default="test_f1",
        help="Metric to sort by (e.g. test_f1, test_fbeta, test_auprc)",
    )
    args = parser.parse_args(argv)

    if not args.study_dir.exists():
        print(f"ERROR: study directory not found: {args.study_dir}", file=sys.stderr)
        return 1

    try:
        md_path, csv_path = write_study_compare(args.study_dir, sort_by=args.sort_by)
    except Exception as exc:
        print(f"ERROR: failed generating compare table: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote comparison tables to:\n  {md_path}\n  {csv_path}")
    return 0


def main_run() -> None:
    sys.exit(run_study_cli())


def main_compare() -> None:
    sys.exit(compare_study_cli())
