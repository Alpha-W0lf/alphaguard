"""PipelineService — sole orchestrator for replay / API / future Kafka consumer."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from alphaguard.agents.analyst import Agent1Analyst
from alphaguard.config import Settings
from alphaguard.contracts.envelope import PipelineRunEnvelope, RunError
from alphaguard.contracts.events import NewsEvent
from alphaguard.contracts.proposals import Agent1Proposal
from alphaguard.ml.features import load_feature_row
from alphaguard.ml.gate import DownsideRiskGate, GateLoadError
from alphaguard.obs.summary import build_obs_status, write_local_envelope
from alphaguard.rag import RagService

logger = logging.getLogger(__name__)


class PipelineService:
    def __init__(
        self,
        settings: Settings,
        analyst: Agent1Analyst | None = None,
        gate: DownsideRiskGate | None = None,
        rag: RagService | None = None,
        skip_ollama_preflight: bool = False,
        resolved_model: str | None = None,
    ) -> None:
        self.settings = settings
        self.rag = rag or RagService(settings)
        self._analyst = analyst
        self._gate = gate
        self.skip_ollama_preflight = skip_ollama_preflight
        self.resolved_model = resolved_model or settings.ollama_model

    def _get_analyst(self) -> Agent1Analyst:
        if self._analyst is None:
            self._analyst = Agent1Analyst(
                model=self.resolved_model,
                base_url=self.settings.ollama_base_url,
            )
        return self._analyst

    def _get_gate(self) -> DownsideRiskGate:
        if self._gate is None:
            self._gate = DownsideRiskGate(self.settings.model_bundle_dir)
        return self._gate

    @staticmethod
    def stamp_identity(proposal: Agent1Proposal, event: NewsEvent) -> Agent1Proposal:
        mismatch = proposal.event_id != event.event_id or proposal.ticker != event.ticker
        if mismatch:
            logger.warning(
                "identity_mismatch llm_event_id=%s llm_ticker=%s "
                "input_event_id=%s input_ticker=%s — overwriting from input event",
                proposal.event_id,
                proposal.ticker,
                event.event_id,
                event.ticker,
            )
        return proposal.model_copy(
            update={"event_id": event.event_id, "ticker": event.ticker}
        )

    def ingest_event(self, event: NewsEvent) -> None:
        """§17 durable handle: validate + idempotent Qdrant upsert (no Agent 1/2)."""
        self.rag.upsert_event(event)

    def run(self, event: NewsEvent) -> PipelineRunEnvelope:
        run_id = str(uuid.uuid4())
        started = datetime.now(timezone.utc)
        proposal: Agent1Proposal | None = None
        decision = None
        hit_count = 0
        status = "success"
        error: RunError | None = None

        try:
            # Load gate before LLM so native libs initialize in a stable order on macOS.
            gate = self._get_gate()
            hits = self.rag.retrieve(event)
            hit_count = len(hits)
            proposal = self._get_analyst().run(event, hits)
            proposal = self.stamp_identity(proposal, event)
            features = load_feature_row(
                event, self.settings.fixtures_dir / "feature_rows.json"
            )
            decision = gate.decide(proposal, features)
        except GateLoadError as exc:
            status = "error"
            error = RunError(code="gate_load_error", message=str(exc), retriable=False)
        except Exception as exc:  # noqa: BLE001 — envelope records structured failure
            status = "error"
            code = "pipeline_error"
            msg = str(exc)
            if "agent1_validation_error" in msg:
                code = "validation_error"
            elif "Ollama" in msg or "ollama" in msg:
                code = "ollama_error"
            error = RunError(code=code, message=msg, retriable=False)

        finished = datetime.now(timezone.utc)
        outputs: dict[str, object] = {}
        if proposal is not None:
            outputs["action"] = proposal.action
        if decision is not None:
            outputs["decision"] = decision.decision

        obs, langsmith_run_id = build_obs_status(
            self.settings,
            self.settings.artifacts_dir / "runs" / f"{run_id}.json",
            run_id=run_id,
            event_id=event.event_id,
            ticker=event.ticker,
            mode=self.settings.alphaguard_mode,
            rag_mode=self.settings.alphaguard_rag_mode,
            status=status,
            outputs=outputs,
        )
        extras: dict[str, object] = {}
        if langsmith_run_id:
            extras["langsmith_run_id"] = langsmith_run_id

        # Degraded if adapters failed but pipeline succeeded.
        if status == "success" and (obs.langsmith == "failed" or obs.phoenix == "failed"):
            status = "degraded"

        # Write placeholder obs path first, then rewrite with final envelope.
        temp_envelope = PipelineRunEnvelope(
            run_id=run_id,
            status=status,  # type: ignore[arg-type]
            event_id=event.event_id,
            ticker=event.ticker,
            mode=self.settings.alphaguard_mode,
            rag_mode=self.settings.alphaguard_rag_mode,
            resource_mode=self.settings.resource_mode,
            proposal=proposal,
            decision=decision,
            retrieval_hit_count=hit_count,
            obs=obs,
            error=error,
            started_at=started,
            finished_at=finished,
            extras=extras,
        )

        path = write_local_envelope(temp_envelope, self.settings.artifacts_dir)
        final = temp_envelope.model_copy(
            update={"obs": temp_envelope.obs.model_copy(update={"local_summary_path": str(path)})}
        )
        write_local_envelope(final, self.settings.artifacts_dir)
        return final
