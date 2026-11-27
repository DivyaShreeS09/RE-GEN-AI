
"""Bounded, evidence-aware analytical tool selection."""

import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from core.ai_client import call_ai, ai_status


ToolName = Literal["water", "energy", "meter"]


class ToolCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    tool: ToolName
    evidence_available: bool
    attempts: int = Field(default=0, ge=0)
    priority: int = Field(default=0, ge=0, le=100)


class PlanningContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    goal: Literal["water", "energy", "resource_review"]
    candidates: list[ToolCandidate] = Field(max_length=3)
    findings_count: int = Field(default=0, ge=0)


class ToolProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool: ToolName


class PlanningDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    tool: ToolName | None
    source: Literal["ai", "deterministic"]
    reason: str
    provider: str | None = None
    model: str | None = None
    inference_attempts: int = 0


def eligible_candidates(
    context: PlanningContext,
) -> list[ToolCandidate]:
    """Enforce tool eligibility independently of AI."""

    allowed = {
        "water": {"water", "meter"},
        "energy": {"energy", "meter"},
        "resource_review": {"water", "energy", "meter"},
    }[context.goal]

    return [
        candidate
        for candidate in context.candidates
        if candidate.tool in allowed
        and candidate.attempts < 2
    ]


def deterministic_plan(
    candidates: list[ToolCandidate],
) -> PlanningDecision:
    """Select a reproducible evidence-first fallback."""

    if not candidates:
        return PlanningDecision(
            tool=None,
            source="deterministic",
            reason="No eligible investigation remains.",
        )

    selected = sorted(
        candidates,
        key=lambda candidate: (
            not candidate.evidence_available,
            candidate.attempts,
            -candidate.priority,
            candidate.tool,
        ),
    )[0]

    return PlanningDecision(
        tool=selected.tool,
        source="deterministic",
        reason="Selected by evidence availability, "
               "attempt count and configured priority.",
    )


def choose_next_tool(
    context: PlanningContext,
    *,
    allow_ai: bool = False,
) -> PlanningDecision:
    """Select an eligible investigation within policy."""

    candidates = eligible_candidates(context)
    fallback = deterministic_plan(candidates)

    if not allow_ai or len(candidates) < 2:
        return fallback

    # AI may only choose between candidates with the
    # strongest available evidence.
    if any(c.evidence_available for c in candidates):
        candidates = [
            c for c in candidates
            if c.evidence_available
        ]
    # Preserve retry and mandatory priority constraints.
    fewest_attempts = min(c.attempts for c in candidates)

    candidates = [
        c for c in candidates
        if c.attempts == fewest_attempts
    ]

    highest_priority = max(c.priority for c in candidates)

    candidates = [
        c for c in candidates
        if c.priority == highest_priority
    ]
    if len(candidates) < 2:
        return fallback

    prompt = (
        "Select the next read-only resource investigation. "
        "Use only the supplied eligible tools. "
        "Prefer investigations with fewer previous attempts. "
        "Do not invent evidence or measurements. "
        "Return only JSON matching this schema: "
        '{"tool": "eligible_tool_name"}. '
        "Planning context: "
        + json.dumps({
            "goal": context.goal,
            "findings_count": context.findings_count,
            "candidates": [
                c.model_dump(mode="json")
                for c in candidates
            ],
        })
    )

    before = ai_status()["attempts"]
    text, used = call_ai(
        prompt,
        fallback="",
        schema=ToolProposal,
    )

    status = ai_status()
    attempts = max(0, status["attempts"] - before)
    fallback = fallback.model_copy(
        update={"inference_attempts": attempts}
    )

    if not used:
        return fallback

    try:
        proposal = ToolProposal.model_validate_json(text)
    except ValueError:
        return fallback

    permitted = {c.tool for c in candidates}

    if proposal.tool not in permitted:
        return fallback

    return PlanningDecision(
        tool=proposal.tool,
        source="ai",
        provider=status["provider"],
        model=status["model"],
        inference_attempts=attempts,
        reason="AI-selected investigation passed "
               "tool eligibility validation.",
    )