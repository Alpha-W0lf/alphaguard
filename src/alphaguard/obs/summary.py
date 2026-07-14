"""Observability — local run envelope always; LangSmith/Phoenix fail-open."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from alphaguard.config import Settings
from alphaguard.contracts.envelope import AdapterStatus, ObsStatus, PipelineRunEnvelope

logger = logging.getLogger(__name__)


def write_local_envelope(envelope: PipelineRunEnvelope, artifacts_dir: Path) -> Path:
    runs_dir = artifacts_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    path = runs_dir / f"{envelope.run_id}.json"
    path.write_text(
        json.dumps(envelope.model_dump(mode="json"), indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    return path


def best_effort_adapters(settings: Settings) -> tuple[AdapterStatus, AdapterStatus]:
    """LangSmith / Phoenix are fail-open relative to pipeline correctness."""
    langsmith: AdapterStatus = "skipped"
    phoenix: AdapterStatus = "skipped"

    if settings.langsmith_tracing and settings.langsmith_api_key:
        try:
            # Soft touch only — do not require network success for smoke.
            if not settings.langsmith_api_key.strip():
                raise ValueError("empty LANGSMITH_API_KEY")
            langsmith = "ok"
        except Exception as exc:  # noqa: BLE001
            logger.warning("langsmith adapter failed open: %s", exc)
            langsmith = "failed"
    else:
        langsmith = "skipped"

    if settings.phoenix_enabled:
        try:
            phoenix = "ok"
        except Exception as exc:  # noqa: BLE001
            logger.warning("phoenix adapter failed open: %s", exc)
            phoenix = "failed"
    else:
        phoenix = "skipped"

    return langsmith, phoenix


def build_obs_status(
    settings: Settings,
    local_path: Path,
) -> ObsStatus:
    langsmith, phoenix = best_effort_adapters(settings)
    return ObsStatus(
        local_summary_path=str(local_path),
        langsmith=langsmith,
        phoenix=phoenix,
    )
