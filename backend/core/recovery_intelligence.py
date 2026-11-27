"""Evidence-constrained recovery intelligence for RE:GEN AI."""

import json
from pydantic import BaseModel, ConfigDict, Field
from core.ai_client import call_ai, ai_status, inference_enabled


class RecoveryProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")
    candidate: int = Field(ge=0, le=7)


def financial_benefit(option):
    net = option.get("net_paise")
    if net is not None:
        return net

    avoided = option.get("avoided_purchase_paise")
    if avoided is not None:
        return avoided - sum(
            option.get("costs_paise", {}).values()
        )

    return None


def evidence_gaps(option):
    gaps = []

    if financial_benefit(option) is None:
        gaps.append("Financial benefit not established")

    if option.get("projected_co2e_g") is None:
        gaps.append("Environmental comparison unavailable")

    if option.get("acceptance_fraction") is None:
        gaps.append("No recorded acceptance history")

    if not option.get("quote_expires") and option.get(
        "pathway"
    ) == "sell":
        gaps.append("Current quote evidence required")

    return gaps


def metrics(option, goal):
    effort = {
        "low": 2,
        "moderate": 1,
        "high": 0
    }

    return (
        int(option["pathway"] == goal),
        financial_benefit(option),
        effort.get(option.get("effort"), 0),
        option.get("acceptance_fraction"),
        option.get("projected_co2e_g")
    )


def dominates(first, second, goal):
    a = metrics(first, goal)
    b = metrics(second, goal)

    # Missing evidence cannot establish superiority.
    if any(
        (x is None) != (y is None)
        for x, y in zip(a, b)
    ):
        return False

    comparable = [
        (x, y)
        for x, y in zip(a, b)
        if x is not None and y is not None
    ]

    return (
        all(x >= y for x, y in comparable)
        and any(x > y for x, y in comparable)
    )


def pareto_frontier(options, goal):
    return [
        option for option in options
        if not any(
            dominates(other, option, goal)
            for other in options
            if other["service_id"] != option["service_id"]
        )
    ]


def recovery_intelligence(options, goal, *, allow_ai=False):
    if not options:
        return {
            "status": "no_verified_match",
            "selected_service_id": None,
            "source": "deterministic",
            "provider": None,
            "model": None,
            "inference_attempts": 0,
            "alternatives": [],
            "next_action": "Request facility-reviewed evidence"
        }

    ranked = sorted(
        options,
        key=lambda item: (
            -item["score"],
            item["service_id"]
        )
    )

    compared = ranked[:30]
    frontier = pareto_frontier(compared, goal)

    # Keep AI selection inside a narrow policy-approved
    # score band, not the entire service directory.
    best_score = frontier[0]["score"]

    candidates = [
        option for option in frontier
        if option["score"] >= best_score - 5
    ][:8]

    if not candidates:
        candidates = [frontier[0]]

    selected = candidates[0]
    source = "deterministic"
    provider = model = None
    attempts = 0

    if (
        allow_ai
        and len(candidates) > 1
        and inference_enabled()
    ):
        # Only numeric and enumerated evidence is sent.
        # No organization names, contact details or PIN.
        summaries = [
            {
                "candidate": i,
                "pathway": item["pathway"],
                "goal_match": item["pathway"] == goal,
                "score": item["score"],
                "net_benefit_paise": financial_benefit(item),
                "effort": item.get("effort"),
                "acceptance_fraction": item.get(
                    "acceptance_fraction"
                ),
                "outcome_count": item.get("outcome_count"),
                "projected_co2e_g": item.get(
                    "projected_co2e_g"
                ),
                "evidence_gaps": evidence_gaps(item)
            }
            for i, item in enumerate(candidates)
        ]

        prompt = (
            "Choose one eligible recovery alternative "
            "for the supplied goal. Compare financial "
            "benefit, effort, environmental evidence and "
            "observed reliability. Unknown values are "
            "not zero. Do not invent missing evidence. "
            'Return JSON only: {"candidate": integer}. '
            + json.dumps({
                "goal": goal,
                "candidates": summaries
            })
        )

        before = ai_status()["attempts"]

        raw, used = call_ai(
            prompt,
            fallback="",
            schema=RecoveryProposal
        )

        status = ai_status()
        attempts = max(0, status["attempts"] - before)

        if used:
            try:
                proposal = RecoveryProposal.model_validate_json(
                    raw
                )

                if proposal.candidate < len(candidates):
                    selected = candidates[proposal.candidate]
                    source = "ai"
                    provider = status["provider"]
                    model = status["model"]

            except ValueError:
                pass

    frontier_ids = {
        item["service_id"] for item in frontier
    }

    return {
        "status": "proposal_ready",
        "goal": goal,
        "eligible_count": len(ranked),
        "compared_count": len(compared),
        "selected_service_id": selected["service_id"],
        "selected_pathway": selected["pathway"],
        "source": source,
        "provider": provider,
        "model": model,
        "inference_attempts": attempts,
        "net_benefit_paise": financial_benefit(selected),
        "evidence_gaps": evidence_gaps(selected),
        "requires_staff_approval": True,
        "alternatives": [
            {
                "service_id": item["service_id"],
                "pathway": item["pathway"],
                "score": item["score"],
                "net_benefit_paise": financial_benefit(item),
                "goal_match": item["pathway"] == goal,
                "pareto_efficient": (
                    item["service_id"] in frontier_ids
                ),
                "evidence_gaps": evidence_gaps(item)
            }
            for item in ranked[:30]
        ],
        "next_action": "Review the proposal and current evidence"
    }
