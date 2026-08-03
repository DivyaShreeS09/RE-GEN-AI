import { Globe, Cpu } from 'lucide-react'

const INDIA_STATS = [
  { stat: '1,000+', label: 'University Campuses',  sub: 'potential deployment sites',    color: '#ff9900' },
  { stat: '5 M+',   label: 'Hostel Residents',     sub: 'daily water + energy consumers', color: '#00e5ff' },
  { stat: '₹500 Cr', label: 'Annual Waste Value',  sub: 'lost to landfill every year',   color: '#00ff88' },
  { stat: '35–40%', label: 'Water Lost',            sub: 'in campus infrastructure',      color: '#a78bfa' },
]

const CAMPUS_DOMAINS = [
  {
    emoji: '🏠', title: 'Hostels & Residences',
    desc: 'Shared plumbing with no individual metering. Night-flow leaks persist for weeks before anyone notices.',
    agent: 'Water Leakage Agent flags hourly flow anomalies.',
    color: '#00e5ff',
  },
  {
    emoji: '🔬', title: 'Labs & Research Blocks',
    desc: 'Equipment left on after hours, mixed waste streams, and high e-waste generation from outdated hardware.',
    agent: 'Energy + Waste agents detect after-hours patterns.',
    color: '#f97316',
  },
  {
    emoji: '🍽', title: 'Canteens & Food Courts',
    desc: 'High daily organic waste volume — composting and biogas recovery are high-feasibility pathways.',
    agent: 'Waste-to-Wealth agent maps highest-value recovery.',
    color: '#00ff88',
  },
  {
    emoji: '🏢', title: 'Admin & Seminar Blocks',
    desc: 'Office lighting and AC running in empty rooms overnight. Smart scheduling cuts 20–30% waste.',
    agent: 'Decision Engine prioritizes occupancy-based automation.',
    color: '#a78bfa',
  },
]

const GLOBAL_SCALE = [
  { icon: '🏙', label: 'Smart Cities',      desc: 'Municipal water and energy grids, ward-level waste management' },
  { icon: '🏭', label: 'Industrial Parks',  desc: 'Production waste streams, per-unit energy intensity tracking' },
  { icon: '🏨', label: 'Hotel Chains',      desc: 'Per-property sustainability scoring, certified waste routing' },
]

export default function IndiaGlobalSection() {
  return (
    <section className="px-6 py-20 max-w-7xl mx-auto" id="india">

      {/* Header */}
      <div className="text-center mb-14">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full mb-6"
          style={{ background: 'rgba(255,153,0,0.08)', border: '1px solid rgba(255,153,0,0.28)' }}>
          <span className="text-base">🇮🇳</span>
          <span className="text-xs font-bold text-orange-400 tracking-widest uppercase">India-First Platform</span>
        </div>

        <h2 className="text-5xl lg:text-6xl font-black text-white mb-5 leading-tight">
          Built for <span className="text-gradient-orange">India.</span><br />
          Scalable to the <span className="text-gradient-green">World.</span>
        </h2>

        <p className="text-slate-400 text-base max-w-2xl mx-auto leading-relaxed">
          India's institutions host millions of students across thousands of campuses.
          Each one loses water, wastes electricity, and discards recoverable materials — every day.
          RE:GEN AI makes those losses visible and actionable.
        </p>
      </div>

      {/* India stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-14">
        {INDIA_STATS.map((s) => (
          <div key={s.label} className="glass-card p-5 text-center agent-card-hover"
            style={{ borderColor: s.color + '22' }}>
            <p className="text-3xl font-black mb-1" style={{ color: s.color }}>{s.stat}</p>
            <p className="text-xs font-bold text-white mb-0.5">{s.label}</p>
            <p className="text-xs text-slate-500">{s.sub}</p>
          </div>
        ))}
      </div>

      {/* Campus domain cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mb-14">
        {CAMPUS_DOMAINS.map((c) => (
          <div key={c.title} className="glass-card p-5 agent-card-hover"
            style={{ borderColor: c.color + '20' }}>
            <span className="text-3xl mb-3 block">{c.emoji}</span>
            <h3 className="font-bold text-white text-sm mb-2">{c.title}</h3>
            <p className="text-xs text-slate-400 leading-relaxed mb-3">{c.desc}</p>
            <div className="p-2.5 rounded-lg" style={{ background: c.color + '0a', border: `1px solid ${c.color}20` }}>
              <p className="text-xs font-medium leading-relaxed" style={{ color: c.color }}>
                <Cpu className="w-3 h-3 inline mr-1 opacity-70" />{c.agent}
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* Global scale block */}
      <div className="glass-card p-8 lg:p-10" style={{ background: 'rgba(0,229,255,0.02)', borderColor: 'rgba(0,229,255,0.1)' }}>
        <div className="flex items-center gap-2 mb-2 justify-center">
          <Globe className="w-4 h-4 text-cyan-400" />
          <p className="text-xs text-cyan-400 uppercase tracking-widest font-bold">Multi-Domain Architecture</p>
        </div>
        <h3 className="text-2xl lg:text-3xl font-black text-white mb-3 text-center">
          The same agent layer scales beyond campuses.
        </h3>
        <p className="text-slate-500 text-sm text-center mb-8 max-w-xl mx-auto">
          Universities are microcosms — they have water grids, energy networks, waste streams,
          and constrained budgets. What works here transfers directly.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8 max-w-3xl mx-auto">
          {GLOBAL_SCALE.map((g) => (
            <div key={g.label} className="text-center p-4 rounded-xl"
              style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)' }}>
              <span className="text-4xl mb-3 block">{g.icon}</span>
              <p className="text-sm font-bold text-white mb-1">{g.label}</p>
              <p className="text-xs text-slate-500 leading-relaxed">{g.desc}</p>
            </div>
          ))}
        </div>

        {/* SDG strip */}
        <div className="border-t pt-6" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
          <p className="text-xs text-slate-600 text-center mb-3 uppercase tracking-widest">
            UN Sustainable Development Goals alignment
          </p>
          <div className="flex flex-wrap justify-center gap-2">
            {[
              { num: 6,  label: 'Clean Water',        color: '#26bde2' },
              { num: 7,  label: 'Affordable Energy',  color: '#fcc30b' },
              { num: 11, label: 'Sustainable Cities', color: '#fd9d24' },
              { num: 12, label: 'Responsible Consumption', color: '#bf8b2e' },
              { num: 13, label: 'Climate Action',     color: '#3f7e44' },
            ].map((sdg) => (
              <div key={sdg.num} className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold"
                style={{ background: sdg.color + '15', border: `1px solid ${sdg.color}30`, color: sdg.color }}>
                SDG {sdg.num} · {sdg.label}
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
