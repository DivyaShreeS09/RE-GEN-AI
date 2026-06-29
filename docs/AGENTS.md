# Multi-Agent Architecture

RE:GEN AI runs **seven purpose-built agents**, each responsible for a distinct analytical
domain. All coordination is handled by `main.py` — agents never call each other directly.

---

## 1. Waste-to-Wealth Agent
**File:** `agents/waste_agent.py` · **Confidence:** 0.92

**Purpose:** Identify recovery value and safest disposal pathway for a campus waste material.

**Inputs:** `waste_type` (str), `quantity_kg` (float, validated 0–100,000 kg)

**Process:**
1. Lazy-load the JSON knowledge base (module-level cache via `_get_kb()`)
2. Normalize key: lowercase + strip
3. Apply `apply_hazard_guardrail()` — suppresses financials for `hazard_level: critical|high`
4. Compute INR recovery range: `unit_rate_min × qty` to `unit_rate_max × qty`
5. Return 7-step reasoning trace

**Key outputs:** `category`, `composition`, `hazard_level`, `hazard_warning`, `possible_products`,
`recommended_pathway`, `hidden_value_score` (0–100), `estimated_recovery` (null if hazardous)

**Knowledge base:** 30 materials — Agricultural (coconut shell, rice husk, banana peel, sugarcane
bagasse, corn husk, coconut coir, dry leaves, garden waste, coffee grounds, eggshells),
Organic (food waste, fish waste, wet waste), Paper (cardboard, paper waste), Plastic (plastic
bottles), Glass (glass bottles), Metal (aluminium cans, steel scrap), Industrial (construction
debris, wood waste, sawdust, rubber tyres, used cooking oil, textile waste, leather scraps,
cotton waste), Hazardous (e-waste, battery waste, medical waste).

---

## 2. Water Leakage Agent
**File:** `agents/water_agent.py` · **Confidence:** 0.89

**Purpose:** Detect night-flow anomalies and estimate volume and cost of water leakage.

**Inputs:** `water_usage.csv` (7-day hourly data via `simulation.py`)

**Process:**
1. Split rows into anomaly / normal by `anomaly` boolean column
2. Compute night-hour baseline (hours 0–5) from non-anomalous readings; default 12 L/hr
3. Wasted litres = anomaly flow − (baseline × anomaly_hour_count)
4. Group events by `(date, location)`
5. Severity thresholds: critical >1000 L, high >500 L, medium >200 L, low >50 L, none
6. Cost: ₹0.05/L · CO₂: 0.001 kg/L

**Key outputs:** `anomaly_events`, `total_wasted_liters`, `severity`, `estimated_cost_inr`,
`co2_equivalent_kg`, `recommendations`, `hourly_chart_data`

---

## 3. Energy Optimization Agent
**File:** `agents/energy_agent.py` · **Confidence:** 0.91

**Purpose:** Detect after-hours energy waste and quantify cost and carbon impact.

**Inputs:** `energy_usage.csv` (7-day hourly data via `simulation.py`)

**After-hours window:** hours 0–5 (midnight–6 AM) **and** 22–23 (10–11 PM)

**Process:**
1. Compute after-hours baseline from non-anomalous readings; default 2.5 kWh/hr
2. Wasted kWh = anomaly consumption − (baseline × hours)
3. Group events by `(date, zone)` with equipment type list
4. Severity thresholds: critical >200 kWh, high >100, medium >50, low >10, none
5. Cost: ₹8.00/kWh · CO₂: **0.82 kg/kWh** (India grid emission factor)

**Key outputs:** `anomaly_events`, `total_wasted_kwh`, `severity`, `estimated_cost_inr`,
`co2_equivalent_kg`, `recommendations`, `hourly_chart_data`

---

## 4. Pollution & Impact Agent
**File:** `agents/impact_agent.py` · **Confidence:** 0.87

**Purpose:** Aggregate cross-domain environmental impact; map to UN SDGs.

**Inputs:** `water_saved_liters`, `energy_saved_kwh`, `waste_value_inr` (passed as params)

**Computations:**
- Water CO₂ = litres × 0.001 kg/L
- Energy CO₂ = kWh × 0.82 kg/kWh
- Tree equivalent = (total_CO₂ / 100) × 4.5
- Water scarcity impact = litres × 1.8 / 1000 kL
- Financial benefit = (water × ₹0.05) + (energy × ₹8.00) + (waste × 0.60)

**Sustainability rating thresholds:**
Outstanding ≥500 kg · Excellent ≥200 · Good ≥100 · Moderate ≥30 · Developing <30

**SDG alignment:** SDG 6 (Clean Water), SDG 7 (Clean Energy), SDG 12 (Responsible
Consumption), SDG 13 (Climate Action)

---

## 5. Decision Engine Agent
**File:** `agents/decision_agent.py` · **Confidence:** 0.90

**Purpose:** Synthesize upstream agent outputs into a ranked intervention plan.

**Inputs:** `water_result`, `energy_result`, `waste_result` (optional)

**Scoring formula:**
```
priority_score = urgency × 0.35
              + min(cost_saving / 1000, 30) × 0.30
              + env_impact_score × 0.25
              + feasibility × 0.10
```

| Factor | Detail |
|--------|--------|
| Urgency | critical→10, high→8, medium→5, low→3, none→1 |
| Feasibility | Water=9, Energy=8, Waste=7 (fixed) |
| Env impact | Water: `min(wasted_L/100, 10)` · Energy: `min(wasted_kWh/20, 10)` |
| Timeline | critical/high → "Immediate" · medium/low → "Within 7 days" |

**Key outputs:** `ranked_actions` (sorted by priority_score), `top_priority_domain`,
`total_potential_saving_inr`

---

## 6. RE:GEN Score Agent
**File:** `agents/regen_score_agent.py` · **Confidence:** 0.88

**Purpose:** Compute a composite 0–100 sustainability score (before and after actions).

**Inputs:** `water_result`, `energy_result`, `impact_result`, `decision_result`

**Sub-dimension derivation:**

| Dimension | Computation |
|-----------|------------|
| waste_recovery_potential | Fixed at 60 (simulated baseline) |
| water_saving_potential | `min(100, 100 − wasted_liters / 10)` |
| energy_saving_potential | `min(100, 100 − wasted_kwh / 5)` |
| co2_reduction_score | `sustainability_score` from Impact Agent |
| urgency_reduction_score | `100 − avg_urgency × 10`; clamped `[0, 100]` |
| feasibility_score | Fixed at 82 |

Before score applies −15 to −25 offsets per dimension. After score uses raw values.

---

## 7. Report Agent
**File:** `agents/report_agent.py` · **Confidence:** 0.95

**Purpose:** Assemble all agent outputs into a structured executive report.

**Action plan tiers:**

| Tier | Source |
|------|--------|
| Immediate | Decision Engine actions with `timeline == "Immediate"` |
| Next 7 days | Decision Engine actions with `"7"` in timeline |
| Next 30 days | 3 hardcoded infrastructure items (audit, sub-meters, segregation stations) |
| Long-term | 4 hardcoded strategic items (IoT, biogas, EPR, score target) |

**Key outputs:** `executive_summary`, `action_plan` (4 tiers), `silent_losses`,
`agent_reasoning_traces`, `regen_score` (before/after/improvement)

---

## Agent Confidence Summary

| Agent | Confidence |
|-------|-----------|
| Waste-to-Wealth | 0.92 |
| Water Leakage | 0.89 |
| Energy Optimization | 0.91 |
| Pollution & Impact | 0.87 |
| Decision Engine | 0.90 |
| RE:GEN Score | 0.88 |
| Report | 0.95 |

---

*See also: [ARCHITECTURE.md](ARCHITECTURE.md) · [API.md](API.md) · [SECURITY.md](SECURITY.md)*
