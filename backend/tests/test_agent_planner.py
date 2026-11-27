
import pytest

from core import agent_planner as planner


def candidate(tool, evidence=True, attempts=0, priority=0):
    return planner.ToolCandidate(
        tool=tool,
        evidence_available=evidence,
        attempts=attempts,
        priority=priority,
    )


def context(*candidates, goal="resource_review"):
    return planner.PlanningContext(
        goal=goal,
        candidates=list(candidates),
    )


def test_no_eligible_tools():
    result = planner.choose_next_tool(context())
    assert result.tool is None


def test_evidence_first():
    result = planner.choose_next_tool(
        context(
            candidate("water", evidence=False),
            candidate("energy", evidence=True),
        )
    )
    assert result.tool == "energy"


def test_exhausted_tool_excluded():
    result = planner.choose_next_tool(
        context(
            candidate("water", attempts=2),
            candidate("energy"),
        )
    )
    assert result.tool == "energy"


def test_goal_restricts_tools():
    result = planner.choose_next_tool(
        context(
            candidate("energy"),
            candidate("water"),
            goal="water",
        )
    )
    assert result.tool == "water"


def test_configured_priority():
    result = planner.choose_next_tool(
        context(
            candidate("water", priority=10),
            candidate("meter", priority=100),
        )
    )
    assert result.tool == "meter"


def test_offline_never_calls_ai(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Offline planner called AI")

    monkeypatch.setattr(planner, "call_ai", forbidden)

    result = planner.choose_next_tool(
        context(candidate("water"), candidate("energy"))
    )
    assert result.source == "deterministic"


def test_valid_ai_selection(monkeypatch):
    monkeypatch.setattr(
        planner,
        "call_ai",
        lambda *a, **k: ('{"tool":"water"}', True),
    )

    result = planner.choose_next_tool(
        context(candidate("water"), candidate("energy")),
        allow_ai=True,
    )

    assert result.tool == "water"
    assert result.source == "ai"


@pytest.mark.parametrize("response", [
    '{"tool":"meter"}',
    '{"tool":"unknown"}',
    '{"tool":"water","extra":"unexpected"}',
    'not valid JSON',
    '',
])
def test_invalid_ai_selection_falls_back(
    monkeypatch, response
):
    monkeypatch.setattr(
        planner,
        "call_ai",
        lambda *a, **k: (response, True),
    )

    result = planner.choose_next_tool(
        context(candidate("water"), candidate("energy")),
        allow_ai=True,
    )

    assert result.source == "deterministic"
    assert result.tool in {"water", "energy"}


def test_provider_unavailable(monkeypatch):
    monkeypatch.setattr(
        planner,
        "call_ai",
        lambda *a, **k: ("", False),
    )

    result = planner.choose_next_tool(
        context(candidate("water"), candidate("energy")),
        allow_ai=True,
    )

    assert result.source == "deterministic"


def test_single_candidate_skips_ai(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Unnecessary AI invocation")

    monkeypatch.setattr(planner, "call_ai", forbidden)

    result = planner.choose_next_tool(
        context(candidate("water")),
        allow_ai=True,
    )

    assert result.tool == "water"


def test_ai_cannot_override_evidence_policy(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Unnecessary AI invocation")

    monkeypatch.setattr(planner, "call_ai", forbidden)

    result = planner.choose_next_tool(
        context(
            candidate("water", evidence=False),
            candidate("energy", evidence=True),
        ),
        allow_ai=True,
    )

    assert result.tool == "energy"
    assert result.source == "deterministic"


def test_ai_cannot_override_priority(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Mandatory priority was ignored")

    monkeypatch.setattr(planner, "call_ai", forbidden)

    result = planner.choose_next_tool(
        context(
            candidate("water", priority=20),
            candidate("meter", priority=100),
        ),
        allow_ai=True,
    )

    assert result.tool == "meter"
    assert result.source == "deterministic"


def test_ai_cannot_override_retry_policy(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Retry priority was ignored")

    monkeypatch.setattr(planner, "call_ai", forbidden)

    result = planner.choose_next_tool(
        context(
            candidate("water", attempts=1),
            candidate("energy", attempts=0),
        ),
        allow_ai=True,
    )

    assert result.tool == "energy"
    assert result.source == "deterministic"


def test_ai_receives_only_equal_priority_tools(monkeypatch):
    def mock_ai(prompt, **kwargs):
        assert '"tool": "meter"' not in prompt
        return '{"tool":"water"}', True

    monkeypatch.setattr(planner, "call_ai", mock_ai)

    result = planner.choose_next_tool(
        context(
            candidate("water", priority=100),
            candidate("energy", priority=100),
            candidate("meter", priority=10),
        ),
        allow_ai=True,
    )

    assert result.tool == "water"
    assert result.source == "ai"
