# Architecture

## System Overview

RE:GEN AI is a full-stack multi-agent application: a FastAPI backend runs seven independent
agents against simulated campus sensor data; a React 19 frontend presents results across
14 interactive sections.

```
Browser ──► React 19 (Vite 8)
              │  axios /api/* proxy
              ▼
         FastAPI 0.111  ──► 7 Agents ──► 3 Data Files
```

## Folder Structure

```
REGEN AI/
├── backend/
│   ├── main.py                    # 7 FastAPI routes, CORS, Pydantic models
│   ├── requirements.txt           # 5 Python packages
│   ├── agents/
│   │   ├── waste_agent.py         # Knowledge base lookup, hazard guardrail
│   │   ├── water_agent.py         # Night-flow anomaly detection
│   │   ├── energy_agent.py        # After-hours consumption analysis
│   │   ├── impact_agent.py        # CO₂ aggregation, SDG mapping
│   │   ├── decision_agent.py      # Multi-criteria action ranking
│   │   ├── regen_score_agent.py   # Composite 0–100 score
│   │   └── report_agent.py        # Executive summary + action plan tiers
│   ├── core/
│   │   ├── simulation.py          # CSV / JSON loaders (pandas)
│   │   ├── scoring.py             # RE:GEN Score formula
│   │   └── guardrails.py          # Hazard suppression, disclaimer constants
│   └── data/
│       ├── water_usage.csv        # 168 rows × 5 cols (Jan 15–21 2024)
│       ├── energy_usage.csv       # 168 rows × 6 cols
│       └── waste_knowledge_base.json  # 30 materials
│
└── frontend/
    ├── vite.config.js             # Tailwind v4 plugin; /api proxy → :8000
    ├── package.json               # React 19, Recharts 3.9, Axios, Lucide
    └── src/
        ├── App.jsx                # Scan state, Mission Control overlay, 14 sections
        ├── api.js                 # 7 Axios functions (baseURL: /api)
        ├── index.css              # Tailwind v4, glass-card variants, 14 keyframe animations
        └── components/            # 15 components (see Component Map below)
```

## Component Map

| Component | Purpose |
|-----------|---------|
| `HeroSection` | Animated orbs, agent network card, scan CTA |
| `CommandCenterDashboard` | Score gauges, stat cards, scan timeline, breakdown |
| `RegenScoreGauge` | Animated SVG arc rings (before / after) |
| `WasteAnalyzer` | 30-type selector, 3-pathway comparison, hazard UI |
| `WaterPanel` | Anomaly list, Recharts AreaChart |
| `EnergyPanel` | After-hours events, Recharts BarChart |
| `AgentWarRoom` | 7 agent cards, live collaboration feed |
| `ActionPlan` | 4-tier plan, domain owners, JSON export |
| `DigitalTwinCampus` | Clickable 6-building campus map |
| `ResourceLossHeatmap` | Zone × domain risk grid |
| `ImpactProjection` | 30-day extrapolation cards |
| `InterventionSimulator` | 6 toggles, live score / savings computation |
| `SustainabilityAchievements` | 6 badge cards with unlock conditions |
| `WhyThisMatters` | Storytelling section |
| `CapstoneMappingSection` | 6 capstone concept cards |

## Agent Pipeline

Agents run **sequentially** within each endpoint — no direct agent-to-agent calls.
`main.py` orchestrates: it calls each agent function, collects the returned dict, and
passes it as a typed argument to the next agent.

```
Water Agent ──┐
Energy Agent ──┼──► Impact Agent ──► Decision Engine ──► Score Agent ──► Report Agent
Waste Agent ──┘
```

**No shared state, no message bus.** All inter-agent communication is through plain
Python dicts passed as function arguments.

## CSS Design System

The `index.css` file implements a glassmorphism design system with:

- Glass card variants: `.glass-card`, `.glass-card-green`, `.glass-card-red`,
  `.glass-card-blue`, `.glass-card-yellow`, `.glass-card-purple`
- Heatmap classes: `.heatmap-{critical|high|medium|low|none}`
- 14 keyframe animations: `floatOrb`, `glowPulse`, `scanSweep`, `agentPulse`,
  `typeIn`, `countUp`, `progressFill`, `slideUp`, `cardFloat`, `shimmerSlide`,
  `achieveGlowGold`, `achieveGlowGreen`, `sectionReveal`, `valuePop`, `ringGlow`

## Data Layer

| File | Columns | Notes |
|------|---------|-------|
| `water_usage.csv` | date, hour, usage_liters, location, anomaly | Jan 15–21 2024; anomaly is boolean |
| `energy_usage.csv` | date, hour, usage_kwh, zone, equipment, anomaly | Same 7-day window |
| `waste_knowledge_base.json` | 30 materials with category, hazard_level, value_range, pathway | Loaded once, cached in module scope |

`simulation.py` loads all three using `pandas.read_csv()` and `json.load()`.
The waste KB is cached in a module-level `_kb` variable to avoid re-reads per request.

## RE:GEN Score Formula

Defined in `core/scoring.py`:

```
RE:GEN Score = waste_score  × 0.20
             + water_score  × 0.20
             + energy_score × 0.20
             + co2_score    × 0.15
             + urgency_score × 0.15
             + feasibility_score × 0.10
```

Result clamped `[0, 100]`, rounded to 1 decimal place.

**Rating labels** (`severity_label()`):

| Score | Rating |
|-------|--------|
| ≥ 80 | Excellent |
| ≥ 60 | Good |
| ≥ 40 | Moderate |
| ≥ 20 | Poor |
| < 20 | Critical |

**Before vs. After scoring:** The Score Agent applies fixed offsets (15–25 pts) to each
sub-dimension to model the current degraded state (before score), then uses raw computed
values for the post-action projection (after score).

---

*See also: [FLOWCHARTS.md](FLOWCHARTS.md) · [AGENTS.md](AGENTS.md) · [API.md](API.md)*
