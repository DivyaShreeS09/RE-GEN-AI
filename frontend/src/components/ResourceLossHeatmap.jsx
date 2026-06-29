import { Droplets, Zap, Trash2, AlertTriangle } from 'lucide-react'

const ZONES = [
  {
    name: 'Block-B Hostel',
    water: 'high',     waterNote: 'Night-flow anomaly detected (Jan 16)',
    energy: 'medium',  energyNote: 'Moderate after-hours usage',
    waste: 'low',      wasteNote: 'Low-value organic waste',
    risk: 'high',
  },
  {
    name: 'Lab Block',
    water: 'critical', waterNote: 'Major leak detected (Jan 19) — 3–5 AM',
    energy: 'high',    energyNote: 'Extended equipment runtime',
    waste: 'medium',   wasteNote: 'E-waste and paper mix',
    risk: 'critical',
  },
  {
    name: 'Seminar Hall',
    water: 'low',      waterNote: 'Normal consumption',
    energy: 'critical',energyNote: 'AC + lighting left on overnight (Jan 16)',
    waste: 'low',      wasteNote: 'Minimal waste generation',
    risk: 'high',
  },
  {
    name: 'Computer Lab',
    water: 'medium',   waterNote: 'Slightly elevated — check AC condensate',
    energy: 'high',    energyNote: 'Equipment + AC anomaly (Jan 19)',
    waste: 'medium',   wasteNote: 'E-waste and packaging',
    risk: 'high',
  },
  {
    name: 'Canteen',
    water: 'low',      waterNote: 'Normal operational usage',
    energy: 'low',     energyNote: 'Within expected range',
    waste: 'high',     wasteNote: 'Food waste + packaging — recoverable',
    risk: 'medium',
  },
  {
    name: 'Admin Block',
    water: 'none',     waterNote: 'No anomalies detected',
    energy: 'medium',  energyNote: 'Some after-hours computer usage',
    waste: 'low',      wasteNote: 'Paper and dry waste — recyclable',
    risk: 'low',
  },
]

const RISK_ORDER = { critical: 4, high: 3, medium: 2, low: 1, none: 0 }
const RISK_LABEL = { critical: 'CRITICAL', high: 'HIGH', medium: 'MODERATE', low: 'LOW', none: 'CLEAR' }
const RISK_COLOR = { critical: '#ef4444', high: '#f97316', medium: '#eab308', low: '#22c55e', none: '#6b7280' }

function RiskCell({ level, note }) {
  return (
    <div className={`px-2 py-1.5 rounded-lg text-center heatmap-${level}`} title={note}>
      <p className="text-xs font-bold">{level.toUpperCase()}</p>
    </div>
  )
}

export default function ResourceLossHeatmap() {
  const sortedZones = [...ZONES].sort((a, b) => RISK_ORDER[b.risk] - RISK_ORDER[a.risk])
  const criticalCount = ZONES.filter(z => z.risk === 'critical').length
  const highCount = ZONES.filter(z => z.risk === 'high').length

  return (
    <section className="px-6 py-16 max-w-7xl mx-auto" id="heatmap">
      <div className="mb-8">
        <h2 className="text-3xl font-black text-white mb-2">
          Campus Zone <span className="text-gradient-orange">Risk Heatmap</span>
        </h2>
        <p className="text-slate-400 text-sm">
          Zone-level resource risk derived from simulated sensor data.
          Risk levels are agent-computed from anomaly frequency, volume, and cost impact.
        </p>
      </div>

      {/* Summary row */}
      <div className="flex flex-wrap gap-4 mb-6">
        {criticalCount > 0 && (
          <div className="flex items-center gap-2 px-4 py-2 rounded-lg" style={{
            background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)'
          }}>
            <AlertTriangle className="w-4 h-4 text-red-400" />
            <span className="text-sm text-red-400 font-bold">{criticalCount} zone{criticalCount > 1 ? 's' : ''} critical</span>
          </div>
        )}
        {highCount > 0 && (
          <div className="flex items-center gap-2 px-4 py-2 rounded-lg" style={{
            background: 'rgba(249,115,22,0.1)', border: '1px solid rgba(249,115,22,0.3)'
          }}>
            <AlertTriangle className="w-4 h-4 text-orange-400" />
            <span className="text-sm text-orange-400 font-bold">{highCount} zone{highCount > 1 ? 's' : ''} high risk</span>
          </div>
        )}
      </div>

      {/* Table heatmap */}
      <div className="glass-card overflow-hidden mb-6">
        {/* Header */}
        <div className="grid grid-cols-5 gap-0 border-b px-4 py-3"
          style={{ borderColor: 'rgba(0,229,255,0.1)', background: 'rgba(0,0,0,0.2)' }}>
          <div className="text-xs font-bold text-slate-400 uppercase tracking-wider">Zone</div>
          <div className="flex items-center justify-center gap-1 text-xs font-bold text-cyan-400 uppercase tracking-wider">
            <Droplets className="w-3 h-3" /> Water
          </div>
          <div className="flex items-center justify-center gap-1 text-xs font-bold text-yellow-400 uppercase tracking-wider">
            <Zap className="w-3 h-3" /> Energy
          </div>
          <div className="flex items-center justify-center gap-1 text-xs font-bold text-green-400 uppercase tracking-wider">
            <Trash2 className="w-3 h-3" /> Waste
          </div>
          <div className="text-xs font-bold text-white uppercase tracking-wider text-center">Overall</div>
        </div>

        <div className="divide-y" style={{ borderColor: 'rgba(255,255,255,0.04)' }}>
          {sortedZones.map((zone, i) => (
            <div key={i} className="grid grid-cols-5 gap-0 px-4 py-3 items-center hover:bg-white/2 transition-colors">
              <div>
                <p className="text-sm font-semibold text-white">{zone.name}</p>
                <p className="text-xs text-slate-500 mt-0.5 leading-tight">{zone.waterNote}</p>
              </div>
              <div className="px-2"><RiskCell level={zone.water} note={zone.waterNote} /></div>
              <div className="px-2"><RiskCell level={zone.energy} note={zone.energyNote} /></div>
              <div className="px-2"><RiskCell level={zone.waste} note={zone.wasteNote} /></div>
              <div className="px-2">
                <div className={`px-2 py-1.5 rounded-lg text-center heatmap-${zone.risk}`}>
                  <p className="text-xs font-black">{RISK_LABEL[zone.risk]}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Zone cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
        {sortedZones.map((zone, i) => (
          <div key={i} className={`p-3 rounded-xl heatmap-${zone.risk} agent-card-hover fade-in`}
            style={{ animationDelay: `${i * 0.07}s` }}>
            <p className="text-xs font-bold mb-1">{zone.name}</p>
            <p className="text-xs opacity-70 font-black">{RISK_LABEL[zone.risk]}</p>
            <div className="flex gap-1 mt-2">
              <span className={`text-xs heatmap-${zone.water} px-1 rounded`} title="Water">💧</span>
              <span className={`text-xs heatmap-${zone.energy} px-1 rounded`} title="Energy">⚡</span>
              <span className={`text-xs heatmap-${zone.waste} px-1 rounded`} title="Waste">♻️</span>
            </div>
          </div>
        ))}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap items-center gap-4 text-xs">
        <span className="text-slate-500 font-semibold">Risk levels:</span>
        {['critical','high','medium','low','none'].map(r => (
          <div key={r} className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded" style={{ background: RISK_COLOR[r] + '40', border: `1px solid ${RISK_COLOR[r]}60` }} />
            <span style={{ color: RISK_COLOR[r] }}>{RISK_LABEL[r]}</span>
          </div>
        ))}
        <span className="text-slate-600 ml-2">— Derived from simulated sensor data</span>
      </div>
    </section>
  )
}
