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
- [ ] Browser dev tools closed
- [ ] Screen recording software started and tested

---

## Script

---

### 0:00–0:20 — Hook

**[Screen: Hero section]**

> "Every week, campuses, hospitals, and industrial facilities silently lose water through night-time pipe leaks, energy through equipment left on overnight, and money through waste that never gets recovered. The data exists — but no one is synthesising it into action."

> "RE:GEN AI is a multi-agent sustainability intelligence platform that does exactly that."

---

### 0:20–0:45 — Two Modes

**[Screen: Click Start Analysis — Mode Selector appears]**

> "RE:GEN AI offers two modes. Demo mode analyses bundled simulated campus data instantly. Upload mode lets you bring your own data — water, energy, or fuel files in CSV or Excel — or enter numbers manually. No dataset is mandatory."

**[Screen: Click Upload Your Data, show the Upload Center]**

> "The Upload Center shows four dataset categories. Each supports both file upload and manual entry. Carbon is never uploaded — it is always calculated automatically from electricity, fuel, water, and waste data using certified emission factors."

**[Screen: Show the carbon auto-notice banner at the top of the Upload Center]**

> "After entering data, you see a Mission Summary — showing which datasets are available, which will be skipped, and your mission readiness score before launching the analysis."

---

### 0:45–1:15 — Agent War Room

**[Screen: After scan completes, scroll to Agent War Room]**

> "The Agent War Room shows the full pipeline. Seven specialised agents — Water, Energy, Waste, Impact, Score, Report, and the Decision Engine — each connected to the AI Core at the centre."

**[Screen: Watch animated connection lines with traveling dots]**

> "Each agent runs independently, returns structured findings with a reasoning trace, and passes its output to the next stage in the pipeline."

**[Screen: Click on the Water Agent node to show its detail panel]**

> "The Water Leakage Agent has identified anomalous night-flow readings, with an estimated waste of several hundred liters and a severity classification. If water data was not uploaded, the agent shows exactly why it was skipped — it never silently disappears."

**[Screen: Click the Decision Engine node]**

> "The Decision Engine ranks all interventions by a weighted composite of urgency, estimated cost saving, environmental impact, and feasibility. OpenAI gpt-4o-mini explains the top-priority action in plain language, grounded in the specific numbers from the deterministic agents."

---

### 1:15–1:45 — Waste Analyzer and Analysis Panels

**[Screen: Scroll to Waste-to-Wealth Analyzer]**

> "The Waste-to-Wealth Analyzer lets the sustainability officer look up any waste material by type and quantity."

**[Screen: Enter 'coconut shell', 50 kg — click Analyse]**

> "The agent looks up coconut shell in a 30-category knowledge base, maps it to recovery pathways like activated carbon or biomass fuel, and returns an estimated value range. Note the qualifier — these are estimates only."

**[Screen: Try 'e-waste']**

> "Switch to e-waste — classified as high hazard. The agent suppresses all financial figures and shows a regulatory warning. OpenAI is never called for hazardous waste. This is a deliberate safety guardrail."

**[Screen: Scroll to Water Panel or Energy Panel briefly]**

> "The Water and Energy panels show 7-day analysis charts with anomalous readings highlighted and recommendations listed in order of urgency."

---

### 1:45–2:15 — Report and RE:GEN Score

**[Screen: Scroll to Action Plan / Report section]**

> "The Report Agent assembles all findings into an executive brief. OpenAI gpt-4o-mini writes the narrative summary — a plain-language synthesis of what the agents found, what it means, and what to do about it."

> "If OpenAI is unavailable, the system falls back to a fully deterministic rule-based summary. All calculations remain correct regardless."

**[Screen: Show the PDF download button, click it]**

> "The full report is downloadable as a PDF, with a Data Summary at the top disclosing which analyses ran, which were skipped, coverage percentage, confidence, and mission readiness."

**[Screen: Show RE:GEN Score gauge — before/after scores]**

> "The RE:GEN Score gives the organisation a health index from zero to one hundred — before and after implementing all agent-recommended interventions."

---

### 2:15–2:35 — Digital Twin

**[Screen: Scroll to Digital Twin section]**

> "The Digital Twin gives a campus-wide view of resource health. Each zone shows its current status — water, energy, and waste risk levels at a glance."

**[Screen: Hover over zones to show tooltips]**

> "Green zones are within normal operating range. Zones flagged in yellow or red have anomalies the agents have detected."

---

### 2:35–3:00 — Closing

**[Screen: Return to hero or scroll through full page]**

> "RE:GEN AI is a prototype. Demo data is simulated, and this is not a regulatory or financial tool. But it demonstrates a real architectural pattern: specialised agents detecting hidden resource loss, an orchestration layer synthesising findings into a ranked action plan, and OpenAI adding explainability where natural language has value."

> "Built with FastAPI, React, and OpenAI gpt-4o-mini. All numerical analysis is fully deterministic Python. All code is open-source."

**[Screen: Show GitHub URL or end card]**

> "Thanks for watching."

---

## Post-Production Notes

- Keep total runtime under 3:10 to allow for natural pauses
- Add captions for accessibility
- If agents take more than 15 seconds to respond on screen, speed up that segment 2× in editing
- End card should show: GitHub link, Live demo link, author name
- Do not include live API keys or `.env` content in any screen recording
