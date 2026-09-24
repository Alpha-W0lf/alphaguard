"""ML features, downside-risk gate, and MLOps experiment harness (JH-63.2)."""

from alphaguard.ml.study_compare import (
    format_csv_table,
    format_markdown_table,
    generate_compare_data,
    write_study_compare,
)
from alphaguard.ml.study_executor import execute_run
from alphaguard.ml.study_metrics import compute_metrics_suite
from alphaguard.ml.study_registry import StudyRegistry
from alphaguard.ml.study_runner import generate_run_configs, run_study
from alphaguard.ml.study_schema import (
    ParentStudyRecord,
    RunConfig,
    RunRecord,
    StudyMatrixConfig,
)

__all__ = [
    "ParentStudyRecord",
    "RunConfig",
    "RunRecord",
    "StudyMatrixConfig",
    "StudyRegistry",
    "compute_metrics_suite",
    "execute_run",
    "format_csv_table",
    "format_markdown_table",
    "generate_compare_data",
    "generate_run_configs",
    "run_study",
    "write_study_compare",
]

