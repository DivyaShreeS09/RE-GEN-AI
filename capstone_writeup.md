# RE:GEN AI — Multi-Agent Sustainability Command Center

**Google Kaggle AI Agents: Intensive Vibe Coding Capstone Project 2026**

---

## 1. Inspiration

I was thinking about a problem that is easy to ignore because it happens slowly and silently: universities spend heavily on utilities, yet the data that would reveal where that money and those resources are being lost sits in disconnected spreadsheets, building management dashboards, and maintenance logs that no one is synthesizing together.

Night-time water leaks run for hours before anyone notices. Lab equipment left on overnight costs thousands of rupees in electricity per year across a single building. Recyclable materials like circuit boards, metals, and organic waste get thrown into general bins because the recovery pathway is not obvious and nobody has made the effort to map it.

The question that drove this project: what if a set of specialized agents could read those resource logs autonomously, calculate what is being lost, and produce a ranked action plan that a sustainability officer could act on immediately?

That is what RE:GEN AI attempts to do.

---

## 2. What It Does

RE:GEN AI is a multi-agent decision-support prototype for campus sustainability. It consists of seven specialized agents working in a coordinated pipeline:

- **Water Leakage Agent** detects night-flow anomalies in 7-day hourly water usage data and estimates wasted liters, cost impact, and severity.
- **Energy Optimization Agent** identifies after-hours energy waste across campus zones and estimates kWh lost and CO2 impact.
- **Waste-to-Wealth Agent** accepts a waste material and quantity, looks it up in a 30-category knowledge base, applies hazard guardrails, and maps it to a recovery pathway with an estimated value range.
- **Pollution & Impact Agent** aggregates water and energy savings into CO2 reduction, expresses impact in relatable terms (trees, vehicle km, household days), and aligns findings to SDGs 6, 7, 12, and 13.
- **Decision Engine** scores and ranks interventions using a weighted composite formula, then calls Gemini 2.5 Flash Lite to explain the top-priority action in plain, actionable language.
- **RE:GEN Score Agent** produces a campus health index (0–100) with a before/after projection showing estimated improvement if all recommendations are implemented.
- **Report Agent** assembles all findings into an executive brief, with Gemini generating the narrative summary.

The frontend visualizes the agent network in a live Agent War Room, maps campus health across zones in a Digital Twin view, and exports a full PDF report.

**All data is simulated. RE:GEN AI is a prototype decision-support system, not a production IoT platform.**

---

## 3. Why It Matters

Campus sustainability is a domain where the gap between data availability and action is large. Sensor data is often collected but rarely synthesized across domains. The bottleneck is not measurement — it is interpretation and prioritization.

A multi-agent architecture is well-suited to this problem because each domain (water, energy, waste) has its own data format, anomaly logic, and impact metric. Separating agents by domain makes each one independently testable and replaceable. The orchestration layer then handles synthesis — something a single monolithic model would struggle to do reliably while also producing auditable numerical outputs.

RE:GEN AI demonstrates that a small, well-structured agent system can surface hidden resource loss and produce actionable, explainable recommendations — not as a polished product, but as a working prototype that shows what is possible with the tools and APIs now available.

---

## 4. Agent Architecture

All agents live in `backend/agents/`. They are plain Python functions — no external agent framework required. Orchestration happens in `backend/main.py` via a FastAPI endpoint (`POST /api/war-room`) that sequences agents and passes outputs between them.

```
Water Agent ─────┐
Energy Agent ─────┼──► Impact Agent ──► Decision Engine ──► Score Agent
Waste Agent ─────┘                              │
                                                └──► Report Agent + Gemini
```

Each agent returns a structured dictionary with:
- `status` — analyzed / error / unknown_material
- `reasoning_trace` — step-by-step audit of how the result was reached
- `confidence` — agent's self-assessed confidence (0–1)
- `disclaimer` — injected by `core/guardrails.py`
- Domain-specific findings

This structure makes agent outputs composable — the Decision Engine reads from any agent's result dict without needing to know how it was computed.

---

## 5. How Gemini Is Used

Gemini 2.5 Flash Lite (`gemini-2.5-flash-lite`) is used in three places, all via `backend/core/gemini_client.py`:

**Waste recommendation:** When a non-hazardous material is analyzed, Gemini generates a 2-sentence recommendation for the sustainability officer. The prompt embeds guardrails: say "estimated" for all financial figures, do not claim exact profit, name one specific recovery product, be actionable. Hazardous materials never call Gemini — they are handled by the deterministic hazard guardrail.

**Decision explanation:** After the Decision Engine ranks interventions, Gemini explains why the top-ranked action must be prioritized. The prompt provides specific numbers from the deterministic agents (urgency score, estimated weekly saving, payback months) so the explanation is grounded in real analysis rather than generic advice.

**Executive report narrative:** The Report Agent calls Gemini to write a full executive summary of all agent findings. The prompt embeds guardrails and a list of forbidden phrases (`revolutionary`, `powerful AI`, `real-time intelligence`, `next-generation solution`), plus a requirement to say "simulated smart-campus resource logs."

If `GEMINI_API_KEY` is absent or the API call fails, every call site falls back to a deterministic rule-based string. The application is fully functional without Gemini.

**What Gemini does not do:** All numerical analysis — anomaly detection, severity classification, cost estimates, CO2 calculations, scoring — is deterministic Python code that does not involve Gemini.

---

## 6. Course Concepts Demonstrated

**Multi-agent systems:** Seven agents, each owning exactly one domain. No agent reaches into another's computation. Outputs are structured data passed between agents by the orchestration layer.

**Tool and data lookup:** The Waste-to-Wealth agent performs a knowledge-base lookup (JSON) keyed by material type. Water and energy agents query pandas DataFrames loaded from CSVs. These are analogues of the tool-use pattern in LLM agent frameworks.

**Agent orchestration:** `POST /api/war-room` sequences all agents, passes water and energy results to the Impact Agent, passes all three to the Decision Engine, and passes everything to the Score Agent. The sequence is explicit and auditable.

**State and memory:** Frontend React state holds all agent outputs after a War Room run. Downstream components (Action Plan, Dashboard, Report) read from this shared state. The Waste Agent caches its knowledge base in a module-level variable to avoid reloading on every call.

**Safety guardrails:** `core/guardrails.py` injects disclaimers, applies the hazard guardrail (suppresses financial figures for hazardous materials), and validates input quantities. Every Gemini prompt embeds rules against misleading claims.

**Evaluation and scoring:** RE:GEN Score is a weighted composite across six sub-dimensions (waste recovery potential, water saving potential, energy saving potential, CO2 reduction, urgency reduction, feasibility). Before-action and after-action scores are computed separately to show the projected impact of implementing recommendations.

**Production-grade deployment:** FastAPI with Uvicorn, environment-variable separation for secrets, CORS configuration, Render-ready start command, Vercel-ready frontend build with `VITE_API_URL` override for the production API endpoint.

**Vibe coding workflow:** Built iteratively with Claude Code. Each component was developed agent-by-agent, with AI assistance for boilerplate, debugging, and UI layout. The workflow matched the course's vibe coding emphasis: rapid iteration, human judgment on architecture, AI assistance on implementation.

---

## 7. Safety and Guardrails

RE:GEN AI has explicit safety design for a domain where misleading claims could cause real harm:

**Financial figures:** Exact profit is never claimed. All financial outputs use "estimated" qualifiers. The Waste-to-Wealth agent explicitly states that market prices vary.

**Hazardous waste:** If a waste material exceeds the hazard threshold, the agent suppresses recovery value calculations entirely, shows a clear regulatory warning, and does not call Gemini. The officer is directed to engage a licensed hazardous waste handler.

**Simulated data disclosure:** Every API response includes a `data_notice` field stating that data is simulated for capstone demonstration. This is surfaced in the UI.

**Gemini prompt guardrails:** All Gemini prompts embed a Rules block forbidding specific phrases and requiring qualifiers on financial estimates.

**Disclaimer injection:** Every agent result includes a disclaimer from `core/guardrails.py` stating that RE:GEN AI is a prototype decision-support system and not professional regulatory, financial, or engineering advice.

---

## 8. Evaluation and Scoring

RE:GEN Score uses a weighted formula across six sub-scores:

| Sub-score | Weight | Source |
|---|---|---|
| Waste recovery potential | 20% | Baseline (60) for this prototype |
| Water saving potential | 20% | Derived from wasted liters |
| Energy saving potential | 20% | Derived from wasted kWh |
| CO2 reduction score | 20% | Impact Agent sustainability score |
| Urgency reduction | 10% | Inverse of average urgency across ranked actions |
| Feasibility | 10% | Baseline (82) representing intervention tractability |

Before-action score simulates current campus state by penalizing each sub-score. After-action score represents estimated outcome if all recommendations are implemented.

The Decision Engine uses a separate scoring formula for ranking interventions: urgency (35%), estimated cost saving (30%), environmental impact (25%), feasibility (10%).

---

## 9. Technical Implementation

**Backend:** Python 3.12, FastAPI, Uvicorn. Agent functions are pure Python. Data loading uses Pandas. Gemini calls use the official `google-genai` SDK. Orchestration is explicit FastAPI code — no LLM framework, making the pipeline fully auditable.

**Frontend:** React 19 with Vite 8. Framer Motion for animations. Recharts for data visualization. Lucide React for icons. Dark-only theme. The Agent War Room renders a live SVG node graph showing the Gemini Core connected to all 7 agents, with animated dots traveling along connection paths during analysis.

**Data:** Water and energy data are synthetic CSVs in `backend/data/`. The waste knowledge base is a JSON file with 30 material entries, each containing hazard level, estimated value range, possible products, buyer types, and sustainability notes.

**API:** Primary endpoint `POST /api/war-room` runs the full pipeline. Individual endpoints allow per-agent debugging. `/api/generate-report` assembles the executive brief.

---

## 10. Challenges Faced

**Gemini quota on free tier.** The initial model (`gemini-2.0-flash`) had zero free-tier quota on this project. Switched to `gemini-2.5-flash-lite`, which is within free-tier limits.

**SDK migration.** The `google-generativeai` SDK was deprecated mid-build. Migrated to `google-genai` SDK and rewrote the Gemini client.

**Agent War Room layout.** Getting 7 agent nodes at equal radial distances from a central Gemini Core node, with animated connection lines, in a responsive layout required careful SVG coordinate math and a zero-size anchor div pattern to guarantee pixel-perfect alignment across viewport sizes.

**Guardrail design.** Deciding what Gemini should and should not do required explicit upfront constraints. The final rule: Gemini touches only language and reasoning; all numbers come from deterministic Python.

---

## 11. What I Learned from Vibe Coding

Vibe coding is most effective when the human maintains clear ownership of architecture and constraints, and delegates implementation to AI assistance. When I was clear about what an agent should and should not do (e.g., Gemini never called for hazardous waste, exact profit never claimed), the AI assistance produced clean, consistent code. When the prompt was ambiguous, the output required more review and correction.

The most useful discipline was writing explicit constraints before coding each component — what this agent is responsible for, what it is not, and what its output contract is. That made it easier to verify the AI-generated code and easier to debug when something was wrong.

Visual components require human judgment that AI assistance cannot fully replace: the War Room layout went through many iterations because the desired visual feel was difficult to express in words and required seeing the actual rendered result.

---

## 12. Future Work

- Connect to real IoT sensors via MQTT or REST polling
- Use Google Sheets as a live campus data source instead of CSV files
- Integrate with campus ERP systems for actual utility bill data
- Add real-time recycler market price API for waste valuation
- Expand to ADK / MCP agent framework for more complex orchestration
- Build a mobile dashboard for facilities management teams
- Add multi-campus comparative scoring and time-series trend analysis

---

## 13. Demo Links

- **Live demo:** [To be added after deployment]
- **Demo video:** [To be added after recording]

---

## 14. GitHub

[https://github.com/DivyaShreeS09/regen-ai](https://github.com/DivyaShreeS09/regen-ai)

---

## 15. Deployment

- **Backend (Render):** [To be added after deployment]
- **Frontend (Vercel):** [To be added after deployment]

See [DEPLOYMENT.md](DEPLOYMENT.md) for full step-by-step deployment instructions.
