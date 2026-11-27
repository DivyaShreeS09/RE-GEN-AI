if (-not (Test-Path .\AGENTS.md)) {
@'
# RE:GEN AI Engineering Instructions

## Before implementation
Read PROJECT_STATE.md, REGEN_ENGINEERING_SPEC.md,
ACCEPTANCE_AUDIT.md and PROGRESS.md.

Inspect actual implementation before making assumptions.
Preserve existing uncommitted work.

## Engineering standards
- Prefer small, testable, maintainable changes.
- Use typed interfaces and validated structured outputs.
- Separate planning, execution and verification.
- Preserve evidence provenance and uncertainty.
- Do not represent simulations as real-world outcomes.
- Never invent external partners or operational evidence.

## Infrastructure
Existing Docker, PostgreSQL, Ollama, Python and Node
installations are verified. Do not reinstall them.

Use npm 11.21.3 with Node 22.22.0.

PostgreSQL integration tests use:
REGEN_TEST_POSTGRES=1
REGEN_TEST_POSTGRES_DSN supplied privately.

Never print database credentials.

## AI policy
Automated regression tests must remain offline.
Use local Ollama only for designated inference tests.
Do not consume Gemini or Groq quota without approval.

## Verification
Run affected tests after every meaningful change.
Run full SQLite, PostgreSQL and frontend regression
before declaring a milestone complete.

Record actual commands, results and limitations.
Never claim a test passed unless it was executed.

## Failure handling
Diagnose concrete errors.
Do not repeatedly retry an unchanged failing command.
Report blockers and request missing evidence.

## Security
Never weaken tenant isolation or authorization.
Do not expose local services publicly.
Do not perform unauthorized deployment or external actions.

## Completion
Update PROJECT_STATE.md, PROGRESS.md and
ACCEPTANCE_AUDIT.md when relevant.

Production readiness requires operational evidence,
not merely passing software tests.
'@ | Set-Content .\AGENTS.md -Encoding UTF8
}