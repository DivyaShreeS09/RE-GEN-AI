# RE:GEN AI â€” Autonomous Sustainability Command Center

> A multi-agent decision-support prototype that detects hidden resource loss in simulated
> smart-campus sensor logs, maps waste-to-value pathways, and generates agent-prioritized
> sustainability interventions.

<p align="center">
  <img src="frontend/src/assets/hero.png" alt="RE:GEN AI Dashboard" width="900" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black" />
  <img src="https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/Tailwind_CSS-v4-38B2AC?logo=tailwindcss&logoColor=white" />
  <img src="https://img.shields.io/badge/Recharts-3.9-8884D8" />
  <img src="https://img.shields.io/badge/Google_AI_Agents-Capstone-4285F4?logo=google&logoColor=white" />
  <img src="https://img.shields.io/badge/License-MIT-22c55e" />
</p>

---

## Live Demo

| Resource | Link |
|----------|------|
| GitHub Repository | *(add link)* |
| Demo Video | *(add link)* |
| Kaggle Notebook | *(add link)* |

---

## The Problem

University campuses waste water, energy, and recoverable materials every day â€” silently,
at 3 AM, in unused seminar halls and leaking pipes. No single dashboard exposes all three
domains at once. No system tells administrators *which problem to fix first* and *why*.

**RE:GEN AI sends agents, not alerts.**

---

## What It Does

Seven specialized agents analyze simulated 7-day campus sensor logs across three domains â€”
water, energy, and solid waste â€” then collaborate through a structured pipeline to deliver:

- Ranked interventions (by urgency, cost savings, and environmental impact)
- A composite **RE:GEN Score** (0â€“100) with before and after projections
- A 4-tier executive **Action Plan** (immediate â†’ 7-day â†’ 30-day â†’ long-term)
- A full **Agent War Room** showing each agent's live status and reasoning

```
Water Agent â”€â”€â”
Energy Agent â”€â”€â”¼â”€â”€â–º Impact Agent â”€â”€â–º Decision Engine â”€â”€â–º Score Agent â”€â”€â–º Report Agent
Waste Agent â”€â”€â”˜
```

All coordination happens in `main.py`. Agents communicate through typed Python dicts â€”
no message bus, no shared state, no machine learning. Every decision is rule-based,
deterministic, and fully traced.

---

## How the Scan Works

Clicking **"Launch Campus Intelligence Scan"** triggers five parallel API calls via
`Promise.all`. While the calls run, a full-screen **Mission Control overlay** advances
through 8 animated steps at 700 ms intervals. Whichever finishes first â€” the API or
the timers â€” drives the transition. The overlay holds for 2 seconds on "complete", then
dissolves into the dashboard.

```
Browser            FastAPI                       Agents
   â”‚                  â”‚                             â”‚
   â”œâ”€â”€â”€ GET /dashboard/summary â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–º  Water Agent
   â”œâ”€â”€â”€ GET /analyze/water â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–º  Energy Agent
   â”œâ”€â”€â”€ GET /analyze/energy â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–º  Impact Agent
   â”œâ”€â”€â”€ GET /agent-war-room â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–º  Decision Engine
   â””â”€â”€â”€ POST /generate/action-plan â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–º   Score Agent â†’ Report Agent
```

Five endpoints return seven agents' worth of data. Results are distributed to 14
React sections: Dashboard, Digital Twin, Waste Analyzer, Water Panel, Energy Panel,
Resource Loss Heatmap, Impact Projection, Intervention Simulator, Achievements,
Agent War Room, Action Plan, Why This Matters, Capstone Mapping.

---

## Simulated Data

All sensor data is generated for January 15â€“21, 2024. No live IoT systems are connected.

| Dataset | Rows | Locations / Zones | Anomalies |
|---------|------|-------------------|-----------|
| `water_usage.csv` | 168 | Campus Main, Block-B Hostel, Lab Block | Night-flow bursts Jan 16 (Hostel), Jan 19 (Lab Block) |
| `energy_usage.csv` | 168 | Admin Block, Seminar Hall, Computer Lab, Campus | After-hours AC Jan 16 (Seminar), Jan 19 (Computer Lab) |
| `waste_knowledge_base.json` | 30 materials | â€” | e-waste, battery waste, medical waste flagged critical |

The data is intentionally designed to demonstrate multi-severity outcomes: Lab Block water
anomaly at CRITICAL (>1,000 L), energy waste at HIGH (>100 kWh), multiple buildings
at different risk levels for the Digital Twin heatmap.

---

## Features

### Waste Intelligence
- **30-material knowledge base** â€” Agricultural, Organic, Industrial, Metal, Plastic, Glass, Hazardous
- **Three-pathway comparison** â€” Sell raw (1.0Ã—), Process into product (1.8Ã—), Partner with recycler (1.3Ã—)
- **Hazard guardrails** â€” e-waste, battery waste, and medical waste trigger CPCB compliance notice
  and suppress all financial estimates
- **Hidden value score** â€” Each material rated 0â€“100 for recovery potential
- **7-step reasoning trace** â€” Auditable step-by-step explanation of every recommendation

### Water Intelligence
- **Night-flow anomaly detection** â€” Scans hours 0â€“5 against a computed baseline; flags readings
  exceeding 4Ã— normal as leakage events
- **Event grouping** â€” Anomalies grouped by date and location with duration and wasted volume
- **Cost + carbon** â€” â‚¹0.05/L, 0.001 kg COâ‚‚/L
- **Severity tiers** â€” critical (>1,000 L) Â· high (>500 L) Â· medium (>200 L) Â· low (>50 L) Â· none

### Energy Intelligence
- **After-hours waste detection** â€” After-hours window: hours 22â€“23 (10â€“11 PM) and 0â€“5 (midnightâ€“6 AM)
- **Zone-level grouping** â€” Events grouped by date and zone with equipment type
- **India grid COâ‚‚** â€” 0.82 kg/kWh (India grid emission factor), â‚¹8.00/kWh tariff
- **Severity tiers** â€” critical (>200 kWh) Â· high (>100) Â· medium (>50) Â· low (>10) Â· none

### Cross-Domain Impact
- **COâ‚‚ aggregation** â€” Water + energy COâ‚‚ combined into total kg and tonne values
- **Tree equivalence** â€” `(total_COâ‚‚ / 100) Ã— 4.5` trees
- **SDG alignment** â€” SDG 6, 7, 12, 13 â€” each with a contribution statement
- **Financial benefit** â€” `waterÃ—â‚¹0.05 + energyÃ—â‚¹8 + waste_valueÃ—0.60`

### Scoring & Prioritization
- **RE:GEN Score** â€” 6-dimension weighted composite, clamped [0, 100]:
  ```
  wasteÃ—0.20 + waterÃ—0.20 + energyÃ—0.20 + COâ‚‚Ã—0.15 + urgencyÃ—0.15 + feasibilityÃ—0.10
  ```
- **Before vs. After** â€” Before-score applies fixed offsets (15â€“25 pts) to show current degraded
  state; after-score reflects full intervention impact
- **Decision Engine** â€” Ranks actions by:
  `urgencyÃ—0.35 + min(cost/1000, 30)Ã—0.30 + env_impactÃ—0.25 + feasibilityÃ—0.10`

### Dashboard & UI
- **Mission Control overlay** â€” 8-step cinematic scan sequence, progress bar 0â†’100%, parallel
  to real API calls; dissolves 2 s after completion
- **RE:GEN Score gauges** â€” Animated SVG arc rings for before and after scores (2 s ease-out)
- **Digital Twin Campus** â€” Clickable 6-building map: Lab Block, Hostel, Seminar Hall,
  Computer Lab, Canteen, Admin Block â€” each with per-zone diagnostic detail
- **Resource Loss Heatmap** â€” Zone Ã— domain risk grid with `heatmap-{level}` color classes
- **30-Day Impact Projection** â€” Extrapolates wasted volumes (water: 85% fix rate, energy: 80%)
- **Intervention Simulator** â€” 6 toggles update score, savings, COâ‚‚, and financial gain instantly
  (frontend arithmetic only â€” no backend calls)
- **Sustainability Achievements** â€” 6 badge cards unlock dynamically from scan results
- **Agent War Room** â€” Live collaboration feed appends messages every 2.8 s via `setInterval`

---

## Screenshots

| Section | Screenshot |
|---------|-----------|
| Hero & Scan | *(add screenshot)* |
| Mission Control Overlay | *(add screenshot)* |
| Command Center Dashboard | *(add screenshot)* |
| Waste Analyzer â€” Safe material | *(add screenshot)* |
| Waste Analyzer â€” Hazard guardrail | *(add screenshot)* |
| Water Loss Panel | *(add screenshot)* |
| Energy Panel | *(add screenshot)* |
| Digital Twin Campus | *(add screenshot)* |
| Resource Loss Heatmap | *(add screenshot)* |
| Intervention Simulator | *(add screenshot)* |
| Sustainability Achievements | *(add screenshot)* |
| Agent War Room | *(add screenshot)* |
| Action Plan | *(add screenshot)* |

---

## Tech Stack

### Backend

| | Technology | Version |
|-|-----------|---------|
| Framework | FastAPI | 0.111.0 |
| Server | Uvicorn (standard) | 0.29.0 |
| Data | Pandas | 2.2.2 |
| Validation | Pydantic | 2.7.1 |
| Language | Python | 3.11+ |

### Frontend

| | Technology | Version |
|-|-----------|---------|
| UI | React | 19.2.7 |
| Build | Vite | 8.1.0 |
| Styling | Tailwind CSS v4 | 4.3.1 |
| Charts | Recharts | 3.9.0 |
| Icons | Lucide React | 1.21.0 |
| HTTP | Axios | 1.18.1 |

### Data

| File | Rows | Description |
|------|------|-------------|
| `water_usage.csv` | 168 | Hourly water consumption, Jan 15â€“21 2024, by location |
| `energy_usage.csv` | 168 | Hourly energy usage by zone and equipment type |
| `waste_knowledge_base.json` | 30 materials | Value ranges, hazard levels, recovery pathways |

---

## Quick Start

**Requirements:** Python 3.11+, Node.js 18+, npm 9+

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

```bash
# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Open: **`http://localhost:5173`**
API docs (Swagger UI): **`http://localhost:8000/docs`**

No environment variables. No external services. Runs entirely locally.

---

## API Endpoints

| Method | Endpoint | Agent | Description |
|--------|----------|-------|-------------|
| `GET` | `/health` | â€” | System status + prototype disclaimer |
| `POST` | `/analyze/waste` | Waste-to-Wealth | Material lookup, hazard check, pathway scoring |
| `GET` | `/analyze/water` | Water Leakage | Night-flow anomaly detection on 7-day CSV |
| `GET` | `/analyze/energy` | Energy Optimization | After-hours waste detection on 7-day CSV |
| `GET` | `/dashboard/summary` | All 6 | Full pipeline â†’ compact summary |
| `GET` | `/agent-war-room` | All 7 | Agent status panel with findings + confidence |
| `POST` | `/generate/action-plan` | All 7 | Full pipeline â†’ unabridged report + traces |

All responses include a `disclaimer` and `data_notice` field. Full request/response
examples in [`docs/API.md`](docs/API.md).

---

## Project Structure

```
REGEN AI/
â”œâ”€â”€ backend/
â”‚   â”œâ”€â”€ main.py              # 7 FastAPI routes, CORS, Pydantic models
â”‚   â”œâ”€â”€ requirements.txt     # 5 packages: fastapi, uvicorn, pandas, pydantic, python-multipart
â”‚   â”œâ”€â”€ agents/              # 7 agent modules (one file per agent)
â”‚   â”œâ”€â”€ core/
â”‚   â”‚   â”œâ”€â”€ scoring.py       # RE:GEN Score formula + severity_label()
â”‚   â”‚   â”œâ”€â”€ guardrails.py    # Hazard suppression, quantity validation, disclaimer constants
â”‚   â”‚   â””â”€â”€ simulation.py    # CSV and JSON loaders (pandas)
â”‚   â””â”€â”€ data/
â”‚       â”œâ”€â”€ water_usage.csv
â”‚       â”œâ”€â”€ energy_usage.csv
â”‚       â””â”€â”€ waste_knowledge_base.json
â””â”€â”€ frontend/
    â”œâ”€â”€ vite.config.js       # Tailwind v4 plugin; /api proxy â†’ localhost:8000
    â”œâ”€â”€ package.json
    â””â”€â”€ src/
        â”œâ”€â”€ App.jsx           # Scan state, Mission Control overlay, 14 sections
        â”œâ”€â”€ api.js            # 7 Axios functions (baseURL: /api)
        â”œâ”€â”€ index.css         # Glassmorphism system, 14 keyframe animations
        â””â”€â”€ components/       # 15 components
```

---

## Guardrails

- **Hazardous materials** â€” `e-waste`, `battery waste`, `medical waste` trigger a mandatory
  CPCB safety notice and suppress all financial estimates (`estimated_recovery: null`)
- **Quantity bounds** â€” `quantity_kg` must be `0 < qty â‰¤ 100,000`; HTTP 400 returned otherwise
- **Disclaimer injection** â€” Every API response includes a prototype disclaimer and
  simulated-data notice â€” this cannot be disabled
- **Forbidden outputs** â€” Agents never claim exact profit, real-time data, or live sensor readings

Full details in [`docs/SECURITY.md`](docs/SECURITY.md).

---

## Documentation

| Document | Contents |
|----------|---------|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | System design, folder structure, component map, scoring formula |
| [`docs/AGENTS.md`](docs/AGENTS.md) | All 7 agents â€” inputs, process, outputs, thresholds, constants |
| [`docs/API.md`](docs/API.md) | All 7 endpoints with request/response JSON examples |
| [`docs/FLOWCHARTS.md`](docs/FLOWCHARTS.md) | 5 Mermaid diagrams: system, sequence, data flow, request flow, components |
| [`docs/SECURITY.md`](docs/SECURITY.md) | Guardrails, disclaimer injection, validation, production gaps |
| [`docs/CAPSTONE.md`](docs/CAPSTONE.md) | Google AI Agents concept mapping, evaluation test cases, SDG alignment |
| [`docs/DEMO.md`](docs/DEMO.md) | Step-by-step demo walkthrough, toggle guide, screenshots table |
| [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) | Local dev, production build, cloud platforms, Docker |
| [`docs/FUTURE_ROADMAP.md`](docs/FUTURE_ROADMAP.md) | Roadmap, known limitations, contributing guide |

---

## Agent Summary

| # | Agent | File | Confidence | Key Output |
|---|-------|------|-----------|-----------|
| 1 | Waste-to-Wealth | `waste_agent.py` | 0.92 | Recovery pathway, hidden value score, hazard check |
| 2 | Water Leakage | `water_agent.py` | 0.89 | Anomaly events, wasted litres, severity (5 tiers) |
| 3 | Energy Optimization | `energy_agent.py` | 0.91 | After-hours kWh waste, COâ‚‚ at 0.82 kg/kWh |
| 4 | Pollution & Impact | `impact_agent.py` | 0.87 | Total COâ‚‚, trees equivalent, SDG alignment |
| 5 | Decision Engine | `decision_agent.py` | 0.90 | Ranked actions by urgency Ã— cost Ã— env Ã— feasibility |
| 6 | RE:GEN Score | `regen_score_agent.py` | 0.88 | Before/after score, 6 sub-dimension breakdown |
| 7 | Report | `report_agent.py` | 0.95 | Executive summary, 4-tier action plan, all traces |

Each agent returns a `reasoning_trace` array (5â€“8 steps) documenting how it reached its
conclusion. Traces are surfaced in the Waste Analyzer panel, the War Room, and the Action
Plan JSON export. See [`docs/AGENTS.md`](docs/AGENTS.md) for full input/output specs.

---

## Capstone Concept Coverage

| Concept | How RE:GEN AI Implements It |
|---------|----------------------------|
| Multi-Agent System | 7 agents, each in its own module, with distinct inputs and outputs |
| Tools & Data Lookup | CSV + JSON retrieval via `simulation.py`; waste agent uses KB as lookup tool |
| State & Memory | Agent dicts chained through `main.py`; Report Agent aggregates full context |
| Guardrails & Safety | `core/guardrails.py` â€” hazard suppression + mandatory disclaimer |
| Evaluation & Scoring | 6-dimension weighted score, per-agent confidence (0.87â€“0.95), priority scoring |
| Production-Grade Structure | FastAPI + Pydantic + CORS + React + Vite + Axios proxy |

Full mapping with codebase evidence in [`docs/CAPSTONE.md`](docs/CAPSTONE.md).

---

## Known Limitations

| Limitation | Detail |
|------------|--------|
| Simulated data | Static CSV (Jan 15â€“21, 2024). No live IoT sensors. |
| Rule-based only | No ML. All decisions are deterministic threshold rules. |
| No authentication | All endpoints open. Do not expose publicly without auth. |
| Estimates only | All INR and COâ‚‚ values use fixed constants, not live pricing. |
| Fixed waste KB | 30 hardcoded materials; unknown types return suggestions, not analysis. |

Full limitations and roadmap in [`docs/FUTURE_ROADMAP.md`](docs/FUTURE_ROADMAP.md).

---

## Contributing

1. Fork and create a feature branch: `git checkout -b feature/your-feature`
2. Backend changes in `backend/`; frontend changes in `frontend/`
3. New agents: add a file to `backend/agents/` and wire it into `main.py`
4. Do not weaken guardrail logic in `core/guardrails.py`
5. All API responses must include `disclaimer` and `data_notice`
6. Run `cd frontend && npm run build` before opening a PR

---

## License

MIT â€” see [LICENSE](LICENSE).

---

> **Disclaimer:** RE:GEN AI is a prototype decision-support system. All sensor data is
> simulated (January 15â€“21, 2024). No live IoT systems are connected. All cost, COâ‚‚,
> and recovery values are estimates â€” not professional regulatory, financial, or
> engineering advice.

