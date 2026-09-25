"""Offline FinBERT batch scoring for Option B (never import from smoke path)."""

from __future__ import annotations

import logging
import warnings
from typing import Sequence

# Soft pin (human-locked 2026-07-16): Hub ID is ProsusAI/finbert — ProsusAI/finbert-tone does not exist.
FINBERT_MODEL_ID = "ProsusAI/finbert"

logger = logging.getLogger(__name__)


def sentiment_from_probs(pos: float, neg: float) -> float:
    """Soft-pin mapping: P(positive) - P(negative) ∈ [-1, 1]."""
    return float(pos) - float(neg)


def _load_finbert_runtime():
    """Import transformers + torch. Requires the ``train`` extra."""
    try:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
    except ImportError as exc:
        raise ImportError(
            "Offline FinBERT needs the train extra: "
            "uv sync --extra train (or pip install 'alphaguard[train]')."
        ) from exc
    return torch, AutoTokenizer, AutoModelForSequenceClassification


def _prefer_device(torch) -> str:
    """Return ``mps`` when Apple Metal is available, else ``cpu``."""
    try:
        if bool(getattr(torch.backends, "mps", None) and torch.backends.mps.is_available()):
            return "mps"
    except Exception:  # noqa: BLE001 — defensive probe
        pass
    return "cpu"


def _score_headlines_on_device(
    headlines: Sequence[str],
    *,
    model_id: str,
    batch_size: int,
    device_name: str,
    torch,
    AutoTokenizer,
    AutoModelForSequenceClassification,
) -> list[float]:
    device = torch.device(device_name)
    logger.info("FinBERT device=%s batch_size=%s", device_name, batch_size)
    print(f"FinBERT device={device_name} batch_size={batch_size}", flush=True)

    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForSequenceClassification.from_pretrained(model_id)
    model.to(device)
    model.eval()
    id2label = {int(k): v.lower() for k, v in model.config.id2label.items()}

    scores: list[float] = []
    with torch.no_grad():
        for i in range(0, len(headlines), batch_size):
            batch = list(headlines[i : i + batch_size])
            enc = tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=128,
                return_tensors="pt",
            )
            enc = {k: v.to(device) for k, v in enc.items()}
            logits = model(**enc).logits
            probs = torch.softmax(logits, dim=-1).cpu().numpy()
            for row in probs:
                pos = neg = 0.0
                for idx, p in enumerate(row):
                    lab = id2label.get(idx, "")
                    if "positive" in lab:
                        pos = float(p)
                    elif "negative" in lab:
                        neg = float(p)
                scores.append(sentiment_from_probs(pos, neg))
    return scores


def score_headlines(
    headlines: Sequence[str],
    *,
    model_id: str = FINBERT_MODEL_ID,
    batch_size: int = 16,
) -> list[float]:
    """Run FinBERT offline. Lazy-imports transformers/torch.

    Prefers Apple MPS when available; falls back to CPU on MPS errors.
    Uses the default Hub auth (HF cache / HF_TOKEN). Public weights; no token=False workaround.
    """
    if not headlines:
        return []
    torch, AutoTokenizer, AutoModelForSequenceClassification = _load_finbert_runtime()
    preferred = _prefer_device(torch)
    try:
        return _score_headlines_on_device(
            headlines,
            model_id=model_id,
            batch_size=batch_size,
            device_name=preferred,
            torch=torch,
            AutoTokenizer=AutoTokenizer,
            AutoModelForSequenceClassification=AutoModelForSequenceClassification,
        )
    except Exception as exc:  # noqa: BLE001 — MPS OOM / unsupported ops
        if preferred != "mps":
            raise
        msg = (
            f"FinBERT MPS failed ({type(exc).__name__}: {exc}); "
            "falling back to CPU for this scoring run"
        )
        warnings.warn(msg, RuntimeWarning, stacklevel=2)
        logger.warning(msg)
        print(f"WARNING: {msg}", flush=True)
        return _score_headlines_on_device(
            headlines,
            model_id=model_id,
            batch_size=batch_size,
            device_name="cpu",
            torch=torch,
            AutoTokenizer=AutoTokenizer,
            AutoModelForSequenceClassification=AutoModelForSequenceClassification,
        )


def score_headlines_resume(
    headlines: Sequence[str],
    existing: Sequence[float | None] | None = None,
    **kwargs: object,
) -> list[float]:
    """Resume-friendly wrapper: recompute only missing scores."""
    if existing is None or len(existing) != len(headlines):
        return score_headlines(headlines, **kwargs)  # type: ignore[arg-type]
    out: list[float] = []
    todo_idx = [i for i, v in enumerate(existing) if v is None]
    if not todo_idx:
        return [float(v) for v in existing]  # type: ignore[arg-type]
    todo_texts = [headlines[i] for i in todo_idx]
    filled = score_headlines(todo_texts, **kwargs)  # type: ignore[arg-type]
    fill_map = dict(zip(todo_idx, filled, strict=True))
    for i, v in enumerate(existing):
        out.append(float(fill_map[i]) if i in fill_map else float(v))  # type: ignore[arg-type]
    return out
