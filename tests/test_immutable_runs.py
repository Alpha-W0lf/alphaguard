"""Run logs and registry entries are write-once (README "immutable" claim)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from alphaguard.config import Settings
from alphaguard.contracts.envelope import ObsStatus, PipelineRunEnvelope
from alphaguard.contracts.events import NewsEvent
from alphaguard.contracts.proposals import Agent1Proposal
from alphaguard.ml.study_registry import StudyRegistry
from alphaguard.ml.study_schema import ParentStudyRecord, RunConfig, RunRecord
from alphaguard.obs import summary
from alphaguard.pipeline.service import PipelineService

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "data" / "fixtures"


def _envelope(run_id: str = "run-immutable-001") -> PipelineRunEnvelope:
    now = datetime(2024, 3, 12, 14, 30, tzinfo=timezone.utc)
    return PipelineRunEnvelope(
        run_id=run_id,
        status="success",
        event_id="evt-aapl-001",
        ticker="AAPL",
        mode="replay",
        rag_mode="fixture",
        resource_mode="replay_fixture",
        obs=ObsStatus(local_summary_path=f"runs/{run_id}.json"),
        started_at=now,
        finished_at=now,
    )


def _run_record(run_id: str = "run_000_abc_s42") -> RunRecord:
    config = RunConfig(
        study_id="immut_study",
        run_id=run_id,
        seed=42,
        dataset_path="x.parquet",
        dataset_hash="h",
        threshold_method="train_f1_max",
    )
    return RunRecord(
        run_id=run_id,
        study_id="immut_study",
        git_sha="sha",
        dataset_hash="h",
        config_hash="c",
        seed=42,
        threshold_method="train_f1_max",
        score_threshold=0.5,
        wall_time_s=0.0,
        bundle_dir="b",
        config=config,
    )


def test_local_envelope_refuses_overwrite(tmp_path: Path) -> None:
    path = summary.write_local_envelope(_envelope(), tmp_path)
    before = path.read_bytes()
    changed = _envelope().model_copy(update={"status": "error"})
    with pytest.raises(FileExistsError, match="write-once"):
        summary.write_local_envelope(changed, tmp_path)
    assert path.read_bytes() == before


def test_pipeline_writes_envelope_exactly_once(tmp_path: Path) -> None:
    settings = Settings(
        langsmith_tracing=False,
        langsmith_api_key=None,
        phoenix_enabled=False,
        artifacts_dir=tmp_path,
        fixtures_dir=FIXTURES,
        model_bundle_dir=FIXTURES / "model_bundle_fixture",
        alphaguard_rag_mode="fixture",
        alphaguard_mode="replay",
    )
    event = NewsEvent(
        event_id="evt-aapl-001",
        headline="Apple announces product",
        ticker="AAPL",
        source="fixture",
        published_at=datetime(2024, 3, 12, 14, 30, tzinfo=timezone.utc),
    )

    class _Analyst:
        def run(self, _event: NewsEvent, _hits: list[Any]) -> Agent1Proposal:
            return Agent1Proposal(
                action="BUY",
                confidence=0.6,
                rationale="fixture",
                event_id=event.event_id,
                ticker=event.ticker,
            )

    svc = PipelineService(settings, analyst=_Analyst(), skip_ollama_preflight=True)  # type: ignore[arg-type]
    with patch(
        "alphaguard.pipeline.service.write_local_envelope",
        wraps=summary.write_local_envelope,
    ) as spy:
        envelope = svc.run(event)
    assert spy.call_count == 1
    on_disk = json.loads(Path(envelope.obs.local_summary_path).read_text(encoding="utf-8"))
    assert on_disk == envelope.model_dump(mode="json")


def test_registry_run_record_refuses_overwrite(tmp_path: Path) -> None:
    registry = StudyRegistry(tmp_path)
    path = registry.save_run(_run_record())
    before = path.read_bytes()
    with pytest.raises(FileExistsError, match="write-once"):
        registry.save_run(_run_record().model_copy(update={"score_threshold": 0.9}))
    assert path.read_bytes() == before


def test_registry_study_frozen_once_completed(tmp_path: Path) -> None:
    registry = StudyRegistry(tmp_path)
    study = ParentStudyRecord(
        study_id="immut_study", git_sha="sha", dataset_hash="h", dataset_path="x"
    )
    registry.save_study(study)
    # In-progress rollup may still be updated while the study runs.
    study.completed_at = "2026-10-18T00:00:00+00:00"
    path = registry.save_study(study)
    before = path.read_bytes()
    rerun = study.model_copy(update={"completed_at": None, "promotion_decision": "candidate"})
    with pytest.raises(FileExistsError, match="completed study"):
        registry.save_study(rerun)
    assert path.read_bytes() == before
