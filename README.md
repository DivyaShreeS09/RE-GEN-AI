# RE:GEN AI — Multi-Agent Sustainability Intelligence Platform

> Autonomous AI agents that detect hidden resource loss, map waste to recovery value, and generate evidence-backed sustainability action plans for any organisation.

**Live demo:** [https://frontend-two-rho-85.vercel.app](https://frontend-two-rho-85.vercel.app)  
**Backend API:** [https://regen-ai-backend.onrender.com/health](https://regen-ai-backend.onrender.com/health)  
**GitHub:** [https://github.com/DivyaShreeS09/RE-GEN-AI](https://github.com/DivyaShreeS09/RE-GEN-AI)  
**Demo video:** [https://youtu.be/pLlweeJ1piU](https://youtu.be/pLlweeJ1piU)

---

## The Problem

Campuses, hospitals, hotels, and industrial facilities silently lose significant water, energy, and waste value every week — not because of a lack of concern, but because the data lives in disconnected systems with no one synthesising it into action.

Night-time pipe leaks run undetected until a bill arrives. Lab equipment left on overnight drains electricity budgets. Recyclable materials accumulate in general waste because no one has mapped their recovery pathway. And when an analyst finally collects the data, it takes weeks of manual work to produce even a basic sustainability report.

RE:GEN AI closes this gap — for any organisation, not just campuses.

---

## Solution

RE:GEN AI runs a coordinated network of seven specialised AI agents against your uploaded resource data (or bundled demo data). Each agent independently detects anomalies in its domain, calculates sustainability impact, and contributes findings to a shared decision pipeline. The Decision Engine ranks interventions by urgency, estimated cost savings, and environmental impact. OpenAI `gpt-4o-mini` adds a narrative reasoning layer — explaining priority decisions in plain language — while all numerical analysis stays fully deterministic.

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                  Data Intelligence Layer                  │
│     Upload CSV/Excel · Manual Entry · Schema Validation   │
│     Coverage % · Confidence % · Analysis Level (1–3)     │
└──────────────────────┬───────────────────────────────────┘
                       │
        ┌──────────────▼──────────────┐
        │      Multi-Agent Core       │
        │  (FastAPI · Python 3.11+)   │
        └──┬───┬───┬───┬───┬───┬─────┘
           │   │   │   │   │   │
    ┌──────▼─┐ │ ┌─▼──┐│ ┌─▼──┐│ ┌────▼───┐
    │ Water  │ │ │Enrg││ │Wste││ │ Impact │
    │ Agent  │ │ │ Ag ││ │ Ag ││ │ Agent  │
    └────────┘ │ └────┘│ └────┘│ └────────┘
        ┌──────▼─┐   ┌──▼────┐   ┌────▼───┐
        │Decision│   │RE:GEN │   │Report  │
        │Engine  │   │Score  │   │Agent   │
        └────────┘   └───────┘   └────────┘
                       │
        ┌──────────────▼──────────────┐
        │       OpenAI gpt-4o-mini    │
        │  Narrative · Explanations   │
        │  (always deterministic KB   │
        │   fallback if unavailable)  │
        └──────────────┬──────────────┘
                       │
        ┌──────────────▼──────────────┐
        │        React Frontend       │
        │  Digital Twin · War Room    │
        │  Waste-to-Wealth · Reports  │
        │  Action Plan · PDF Export   │
        └─────────────────────────────┘
```

---

## Agent Flow

| Agent | Input | Output |
|---|---|---|
| Water Leakage Agent | Hourly water usage logs | Anomaly events, wasted litres, severity, cost estimate |
| Energy Optimization Agent | Hourly energy logs | After-hours waste events, kWh wasted, severity |
| Waste-to-Wealth Agent | Waste type + quantity | Recovery pathway, estimated value, CO₂ savings, compliance notes |
| Pollution & Impact Agent | Water + energy + fuel data | Total CO₂, SDG alignment, annual projections |
| Decision Engine Agent | All agent outputs | Ranked interventions by urgency × impact × cost |
| RE:GEN Score Agent | All agent outputs | Sustainability health index before/after intervention |
| Report Agent | All agent outputs | Executive summary + action plan + PDF export |

**All agents run in parallel. No agent blocks another. Missing data causes a graceful skip, not a failure.**

---

## OpenAI Integration

RE:GEN AI integrates `gpt-4o-mini` at three points in the pipeline, all with deterministic fallbacks:

1. **Waste-to-Wealth recommendations** — Given the material, quantity, recovery pathway, and estimated value range, GPT writes 2 actionable sentences for the sustainability officer. Fallback: constructed from KB fields.

2. **AI reasoning in War Room** — Each agent's finding, reasoning, and recommendation is surfaced live. In upload mode, these are populated from actual backend data — never from hardcoded demo text.

3. **Executive summary in Report Agent** — GPT writes a 3-paragraph summary calibrated to the analysis level (Level 1/2/3), explicitly disclosing if anomaly detection was unavailable. Fallback: deterministic template using actual numbers.

**Rule**: Every financial figure is prefixed with "estimated". No exact profit is claimed. No data is invented. If OpenAI is unavailable, the system degrades gracefully to rule-based outputs identical in structure.

---

## Analysis Levels

The system auto-detects data resolution and adjusts confidence accordingly:

| Level | Data Required | Features | Confidence |
|---|---|---|---|
| Level 1 — Basic Assessment | Manual entry or monthly totals | Sustainability score, carbon estimation, cost benchmarking | ≤55% |
| Level 2 — Operational Analysis | Daily/weekly meter exports | Trend analysis, building comparison, consumption hotspots | ≤72% |
| Level 3 — Advanced AI Analysis | Hourly data, ≥3 days, ≥12 slots/day | Full anomaly detection, leak detection, predictive maintenance | 85–95% |

When anomaly detection is unavailable, the system explicitly discloses this in the War Room, Digital Twin, and every generated report — never silently pretending to detect leaks from monthly aggregates.

---

## Waste-to-Wealth Knowledge Base

The Waste-to-Wealth agent uses a production-quality knowledge base of **97 materials** across 15 categories. Every material entry includes:

| Field | Description |
|---|---|
| `category` | Material category (Organic, Plastic, Metal, etc.) |
| `recommended_pathway` | Best recovery route (composting, recycling, certified handler, etc.) |
| `estimated_value_range` | Min/max INR per kg (market reference, not a guarantee) |
| `co2_savings_kg_per_tonne` | CO₂ avoidance vs landfill disposal (LCA-sourced) |
| `compliance_notes` | Applicable Indian regulation (SWM Rules 2016, E-Waste Rules 2022, HWM Rules 2016, etc.) |
| `required_handling` | PPE and segregation requirements |
| `preparation_before_sale` | Step-by-step action before contacting buyer |
| `collection_frequency` | Operational guidance for pickup scheduling |
| `buyer_types` | Types of buyers (kabadiwala, paper mill, CPCB-authorised handler, etc.) |
| `knowledge_source` | Regulatory citation or industry body |
| `hazard_level` | none / low / medium / high / critical |

**Alias normalization**: 100+ common variant spellings are normalized before lookup (e.g. "PET bottles" → `pet`, "corrugated cardboard" → `cardboard`, "biomedical waste" → `medical waste`). Unknown materials receive inferred category guidance and interim handling advice — never a silent failure.

**Dropdown is dynamically generated** from the live knowledge base at `/analyze/waste/materials`. Future additions to the KB automatically appear without any frontend edits.

---

## Digital Twin

The Digital Twin visualizes the facility at the correct analysis level:

- **Level 1**: Five resource nodes (Water, Energy, Fuel, Waste, Carbon) — each showing actual uploaded totals with clear disclosure that zone-level detection is unavailable
- **Level 2**: Org-type zone archetypes (University, Hospital, Hotel, Factory, etc.) with proportional consumption estimates — no fake anomaly colours
- **Level 3**: Full anomaly-driven zone map — risk levels derived from actual detected events

Carbon is always automatically calculated: `CO₂ = (water_liters × 0.001) + (energy_kwh × 0.82) + (fuel_liters × emission_factor)`, using IPCC 2006 and BEE India emission factors. The formula breakdown is shown in the Carbon node tooltip.

---

## War Room

Seven agents are visualised as an animated node network. In upload mode:

- Every agent card shows actual backend data (finding, reasoning, recommendation, confidence)
- Skipped agents show the exact reason they were skipped and what data would activate them
- The Waste-to-Wealth agent shows the top recovery opportunity and estimated value
- The live reasoning feed is built from real agent outputs — no hardcoded demo text leaks in

---

## Data Flow

Every displayed value originates from a single backend field. No frontend recomputation when the backend already computed it.

| Display location | Backend source |
|---|---|
| Dashboard total_wasted_liters | `water_result.total_wasted_liters` |
| Dashboard total_wasted_kwh | `energy_result.total_wasted_kwh` |
| Dashboard total_co2_saved_kg | `impact_result.total_co2_saved_kg` |
| Dashboard regen_score | `regen_score_result.before_score` |
| Waste recovery estimate | `waste_result.total_recovery_max_inr` |
| Carbon formula breakdown | `impact_result` + `water/energy/fuel` CO₂ sub-fields |
| War Room recommendations | `war_room[].recommendation` from `/analyze/upload` |
| Report executive summary | `report_result.executive_summary` |
| PDF numbers | Same `report_result` object — no re-derivation |

---

## Deployment

**Frontend** — Vercel (auto-deployed from `main` branch)  
**Backend** — Render (FastAPI, Python 3.11, auto-deployed)

```bash
# Local development
cd backend && pip install -r requirements.txt && uvicorn main:app --reload
cd frontend && npm install && npm run dev
```

Environment variables:
```
OPENAI_API_KEY=sk-...          # Optional — system degrades gracefully without it
VITE_API_URL=http://localhost:8000  # Frontend .env for local dev
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 19, Vite 8, Framer Motion, Lucide React, Tailwind CSS 4 |
| Backend | FastAPI, Python 3.11+, Pydantic v2, pandas, openpyxl |
| AI Layer | OpenAI gpt-4o-mini (with deterministic fallback) |
| Deployment | Vercel (frontend) + Render (backend) |
| Data | JSON knowledge base (97 materials) + CSV demo datasets |
| Export | Browser print API (`window.print()`) — formatted print stylesheet, no external library |

---

## Hackathon Context — ChatGPT Codex Hackathon

RE:GEN AI was developed and refined with AI-assisted engineering throughout the build cycle. Key highlights relevant to the judging criteria:

### Technical Execution
- Seven specialised agents with typed interfaces, deterministic calculations, and explicit confidence levels
- Three-tier analysis level system that honestly discloses data resolution limitations
- Production-quality knowledge base with 97 materials, 100+ alias normalizations, and regulatory citations
- Zero data fabrication — every displayed number traces to a single backend field
- Graceful degradation: missing OpenAI API key, missing datasets, and unknown materials are all handled without crashes

### Agentic Development
- Each agent is independently callable with typed inputs and outputs
- The Decision Engine consumes all agent outputs and produces a ranked intervention stack
- The Report Agent synthesises findings across all agents into a professional executive summary
- The War Room visualises live agent reasoning, skip reasons, and confidence levels
- AI enhancement is layered on top of deterministic KB — never replacing it

### Impact
- Quantifiable output: litres saved, kWh recovered, INR recovery estimated, CO₂ avoided
- SDG alignment: SDG 6 (Clean Water), SDG 7 (Affordable Energy), SDG 12 (Responsible Consumption), SDG 13 (Climate Action)
- Applicable to any organisation type (University, Hospital, Hotel, Factory, Airport, Mall, Office)
- Waste-to-Wealth maps 97 material streams to recovery value and compliance guidance

### Originality
- Analysis level system honestly calibrates AI confidence to data resolution — rare in sustainability tools
- Alias normalization before KB lookup prevents false "unknown" classifications for variant spellings
- War Room never shows hardcoded demo text in upload mode — all reasoning is derived from real agent outputs
- Carbon formula is transparent and shown inline: components, emission factors, and regulatory source

### Completeness
- Two modes: Demo (instant) and Upload (CSV/Excel/manual for any combination of datasets)
- End-to-end: Upload → Validation → Analysis → War Room → Digital Twin → Report → PDF export
- Mobile responsive, keyboard navigable, and theme-aware (light/dark)
- All advanced modules that require higher-resolution data are explicitly disclosed as skipped

---

## Formulae (Verified)

| Calculation | Formula | Source |
|---|---|---|
| Water CO₂ | `litres × 0.001 kg/L` | UK Water Industry Research |
| Energy CO₂ | `kWh × 0.82 kg/kWh` | BEE India grid emission factor |
| Diesel CO₂ | `litres × 2.68 kg/L` | IPCC 2006 |
| Petrol CO₂ | `litres × 2.31 kg/L` | IPCC 2006 |
| LPG CO₂ | `litres × 1.51 kg/L` | IPCC 2006 |
| Total Carbon | `water_co2 + energy_co2 + fuel_co2` | Scope 1+2 |
| RE:GEN Score | Weighted composite of water/energy/carbon/waste/coverage | Internal |
| Recovery value | `quantity_kg × value_range_per_kg` | KB benchmark rates |

---

## Known Limitations

- **Demo mode**: Uses bundled simulated sensor logs (January 15–21, 2024). Not real data.
- **Anomaly detection**: Requires hourly time-series data with ≥3 days and ≥12 slots/day. Monthly totals produce Level 1 only.
- **Recovery value estimates**: Knowledge base benchmark rates. Actual market prices vary by location, grade, and season.
- **Carbon scope**: Scope 1 and 2 only. Scope 3 (supply chain, business travel) not included.
- **OpenAI dependency**: If the API key is absent or rate-limited, the system falls back to deterministic outputs. No analysis fails.
- **PDF generation**: Client-side via browser print API. Uses the same `report_result` object — no re-derivation of numbers. Requires pop-ups to be allowed in the browser.

---

## Contributing

Issues and PRs welcome. All pull requests must:
- Preserve the single-source-of-truth data flow (no frontend recomputation of backend values)
- Never invent data or silently fall back to demo values in upload mode
- Maintain the deterministic KB as the ground truth for waste analysis

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

*RE:GEN AI is a decision-support prototype. It is not professional regulatory, financial, or engineering advice. Designed for future integration with live IoT and building management systems.*
