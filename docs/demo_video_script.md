# RE:GEN AI — 3-Minute Demo Video Script

**Target duration:** 3 minutes  
**Format:** Screen recording with voiceover  
**Resolution:** 1920×1080 recommended

---

## Screen Recording Checklist

Before recording:
- [ ] Backend running locally: `uvicorn main:app --reload --port 8000`
- [ ] Frontend running locally: `npm run dev`
- [ ] Browser at `http://localhost:5173`, zoom at 100%
- [ ] Dark mode enabled on OS (RE:GEN AI is dark-only)
- [ ] Microphone tested — clear audio, no background noise
- [ ] Browser dev tools closed
- [ ] All test data pre-loaded (run War Room once before recording so data is ready)
- [ ] Waste Analyzer: coconut shell (50 kg) auto-runs on load; have "e-waste" ready to switch to for hazard demo
- [ ] Screen recording software started and tested

---

## Script

---

### 0:00–0:20 — Hook

**[Screen: Hero section — campus aerial visual, tagline visible]**

> "Every week, campuses silently lose water through night-time pipe leaks, energy through equipment left on overnight, and money through waste that never gets recovered. The data exists — but no one is synthesizing it into action."

> "RE:GEN AI is a multi-agent decision-support prototype that does exactly that."

---

### 0:20–0:45 — Problem

**[Screen: Scroll slowly through the hero, pause on the problem statement text if visible]**

> "The problem is not measurement. Campus buildings collect water usage data, energy logs, and waste records. The problem is that these data streams live in separate systems, and no single person has the time or tools to connect them and figure out what to fix first."

> "RE:GEN AI runs seven specialized agents against simulated smart-campus resource logs. Each agent detects hidden resource loss in its domain. The findings are combined into a ranked action plan. Gemini 2.5 Flash Lite adds a natural-language reasoning layer so the sustainability officer knows not just what to fix, but why it matters most."

---

### 0:45–1:20 — Digital Twin

**[Screen: Scroll to Digital Twin section]**

> "The Digital Twin gives a campus-wide view of resource health. Each zone shows its current status — water, energy, and waste risk levels at a glance."

**[Screen: Hover over zones to show tooltips or status indicators]**

> "Green zones are within normal operating range. Zones flagged in yellow or red have anomalies that the agents have detected."

**[Screen: Point out the campus map or zone visualization]**

> "This is not live sensor data — it is simulated smart-campus resource logs generated for this capstone demonstration. The purpose is to show what this kind of system would look like with real data connected."

---

### 1:20–1:55 — Agent War Room

**[Screen: Scroll to Agent War Room section]**

> "The Agent War Room is where the analysis runs."

**[Screen: Click the 'Run Agents' or 'Re-run Agents' button]**

> "Watch the agent network activate. Seven specialized agents — Water, Energy, Waste, Impact, Score, Report, and the Decision Engine — each connected to the Gemini Core at the center."

**[Screen: Watch animated dots travel along connection lines as agents complete]**

> "Each agent runs independently, returns structured findings with a reasoning trace, and passes its output to the next stage in the pipeline."

**[Screen: Click on one agent node — e.g., Water Agent — to show its panel on the right]**

> "Clicking any agent node shows its findings. Here, the Water Leakage Agent has identified anomalous night-flow readings at two campus locations, with an estimated waste of several hundred liters and a severity classification."

**[Screen: Click another node — e.g., Decision Engine]**

> "The Decision Engine ranks all interventions by a weighted composite of urgency, estimated cost saving, environmental impact, and feasibility. Gemini explains why the top-priority action must be addressed first — in plain language, grounded in the specific numbers from the deterministic agents."

---

### 1:55–2:25 — Waste Analyzer and Analysis Panels

**[Screen: Scroll to Waste-to-Wealth Analyzer]**

> "The Waste-to-Wealth Analyzer lets the sustainability officer look up any campus waste material."

**[Screen: Waste Analyzer auto-loads with coconut shell 50 kg — result is already visible]**

> "The agent auto-analyzes coconut shell — 50 kilograms. It looks up the material in a 30-category knowledge base, maps it to recovery pathways like activated carbon or biomass fuel, and returns an estimated value range with three pathway options. Note the qualifier: these are estimates. Actual market prices vary."

**[Screen: Change material to "e-waste" in the dropdown, click Analyze]**

> "Switch to e-waste — classified as high hazard. The agent suppresses all financial figures and shows a regulatory warning. Gemini is never called for hazardous waste. This is a deliberate safety guardrail — the system will not generate financial estimates for materials that require licensed handlers."

**[Screen: Scroll to Water Panel or Energy Panel briefly]**

> "The Water and Energy panels show 7-day analysis charts with anomalous readings highlighted and recommendations listed in order of urgency."

---

### 2:25–2:45 — Report and RE:GEN Score

**[Screen: Scroll to Report or click Generate Report]**

> "The Report Agent assembles all findings into an executive brief. Gemini 2.5 Flash Lite writes the narrative summary — a plain-language synthesis of what the agents found, what it means, and what to do about it."

**[Screen: Show the PDF download button, click it]**

> "The full report is downloadable as a PDF — ready to hand to a facilities manager or sustainability committee."

**[Screen: Show RE:GEN Score gauge — before/after scores]**

> "The RE:GEN Score gives the campus a health index from zero to one hundred. Before implementing any recommendations, the score reflects the current resource loss. After implementing all agent-recommended interventions, the projected score shows the estimated improvement."

---

### 2:45–3:00 — Closing

**[Screen: Return to hero or show the full page scrolling up]**

> "RE:GEN AI is a prototype. The data is simulated, and this is not a regulatory or financial tool. But it demonstrates a real architectural pattern: specialized agents detecting hidden resource loss, an orchestration layer synthesizing findings into a ranked action plan, and Gemini adding explainability where natural language has value."

> "Built with FastAPI, React, and Gemini 2.5 Flash Lite. All code is open-source."

**[Screen: Show GitHub URL or end card]**

> "Thanks for watching."

---

## Post-Production Notes

- Keep total runtime under 3:10 to allow for natural pauses
- Add captions for accessibility
- If agents take more than 15 seconds to respond on screen, speed up that segment 2x in editing
- End card should show: GitHub link, Kaggle project link, author name
- Do not include live API keys or `.env` content in any screen recording
