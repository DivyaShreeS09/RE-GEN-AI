# Google AI Agents Capstone

RE:GEN AI was built for the **Google Kaggle AI Agents Capstone**. This document maps every
required capstone concept to a concrete implementation in the codebase.

---

## Concept Mapping

| Capstone Concept | Implementation | Codebase Evidence |
|-----------------|----------------|-------------------|
| **Multi-Agent System** | 7 specialized agents with distinct inputs, outputs, and responsibilities | `backend/agents/*.py` — one file per agent |
| **Tools & Data Lookup** | Agents use CSV data and JSON knowledge base as retrieval tools: load → reason → output | `core/simulation.py`, `data/waste_knowledge_base.json`, `data/water_usage.csv`, `data/energy_usage.csv` |
| **State & Memory** | Agent results flow through `main.py` orchestration; full context chain passed to `report_agent.py`; War Room aggregates multi-agent state | `/dashboard/summary`, `/agent-war-room`, `/generate/action-plan` |
| **Guardrails & Safety** | Hazardous waste triggers mandatory CPCB warning; financial values suppressed; disclaimer injected into all responses; quantity bounds enforced | `core/guardrails.py` — `apply_hazard_guardrail()`, `validate_quantity()`, `DISCLAIMER` constant |
| **Evaluation & Scoring** | RE:GEN Score (0–100) from 6 weighted sub-dimensions; before/after scoring; per-agent confidence values (0.87–0.95); Decision Engine priority scoring | `core/scoring.py`, `agents/regen_score_agent.py`, `agents/decision_agent.py` |
| **Production-Grade Architecture** | FastAPI with typed Pydantic models, CORS middleware, modular agent package, React 19 + Vite 8 frontend, real Axios API integration | `main.py`, `requirements.txt`, `frontend/src/api.js` |

---

## Evaluation Test Cases

| # | Scenario | Input | Expected Result | Status |
|---|----------|-------|----------------|--------|
| 1 | Water anomaly detection | `GET /analyze/water` | `anomaly_events` list with date, location, duration, wasted litres; severity HIGH or CRITICAL | ✅ Pass |
| 2 | Energy after-hours detection | `GET /analyze/energy` | After-hours anomaly events with zone, equipment, wasted kWh; severity HIGH or CRITICAL | ✅ Pass |
| 3 | Hazardous waste guardrail | `POST /analyze/waste` — `waste_type: "e-waste"` | `hazard_warning: true`, `estimated_recovery: null`, CPCB notice in response | ✅ Pass |
| 4 | Clean waste pathway | `POST /analyze/waste` — `waste_type: "coconut shell"`, `quantity_kg: 50` | `hazard_warning: false`, `estimated_recovery` with INR range, pathway recommendation | ✅ Pass |
| 5 | RE:GEN Score computation | `GET /dashboard/summary` | `before_score` < `after_score`, `improvement` > 0, all 6 `score_breakdown` values present | ✅ Pass |
| 6 | Full action plan | `POST /generate/action-plan` — `include_waste: false` | `action_plan` with 4 tiers (immediate/7-day/30-day/long-term); `executive_summary` non-empty | ✅ Pass |

---

## RE:GEN Score Formula (Capstone Scoring Reference)

```
RE:GEN Score = waste_score  × 0.20
             + water_score  × 0.20
             + energy_score × 0.20
             + co2_score    × 0.15
             + urgency_score × 0.15
             + feasibility_score × 0.10
```

- Result clamped `[0, 100]`, rounded to 1 decimal place
- Rating: ≥80 Excellent · ≥60 Good · ≥40 Moderate · ≥20 Poor · <20 Critical
- "Before" score applies −15 to −25 offsets to model current degraded campus state
- "After" score uses raw sub-dimension values (post-intervention projection)

---

## Decision Engine Scoring (Intervention Prioritization)

```
priority_score = urgency × 0.35
              + min(cost_saving / 1000, 30) × 0.30
              + env_impact_score × 0.25
              + feasibility × 0.10
```

Urgency: critical→10, high→8, medium→5, low→3, none→1

---

## Agent Reasoning Traces

Every agent returns a `reasoning_trace` array of 5–8 plain-language steps documenting
how the agent arrived at its conclusion. These are surfaced in:

- `WasteAnalyzer` component — shown with `›` prefix markers
- `ActionPlan` component — `agent_reasoning_traces` in the JSON export
- `POST /generate/action-plan` — full traces for all active agents

This provides **full auditability** of every decision in the pipeline.

---

## SDG Alignment

The Pollution & Impact Agent maps recommendations to four UN Sustainable Development Goals:

| SDG | Goal | RE:GEN Contribution |
|-----|------|---------------------|
| SDG 6 | Clean Water and Sanitation | Water leakage detection and repair |
| SDG 7 | Affordable and Clean Energy | After-hours energy waste elimination |
| SDG 12 | Responsible Consumption and Production | Waste-to-value recovery pathways |
| SDG 13 | Climate Action | CO₂ reduction across all domains |

---

*See also: [AGENTS.md](AGENTS.md) · [SECURITY.md](SECURITY.md) · [ARCHITECTURE.md](ARCHITECTURE.md)*
