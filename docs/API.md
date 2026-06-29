# API Reference

Base URL: `http://localhost:8000`

Frontend proxy: `/api/*` → `http://localhost:8000/*` (configured in `vite.config.js`)

Interactive docs (Swagger UI): `http://localhost:8000/docs`

---

## `GET /health`

Returns system status and prototype notices.

```json
{
  "status": "online",
  "system": "RE:GEN AI Sustainability Command Center",
  "version": "1.0.0",
  "disclaimer": "RE:GEN AI is a prototype decision-support system...",
  "data_notice": "Data shown is simulated for demonstration..."
}
```

---

## `POST /analyze/waste`

Runs the Waste-to-Wealth Agent on a material and quantity.

**Request body:**
```json
{
  "waste_type": "coconut shell",
  "quantity_kg": 50.0
}
```

**Validation:** `quantity_kg` must be > 0 and ≤ 100,000. Returns HTTP 400 on failure.

**Response — non-hazardous material:**
```json
{
  "agent": "Waste-to-Wealth Agent",
  "status": "analyzed",
  "waste_type": "coconut shell",
  "quantity_kg": 50.0,
  "category": "Agricultural Waste",
  "hazard_level": "none",
  "hazard_warning": false,
  "possible_products": ["activated carbon", "charcoal briquettes", "handicrafts"],
  "recommended_pathway": "sell_or_process",
  "hidden_value_score": 72,
  "estimated_recovery": {
    "min_inr": 100.0,
    "max_inr": 400.0,
    "unit_rate": "2–8 INR/kg",
    "note": "Estimated only. Actual market prices vary."
  },
  "reasoning_trace": ["Step 1 — ...", "Step 2 — ...", "..."],
  "confidence": 0.92
}
```

**Response — hazardous material (e.g. `e-waste`):**
```json
{
  "hazard_warning": true,
  "hazard_message": "⚠️ HAZARDOUS WASTE DETECTED: Requires certified licensed processors...",
  "estimated_recovery": null,
  "estimated_recovery_note": "Financial values suppressed for hazardous materials.",
  "confidence": 0.92
}
```

---

## `GET /analyze/water`

Runs the Water Leakage Agent on the static 7-day CSV.

**Response:**
```json
{
  "agent": "Water Leakage Agent",
  "total_wasted_liters": 678.8,
  "severity": "high",
  "severity_score": 30,
  "estimated_cost_inr": 33.94,
  "co2_equivalent_kg": 0.68,
  "anomaly_events": [
    {
      "date": "2024-01-16",
      "location": "Block-B Hostel",
      "anomaly_hours": [2, 3, 4],
      "duration_hours": 3,
      "total_flow_liters": 142.0,
      "estimated_waste_liters": 118.0
    }
  ],
  "hourly_chart_data": [
    {"hour": 0, "avg_usage": 12.0}
  ],
  "recommendations": ["..."],
  "reasoning_trace": ["Step 1 — ...", "..."],
  "confidence": 0.89
}
```

---

## `GET /analyze/energy`

Runs the Energy Optimization Agent on the static 7-day CSV.

**Response:**
```json
{
  "agent": "Energy Optimization Agent",
  "total_wasted_kwh": 228.98,
  "severity": "high",
  "severity_score": 28,
  "estimated_cost_inr": 1831.84,
  "co2_equivalent_kg": 187.76,
  "anomaly_events": [
    {
      "date": "2024-01-16",
      "zone": "Seminar Hall",
      "anomaly_hours": [22, 23, 0, 1, 2, 3, 4, 5],
      "duration_hours": 8,
      "total_kwh": 68.0,
      "wasted_kwh": 48.0,
      "equipment": ["AC", "Lighting"]
    }
  ],
  "hourly_chart_data": [{"hour": 0, "avg_kwh": 1.9}],
  "recommendations": ["..."],
  "reasoning_trace": ["Step 1 — ...", "..."],
  "confidence": 0.91
}
```

---

## `GET /dashboard/summary`

Orchestrates the full pipeline (Water → Energy → Impact → Decision → Score → Report)
and returns a compact summary.

**Response shape:**
```json
{
  "regen_score": {
    "before_score": 30,
    "after_score": 51,
    "improvement": 21.0,
    "current_rating": "Poor",
    "target_rating": "Moderate"
  },
  "silent_losses": {
    "water_leakage_liters": 678.8,
    "water_cost_inr": 33.94,
    "energy_waste_kwh": 228.98,
    "energy_cost_inr": 1831.84
  },
  "water_summary": { "total_wasted_liters": 678.8, "severity": "high" },
  "energy_summary": { "total_wasted_kwh": 228.98, "severity": "high" },
  "impact_summary": {
    "total_co2_saved_kg": 188.44,
    "trees_equivalent": 8.5,
    "sustainability_rating": "Good"
  },
  "top_actions": [
    { "domain": "Energy", "rank": 1, "recommended_action": "...", "timeline": "Immediate" }
  ],
  "disclaimer": "...",
  "data_notice": "..."
}
```

---

## `GET /agent-war-room`

Returns 7-agent status panel. Runs the complete pipeline internally.

**Response:**
```json
{
  "war_room": [
    {
      "agent": "Water Leakage Agent",
      "icon": "💧",
      "status": "active",
      "finding": "Detected 2 leakage events. 678.8 L wasted. Severity: HIGH.",
      "confidence": 0.89,
      "recommendation": "Immediate physical inspection of night-flow pipes...",
      "severity": "high",
      "key_metric": "678.8 L lost"
    }
  ],
  "disclaimer": "..."
}
```

> **Note:** The Waste-to-Wealth Agent appears as `status: "standby"` here — it requires
> a material submission via `POST /analyze/waste` and cannot auto-run without user input.

---

## `POST /generate/action-plan`

Runs the full pipeline with optional waste input. Returns the complete, unabridged report.

**Request body:**
```json
{
  "include_waste": false,
  "waste_type": null,
  "waste_quantity_kg": null
}
```

**Response:** Full agent output dicts for `water`, `energy`, `waste`, `impact`,
`decision`, `regen_score`, and `report`, where `report` contains:
- `executive_summary` (formatted text)
- `action_plan` (4 tiers: immediate / next_7_days / next_30_days / long_term)
- `agent_reasoning_traces` (all agent traces aggregated)
- `silent_losses`

---

## API Client (`frontend/src/api.js`)

```js
const api = axios.create({ baseURL: '/api' })

export const healthCheck       = ()           => api.get('/health')
export const analyzeWaste      = (type, qty)  => api.post('/analyze/waste', { waste_type: type, quantity_kg: qty })
export const analyzeWater      = ()           => api.get('/analyze/water')
export const analyzeEnergy     = ()           => api.get('/analyze/energy')
export const getDashboardSummary = ()         => api.get('/dashboard/summary')
export const getWarRoom        = ()           => api.get('/agent-war-room')
export const generateActionPlan = (payload)  => api.post('/generate/action-plan', payload)
```

---

*See also: [AGENTS.md](AGENTS.md) · [SECURITY.md](SECURITY.md) · [DEPLOYMENT.md](DEPLOYMENT.md)*
