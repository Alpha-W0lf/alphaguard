"""Offline FinBERT batch scoring for Option B (never import from smoke path)."""

from __future__ import annotations

from typing import Iterable, Sequence

# Soft pin (human-locked 2026-07-16): Hub ID is ProsusAI/finbert — ProsusAI/finbert-tone does not exist.
FINBERT_MODEL_ID = "ProsusAI/finbert"


def sentiment_from_probs(pos: float, neg: float) -> float:
    """Soft-pin mapping: P(positive) - P(negative) ∈ [-1, 1]."""
    return float(pos) - float(neg)


def score_headlines(
    headlines: Sequence[str],
    *,
    model_id: str = FINBERT_MODEL_ID,
    batch_size: int = 16,
) -> list[float]:
    """Run FinBERT offline. Lazy-imports transformers/torch.

    Uses the default Hub auth (HF cache / HF_TOKEN). Public weights; no token=False workaround.
    """
    if not headlines:
        return []
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    import torch

    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForSequenceClassification.from_pretrained(model_id)
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
