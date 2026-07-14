"""Agent 2 decision contract (ARCHITECTURE §7.4 / AG1)."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from alphaguard.contracts.proposals import Agent1Action

GateDecision = Literal["approve", "reject"]

FEATURE_NAMES: tuple[str, ...] = (
    "finbert_sentiment",
    "volatility_20d",
    "return_5d_prior",
    "return_20d_prior",
    "spy_return_5d",
)


class Agent2Decision(BaseModel):
    """Downside-risk score + deterministic policy outcome."""

    event_id: str
    ticker: str
    action: Agent1Action
    downside_risk_score: float = Field(ge=0.0, le=1.0)
    decision: GateDecision
    decision_reason: str
    model_version: str
    bundle_id: str
    features_used: list[str]
    feature_as_of: date
    policy_version: str = "v1"
