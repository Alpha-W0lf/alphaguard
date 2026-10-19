"""Agent 1 proposal contract (ARCHITECTURE §7.2 / AG1)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

Agent1Action = Literal["BUY", "HOLD", "PASS"]


class Agent1Proposal(BaseModel):
    """LLM analyst proposal. SELL is unsupported and rejected by schema."""

    action: Agent1Action
    confidence: float
    rationale: str = Field(min_length=1, max_length=2000)
    event_id: str = Field(min_length=1)
    ticker: str = Field(min_length=1)

    @field_validator("confidence", mode="before")
    @classmethod
    def confidence_range(cls, value: object) -> float:
        # Prefer reject + retry over silent coerce of string confidence.
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise ValueError("confidence must be a number in [0, 1]")
        score = float(value)
        if score < 0.0 or score > 1.0:
            raise ValueError("confidence must be in [0, 1]")
        return score
