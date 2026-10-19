"""Pytest session hooks.

Apply native BLAS/OpenMP/XGBoost thread caps before any test module imports
xgboost (via alphaguard.ml), which can SIGSEGV on macOS with unbounded OpenMP.
"""

from alphaguard.ml.thread_limits import apply_native_thread_limits

apply_native_thread_limits()
