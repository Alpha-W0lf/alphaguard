"""Pydantic contracts (ARCHITECTURE §7) — SSOT shapes for the vertical slice."""

from alphaguard.contracts.decisions import Agent2Decision
from alphaguard.contracts.envelope import ObsStatus, PipelineRunEnvelope, RunError
from alphaguard.contracts.events import NewsEvent, TICKER_UNIVERSE
from alphaguard.contracts.manifest import ModelBundleManifest
from alphaguard.contracts.proposals import Agent1Proposal
from alphaguard.contracts.retrieval import RetrievalHit

__all__ = [
    "Agent1Proposal",
    "Agent2Decision",
    "ModelBundleManifest",
    "NewsEvent",
    "ObsStatus",
    "PipelineRunEnvelope",
    "RetrievalHit",
    "RunError",
    "TICKER_UNIVERSE",
]
