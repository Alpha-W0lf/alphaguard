"""Single-seed Phase B CLI. Default threshold policy is train_f1_max.

Model hyperparameters, calibration, and beta come from the study YAML.
The YAML file is not modified. Seeds come from `--seed`.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from alphaguard.ml.study_cli import load_matrix_yaml
from alphaguard.ml.study_executor import execute_run
from alphaguard.ml.study_phaseb import promote_phaseb, summarize_phaseb
from alphaguard.ml.study_registry import dump_run_record
from alphaguard.ml.study_schema import ModelHyperparams, RunConfig
from alphaguard.ml.train_eval import METHOD_TRAIN_F1_MAX

logger = logging.getLogger(__name__)


def config_for_seed(yaml_path: Path, seed: int, freeze: str) -> RunConfig:
    """One cell: YAML hparams, CLI seed, threshold_method train_f1_max."""
    matrix = load_matrix_yaml(yaml_path)
    dataset_hash = matrix.dataset_hash or ""
    if not dataset_hash.startswith(freeze):
        raise ValueError(
            f"freeze {freeze!r} is not a prefix of dataset_hash {dataset_hash!r}"
        )
    if matrix.threshold_methods != [METHOD_TRAIN_F1_MAX]:
        logger.info(
            "phase B threshold_method=%s (plan default); yaml listed %s",
            METHOD_TRAIN_F1_MAX,
            matrix.threshold_methods,
        )
    model_params = ModelHyperparams(
        max_depth=matrix.max_depths[0],
        eta=matrix.etas[0],
        num_boost_round=matrix.num_boost_rounds[0],
        scale_pos_weight=matrix.scale_pos_weights[0],
    )
    prelim = RunConfig(
        study_id=matrix.study_id,
        run_id="temp",
        seed=seed,
        dataset_path=matrix.dataset_path,
        dataset_hash=dataset_hash,
        threshold_method=METHOD_TRAIN_F1_MAX,
        beta=matrix.betas[0],
        calibration_method=matrix.calibration_methods[0],
        model_params=model_params,
        split_policy=matrix.split_policy,
        train_frac=matrix.train_frac,
        val_frac=matrix.val_frac,
    )
    digest = prelim.compute_config_hash()
    prelim.run_id = f"phaseb_{digest[:8]}_s{seed}"
    return prelim


def run_phaseb(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Run one Phase B seed")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--freeze", type=str, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--walk-forward", choices=["off", "expanding4"], default="off")
    parser.add_argument("--economic", choices=["off", "on"], default="off")
    parser.add_argument("--cost-fp", type=float, default=1.0)
    parser.add_argument("--cost-fn", type=float, default=10.0)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    if not args.config.exists():
        print(f"ERROR: config not found: {args.config}", file=sys.stderr)
        return 1
    try:
        config = config_for_seed(args.config, args.seed, args.freeze)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    args.out.mkdir(parents=True, exist_ok=True)
    record = execute_run(
        config,
        args.out / "bundle",
        walk_forward=args.walk_forward,
        economic=args.economic,
        cost_fp=args.cost_fp,
        cost_fn=args.cost_fn,
    )
    payload = dump_run_record(record)
    (args.out / "run.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"seed={record.seed} aborted={record.aborted} "
        f"dataset_hash={record.dataset_hash} git_sha={record.git_sha} "
        f"out={args.out / 'run.json'}"
    )
    if record.aborted:
        print(f"FAIL: {record.abort_reason}", file=sys.stderr)
        return 2
    return 0


def summarize_phaseb_cli(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Summarize Phase B run directories")
    parser.add_argument("out_dir", type=Path)
    args = parser.parse_args(argv)
    if not args.out_dir.exists():
        print(f"ERROR: directory not found: {args.out_dir}", file=sys.stderr)
        return 1
    sys.stdout.write(summarize_phaseb(args.out_dir))
    return 0


def promote_phaseb_cli(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Propose candidate or no candidate")
    parser.add_argument("out_dir", type=Path)
    args = parser.parse_args(argv)
    if not args.out_dir.exists():
        print(f"ERROR: directory not found: {args.out_dir}", file=sys.stderr)
        return 1
    text = promote_phaseb(args.out_dir)
    sys.stdout.write(text if text.endswith("\n") else text + "\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="AlphaGuard Phase B study CLI")
    parser.add_argument("command", choices=["run", "summarize", "promote"])
    parser.add_argument("rest", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    if args.command == "run":
        return run_phaseb(args.rest)
    if args.command == "summarize":
        return summarize_phaseb_cli(args.rest)
    return promote_phaseb_cli(args.rest)
