"""FastAPI thin façade over PipelineService."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from alphaguard.config import get_settings
from alphaguard.infra.preflight import PreflightError, preflight_ollama
from alphaguard.ingest.replay import FixtureLoadError, get_event_by_id, load_replay_events
from alphaguard.pipeline.service import PipelineService


class ReplayRequest(BaseModel):
    event_id: str | None = None
    event: dict[str, Any] | None = None


class HealthDependency(BaseModel):
    name: str
    status: str
    detail: str = ""


def create_app() -> FastAPI:
    app = FastAPI(title="AlphaGuard", version="0.1.0")
    settings = get_settings()

    @app.get("/health")
    def health() -> dict[str, Any]:
        deps: list[HealthDependency] = [
            HealthDependency(name="app", status="ok"),
            HealthDependency(
                name="kafka",
                status="skipped",
                detail="not required for replay_fixture smoke",
            ),
        ]
        # Ollama
        try:
            model = preflight_ollama(settings)
            deps.append(HealthDependency(name="ollama", status="ok", detail=model))
        except PreflightError as exc:
            deps.append(HealthDependency(name="ollama", status="error", detail=str(exc)))

        # Qdrant
        if settings.alphaguard_rag_mode == "fixture":
            deps.append(
                HealthDependency(
                    name="qdrant",
                    status="skipped",
                    detail="ALPHAGUARD_RAG_MODE=fixture",
                )
            )
        else:
            try:
                import urllib.request

                with urllib.request.urlopen(
                    settings.qdrant_url.rstrip("/") + "/readyz", timeout=2.0
                ) as resp:
                    ok = resp.status == 200
                deps.append(
                    HealthDependency(
                        name="qdrant",
                        status="ok" if ok else "error",
                        detail=settings.qdrant_url,
                    )
                )
            except Exception as exc:  # noqa: BLE001
                deps.append(
                    HealthDependency(name="qdrant", status="error", detail=str(exc))
                )

        overall = "ok" if all(d.status in {"ok", "skipped"} for d in deps) else "degraded"
        return {
            "status": overall,
            "resource_mode": settings.resource_mode,
            "dependencies": [d.model_dump() for d in deps],
        }

    @app.post("/replay")
    def replay(body: ReplayRequest) -> dict[str, Any]:
        from alphaguard.contracts.events import NewsEvent

        fixtures = settings.fixtures_dir / "replay_events.jsonl"
        try:
            if body.event is not None:
                event = NewsEvent.model_validate(body.event)
            elif body.event_id:
                event = get_event_by_id(fixtures, body.event_id)
            else:
                event = load_replay_events(fixtures)[0]
        except FixtureLoadError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        try:
            model = preflight_ollama(settings)
        except PreflightError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

        service = PipelineService(settings=settings, resolved_model=model)
        envelope = service.run(event)
        if envelope.status == "error" and envelope.error and "unknown event" in (
            envelope.error.message or ""
        ):
            raise HTTPException(status_code=404, detail=envelope.error.message)
        return envelope.model_dump(mode="json")

    return app


app = create_app()
