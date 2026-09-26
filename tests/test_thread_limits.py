"""Unit tests for native thread-limit hardening (macOS OpenMP/XGBoost)."""

from __future__ import annotations

import os
from unittest.mock import patch

from alphaguard.ml.thread_limits import apply_native_thread_limits
from alphaguard.ml.study_cli import run_study_cli


def test_apply_native_thread_limits_setdefaults_without_clobber(monkeypatch) -> None:
    monkeypatch.delenv("OMP_NUM_THREADS", raising=False)
    monkeypatch.delenv("MKL_NUM_THREADS", raising=False)
    monkeypatch.delenv("OPENBLAS_NUM_THREADS", raising=False)
    monkeypatch.delenv("VECLIB_MAXIMUM_THREADS", raising=False)
    monkeypatch.delenv("NUMEXPR_NUM_THREADS", raising=False)
    monkeypatch.delenv("XGB_NUM_THREAD", raising=False)

    monkeypatch.setenv("OMP_NUM_THREADS", "8")

    apply_native_thread_limits()

    assert os.environ["OMP_NUM_THREADS"] == "8"
    assert os.environ["MKL_NUM_THREADS"] == "1"
    assert os.environ["OPENBLAS_NUM_THREADS"] == "1"
    assert os.environ["VECLIB_MAXIMUM_THREADS"] == "1"
    assert os.environ["NUMEXPR_NUM_THREADS"] == "1"
    assert os.environ["XGB_NUM_THREAD"] == "1"

    # Idempotent: second call still does not clobber user value.
    apply_native_thread_limits()
    assert os.environ["OMP_NUM_THREADS"] == "8"


def test_darwin_cli_default_workers_is_one(capsys, tmp_path) -> None:
    missing = tmp_path / "missing_study.yaml"
    with patch("sys.platform", "darwin"):
        code = run_study_cli(["--study", str(missing)])
    assert code == 1
    out = capsys.readouterr().out
    assert "Darwin: defaulting --workers to 1" in out


def test_darwin_cli_workers_override_is_logged(capsys, tmp_path) -> None:
    missing = tmp_path / "missing_study.yaml"
    with patch("sys.platform", "darwin"):
        code = run_study_cli(["--study", str(missing), "--workers", "3"])
    assert code == 1
    out = capsys.readouterr().out
    assert "Darwin: using user-specified --workers=3" in out


def test_non_darwin_cli_default_workers_is_four(capsys, tmp_path) -> None:
    missing = tmp_path / "missing_study.yaml"
    with patch("sys.platform", "linux"):
        code = run_study_cli(["--study", str(missing)])
    assert code == 1
    out = capsys.readouterr().out
    assert "Darwin: defaulting --workers to 1" not in out
