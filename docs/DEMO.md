# Demo Guide

## Prerequisites

Both servers must be running before opening the browser:

```bash
# Terminal 1 — backend
cd backend
uvicorn main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend
npm run dev
```

Open: `http://localhost:5173`

---

## 2-Minute Walkthrough

### Step 1 — Hero Section
Observe the animated agent network card with live node labels and glowing orbs.
The "Launch Campus Intelligence Scan" button is the single entry point.

### Step 2 — Mission Control Overlay
Click the scan button. A full-screen overlay appears and sequences through **8 mission steps**:

1. 🛰 Connecting to Campus Resource Network
2. ♻️ Waste Agent Online — Knowledge base loaded
3. 💧 Water Agent Online — Night-flow logs indexed
4. ⚡ Energy Agent Online — Anomaly detection active
5. 🌿 Environmental Intelligence — Impact models ready
6. 🧠 Decision Engine — Interventions ranked by priority
7. 📊 RE:GEN Score Calculated — Executive report generated
8. ✅ Campus Intelligence Scan Complete

Step timers fire at 700 ms intervals alongside the real API calls. Whichever finishes
first (API or timer) advances to the complete state. The overlay holds for 2 seconds after
completion, then dissolves.

### Step 3 — Command Center Dashboard
- **RE:GEN Score gauges:** Two animated SVG rings show before and after scores
- **Silent Loss Detector:** Total weekly water + energy cost exposure
- **Scan Pipeline:** 5-stage animated timeline (Sensor Load → Anomaly Detection →
  Impact Quantification → Intervention Ranking → Plan Generation)
- **Score Breakdown:** Six mini gauges, one per sub-dimension

### Step 4 — Waste-to-Wealth Analyzer

**Demo A — Safe material:**
1. Select `coconut shell` from the 30-type dropdown
2. Keep quantity at 50 kg
3. Click Analyze
4. Observe: category, possible products, hidden value score, 3-pathway comparison,
   7-step reasoning trace, estimated INR range

**Demo B — Hazardous material:**
1. Select `e-waste`
2. Click Analyze
3. Observe: red CPCB compliance warning, all financial values suppressed (`estimated_recovery: null`),
   pathway cards replaced with compliance notice

### Step 5 — Water & Energy Panels
- Review anomaly events with date, location, duration, and wasted volume
- Examine the hourly usage chart (AreaChart for water, BarChart for energy)
- Note the severity badge (HIGH in the simulated 7-day dataset)

### Step 6 — Digital Twin Campus
- Click **Lab Block** → expand to see CRITICAL risk detail
- Domain breakdown shows Water (CRITICAL), Energy (HIGH), Waste (MODERATE)
- Agent recommendation and 3-domain score grid appear in the expanded panel

### Step 7 — Resource Loss Heatmap
- Color-coded `heatmap-{level}` classes across 6 zones × 3 domains
- Lab Block and Seminar Hall appear as critical/high risk

### Step 8 — Intervention Simulator
Toggle these to see scores update **instantly** (no API call):

| Toggle | Score Gain | Key Impact |
|--------|-----------|-----------|
| Fix Water Leakage | +6 pts | ~578 L/week saved |
| Smart AC Scheduling | +7 pts | ~183 kWh/week saved |
| Replace Lights with LEDs | +5 pts | ~50 kWh/week saved |
| Waste Segregation Drive | +4 pts | ≈₹4,200 est. value/month |
| Install Rooftop Solar | +9 pts | ~92 kWh/week grid offset |
| Compost Food Waste | +3 pts | ≈₹3,200 est. value/month |

All 6 active = **+34 pts** maximum score gain.

### Step 9 — Sustainability Achievements
Observe which of the 6 badge cards are unlocked based on scan results:
- Water Guardian (unlocked: water severity is medium/high/critical)
- Energy Optimizer (unlocked: energy severity is medium/high/critical)
- Carbon Saver (unlocked: co2_saved > 0)
- Circular Economy Champion (always unlocked — 3 pathways evaluated)
- Hazard Guardian (always unlocked — guardrail tested at boot)
- Green Campus (unlocked: after_score ≥ 70)

### Step 10 — Agent War Room
- 7 agent cards show status chip, confidence bar, urgency bar, finding, recommendation
- The **Agent Collaboration Feed** appends a new message every 2.8 seconds,
  cycling through 7 pre-authored inter-agent messages
- Click "Re-run Agents" to refresh the War Room via `GET /agent-war-room`

### Step 11 — Action Plan
- 4-tier plan: Immediate / Next 7 Days / Next 30 Days / Long-term
- Domain owner chips (Water Ops / Energy Team / Waste Mgmt / etc.)
- Click **Export Plan** to download `regen-action-plan-<timestamp>.json`

---

## Screenshots Table

> Add screenshots after running the application.

| Section | Screenshot |
|---------|-----------|
| Hero & Scan Button | *(add)* |
| Mission Control Overlay | *(add)* |
| Command Center Dashboard | *(add)* |
| RE:GEN Score Gauges | *(add)* |
| Waste Analyzer — Safe Material | *(add)* |
| Waste Analyzer — Hazard Guardrail | *(add)* |
| Water Loss Panel | *(add)* |
| Energy Panel | *(add)* |
| Digital Twin Campus | *(add)* |
| Resource Loss Heatmap | *(add)* |
| Intervention Simulator | *(add)* |
| Sustainability Achievements | *(add)* |
| Agent War Room | *(add)* |
| Action Plan | *(add)* |

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "Unable to reach RE:GEN AI backend" | Ensure `uvicorn main:app --port 8000` is running in `backend/` |
| Blank dashboard after scan | Check browser console for CORS errors; confirm backend is on port 8000 |
| `ModuleNotFoundError` on backend start | Run `uvicorn` from the `backend/` directory, not the project root |
| Tailwind styles missing | Confirm Vite is using `@tailwindcss/vite` plugin (not PostCSS); check `vite.config.js` |

---

*See also: [DEPLOYMENT.md](DEPLOYMENT.md) · [API.md](API.md)*
