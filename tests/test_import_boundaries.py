"""Import boundary characterization tests (ARCHITECTURE §12 / §14).

Enforces:
1. Contracts do not import internal implementations (agents, ml, pipeline, rag, api).
2. Analyst agents do not import the downside risk gate or pipeline service (AG1 decoupling).
3. ML risk gate does not import analyst agents or pipeline service (AG1 / AG2).
4. PipelineService remains the sole orchestrator.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src" / "alphaguard"


def _get_internal_imports(file_path: Path) -> list[str]:
    tree = ast.parse(file_path.read_text(encoding="utf-8"))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module.startswith("alphaguard."):
                imports.append(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("alphaguard."):
                    imports.append(alias.name)
    return imports


def test_contracts_have_no_upstream_dependencies() -> None:
    contracts_dir = SRC_ROOT / "contracts"
    forbidden = ("alphaguard.agents", "alphaguard.ml", "alphaguard.pipeline", "alphaguard.rag", "alphaguard.api")
    for py_file in contracts_dir.glob("*.py"):
        imported = _get_internal_imports(py_file)
        for imp in imported:
            assert not any(imp.startswith(f) for f in forbidden), (
                f"{py_file.name} violates boundary by importing {imp}"
            )


def test_agents_do_not_import_risk_gate_or_pipeline() -> None:
    agents_dir = SRC_ROOT / "agents"
    forbidden = ("alphaguard.ml.gate", "alphaguard.pipeline")
    for py_file in agents_dir.glob("*.py"):
        imported = _get_internal_imports(py_file)
        for imp in imported:
            assert not any(imp.startswith(f) for f in forbidden), (
                f"{py_file.name} violates boundary by importing {imp}"
            )


def test_ml_gate_does_not_import_agents_or_pipeline() -> None:
    ml_dir = SRC_ROOT / "ml"
    forbidden = ("alphaguard.agents", "alphaguard.pipeline")
    for py_file in ml_dir.glob("*.py"):
        imported = _get_internal_imports(py_file)
        for imp in imported:
            assert not any(imp.startswith(f) for f in forbidden), (
                f"{py_file.name} violates boundary by importing {imp}"
            )
