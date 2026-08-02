# RE:GEN AI — Multi-Agent Sustainability Intelligence Platform

**Multi-Agent Sustainability Intelligence Platform**

---

## 1. Inspiration

I was thinking about a problem that is easy to ignore because it happens slowly and silently: organisations spend heavily on utilities, yet the data that would reveal where that money and those resources are being lost sits in disconnected spreadsheets, building management dashboards, and maintenance logs that no one is synthesising together.

Night-time water leaks run for hours before anyone notices. Lab equipment left on overnight costs thousands of rupees in electricity per year across a single building. Recyclable materials like circuit boards, metals, and organic waste get thrown into general bins because the recovery pathway is not obvious and nobody has mapped it.

The question that drove this project: what if a set of specialised agents could read those resource logs autonomously, calculate what is being lost, and produce a ranked action plan that a sustainability officer could act on immediately?

That is what RE:GEN AI attempts to do.

---

## 2. What It Does

RE:GEN AI is a multi-agent sustainability intelligence platform with two modes:

- **Demo Mode** — analyses bundled simulated campus sensor data instantly
- **Upload Mode** — accepts uploaded CSV/Excel files (water, energy, fuel) or manual numerical entry; any combination of datasets is accepted; missing datasets are skipped and documented, never estimated

Seven specialised agents work in a coordinated pipeline:

- **Water Leakage Agent** detects night-flow anomalies in hourly water usage data and estimates wasted liters, cost impact, and severity.
- **Energy Optimization Agent** identifies after-hours energy waste across zones and estimates kWh lost and CO2 impact.
- **Waste-to-Wealth Agent** accepts a waste material and quantity, looks it up in a 30-category knowledge base, applies hazard guardrails, and maps it to a recovery pathway with an estimated value range.
- **Pollution & Impact Agent** aggregates water CO2, energy CO2, and fuel CO2 (each passed directly — no cross-domain conversion). Expresses impact in relatable terms and aligns to SDGs 6, 7, 12, and 13. **Carbon is always derived automatically — never uploaded.**
- **Decision Engine** scores and ranks interventions using a weighted composite formula, then calls OpenAI `gpt-4o-mini` to explain the top-priority action in plain, actionable language.
- **RE:GEN Score Agent** produces a sustainability health index (0–100) with a before/after projection showing estimated improvement if all recommendations are implemented.
- **Report Agent** assembles all findings into an executive brief. Skipped agents are documented — not treated as complete. OpenAI generates the narrative summary; a deterministic fallback is used if unavailable.

**All numerical analysis is deterministic Python. OpenAI adds only language and reasoning layers.**

---

## 3. Why It Matters

Campus sustainability is a domain where the gap between data availability and action is large. Sensor data is often collected but rarely synthesised across domains. The bottleneck is not measurement — it is interpretation and prioritisation.

A multi-agent architecture is well-suited to this problem because each domain (water, energy, waste) has its own data format, anomaly logic, and impact metric. Separating agents by domain makes each one independently testable and replaceable. The orchestration layer handles synthesis.

RE:GEN AI demonstrates that a small, well-structured agent system can surface hidden resource loss and produce actionable, explainable recommendations from any uploaded data — not as a polished product, but as a working prototype that shows what is possible.

---

## 4. Agent Architecture

All agents live in `backend/agents/`. They are plain Python functions — no external agent framework required. Orchestration happens in `backend/main.py` via a FastAPI endpoint (`POST /analyze/upload` for upload mode, `GET /agent-war-room` for demo mode).

```
Data Intelligence Layer (validate / normalise uploaded CSV/Excel)
        │
        ├── Water Agent ──────┐
        ├── Energy Agent ─────┼──► Impact Agent ──► Decision Engine ──► Score Agent
        ├── Waste Agent ──────┘              │
        └── Fuel CO2 (automatic)            └──► Report Agent + OpenAI
```

Each agent returns a structured dictionary with:
- `status` — analyzed / skipped / error / unknown_material
- `skip_reason` — present when skipped, explaining why
- `reasoning_trace` — step-by-step audit of how the result was reached
- `confidence` — agent's self-assessed confidence (0–1)
- `disclaimer` — injected by `core/guardrails.py`
- Domain-specific findings

This structure makes agent outputs composable and the pipeline fully auditable.

---

## 5. How OpenAI Is Used

`gpt-4o-mini` is used via the `openai` SDK (≥ 1.0.0) in three places only:

**Waste recommendation:** When a non-hazardous material is analysed, OpenAI generates a 2-sentence recommendation for the sustainability officer. The prompt embeds guardrails: say "estimated" for all financial figures, do not claim exact profit, name one specific recovery product, be actionable. Hazardous materials never call OpenAI.

**Decision explanation:** After the Decision Engine ranks interventions, OpenAI explains why the top-ranked action must be prioritised. The prompt provides specific numbers from the deterministic agents so the explanation is grounded in real analysis rather than generic advice.

**Executive report narrative:** The Report Agent calls OpenAI to write a full executive summary of all agent findings. The prompt embeds guardrails, a list of forbidden phrases, and a requirement to reference the data source accurately.

If `OPENAI_API_KEY` is absent or the API call fails, every call site falls back to a deterministic rule-based string. The application is fully functional without OpenAI.

**What OpenAI does not do:** All numerical analysis — anomaly detection, severity classification, cost estimates, CO2 calculations, coverage/confidence/readiness scoring — is deterministic Python code that does not involve OpenAI.

---

## 6. Course Concepts Demonstrated

**Multi-agent systems:** Seven agents, each owning exactly one domain. No agent reaches into another's computation. Outputs are structured data passed between agents by the orchestration layer.

**Tool and data lookup:** The Waste-to-Wealth agent performs a knowledge-base lookup (JSON) keyed by material type. Water and energy agents validate and normalise uploaded DataFrames. These are analogues of the tool-use pattern in LLM agent frameworks.

**Agent orchestration:** `/analyze/upload` sequences all agents, passes water and energy results to the Impact Agent, passes all three to the Decision Engine, and passes everything to the Score Agent. The sequence is explicit and auditable.

**Graceful degradation:** Missing datasets produce skipped stubs (`status: "skipped"`, all metrics at 0). The report discloses which analyses ran and which were absent. Missing data is never estimated or invented.

**State and memory:** Frontend React state holds all agent outputs after an analysis run. Downstream components (Action Plan, Dashboard, Report) read from this shared state.

**Safety guardrails:** `core/guardrails.py` injects disclaimers, applies the hazard guardrail, and validates input quantities. Every OpenAI prompt embeds rules against misleading claims.

**Evaluation and scoring:** RE:GEN Score is a weighted composite across six sub-dimensions. Before-action and after-action scores are computed separately to show the projected impact of implementing recommendations. Coverage, confidence, and mission readiness are computed from which datasets are present.

**Production-grade deployment:** FastAPI with Uvicorn, environment-variable separation for secrets, CORS configuration, Render-ready start command, Vercel-ready frontend build.

**Development workflow:** Built iteratively with AI coding assistance. Each component was developed agent-by-agent, with structured iteration for debugging and UI layout.

---

## 7. Safety and Guardrails

RE:GEN AI has explicit safety design for a domain where misleading claims could cause real harm:

**Financial figures:** Exact profit is never claimed. All financial outputs use "estimated" qualifiers. The Waste-to-Wealth agent explicitly states that market prices vary.

**Hazardous waste:** If a waste material exceeds the hazard threshold, the agent suppresses recovery value calculations entirely, shows a clear regulatory warning, and does not call OpenAI. The officer is directed to engage a licensed hazardous waste handler.

**Data transparency:** Every API response includes a `data_notice` field stating the data source (uploaded vs. simulated). The report begins with a DATA SUMMARY section disclosing coverage, confidence, available datasets, and skipped analyses.

**OpenAI prompt guardrails:** All OpenAI prompts embed a Rules block forbidding specific phrases and requiring qualifiers on financial estimates.

**Negative value guard:** Wasted liters and wasted kWh are both clamped to `max(0, ...)` — they can never go negative even with sparse or unusual uploaded data.

**Disclaimer injection:** Every agent result includes a disclaimer from `core/guardrails.py` stating that RE:GEN AI is a prototype decision-support system and not professional regulatory, financial, or engineering advice.

---

## 8. Evaluation and Scoring

RE:GEN Score uses a weighted formula across six sub-scores:

| Sub-score | Weight | Source |
|---|---|---|
| Waste recovery potential | 20% | Baseline (60) for this prototype |
| Water saving potential | 20% | Derived from wasted liters |
| Energy saving potential | 20% | Derived from wasted kWh |
| CO2 reduction score | 15% | Impact Agent sustainability score |
| Urgency reduction | 15% | Inverse of average urgency across ranked actions |
| Feasibility | 10% | Baseline (82) representing intervention tractability |

The Decision Engine uses a separate scoring formula for ranking interventions: urgency (35%), estimated cost saving (30%), environmental impact (25%), feasibility (10%).

Mission Readiness uses: `coverage × 0.6 + confidence × 0.4` where coverage and confidence are weighted sums over present/missing dataset slots.

---

## 9. Technical Implementation

**Backend:** Python 3.12, FastAPI, Uvicorn. Agent functions are pure Python. Data loading uses Pandas; file parsing supports CSV and Excel (`.xlsx`, `.xls`) with multi-encoding fallback. OpenAI calls use the official `openai` SDK (≥ 1.0.0). Orchestration is explicit FastAPI code — no LLM framework, making the pipeline fully auditable.

**Frontend:** React 19 with Vite 8. Framer Motion for animations. Recharts for data visualisation. Lucide React for icons. Dark theme. The Agent War Room renders a live SVG node graph showing the AI Core connected to all 7 agents, with animated dots travelling along connection paths during analysis.

**Data:** Water and energy demo data are synthetic CSVs in `backend/data/`. The waste knowledge base is a JSON file with 30 material entries, each containing hazard level, estimated value range, possible products, buyer types, and sustainability notes.

**Upload pipeline:** `core/data_processor.py` handles CSV/Excel parsing, column synonym detection, anomaly auto-detection, and coverage/confidence/readiness computation. All validation is deterministic.

---

## 10. Challenges Faced

**AI provider selection.** The `core/openai_client.py` module uses the stable `openai` SDK with a deterministic fallback pattern. All numerical analysis is deterministic Python — the AI layer is isolated so it can be swapped without touching any agent logic.

**Fuel CO2 architecture.** An early implementation converted fuel CO2 to a kWh-equivalent using the electricity grid factor (fuel_co2_kg / 0.82) to feed it into the Impact Agent. This was semantically wrong — fuel and electricity have different emission sources. Fixed by adding `fuel_co2_kg` as a direct parameter to `analyze_impact()`, so each CO2 source is summed directly.

**Negative wasted values.** In edge cases with sparse or unusual uploaded data, `wasted_liters` and `wasted_kwh` could go negative when the baseline × anomaly_count exceeded total anomaly flow. Fixed with `max(0, ...)` clamping in both agents.

**Agent War Room layout.** Getting 7 agent nodes at equal radial distances from a central AI Core, with animated connection lines, in a responsive layout required careful SVG coordinate math and a zero-size anchor div pattern for pixel-perfect alignment.

**Guardrail design.** Deciding what OpenAI should and should not do required explicit upfront constraints: OpenAI touches only language and reasoning; all numbers come from deterministic Python.

---

## 11. Development Insights

The most effective discipline was defining explicit constraints before building each component — what this agent is responsible for, what it is not, and what its output contract is. When those boundaries were clear (e.g., OpenAI never called for hazardous waste, exact profit never claimed, negative values never allowed), the code stayed clean and consistent.

Visual components require human judgment that tooling cannot fully replace: the War Room layout went through many iterations because the desired visual feel was difficult to specify and required seeing the actual rendered result.

The key architectural decision — keeping all numerical analysis in deterministic Python and using OpenAI only for language and reasoning — proved stable throughout development. No agent logic changed when the language model was swapped; only the language layer changed.

---

## 12. Future Work

- Connect to real IoT sensors via MQTT or REST polling
- Occupancy data upload path (currently always absent, always penalises confidence by 4%)
- PDF and image upload via document parsing
- ERP and Building Management System integration
- Real-time recycler market price API for waste valuation
- Multi-site comparative scoring and time-series trend analysis
- Mobile dashboard for facilities management teams

---

## 13. Demo Links

- **Live demo:** [https://frontend-two-rho-85.vercel.app](https://frontend-two-rho-85.vercel.app)
- **Backend API:** [https://regen-ai-backend.onrender.com/health](https://regen-ai-backend.onrender.com/health)
- **Demo notebook:** `regen_ai_capstone_demo.ipynb` — self-contained, runs without backend
- **Demo video script:** `docs/demo_video_script.md` — 3-minute timestamped script

---

## 14. GitHub

[https://github.com/DivyaShreeS09/RE-GEN-AI](https://github.com/DivyaShreeS09/RE-GEN-AI)

---

## 15. Deployment

- **Backend (Render):** [https://regen-ai-backend.onrender.com](https://regen-ai-backend.onrender.com) — Python 3.12, FastAPI, root directory `backend`, start command `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Frontend (Vercel):** [https://frontend-two-rho-85.vercel.app](https://frontend-two-rho-85.vercel.app) — Vite build, root directory `frontend`, `VITE_API_URL` set to Render backend URL
