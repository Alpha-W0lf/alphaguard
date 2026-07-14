"""Pipeline run envelope (ARCHITECTURE §7.7)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from alphaguard.contracts.decisions import Agent2Decision
from alphaguard.contracts.proposals import Agent1Proposal

RunStatus = Literal["success", "error", "degraded"]
RunMode = Literal["replay", "live"]
RagMode = Literal["fixture", "qdrant"]
ResourceMode = Literal[
    "replay_fixture",
    "replay_qdrant",
    "kafka_integration",
    "finbert_train",
]
AdapterStatus = Literal["ok", "skipped", "failed"]


class RunError(BaseModel):
    code: str
    message: str
    retriable: bool = False


class ObsStatus(BaseModel):
    local_summary_path: str
    langsmith: AdapterStatus = "skipped"
    phoenix: AdapterStatus = "skipped"


class PipelineRunEnvelope(BaseModel):
    run_id: str
    status: RunStatus
    event_id: str
    ticker: str
    mode: RunMode
    rag_mode: RagMode
    resource_mode: ResourceMode
    proposal: Agent1Proposal | None = None
    decision: Agent2Decision | None = None
    retrieval_hit_count: int = 0
    obs: ObsStatus
    error: RunError | None = None
    started_at: datetime
    finished_at: datetime
    extras: dict[str, Any] = Field(default_factory=dict)
