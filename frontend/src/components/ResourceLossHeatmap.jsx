import { Droplets, Zap, Trash2, AlertTriangle, CheckCircle, XCircle } from 'lucide-react'

/* ── Demo zones (only shown in Demo Mode) ─────────────────────────── */
const DEMO_ZONES = [
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

/* ── Build upload-mode zones from anomaly events ─────────────────── */
function buildUploadZones(waterData, energyData) {
  const zoneMap = {}

  const addWater = (loc, severity, note) => {
    if (!zoneMap[loc]) zoneMap[loc] = { name: loc, water: 'none', energy: 'none', waste: 'low', waterNote: 'No anomalies', energyNote: 'No data', wasteNote: 'Not analysed' }
    const cur = RISK_ORDER[zoneMap[loc].water] || 0
    if ((RISK_ORDER[severity] || 0) > cur) {
      zoneMap[loc].water = severity
      zoneMap[loc].waterNote = note
    }
  }

  const addEnergy = (zone, severity, note) => {
    if (!zoneMap[zone]) zoneMap[zone] = { name: zone, water: 'none', energy: 'none', waste: 'low', waterNote: 'No data', energyNote: 'No anomalies', wasteNote: 'Not analysed' }
    const cur = RISK_ORDER[zoneMap[zone].energy] || 0
    if ((RISK_ORDER[severity] || 0) > cur) {
      zoneMap[zone].energy = severity
      zoneMap[zone].energyNote = note
    }
  }

  if (waterData?.anomaly_events?.length) {
    waterData.anomaly_events.forEach(ev => {
      const loc = ev.location || 'Water Zone'
      const sev = ev.severity || 'medium'
      const note = ev.liters_wasted
        ? `${ev.liters_wasted.toFixed(0)} L anomalous flow`
        : 'Anomaly detected'
      addWater(loc, sev, note)
    })
  } else if (waterData?.status === 'analyzed') {
    const loc = 'Main Water Zone'
    const sev = waterData.severity || 'medium'
    addWater(loc, sev, `${(waterData.total_wasted_liters || 0).toFixed(0)} L wasted`)
  }

  if (energyData?.anomaly_events?.length) {
    energyData.anomaly_events.forEach(ev => {
      const zone = ev.zone || ev.location || 'Energy Zone'
      const sev = ev.severity || 'medium'
      const note = ev.kwh_wasted
        ? `${ev.kwh_wasted.toFixed(1)} kWh after-hours waste`
        : 'After-hours anomaly'
      addEnergy(zone, sev, note)
    })
  } else if (energyData?.status === 'analyzed') {
    const zone = 'Main Energy Zone'
    const sev = energyData.severity || 'medium'
    addEnergy(zone, sev, `${(energyData.total_wasted_kwh || 0).toFixed(1)} kWh wasted`)
  }

  return Object.values(zoneMap).map(z => {
    const wRisk = RISK_ORDER[z.water] || 0
    const eRisk = RISK_ORDER[z.energy] || 0
    const total = wRisk + eRisk
    z.risk = total >= 7 ? 'critical' : total >= 5 ? 'high' : total >= 3 ? 'medium' : total >= 1 ? 'low' : 'none'
    return z
  })
}

function RiskCell({ level, note }) {
  return (
    <div className={`px-2 py-1.5 rounded-lg text-center heatmap-${level}`} title={note}>
      <p className="text-xs font-bold">{level.toUpperCase()}</p>
    </div>
  )
}

/* ── Coverage map for Level 1/2 (no anomaly detection) ──────────── */
function CoverageMap({ waterData, energyData, uploadResult }) {
  const meta = uploadResult?.analysis_metadata || {}
  const skipped = meta.skipped_modules || []
  const levelLabel = meta.overall_label || 'Basic Assessment'
  const conf = meta.confidence_pct || 0

  const hasWater  = waterData && waterData.status !== 'skipped'
  const hasEnergy = energyData && energyData.status !== 'skipped'
  const hasWaste  = false // waste is handled separately via WasteAnalyzer

  const availableAnalyses = [
    { label: 'Sustainability Scoring',    available: true },
    { label: 'Carbon Estimation',         available: true },
    { label: 'Cost Benchmarking',         available: hasWater || hasEnergy },
    { label: 'Executive Summary',         available: true },
    { label: 'Broad Recommendations',     available: true },
  ]

  const unavailableAnalyses = [
    { label: 'Leak Detection',            reason: 'Requires hourly water data (≥ 3 days)' },
    { label: 'Anomaly Detection',         reason: 'Requires hourly time-series (≥ 12 hrs/day, ≥ 48 records)' },
    { label: 'Zone-Level Risk Heatmap',   reason: 'Derived from anomaly events — unavailable at this resolution' },
    { label: 'After-Hours Energy Waste',  reason: 'Requires hourly energy timestamps' },
    { label: 'Predictive Maintenance',    reason: 'Requires multi-day hourly patterns' },
  ]

  const datasets = [
    { label: 'Water',  available: hasWater,  value: hasWater  ? `${(waterData.total_consumption_liters || 0).toLocaleString()} L` : null },
    { label: 'Energy', available: hasEnergy, value: hasEnergy ? `${(energyData.total_consumption_kwh || 0).toFixed(1)} kWh` : null },
    { label: 'Waste',  available: hasWaste,  value: null },
    { label: 'Fuel',   available: false,     value: null },
  ]

  return (
    <section className="px-6 py-16 max-w-7xl mx-auto" id="heatmap">
      <div className="mb-8">
        <h2 className="text-3xl font-black text-white mb-2">
          Analysis <span className="text-gradient-orange">Coverage Map</span>
        </h2>
        <p className="text-slate-400 text-sm">
          Zone-level risk heatmap requires anomaly detection (Level 3 hourly data).
          Showing what was analysed and what requires additional data.
        </p>
      </div>

      {/* Level notice */}
      <div className="glass-card p-5 mb-6" style={{ border: '1px solid rgba(245,158,11,0.22)' }}>
        <div className="flex items-start gap-3">
          <div style={{ fontSize: 24, flexShrink: 0 }}>⊘</div>
          <div>
            <p className="font-bold text-sm mb-1" style={{ color: '#f59e0b' }}>
              Zone Risk Heatmap Unavailable — {levelLabel}
            </p>
            <p className="text-xs text-slate-400 leading-relaxed">
              The zone-level resource risk heatmap is generated from anomaly detection events.
              Anomaly detection requires hourly time-series data spanning ≥ 3 days with ≥ 12 unique hours per day.
              The current data resolution ({levelLabel}, confidence {conf}%) does not support this analysis.
              Provide hourly operational logs (CSV from smart meters or BMS) to unlock the full heatmap.
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Provided datasets */}
        <div className="glass-card p-5">
          <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4">Datasets Provided</p>
          <div className="space-y-3">
            {datasets.map(({ label, available, value }) => (
              <div key={label} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {available
                    ? <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0" />
                    : <XCircle className="w-4 h-4 text-slate-600 flex-shrink-0" />
                  }
                  <span className="text-sm" style={{ color: available ? '#e2e8f0' : '#475569' }}>{label}</span>
                </div>
                {value && <span className="text-xs text-cyan-400 font-bold">{value}</span>}
                {!available && <span className="text-xs text-slate-600">Not provided</span>}
              </div>
            ))}
          </div>
        </div>

        {/* Available analyses */}
        <div className="glass-card p-5">
          <p className="text-xs font-bold text-green-400 uppercase tracking-wider mb-4">Available at This Level</p>
          <div className="space-y-2">
            {availableAnalyses.map(({ label, available }) => (
              <div key={label} className="flex items-center gap-2">
                {available
                  ? <CheckCircle className="w-3.5 h-3.5 text-green-400 flex-shrink-0" />
                  : <XCircle className="w-3.5 h-3.5 text-slate-600 flex-shrink-0" />
                }
                <span className="text-xs" style={{ color: available ? '#94a3b8' : '#475569' }}>{label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Unavailable analyses */}
        <div className="glass-card p-5">
          <p className="text-xs font-bold text-amber-400 uppercase tracking-wider mb-4">Requires Higher-Resolution Data</p>
          <div className="space-y-3">
            {unavailableAnalyses.map(({ label, reason }) => (
              <div key={label}>
                <div className="flex items-center gap-2 mb-0.5">
                  <XCircle className="w-3.5 h-3.5 text-amber-500 flex-shrink-0" />
                  <span className="text-xs text-amber-400 font-semibold">{label}</span>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed ml-5">{reason}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-6 p-4 rounded-xl text-xs leading-relaxed text-slate-500"
        style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)' }}>
        <strong className="text-slate-400">How to unlock the full heatmap:</strong> Export hourly sensor data from your water meters,
        energy meters, or Building Management System (BMS) as CSV files with timestamp, consumption, and zone columns.
        Upload these files for Level 3 Advanced Analysis with full anomaly detection and zone-level risk mapping.
      </div>
    </section>
  )
}

export default function ResourceLossHeatmap({ waterData, energyData, uploadResult }) {
  const isUploadMode = !!uploadResult
  const anomalyAvailable = !isUploadMode || (uploadResult?.analysis_metadata?.anomaly_detection_available !== false)

  // In upload mode without anomaly detection: show Coverage Map instead of fabricated zones
  if (isUploadMode && !anomalyAvailable) {
    return <CoverageMap waterData={waterData} energyData={energyData} uploadResult={uploadResult} />
  }

  const zones = isUploadMode
    ? buildUploadZones(waterData, energyData)
    : DEMO_ZONES

  // In upload mode: never fall back to DEMO_ZONES — show empty state with message instead
  const zonesWithData = isUploadMode ? zones : (zones.length > 0 ? zones : DEMO_ZONES)
  const sortedZones = [...zonesWithData].sort((a, b) => RISK_ORDER[b.risk] - RISK_ORDER[a.risk])
  const criticalCount = zonesWithData.filter(z => z.risk === 'critical').length
  const highCount = zonesWithData.filter(z => z.risk === 'high').length

  const headingLabel = isUploadMode ? 'Resource Zone' : 'Campus Zone'
  const dataSourceNote = isUploadMode
    ? `Zone risk derived from detected anomaly events in uploaded data. ${zonesWithData.length} zone${zonesWithData.length !== 1 ? 's' : ''} with anomalies.`
    : 'Zone-level resource risk derived from simulated sensor data. Risk levels are agent-computed from anomaly frequency, volume, and cost impact.'

  // Upload mode with no anomaly zones found — show honest empty state
  if (isUploadMode && zonesWithData.length === 0) {
    return (
      <section className="px-6 py-16 max-w-7xl mx-auto" id="heatmap">
        <div className="mb-8">
          <h2 className="text-3xl font-black text-white mb-2">
            Resource Zone <span className="text-gradient-orange">Risk Heatmap</span>
          </h2>
        </div>
        <div className="glass-card p-8 text-center">
          <p className="text-slate-400 mb-3">No anomaly zones detected in the uploaded data.</p>
          <p className="text-slate-600 text-sm">
            The heatmap is populated by anomaly events from water and energy analysis.
            No anomalies were flagged in the current dataset.
          </p>
        </div>
      </section>
    )
  }

  return (
    <section className="px-6 py-16 max-w-7xl mx-auto" id="heatmap">
      <div className="mb-8">
        <h2 className="text-3xl font-black text-white mb-2">
          {headingLabel} <span className="text-gradient-orange">Risk Heatmap</span>
        </h2>
        <p className="text-slate-400 text-sm">{dataSourceNote}</p>
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
        <span className="text-slate-600 ml-2">
          — {isUploadMode ? 'Derived from detected anomaly events in uploaded data' : 'Derived from simulated sensor data'}
        </span>
      </div>
    </section>
  )
}
