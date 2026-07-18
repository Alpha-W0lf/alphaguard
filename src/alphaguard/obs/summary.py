"""Observability — local run envelope always; LangSmith/Phoenix fail-open."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from alphaguard.config import Settings
from alphaguard.contracts.envelope import AdapterStatus, ObsStatus, PipelineRunEnvelope
from alphaguard.obs.langsmith_adapter import ClientFactory, emit_pipeline_run
from alphaguard.obs.phoenix_adapter import TracerFactory, emit_pipeline_span


def write_local_envelope(envelope: PipelineRunEnvelope, artifacts_dir: Path) -> Path:
    runs_dir = artifacts_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    path = runs_dir / f"{envelope.run_id}.json"
    path.write_text(
        json.dumps(envelope.model_dump(mode="json"), indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    return path


def best_effort_adapters(
    settings: Settings,
    *,
    run_id: str,
    event_id: str,
    ticker: str,
    mode: str,
    rag_mode: str,
    status: str,
    outputs: dict[str, Any] | None = None,
    client_factory: ClientFactory | None = None,
    tracer_factory: TracerFactory | None = None,
) -> tuple[AdapterStatus, AdapterStatus, str | None, str | None]:
    """LangSmith + Phoenix real emit when configured; else skipped/failed fail-open."""
    langsmith, langsmith_run_id = emit_pipeline_run(
        settings,
        run_id=run_id,
        event_id=event_id,
        ticker=ticker,
        mode=mode,
        rag_mode=rag_mode,
        status=status,
        outputs=outputs,
        client_factory=client_factory,
    )
    phoenix, phoenix_span_id = emit_pipeline_span(
        settings,
        run_id=run_id,
        event_id=event_id,
        ticker=ticker,
        mode=mode,
        rag_mode=rag_mode,
        status=status,
        outputs=outputs,
        tracer_factory=tracer_factory,
    )
    return langsmith, phoenix, langsmith_run_id, phoenix_span_id


def build_obs_status(
    settings: Settings,
    local_path: Path,
    *,
    run_id: str,
    event_id: str,
    ticker: str,
    mode: str,
    rag_mode: str,
    status: str,
    outputs: dict[str, Any] | None = None,
    client_factory: ClientFactory | None = None,
    tracer_factory: TracerFactory | None = None,
) -> tuple[ObsStatus, str | None, str | None]:
    langsmith, phoenix, langsmith_run_id, phoenix_span_id = best_effort_adapters(
        settings,
        run_id=run_id,
        event_id=event_id,
        ticker=ticker,
        mode=mode,
        rag_mode=rag_mode,
        status=status,
        outputs=outputs,
        client_factory=client_factory,
        tracer_factory=tracer_factory,
    )
    return (
        ObsStatus(
            local_summary_path=str(local_path),
            langsmith=langsmith,
            phoenix=phoenix,
        ),
        langsmith_run_id,
        phoenix_span_id,
    )
