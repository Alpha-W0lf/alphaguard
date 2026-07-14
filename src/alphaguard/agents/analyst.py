"""Agent 1 — LangGraph analyst consuming preloaded RetrievalHit[] (no second retrieve)."""

from __future__ import annotations

import json
import logging
from typing import Any, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph
from pydantic import ValidationError

from alphaguard.contracts.events import NewsEvent
from alphaguard.contracts.proposals import Agent1Proposal
from alphaguard.contracts.retrieval import RetrievalHit

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are AlphaGuard Agent 1, a cautious equity news analyst.
Return ONLY valid JSON with keys: action, confidence, rationale, event_id, ticker.
action must be one of BUY, HOLD, PASS. Never use SELL.
confidence must be a number between 0 and 1 (not a string).
rationale must be a short non-empty string (max 2000 chars).
Use only the provided headline and retrieval context. If context is thin, prefer HOLD or PASS.
"""


class AnalystState(TypedDict, total=False):
    event: dict[str, Any]
    hits: list[dict[str, Any]]
    raw_response: str
    proposal: dict[str, Any]
    attempt: int
    error: str


def _format_hits(hits: list[RetrievalHit]) -> str:
    if not hits:
        return "(no retrieval context after as-of filter)"
    lines = []
    for h in hits:
        lines.append(
            f"- [{h.document_id}] score={h.score:.3f} available_at={h.available_at.isoformat()} "
            f":: {h.text}"
        )
    return "\n".join(lines)


def _build_user_prompt(event: NewsEvent, hits: list[RetrievalHit], repair: str | None) -> str:
    body = (
        f"event_id: {event.event_id}\n"
        f"ticker: {event.ticker}\n"
        f"published_at: {event.published_at.isoformat()}\n"
        f"headline: {event.headline}\n"
        f"context:\n{_format_hits(hits)}\n"
    )
    if repair:
        body += f"\nPrevious output was invalid: {repair}\nFix and return valid JSON only.\n"
    return body


def _parse_proposal(text: str) -> Agent1Proposal:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()
    data = json.loads(cleaned)
    return Agent1Proposal.model_validate(data)


class Agent1Analyst:
    """LangGraph: prompt → structured JSON → validate; exactly one repair retry."""

    def __init__(self, model: str, base_url: str) -> None:
        self.llm = ChatOllama(
            model=model,
            base_url=base_url,
            temperature=0.1,
            format="json",
        )
        self.graph = self._build_graph()

    def _build_graph(self) -> Any:
        graph: StateGraph = StateGraph(AnalystState)

        def call_llm(state: AnalystState) -> AnalystState:
            event = NewsEvent.model_validate(state["event"])
            hits = [RetrievalHit.model_validate(h) for h in state.get("hits", [])]
            attempt = int(state.get("attempt", 0))
            repair = state.get("error") if attempt > 0 else None
            messages = [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=_build_user_prompt(event, hits, repair)),
            ]
            response = self.llm.invoke(messages)
            content = response.content if isinstance(response.content, str) else str(response.content)
            return {"raw_response": content, "attempt": attempt}

        def validate(state: AnalystState) -> AnalystState:
            try:
                proposal = _parse_proposal(state.get("raw_response", ""))
                return {"proposal": proposal.model_dump(mode="json"), "error": ""}
            except (json.JSONDecodeError, ValidationError, ValueError, TypeError) as exc:
                return {"error": str(exc)}

        def route_after_validate(state: AnalystState) -> str:
            if not state.get("error"):
                return "ok"
            if int(state.get("attempt", 0)) >= 1:
                return "fail"
            return "retry"

        def bump_attempt(state: AnalystState) -> AnalystState:
            return {"attempt": int(state.get("attempt", 0)) + 1}

        def fail(state: AnalystState) -> AnalystState:
            return {
                "error": (
                    "agent1_validation_error after one repair retry: "
                    f"{state.get('error', 'unknown')}"
                )
            }

        graph.add_node("call_llm", call_llm)
        graph.add_node("validate", validate)
        graph.add_node("bump_attempt", bump_attempt)
        graph.add_node("fail", fail)
        graph.set_entry_point("call_llm")
        graph.add_edge("call_llm", "validate")
        graph.add_conditional_edges(
            "validate",
            route_after_validate,
            {"ok": END, "retry": "bump_attempt", "fail": "fail"},
        )
        graph.add_edge("bump_attempt", "call_llm")
        graph.add_edge("fail", END)
        return graph.compile()

    def run(self, event: NewsEvent, hits: list[RetrievalHit]) -> Agent1Proposal:
        result = self.graph.invoke(
            {
                "event": event.model_dump(mode="json"),
                "hits": [h.model_dump(mode="json") for h in hits],
                "attempt": 0,
            }
        )
        if result.get("error"):
            raise ValueError(result["error"])
        return Agent1Proposal.model_validate(result["proposal"])
