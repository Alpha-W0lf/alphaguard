"""Native BLAS/OpenMP/XGBoost thread caps (macOS SIGSEGV hardening).

XGBoost / libomp can crash after fork or with unbounded OpenMP during
study+pytest. Call apply_native_thread_limits() before importing xgboost.
Uses os.environ.setdefault so user-provided values are never overwritten.
"""

from __future__ import annotations

import os

_THREAD_ENV_DEFAULTS: tuple[tuple[str, str], ...] = (
    ("OMP_NUM_THREADS", "1"),
    ("MKL_NUM_THREADS", "1"),
    ("OPENBLAS_NUM_THREADS", "1"),
    ("VECLIB_MAXIMUM_THREADS", "1"),
    ("NUMEXPR_NUM_THREADS", "1"),
    ("XGB_NUM_THREAD", "1"),
)


def apply_native_thread_limits() -> None:
    """Idempotently setdefault native math/OpenMP thread env vars to 1."""
    for key, value in _THREAD_ENV_DEFAULTS:
        os.environ.setdefault(key, value)
