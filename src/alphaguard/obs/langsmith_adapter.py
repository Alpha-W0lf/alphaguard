"""LangSmith fail-open pipeline run emit (Guide 07)."""

from __future__ import annotations

import logging
import uuid
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from alphaguard.config import Settings
from alphaguard.contracts.envelope import AdapterStatus

logger = logging.getLogger(__name__)

ClientFactory = Callable[[], Any]

RUN_NAME = "alphaguard.pipeline.run"


def emit_pipeline_run(
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
) -> tuple[AdapterStatus, str | None]:
    """Emit one LangSmith run when tracing+key set; else skip. Never raises."""
    key = (settings.langsmith_api_key or "").strip()
    if not settings.langsmith_tracing or not key:
        return "skipped", None

    try:
        if client_factory is not None:
            client = client_factory()
        else:
            from langsmith import Client

            client = Client(api_key=key)

        ls_run_id = uuid.uuid4()
        start = datetime.now(timezone.utc)
        inputs = {
            "run_id": run_id,
            "event_id": event_id,
            "ticker": ticker,
            "mode": mode,
            "rag_mode": rag_mode,
            "status": status,
        }
        # Soft Adjust (langsmith>=0.10): create_run(name, inputs, run_type, **kwargs)
        client.create_run(
            RUN_NAME,
            inputs,
            "chain",
            id=ls_run_id,
            project_name=settings.langsmith_project,
            start_time=start,
        )
        client.update_run(
            ls_run_id,
            outputs=outputs or {},
            end_time=datetime.now(timezone.utc),
        )
        return "ok", str(ls_run_id)
    except Exception as exc:  # noqa: BLE001 — fail-open relative to pipeline
        logger.warning("langsmith adapter failed open: %s", exc)
        return "failed", None
