# RE:GEN AI

> **Multi-agent sustainability intelligence.** Seven specialised AI agents detect hidden resource loss, map waste streams to recovery value, and generate evidence-backed intervention plans — for any campus, hospital, hotel, or industrial facility.

**[Live Demo](https://frontend-two-rho-85.vercel.app)** · **[Backend API](https://regen-ai-backend.onrender.com/health)** · **[Demo Video](https://youtu.be/yrCC-NWa108)** · **[GitHub](https://github.com/DivyaShreeS09/RE-GEN-AI)**

[![CI](https://github.com/DivyaShreeS09/RE-GEN-AI/actions/workflows/ci.yml/badge.svg)](https://github.com/DivyaShreeS09/RE-GEN-AI/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black)
![OpenAI](https://img.shields.io/badge/OpenAI-gpt--4o--mini-412991?style=flat-square&logo=openai&logoColor=white)
![Vercel](https://img.shields.io/badge/Vercel-deployed-000000?style=flat-square&logo=vercel&logoColor=white)
![Render](https://img.shields.io/badge/Render-deployed-46E3B7?style=flat-square&logo=render&logoColor=white)

---

## The Problem

Campuses, hospitals, hotels, and industrial facilities silently lose significant water, energy, and waste value every week — not from a lack of concern, but because the data lives in disconnected systems with no one synthesising it into action.

Night-time pipe leaks run undetected until the bill arrives. Lab equipment left on overnight drains electricity budgets. Recyclable materials accumulate in general waste because no one has mapped their recovery pathway. When an analyst finally collects the data, it takes weeks of manual work to produce even a basic sustainability report — by which time the next month's losses have already compounded.

---

## Solution

RE:GEN AI runs a coordinated network of seven specialised AI agents against your uploaded resource data. Each agent independently detects anomalies in its domain, calculates sustainability impact, and contributes findings to a shared decision pipeline. The Decision Engine ranks interventions by urgency, estimated cost savings, and environmental impact. OpenAI `gpt-4o-mini` adds a narrative reasoning layer — explaining priority decisions in plain language — while all numerical analysis remains fully deterministic and auditable.

**Two modes.** Demo mode runs instantly on bundled sensor data. Upload mode accepts your organisation's CSV, Excel, or manually entered figures for any combination of water, energy, fuel, and waste datasets.

---

## Key Features

| | | |
|---|---|---|
| **Multi-Agent AI** — Seven specialised agents run in parallel, each owning a distinct resource domain | **Three Analysis Levels** — Auto-detected from data resolution; confidence calibrated honestly to what the data supports | **Upload + Demo Modes** — Upload your own CSV/Excel data or explore instantly with bundled sensor logs |
| **Digital Twin** — Facility visualisation at the correct analysis level: resource nodes (L1), zone archetypes (L2), or anomaly-driven map (L3) | **Agent War Room** — Live agent reasoning, findings, skip reasons, and confidence levels — all from real backend data in upload mode | **97-Material Waste KB** — Production knowledge base: 15 categories, 100+ alias normalisations, Indian regulatory compliance notes |
| **RE:GEN Score** — Weighted sustainability health index before and after interventions | **Action Plan + PDF** — Ranked intervention stack with estimated savings, exported via browser print API | **Carbon Calculator** — Scope 1+2 CO₂ formula using IPCC 2006 and BEE India emission factors, shown inline with sources |
| **IsolationForest Anomaly Detection** — scikit-learn ML model replaces static Z-score thresholds; degrades gracefully when data is insufficient | **Peer Benchmarking** — Per-occupant consumption scored against sector reference baselines (hospital, university, hotel, factory) | **Slack Alerting** — Webhook notification dispatched automatically for every critical or high-severity finding |
| **Device Control Simulation** — Execute Now button dispatches mock commands to valve, HVAC, and sensor systems; no false "live" claims | **Run History** — Every analysis persisted to SQLite via SQLAlchemy; full history retrievable per organisation | **OpenAI Integration** — Narrative layer with deterministic fallback; no analysis fails without a key |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Data Intelligence Layer                   │
│   Upload CSV / Excel  ·  Manual Entry  ·  Schema Validation  │
│   Coverage %  ·  Confidence %  ·  Analysis Level (1 – 3)    │
└──────────────────────────┬──────────────────────────────────┘
                           │
           ┌───────────────▼───────────────┐
           │        Multi-Agent Core        │
           │    FastAPI  ·  Python 3.11+    │
           └──┬────┬────┬────┬────┬────┬───┘
              │    │    │    │    │    │
         ┌────▼──┐ │ ┌──▼─┐ │ ┌──▼─┐ │ ┌────▼───┐
         │ Water │ │ │Enrg│ │ │Wste│ │ │ Impact │
         │ Agent │ │ │ Ag │ │ │ Ag │ │ │  Agent │
         └───────┘ │ └────┘ │ └────┘ │ └────────┘
              ┌────▼──┐  ┌──▼─────┐  ┌─────▼──┐
              │Decisn │  │ RE:GEN │  │ Report │
              │Engine │  │ Score  │  │  Agent │
              └───────┘  └────────┘  └────────┘
                           │
           ┌───────────────▼───────────────┐
           │        OpenAI gpt-4o-mini      │
           │   Narrative  ·  Explanations   │
           │  (deterministic KB fallback)   │
           └───────────────┬───────────────┘
                           │
           ┌───────────────▼───────────────┐
           │          React Frontend        │
           │  Dashboard  ·  Digital Twin    │
           │  War Room  ·  Waste-to-Wealth  │
           │  Action Plan  ·  PDF Export    │
           └───────────────────────────────┘
```

---

## Agent Pipeline

```
  Upload / Demo
       │
       ▼
  Schema Validation ──► Analysis Level Detection (L1 / L2 / L3)
       │
       ├──────────────────────────────────────────────┐
       │                                              │
       ▼                                              ▼
  Water Leakage Agent              Energy Optimization Agent
  Waste-to-Wealth Agent            Pollution & Impact Agent
       │                                              │
       └──────────────────┬───────────────────────────┘
                          │
                          ▼
                  Decision Engine Agent
                  (ranks by urgency × impact × cost)
                          │
              ┌───────────┴───────────┐
              │                       │
              ▼                       ▼
       RE:GEN Score Agent       Report Agent
       (before / after)    (executive summary + action plan)
              │                       │
              └───────────┬───────────┘
                          │
                          ▼
               React Frontend
       Dashboard  ·  Digital Twin  ·  War Room
       Waste-to-Wealth  ·  Action Plan  ·  PDF
```

All agents run in parallel. No agent blocks another. A missing dataset produces a graceful skip with an explicit reason — never a crash or a silent failure.

---

## Analysis Levels

The system auto-detects data resolution from the uploaded file and adjusts every output accordingly.

| Level | Data Required | Capabilities | Confidence |
|---|---|---|---|
| **Level 1** — Basic Assessment | Manual entry or monthly totals | Sustainability score, carbon estimation, cost benchmarking | ≤ 55% |
| **Level 2** — Operational Analysis | Daily or weekly meter exports (≥ 3 days) | Trend analysis, consumption hotspots, building comparison | ≤ 72% |
| **Level 3** — Advanced AI Analysis | Hourly data, ≥ 3 days, ≥ 12 hour-slots/day | Full anomaly detection, leak detection, predictive maintenance | 85 – 95% |

When anomaly detection is unavailable, the system explicitly discloses this in the War Room, Digital Twin, every generated report, and the Mission Summary — never silently claiming to detect leaks from monthly aggregates.

---

## Anomaly Detection

Water and energy agents use **IsolationForest** (scikit-learn) to detect anomalous consumption events. The model is trained per-run on the uploaded time series; outliers are flagged with an isolation score, not a static threshold.

When the dataset is too small to train a reliable model (< 10 rows), the agent falls back to a simple percentile-based method and explicitly discloses the degraded detection mode in the War Room reasoning trace. This disclosure propagates to the report and Mission Summary — the system never claims ML-powered detection from a 3-row dataset.

---

## Peer Benchmarking

After each analysis, the platform compares the facility's per-occupant consumption against sector reference baselines:

| Sector | Water (L/person/day) | Energy (kWh/person/day) |
|---|---|---|
| Hospital | 400 | 25 |
| University | 120 | 8 |
| Hotel | 300 | 18 |
| Factory | 80 | 35 |
| Office | 50 | 6 |

The benchmark score shows where the facility sits relative to its peer group — above or below the reference baseline — and feeds into the RE:GEN Score as an additional weighted dimension. Reference values are stored in `backend/core/benchmark_reference.json` and are updatable without code changes.

---

## Slack Alerting

When the Decision Engine produces a finding at `critical` or `high` severity, the platform dispatches a Slack webhook notification containing:

- Severity level and finding summary
- Estimated monthly impact (cost + CO₂)
- Organisation name and analysis timestamp

The Slack webhook URL is configured via the `SLACK_WEBHOOK_URL` environment variable. When unset, alerting is silently skipped — no analysis failure occurs.

---

## Device Control Simulation

The Action Plan's **Execute Now** button dispatches a simulated command to the relevant device control system. All executions are simulated — no real hardware is connected.

Registered actions:

| Action ID | Name | Device Type |
|---|---|---|
| W1 | Install pressure-reduction valve | valve_control |
| W2 | Inspect night-flow pipes | sensor_query |
| E1 | Schedule HVAC/lighting shutdown | building_automation |
| E2 | Smart occupancy-based auto-shutoff | occupancy_sensor |

The response always returns `mode: "mock"` and a simulation note. The API never claims live hardware execution without a real external call.

---

## Waste-to-Wealth Intelligence

The Waste-to-Wealth agent uses a production-quality knowledge base of **97 materials** across 15 categories.

| Field | Description |
|---|---|
| `recommended_pathway` | Best recovery route: composting, recycling, certified handler, energy recovery |
| `estimated_value_range` | Min / max INR per kg — market reference, not a guarantee |
| `co2_savings_kg_per_tonne` | CO₂ avoidance vs landfill (LCA-sourced) |
| `compliance_notes` | Applicable regulation: SWM Rules 2016, E-Waste Rules 2022, HWM Rules 2016 |
| `required_handling` | PPE and segregation requirements |
| `preparation_before_sale` | Step-by-step actions before contacting a buyer |
| `buyer_types` | Kabadiwala, paper mill, CPCB-authorised handler, and others |
| `hazard_level` | none / low / medium / high / critical |

**Alias normalisation** — 100+ variant spellings are normalised before lookup: "PET bottles" → `pet`, "corrugated cardboard" → `cardboard`, "biomedical waste" → `medical waste`. Unknown materials receive inferred category guidance and interim handling advice — never a silent failure.

The material dropdown is generated live from `/analyze/waste/materials`. Additions to the knowledge base surface automatically with no frontend edits required.

---

## Digital Twin

The Digital Twin renders the facility at the correct analysis level — never over-claiming.

- **Level 1** — Five resource nodes (Water, Energy, Fuel, Waste, Carbon) showing actual uploaded totals; zone-level detection explicitly marked unavailable
- **Level 2** — Organisation-type zone archetypes (University, Hospital, Hotel, Factory, etc.) with proportional consumption estimates; no fabricated anomaly colouring
- **Level 3** — Full anomaly-driven zone map; risk levels derived from detected events

Carbon is always calculated automatically:

```
CO₂ = (water_L × 0.001) + (energy_kWh × 0.82) + (fuel_L × emission_factor)
```

Sources: UK Water Industry Research, BEE India, IPCC 2006. The formula breakdown and emission factors are shown inline in the Carbon node tooltip.

---

## Agent War Room

Seven agents are visualised as an animated node network. In upload mode:

- Every agent card shows real backend data: finding, reasoning, recommendation, confidence
- Skipped agents show the exact reason they were skipped and which data would re-activate them
- The Waste-to-Wealth agent shows the top recovery opportunity and estimated value range
- The live reasoning feed is built entirely from agent outputs — no hardcoded demo text can leak through

---

## OpenAI Integration

`gpt-4o-mini` is integrated at three points in the pipeline, each with a deterministic fallback:

| Point | GPT contribution | Fallback |
|---|---|---|
| Waste-to-Wealth | 2-sentence actionable guidance for the sustainability officer | Constructed from KB fields |
| War Room reasoning | Plain-language explanation of each agent's finding and priority | Rule-based template from agent output |
| Executive summary | 3-paragraph report calibrated to analysis level; discloses if anomaly detection was unavailable | Deterministic template using actual numbers |

Every financial figure is prefixed with *estimated*. No exact profit is claimed. No data is invented. If OpenAI is unavailable or rate-limited, the system degrades gracefully — no analysis fails.

---

## Data Flow

Every displayed value originates from a single backend field. No frontend recomputation when the backend has already computed it.

| Display location | Backend source |
|---|---|
| Dashboard total wasted litres | `water_result.total_wasted_liters` |
| Dashboard total wasted kWh | `energy_result.total_wasted_kwh` |
| Dashboard total CO₂ saved | `impact_result.total_co2_saved_kg` |
| Dashboard RE:GEN Score | `regen_score_result.before_score` |
| Waste recovery estimate | `waste_result.total_recovery_max_inr` |
| Carbon formula breakdown | `impact_result` + per-fuel CO₂ sub-fields |
| War Room recommendations | `war_room[].recommendation` from `/analyze/upload` |
| Report executive summary | `report_result.executive_summary` |
| PDF numbers | Same `report_result` object — no re-derivation |
| Peer benchmark score | `benchmark_result.score` from `/analyze/upload` |

---

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React 19, Vite 8, Framer Motion, Lucide React, Tailwind CSS 4 |
| Backend | FastAPI, Python 3.11+, Pydantic v2, pandas, openpyxl, SQLAlchemy |
| AI / ML | OpenAI gpt-4o-mini (with deterministic fallback), scikit-learn IsolationForest |
| Alerting | Slack Incoming Webhooks |
| Deployment | Vercel (frontend) + Render (backend) |
| CI | GitHub Actions — pytest (backend) + oxlint + vitest (frontend) |
| Data | JSON knowledge base (97 materials) + CSV demo datasets + SQLite run history |
| Export | Browser print API (`window.print()`) — formatted print stylesheet, no external library |

---

## CI Pipeline

GitHub Actions runs on every push and pull request to `main`:

```
Backend (pytest)
  ├── Python 3.12
  ├── pip install -r backend/requirements.txt
  └── pytest backend/tests/ -v   (124 tests)

Frontend (oxlint + vitest)
  ├── Node 22
  ├── npm install
  ├── npm run lint   (oxlint)
  └── npm run test   (vitest, 16 tests)
```

Both jobs must pass before a PR can merge.

---

## Deployment

**Frontend** — Vercel (auto-deployed from `main`)  
**Backend** — Render (FastAPI, Python 3.11, auto-deployed)

```bash
# Local development
cd backend && pip install -r requirements.txt && uvicorn main:app --reload
cd frontend && npm install && npm run dev
```

Environment variables:

```
# backend/.env
OPENAI_API_KEY=sk-...            # Optional — system degrades gracefully without it
SLACK_WEBHOOK_URL=https://...    # Optional — alerting silently skipped when unset

# Vercel project settings
VITE_API_URL=https://regen-ai-backend.onrender.com
```

> **Cold start** — Render's free tier sleeps after 15 minutes of inactivity. The first request after a sleep takes 30 – 90 seconds. The UI shows a specific message during this wait.

---

## Screenshots

### Landing Hero

![Landing Hero](docs/screenshots/01-landing.png)

*Entry point — live demo and upload mode options, with mission status and RE:GEN Score overview.*

---

### Upload Center

![Upload Center](docs/screenshots/03-upload-center.png)

*Upload CSV, Excel, or manually enter water, energy, fuel, and waste data — every dataset is optional.*

---

### Command Center Dashboard

![Command Center Dashboard](docs/screenshots/05-dashboard.png)

*Real-time key metrics: total wasted litres, kWh lost, CO₂ avoided, and RE:GEN Score across all resource domains.*

---

### Digital Twin

![Digital Twin](docs/screenshots/06-digital-twin.png)

*Facility visualised at the correct analysis level — resource nodes (L1), zone archetypes (L2), or anomaly-driven map (L3).*

---

### Agent War Room

![Agent War Room](docs/screenshots/07-war-room.png)

*Seven autonomous agents — live reasoning, findings, confidence levels, and skip reasons all sourced from real backend data.*

---

### Waste-to-Wealth

![Waste-to-Wealth](docs/screenshots/08-waste-to-wealth.png)

*Recovery pathway analysis across 97 materials — estimated value range, CO₂ savings, and regulatory compliance guidance.*

---

### Sustainability Action Plan

![Sustainability Action Plan](docs/screenshots/09-action-plan.png)

*Ranked intervention stack with estimated savings, export to PDF via browser print API.*

---

## Formula Verification

| Calculation | Formula | Source |
|---|---|---|
| Water CO₂ | `litres × 0.001 kg/L` | UK Water Industry Research |
| Energy CO₂ | `kWh × 0.82 kg/kWh` | BEE India grid emission factor |
| Diesel CO₂ | `litres × 2.68 kg/L` | IPCC 2006 |
| Petrol CO₂ | `litres × 2.31 kg/L` | IPCC 2006 |
| LPG CO₂ | `litres × 1.51 kg/L` | IPCC 2006 |
| Total Carbon | `water_co2 + energy_co2 + fuel_co2` | Scope 1 + 2 |
| RE:GEN Score | Weighted composite of water / energy / carbon / waste / coverage / benchmark | Internal |
| Recovery value | `quantity_kg × value_range_per_kg` | KB benchmark rates |

---

*RE:GEN AI is a decision-support prototype. Not professional regulatory, financial, or engineering advice.*
