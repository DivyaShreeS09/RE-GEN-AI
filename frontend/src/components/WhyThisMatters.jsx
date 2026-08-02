import { Eye, Target, Layers, Globe } from 'lucide-react'

const POINTS = [
  {
    icon: <Eye className="w-6 h-6" />,
    color: '#ef4444',
    title: 'Invisible Losses',
    body: `Campus water leaks at 3 AM go unnoticed for weeks. After-hours AC in an empty seminar hall
runs all night. Waste bins mix recoverable materials with landfill. None of this appears on
any single dashboard. RE:GEN AI makes these silent losses visible.`,
  },
  {
    icon: <Target className="w-6 h-6" />,
    color: '#00e5ff',
    title: 'Data to Action',
    body: `Detection alone is not enough. RE:GEN AI converts anomaly readings into ranked interventions —
each scored by urgency, financial impact, environmental benefit, and implementation feasibility.
The Decision Engine eliminates the guesswork from sustainability management.`,
  },
  {
    icon: <Layers className="w-6 h-6" />,
    color: '#a78bfa',
    title: 'Agents, Not Alerts',
    body: `Traditional monitoring sends alerts. RE:GEN AI sends agents. Each agent owns a domain,
produces a typed finding, passes context to the next agent, and escalates anomalies with
confidence scores. The result is a collaborative, multi-domain intelligence layer —
not a notification dashboard.`,
  },
  {
    icon: <Globe className="w-6 h-6" />,
    color: '#00ff88',
    title: 'Smart Campuses, Future Cities',
    body: `Universities are microcosms of cities — they have energy grids, water infrastructure,
waste streams, and decision-makers with constrained resources. What works here scales.
RE:GEN AI is built for campuses today, but the multi-agent architecture transfers to
municipal resource management, industrial sustainability, and smart city operations.`,
  },
]

export default function WhyThisMatters() {
  return (
    <section className="px-6 py-16 max-w-7xl mx-auto" id="why">
      <div className="mb-10">
        <h2 className="text-3xl font-black text-white mb-2">
          Why This <span className="text-gradient-green">Matters</span>
        </h2>
        <p className="text-slate-400 text-sm max-w-2xl">
          A sustainability problem with no common intelligence layer.
          A multi-agent system designed to solve it.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-10">
        {POINTS.map((p, i) => (
          <div key={i} className="glass-card p-6 agent-card-hover fade-in" style={{
            animationDelay: `${i * 0.1}s`, borderColor: p.color + '20'
          }}>
            <div className="flex items-start gap-4">
              <div className="p-2.5 rounded-xl flex-shrink-0" style={{ background: p.color + '12' }}>
                <div style={{ color: p.color }}>{p.icon}</div>
              </div>
              <div>
                <h3 className="font-bold text-white mb-2" style={{ color: p.color }}>{p.title}</h3>
                <p className="text-sm text-slate-400 leading-relaxed">{p.body}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Stats banner */}
      <div className="glass-card p-6">
        <p className="text-xs text-slate-500 uppercase tracking-widest mb-6 text-center">
          Projected impact at scale — if deployed across a 5,000-student campus
        </p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
          {[
            { value: '400–800 L', unit: 'water/day', label: 'Potential leakage recovery', color: '#00e5ff' },
            { value: '200–500', unit: 'kWh/week', label: 'After-hours energy recovery', color: '#eab308' },
            { value: '1–2 t', unit: 'CO₂/year', label: 'Reduction per campus unit', color: '#22c55e' },
            { value: '₹1.3–5 L', unit: 'per year', label: 'Estimated utility + waste saving', color: '#00ff88' },
          ].map((s, i) => (
            <div key={i}>
              <p className="text-2xl font-black" style={{ color: s.color }}>{s.value}</p>
              <p className="text-xs text-slate-500">{s.unit}</p>
              <p className="text-xs text-slate-600 mt-1">{s.label}</p>
            </div>
          ))}
        </div>
        <p className="text-xs text-slate-600 text-center mt-5">
          Figures are benchmark estimates for a 5,000-student campus. Actual impact depends on campus size,
          infrastructure condition, and intervention quality.
        </p>
      </div>
    </section>
  )
}
