"""Phoenix fail-open pipeline span emit (Guide 08)."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from typing import Any

from alphaguard.config import Settings
from alphaguard.contracts.envelope import AdapterStatus

logger = logging.getLogger(__name__)

# Soft Adjust: (tracer, provider) — provider must support force_flush.
TracerFactory = Callable[[], tuple[Any, Any]]

RUN_NAME = "alphaguard.pipeline.run"
DEFAULT_COLLECTOR_ENDPOINT = "http://localhost:6006/v1/traces"
DEFAULT_PROJECT_NAME = "alphaguard"


def emit_pipeline_span(
    settings: Settings,
    *,
    run_id: str,
    event_id: str,
    ticker: str,
    mode: str,
    rag_mode: str,
    status: str,
    outputs: dict[str, Any] | None = None,
    tracer_factory: TracerFactory | None = None,
) -> tuple[AdapterStatus, str | None]:
    """Emit one Phoenix/OTEL chain span when enabled; else skip. Never raises.

    On success returns ``ok`` and a hex ``span_id`` string for ``extras.phoenix_span_id``.
    Soft Adjust (arize-phoenix-otel>=0.16): keyword-only ``register``,
    ``set_global_tracer_provider=False``, ``openinference_span_kind=\"chain\"``,
    ``force_flush`` before ``ok``.
    """
    if not settings.phoenix_enabled:
        return "skipped", None

    try:
        if tracer_factory is not None:
            tracer, provider = tracer_factory()
        else:
            from phoenix.otel import register

            endpoint = (settings.phoenix_collector_endpoint or "").strip()
            if not endpoint:
                endpoint = DEFAULT_COLLECTOR_ENDPOINT
            project = (settings.phoenix_project_name or "").strip() or DEFAULT_PROJECT_NAME
            provider = register(
                project_name=project,
                endpoint=endpoint,
                protocol="http/protobuf",
                batch=False,
                auto_instrument=False,
                set_global_tracer_provider=False,
                verbose=False,
            )
            tracer = provider.get_tracer("alphaguard.obs.phoenix")

        inputs = {
            "run_id": run_id,
            "event_id": event_id,
            "ticker": ticker,
            "mode": mode,
            "rag_mode": rag_mode,
            "status": status,
        }
        out = outputs or {}

        with tracer.start_as_current_span(
            RUN_NAME,
            openinference_span_kind="chain",
        ) as span:
            if hasattr(span, "set_input"):
                span.set_input(inputs)
            else:
                span.set_attribute("input.value", json.dumps(inputs, default=str))
            if hasattr(span, "set_output"):
                span.set_output(out)
            else:
                span.set_attribute("output.value", json.dumps(out, default=str))
            ctx = span.get_span_context()
            span_id = format(ctx.span_id, "016x")

        flushed = provider.force_flush(timeout_millis=5_000)
        if flushed is False:
            raise RuntimeError("phoenix force_flush returned False")
        return "ok", span_id
    except Exception as exc:  # noqa: BLE001 — fail-open relative to pipeline
        logger.warning("phoenix adapter failed open: %s", exc)
        return "failed", None
