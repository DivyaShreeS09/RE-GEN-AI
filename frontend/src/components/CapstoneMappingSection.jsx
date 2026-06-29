const mappings = [
  {
    concept: 'Multi-Agent System',
    emoji: '🤖',
    color: '#00ff88',
    description: '7 specialized agents — Waste, Water, Energy, Impact, Decision, RE:GEN Score, Report — each with distinct responsibilities, inputs, and outputs.',
    evidence: 'waste_agent.py, water_agent.py, energy_agent.py, impact_agent.py, decision_agent.py, regen_score_agent.py, report_agent.py',
  },
  {
    concept: 'Tools & Data Lookup',
    emoji: '🔧',
    color: '#00e5ff',
    description: 'Agents use local JSON knowledge base (30 waste materials) and CSV data (7-day water/energy) as their tools. Lookup → reasoning → output.',
    evidence: 'waste_knowledge_base.json, water_usage.csv, energy_usage.csv + load functions in simulation.py',
  },
  {
    concept: 'State & Memory',
    emoji: '🧠',
    color: '#a78bfa',
    description: 'Agent results flow through orchestration in main.py. dashboard/summary and agent-war-room endpoints aggregate multi-agent state into unified context.',
    evidence: '/generate/action-plan endpoint passes full agent context chain to report_agent.py',
  },
  {
    concept: 'Guardrails & Safety',
    emoji: '🛡️',
    color: '#f97316',
    description: 'Hazardous waste triggers mandatory CPCB warning. Financial values suppressed for critical waste. Disclaimer injected into all responses. Quantity validation blocks invalid inputs.',
    evidence: 'core/guardrails.py — apply_hazard_guardrail(), validate_quantity(), DISCLAIMER constant',
  },
  {
    concept: 'Evaluation & Scoring',
    emoji: '📊',
    color: '#eab308',
    description: 'RE:GEN Score (0–100) calculated from 6 sub-dimensions with weighted formula. Before/after scoring demonstrates measurable impact. Confidence scores per agent.',
    evidence: 'core/scoring.py, regen_score_agent.py — weighted formula + improvement calculation',
  },
  {
    concept: 'Production-Grade Structure',
    emoji: '🏗️',
    color: '#3b82f6',
    description: 'FastAPI REST backend with typed Pydantic models, CORS middleware, modular agent architecture, and React + Vite + Tailwind frontend with real API integration.',
    evidence: 'main.py, requirements.txt, frontend/src/api.js — full-stack deployment ready',
  },
]

export default function CapstoneMappingSection() {
  return (
    <section className="px-6 py-16 max-w-7xl mx-auto" id="capstone">
      <div className="mb-8">
        <h2 className="text-3xl font-black text-white mb-2">
          Capstone <span className="text-gradient-blue">Concept Mapping</span>
        </h2>
        <p className="text-slate-400">How RE:GEN AI demonstrates Google AI Agents course concepts</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {mappings.map((m, i) => (
          <div key={i} className="glass-card p-5 agent-card-hover fade-in" style={{
            animationDelay: `${i * 0.1}s`
          }}>
            <div className="flex items-center gap-3 mb-3">
              <span className="text-2xl">{m.emoji}</span>
              <h3 className="font-bold text-sm" style={{ color: m.color }}>{m.concept}</h3>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed mb-3">{m.description}</p>
            <div className="p-2 rounded text-xs text-slate-500 font-mono" style={{
              background: 'rgba(0,0,0,0.3)', border: `1px solid ${m.color}20`
            }}>
              {m.evidence}
            </div>
          </div>
        ))}
      </div>

      {/* Architecture Diagram (Text-based) */}
      <div className="mt-8 glass-card p-6">
        <h3 className="text-sm font-semibold text-cyan-400 uppercase tracking-wider mb-4">Multi-Agent Architecture Flow</h3>
        <div className="overflow-x-auto">
          <pre className="text-xs text-slate-400 leading-relaxed font-mono">
{`
Campus Data (Simulated)
    ├── water_usage.csv  ──►  Water Leakage Agent  ──►  anomaly events, liters wasted, severity
    ├── energy_usage.csv ──►  Energy Optimization Agent  ──►  wasted kWh, cost, recommendations
    └── waste_knowledge_base.json  ──►  Waste-to-Wealth Agent  ──►  value score, pathway, warning
                                                                            │
                                                                            ▼
                                                              Impact Agent (CO2, SDG, sustainability score)
                                                                            │
                                                                            ▼
                                                              Decision Engine Agent (prioritized action ranking)
                                                                            │
                                                                            ▼
                                                              RE:GEN Score Agent (0-100 composite score)
                                                                            │
                                                                            ▼
                                                              Report Agent (executive summary + action plan)
                                                                            │
                                                                            ▼
                                                        FastAPI REST Endpoints → React Dashboard
`}
          </pre>
        </div>
      </div>

      {/* Disclaimer */}
      <div className="mt-6 p-4 rounded-lg text-center" style={{
        background: 'rgba(234,179,8,0.05)', border: '1px solid rgba(234,179,8,0.15)'
      }}>
        <p className="text-xs text-yellow-600 leading-relaxed">
          ⚠️ RE:GEN AI is a prototype decision-support system and not professional regulatory, financial, or engineering advice.
          All data is simulated for capstone demonstration purposes. No real IoT sensors or live systems are connected.
        </p>
      </div>
    </section>
  )
}
