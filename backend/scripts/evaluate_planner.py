
"""Local-only smoke evaluation of the analytical planner."""

import os
import sys
import time
import json
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1])
)

# Never use cloud providers during this evaluation.
os.environ["REGEN_ENV"] = "development"
os.environ["REGEN_AI_PROVIDER"] = "ollama"
os.environ["GEMINI_API_KEY"] = ""
os.environ["GROQ_API_KEY"] = ""
os.environ["REGEN_GROQ_MODEL"] = ""
os.environ["REGEN_OLLAMA_MODEL"] = "qwen3:8b"

from core import ai_client
from core.agent_planner import (
    ToolCandidate,
    PlanningContext,
    choose_next_tool,
)


def candidate(tool, evidence=True, attempts=0, priority=0):
    return ToolCandidate(
        tool=tool,
        evidence_available=evidence,
        attempts=attempts,
        priority=priority,
    )


cases = [
    (
        "Balanced resource investigation",
        "resource_review",
        [candidate("water"), candidate("energy")],
        {"water", "energy"},
        True,
    ),
    (
        "Three eligible investigations",
        "resource_review",
        [
            candidate("water"),
            candidate("energy"),
            candidate("meter", priority=100),
        ],
        {"meter"},
        False,
    ),
    (
        "Missing water evidence",
        "resource_review",
        [
            candidate("water", evidence=False),
            candidate("energy"),
        ],
        {"energy"},
        False,
    ),
    (
        "Exhausted investigation",
        "resource_review",
        [
            candidate("water", attempts=2),
            candidate("energy"),
        ],
        {"energy"},
        False,
    ),
    (
        "Water goal restriction",
        "water",
        [
            candidate("energy"),
            candidate("water"),
        ],
        {"water"},
        False,
    ),
    (
        "Meter or stored water analysis",
        "water",
        [
            candidate("water", priority=20),
            candidate("meter", priority=100),
        ],
        {"meter"},
        False,
    ),
    (
        "No remaining investigations",
        "resource_review",
        [],
        {None},
        False,
    ),
    (
        "All investigations exhausted",
        "resource_review",
        [
            candidate("water", attempts=2),
            candidate("energy", attempts=2),
        ],
        {None},
        False,
    ),
]

results = []

for index, case in enumerate(cases, 1):
    name, goal, candidates, expected, expect_ai = case

    tenant_token = ai_client._tenant.set(
        f"planner-evaluation-{index}"
    )
    usage_token = ai_client._usage.set(0)
    provider_token = ai_client._last_provider.set(None)

    try:
        start = time.perf_counter()

        decision = choose_next_tool(
            PlanningContext(
                goal=goal,
                candidates=candidates,
            ),
            allow_ai=True,
        )

        elapsed = time.perf_counter() - start
        status = ai_client.ai_status()

        policy_pass = decision.tool in expected

        provider_pass = (
            decision.source == "ai"
            and status["provider"] == "Ollama"
            if expect_ai
            else decision.source == "deterministic"
            and status["attempts"] == 0
        )

        results.append({
            "case": name,
            "tool": decision.tool,
            "source": decision.source,
            "provider": status["provider"],
            "seconds": round(elapsed, 3),
            "policy_pass": policy_pass,
            "provider_pass": provider_pass,
        })

    finally:
        ai_client._tenant.reset(tenant_token)
        ai_client._usage.reset(usage_token)
        ai_client._last_provider.reset(provider_token)

print(json.dumps(results, indent=2))

policy_passed = sum(r["policy_pass"] for r in results)
provider_passed = sum(r["provider_pass"] for r in results)

print("\n=== EVALUATION SUMMARY ===")
print(f"Policy checks: {policy_passed}/{len(results)}")
print(f"Provider checks: {provider_passed}/{len(results)}")
print(f"Total cases: {len(results)}")
print("Cloud providers: disabled by evaluation configuration")

ai_results = [
    r for r in results if r["source"] == "ai"
]

if ai_results:
    average = sum(
        r["seconds"] for r in ai_results
    ) / len(ai_results)

    print(f"Successful AI decisions: {len(ai_results)}")
    print(f"Average AI latency: {average:.3f}s")

sys.exit(
    0 if policy_passed == provider_passed == len(results)
    else 1
)
