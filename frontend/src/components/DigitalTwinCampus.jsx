import { useState } from 'react'
import { Droplets, Zap, Trash2, AlertTriangle, MapPin, ChevronDown, ChevronUp } from 'lucide-react'

const RC = { critical: '#ef4444', high: '#f97316', medium: '#eab308', low: '#22c55e', none: '#6b7280' }
const RL = { critical: 'CRITICAL', high: 'HIGH', medium: 'MODERATE', low: 'LOW', none: 'CLEAR' }
const RB = {
  critical: 'rgba(239,68,68,0.09)',   high: 'rgba(249,115,22,0.09)',
  medium:   'rgba(234,179,8,0.07)',   low:  'rgba(34,197,94,0.07)',  none: 'rgba(107,114,128,0.06)',
}
const RBR = {
  critical: 'rgba(239,68,68,0.38)',   high: 'rgba(249,115,22,0.32)',
  medium:   'rgba(234,179,8,0.28)',   low:  'rgba(34,197,94,0.22)', none: 'rgba(107,114,128,0.16)',
}
const RO = { critical: 6, high: 5, medium: 4, low: 3, none: 2 }

const BUILDINGS = [
  {
    id: 'lab',        name: 'Lab Block',         emoji: '🔬', type: 'Research',
    risk: 'critical', occupancy: '~80 researchers',
    water:  { level: 'critical', value: '380 L in 2 hrs',     note: 'Major pipe leak Jan 19, 3–5 AM burst pattern' },
    energy: { level: 'high',     value: '48 kWh/day',         note: 'Extended equipment runtime detected' },
    waste:  { level: 'medium',   value: '15 kg/day',          note: 'E-waste and paper mixed — needs segregation' },
    rec: 'URGENT: Emergency plumbing inspection required. Install dedicated e-waste collection bin by Jan 22.',
    agent: 'Water + Energy Agent',
  },
  {
    id: 'hostel',     name: 'Block-B Hostel',    emoji: '🏠', type: 'Residential',
    risk: 'high',     occupancy: '~240 students',
    water:  { level: 'high',     value: '142 L excess/day',   note: 'Night-flow anomaly detected (Jan 16, 2–4 AM)' },
    energy: { level: 'medium',   value: '12 kWh after-hours', note: 'Moderate overnight consumption' },
    waste:  { level: 'low',      value: '8 kg/day',           note: 'Mostly organic — limited recyclables' },
    rec: 'Inspect ground-floor pipe fittings. Deploy night auto-shutoff valve by Jan 22.',
    agent: 'Water Leakage Agent',
  },
  {
    id: 'seminar',    name: 'Seminar Hall',       emoji: '🎓', type: 'Academic',
    risk: 'high',     occupancy: 'Variable — event-driven',
    water:  { level: 'low',      value: 'Normal',             note: 'No anomalies in monitoring window' },
    energy: { level: 'critical', value: '68 kWh overnight',   note: 'AC + lighting left on all night (Jan 16)' },
    waste:  { level: 'low',      value: '3 kg/day',           note: 'Minimal — paper and packaging only' },
    rec: 'Occupancy sensors for AC + lights. Enforce after-hours automated shutdown policy.',
    agent: 'Energy Optimizer Agent',
  },
  {
    id: 'computer',   name: 'Computer Lab',       emoji: '💻', type: 'Technology',
    risk: 'high',     occupancy: '~60 users (peak)',
    water:  { level: 'medium',   value: 'Slightly elevated',  note: 'Possible AC condensate drain issue' },
    energy: { level: 'high',     value: '39 kWh/day',         note: 'Workstation + AC anomaly detected (Jan 19)' },
    waste:  { level: 'medium',   value: '12 kg/day',          note: 'E-waste and packaging — partly recoverable' },
    rec: 'Smart power strips for auto-cutoff. Monthly e-waste certified collection recommended.',
    agent: 'Energy + Waste Agent',
  },
  {
    id: 'canteen',    name: 'Canteen',             emoji: '🍽', type: 'Food Service',
    risk: 'medium',   occupancy: '~500 meals/day',
    water:  { level: 'low',      value: 'Normal',             note: 'Operational usage within baseline' },
    energy: { level: 'low',      value: '8 kWh/day',          note: 'Within expected operational range' },
    waste:  { level: 'high',     value: '28 kg/day',          note: 'High organic + packaging — high recovery potential' },
    rec: 'Compost organic waste on-site. Transition to biodegradable packaging by next quarter.',
    agent: 'Waste-to-Wealth Agent',
  },
  {
    id: 'admin',      name: 'Admin Block',         emoji: '🏢', type: 'Administrative',
    risk: 'low',      occupancy: '~35 staff',
    water:  { level: 'none',     value: 'No anomalies',       note: 'All readings within normal range' },
    energy: { level: 'medium',   value: '14 kWh/day',         note: 'Some computers left on after hours' },
    waste:  { level: 'low',      value: '5 kg/day',           note: 'Paper and dry waste — recyclable' },
    rec: 'Default-off computer policy. Add paper recycling bins at each workstation cluster.',
    agent: 'Decision Engine',
  },
]

function DomainRow({ icon, label, level, value, note }) {
  const col = RC[level] || '#6b7280'
  return (
    <div className="flex items-start gap-3 py-2.5 border-b last:border-0" style={{ borderColor: 'rgba(255,255,255,0.05)' }}>
      <div className="flex items-center gap-1.5 w-20 flex-shrink-0 mt-0.5" style={{ color: col }}>
        {icon}
        <span className="text-xs text-slate-500">{label}</span>
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5">
          <span className="text-xs font-bold" style={{ color: col }}>{RL[level]}</span>
          <span className="text-xs text-slate-400 truncate">{value}</span>
        </div>
        <p className="text-xs text-slate-600 leading-relaxed">{note}</p>
      </div>
    </div>
  )
}

function BuildingCard({ b, isSelected, onClick }) {
  return (
    <div onClick={onClick} className="building-card rounded-xl p-4" style={{
      background: RB[b.risk],
      border: `1px solid ${isSelected ? RC[b.risk] + '80' : RBR[b.risk]}`,
      boxShadow: isSelected ? `0 0 20px ${RC[b.risk]}22, 0 8px 30px rgba(0,0,0,0.35)` : undefined,
    }}>
      <div className="flex items-start justify-between mb-3">
        <div>
          <span className="text-2xl mb-1.5 block leading-none">{b.emoji}</span>
          <p className="text-xs font-bold text-white leading-tight">{b.name}</p>
          <p className="text-xs text-slate-500 mt-0.5">{b.type}</p>
        </div>
        <span className="text-xs px-2 py-1 rounded-full font-black" style={{
          background: RC[b.risk] + '18', border: `1px solid ${RC[b.risk]}40`, color: RC[b.risk],
        }}>{RL[b.risk]}</span>
      </div>
      <div className="flex items-center gap-2 mt-2 pt-2" style={{ borderTop: `1px solid ${RC[b.risk]}18` }}>
        {[
          { icon: '💧', level: b.water.level },
          { icon: '⚡', level: b.energy.level },
          { icon: '♻', level: b.waste.level },
        ].map((d, i) => (
          <div key={i} className="flex items-center gap-1 text-xs">
            <span>{d.icon}</span>
            <div className="w-1.5 h-1.5 rounded-full" style={{ background: RC[d.level] }} />
          </div>
        ))}
        <span className="ml-auto text-slate-600">
          {isSelected
            ? <ChevronUp className="w-3.5 h-3.5" />
            : <ChevronDown className="w-3.5 h-3.5" />}
        </span>
      </div>
    </div>
  )
}

export default function DigitalTwinCampus() {
  const [selected, setSelected] = useState(null)
  const sorted = [...BUILDINGS].sort((a, b) => RO[b.risk] - RO[a.risk])
  const sel = BUILDINGS.find(b => b.id === selected)

  const criticalCount = BUILDINGS.filter(b => b.risk === 'critical').length
  const highCount     = BUILDINGS.filter(b => b.risk === 'high').length

  return (
    <section className="px-6 py-16 max-w-7xl mx-auto" id="twin">
      <div className="mb-8">
        <h2 className="text-3xl font-black text-white mb-2">
          Campus <span className="text-gradient-blue">Digital Twin</span>
        </h2>
        <p className="text-slate-400 text-sm max-w-2xl">
          Agent-computed building-level risk map derived from simulated 7-day sensor logs.
          Click any zone to expand its full diagnostic breakdown and recommended intervention.
        </p>
      </div>

      {/* Summary alerts */}
      <div className="flex flex-wrap gap-3 mb-6">
        {criticalCount > 0 && (
          <div className="flex items-center gap-2 px-4 py-2 rounded-lg"
            style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.3)' }}>
            <AlertTriangle className="w-4 h-4 text-red-400" />
            <span className="text-sm font-bold text-red-400">
              {criticalCount} building critical — immediate action required
            </span>
          </div>
        )}
        {highCount > 0 && (
          <div className="flex items-center gap-2 px-4 py-2 rounded-lg"
            style={{ background: 'rgba(249,115,22,0.08)', border: '1px solid rgba(249,115,22,0.3)' }}>
            <AlertTriangle className="w-4 h-4 text-orange-400" />
            <span className="text-sm font-bold text-orange-400">{highCount} buildings high risk</span>
          </div>
        )}
        <div className="flex items-center gap-2 px-4 py-2 rounded-lg"
          style={{ background: 'rgba(0,229,255,0.05)', border: '1px solid rgba(0,229,255,0.15)' }}>
          <MapPin className="w-4 h-4 text-cyan-400" />
          <span className="text-sm text-cyan-400">{BUILDINGS.length} campus zones monitored</span>
        </div>
      </div>

      {/* Building grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-5">
        {sorted.map(b => (
          <BuildingCard
            key={b.id}
            b={b}
            isSelected={selected === b.id}
            onClick={() => setSelected(selected === b.id ? null : b.id)}
          />
        ))}
      </div>

      {/* Expanded detail */}
      {sel && (
        <div className="glass-card p-6 fade-in" style={{ borderColor: RC[sel.risk] + '30' }}>
          <div className="flex flex-col sm:flex-row items-start gap-4 mb-6">
            <div className="flex items-center gap-4">
              <span className="text-4xl">{sel.emoji}</span>
              <div>
                <h3 className="text-xl font-black text-white">{sel.name}</h3>
                <p className="text-slate-500 text-sm">{sel.type} · {sel.occupancy}</p>
              </div>
            </div>
            <div className="sm:ml-auto text-left sm:text-right">
              <span className="inline-block px-3 py-1.5 rounded-full font-black text-sm" style={{
                background: RC[sel.risk] + '18', border: `1px solid ${RC[sel.risk]}50`, color: RC[sel.risk],
              }}>{RL[sel.risk]} RISK</span>
              <p className="text-xs text-slate-600 mt-1">Flagged by: {sel.agent}</p>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-widest mb-3">Resource Domain Analysis</p>
              <DomainRow icon={<Droplets className="w-3.5 h-3.5" />} label="Water"
                level={sel.water.level} value={sel.water.value} note={sel.water.note} />
              <DomainRow icon={<Zap className="w-3.5 h-3.5" />} label="Energy"
                level={sel.energy.level} value={sel.energy.value} note={sel.energy.note} />
              <DomainRow icon={<Trash2 className="w-3.5 h-3.5" />} label="Waste"
                level={sel.waste.level} value={sel.waste.value} note={sel.waste.note} />
            </div>

            <div>
              <p className="text-xs text-slate-500 uppercase tracking-widest mb-3">Agent Recommendation</p>
              <div className="p-4 rounded-xl mb-4" style={{
                background: 'rgba(0,255,136,0.04)', border: '1px solid rgba(0,255,136,0.15)',
              }}>
                <p className="text-sm text-green-400 leading-relaxed">{sel.rec}</p>
              </div>

              <div className="grid grid-cols-3 gap-2 text-center">
                {[
                  { label: 'Water',  level: sel.water.level },
                  { label: 'Energy', level: sel.energy.level },
                  { label: 'Waste',  level: sel.waste.level },
                ].map(d => (
                  <div key={d.label} className="p-2 rounded-lg" style={{
                    background: RC[d.level] + '0e', border: `1px solid ${RC[d.level]}25`,
                  }}>
                    <p className="text-xs text-slate-500 mb-0.5">{d.label}</p>
                    <p className="text-xs font-bold" style={{ color: RC[d.level] }}>{RL[d.level]}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="flex flex-wrap items-center gap-4 mt-4 text-xs">
        <span className="text-slate-500 font-semibold">Risk:</span>
        {Object.entries(RL).map(([key, label]) => (
          <div key={key} className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full" style={{
              background: RC[key] + '80', border: `1px solid ${RC[key]}`,
            }} />
            <span style={{ color: RC[key] }}>{label}</span>
          </div>
        ))}
        <span className="text-slate-600 ml-2">— Click building to expand · Simulated sensor data</span>
      </div>
    </section>
  )
}
