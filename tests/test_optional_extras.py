"""Default install must not require Torch, transformers, or sentence-transformers."""

from __future__ import annotations

import ast
import builtins
from pathlib import Path

import pytest

from alphaguard.ml.dataset_finbert import _load_finbert_runtime, score_headlines
from alphaguard.rag import service as rag_service

REPO_ROOT = Path(__file__).resolve().parents[1]


def _top_level_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
    return names


def test_torch_stacks_are_not_top_level_imports() -> None:
    finbert = _top_level_imports(REPO_ROOT / "src/alphaguard/ml/dataset_finbert.py")
    embed = _top_level_imports(REPO_ROOT / "src/alphaguard/rag/service.py")
    assert finbert.isdisjoint({"torch", "transformers"})
    assert embed.isdisjoint({"sentence_transformers", "torch"})


def test_empty_finbert_batch_does_not_load_runtime() -> None:
    assert score_headlines([]) == []


def test_finbert_missing_train_extra(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = builtins.__import__

    def guarded(name, *args, **kwargs):
        if name == "torch" or name == "transformers" or name.startswith("transformers."):
            raise ImportError(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded)
    with pytest.raises(ImportError, match="train extra"):
        _load_finbert_runtime()


def test_embedder_missing_embed_extra(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = builtins.__import__
    monkeypatch.setattr(rag_service, "_EMBEDDER", None)

    def guarded(name, *args, **kwargs):
        if name == "sentence_transformers" or name.startswith("sentence_transformers."):
            raise ImportError(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded)
    with pytest.raises(ImportError, match="embed extra"):
        rag_service._get_embedder()
