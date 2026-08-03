import { useEffect, useState } from 'react'
import { Droplets, Zap, Leaf, AlertTriangle, TrendingUp, DollarSign, TrendingDown, CheckCircle, Activity, Car, Home, Plane } from 'lucide-react'
import RegenScoreGauge from './RegenScoreGauge'
import useCountUp from '../hooks/useCountUp'

function ScanTimeline({ anomalyAvailable }) {
  const SCAN_STAGES = [
    { label: 'Sensor data loaded',                                          icon: '📡' },
    { label: anomalyAvailable ? 'Anomalies detected' : 'Consumption analysed', icon: '🔍' },
    { label: 'Impact quantified',                                           icon: '📊' },
    { label: 'Interventions ranked',                                        icon: '🧠' },
    { label: 'Action plan generated',                                       icon: '✅' },
  ]
  const [active, setActive] = useState(0)
  useEffect(() => {
    if (active >= SCAN_STAGES.length - 1) return
    const t = setTimeout(() => setActive(i => i + 1), 500)
    return () => clearTimeout(t)
  }, [active, SCAN_STAGES.length])
  return (
    <div className="glass-card p-5 mb-8">
      <p className="text-xs font-bold text-cyan-400 uppercase tracking-widest mb-4">Analysis Pipeline</p>
      <div className="flex items-center gap-1 flex-wrap">
        {SCAN_STAGES.map((s, i) => (
          <div key={i} className="flex items-center gap-1">
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-500 ${
              i < active  ? 'bg-green-500/10 text-green-400 border border-green-500/25' :
              i === active ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-400/40 animate-pulse' :
                             'bg-slate-800/50 text-slate-600 border border-slate-700/50'
            }`}>
              {i < active ? <CheckCircle className="w-3 h-3" /> : <span>{s.icon}</span>}
              {s.label}
            </div>
            {i < SCAN_STAGES.length - 1 && (
              <div className={`w-6 h-px transition-all duration-500 ${i < active ? 'bg-green-400' : 'bg-slate-700'}`} />
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

/* Story tooltip rows — What / Why / Next / Impact */
function StoryBlock({ what, why, next, impact }) {
  return (
    <div className="mt-3 pt-3 space-y-1" style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}>
      {[['What?', what, '#94a3b8'], ['Why?', why, '#64748b'], ['Next?', next, '#00e5ff'], ['Impact?', impact, '#00ff88']].map(([q, a, c]) => (
        <div key={q} className="story-item">
          <span className="story-q">{q}</span>
          <span className="story-a" style={{ color: c }}>{a}</span>
        </div>
      ))}
    </div>
  )
}

function StatCard({ icon, label, value, unit, color, sublabel, trend, story }) {
  return (
    <div className="glass-card p-5 agent-card-hover">
      <div className="flex items-start justify-between mb-3">
        <div className="p-2 rounded-lg" style={{ background: `${color}15` }}>
          <div style={{ color }}>{icon}</div>
        </div>
        {trend && (
          <div className={`flex items-center gap-0.5 text-xs font-semibold ${
            trend === 'up' ? 'text-green-400' : trend === 'down' ? 'text-red-400' : 'text-slate-500'
          }`}>
            {trend === 'up' ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
            {trend === 'up' ? 'Recoverable' : 'Loss Risk'}
          </div>
        )}
      </div>
      <p className="text-slate-400 text-xs uppercase tracking-wider mb-1">{label}</p>
      <p className="text-2xl font-black count-up" style={{ color }}>
        {value} <span className="text-sm font-normal text-slate-400">{unit}</span>
      </p>
      {sublabel && <p className="text-slate-500 text-xs mt-1">{sublabel}</p>}
      {story && <StoryBlock {...story} />}
    </div>
  )
}

function SilentLossCard({ losses, isUploadMode, orgType, anomalyAvailable, waterConsumption, energyConsumption }) {
  const waterLoss = losses?.water_leakage_liters || 0
  const energyLoss = losses?.energy_wasted_kwh   || 0
  const waterCost  = losses?.water_cost_inr       || 0
  const energyCost = losses?.energy_cost_inr      || 0
  const totalCost  = waterCost + energyCost

  if (isUploadMode && !anomalyAvailable) {
    return (
      <div className="glass-card p-6" style={{ border: '1px solid rgba(245,158,11,0.20)' }}>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-amber-400" />
            <h3 className="font-bold uppercase tracking-wider text-sm" style={{ color: '#f59e0b' }}>Resource Consumption Summary</h3>
          </div>
          <span className="text-xs px-2 py-1 rounded-full"
            style={{ background: 'rgba(245,158,11,0.10)', border: '1px solid rgba(245,158,11,0.28)', color: '#f59e0b' }}>
            Consumption estimates only
          </span>
        </div>
        <p className="text-xs text-slate-500 mb-4 leading-relaxed">
          Consumption data from uploaded {orgType || 'organizational'} data.
          Leak detection, after-hours energy waste, and anomaly events require hourly time-series data (Level 3).
          All values are estimates derived from the provided totals.
        </p>
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center p-3 rounded-lg" style={{ background: 'rgba(0,229,255,0.06)', border: '1px solid rgba(0,229,255,0.15)' }}>
            <p className="text-slate-500 text-xs mb-1">Water Consumption</p>
            <p className="text-2xl font-bold text-cyan-400">{(waterConsumption || 0).toLocaleString()}</p>
            <p className="text-xs text-slate-500">liters (period total)</p>
            <p className="text-xs mt-2" style={{ color: '#f59e0b' }}>Leak detection: unavailable</p>
          </div>
          <div className="text-center p-3 rounded-lg" style={{ background: 'rgba(234,179,8,0.06)', border: '1px solid rgba(234,179,8,0.15)' }}>
            <p className="text-slate-500 text-xs mb-1">Energy Consumption</p>
            <p className="text-2xl font-bold text-yellow-400">{(energyConsumption || 0).toFixed(1)}</p>
            <p className="text-xs text-slate-500">kWh (period total)</p>
            <p className="text-xs mt-2" style={{ color: '#f59e0b' }}>After-hours detection: unavailable</p>
          </div>
          <div className="text-center p-3 rounded-lg" style={{ background: 'rgba(0,255,136,0.06)', border: '1px solid rgba(0,255,136,0.15)' }}>
            <p className="text-slate-500 text-xs mb-1">Recoverable Waste Value</p>
            <p className="text-2xl font-bold text-green-400">₹{(losses?.waste_hidden_value_inr || losses?.total_recoverable_inr || 0).toFixed(0)}</p>
            <p className="text-xs text-slate-500">est. potential</p>
            <p className="text-xs text-green-400 mt-2">Waste streams only</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="glass-card-red p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-red-400" />
          <h3 className="text-red-400 font-bold uppercase tracking-wider text-sm">Hidden Resource Loss</h3>
        </div>
        <span className="text-xs px-2 py-1 rounded-full"
          style={{ background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.3)', color: '#ef4444' }}>
          ₹{totalCost.toFixed(0)} estimated weekly loss
        </span>
      </div>
      <p className="text-xs text-slate-500 mb-4 leading-relaxed">
        {isUploadMode
          ? `Hidden resource loss detected from uploaded ${orgType || 'organizational'} data across water, energy, and waste streams. Costs are estimates based on standard utility rates.`
          : 'Hidden resource loss detected from simulated sensor logs across water, energy, and waste streams. Costs are estimates based on standard utility rates — not real billing data.'}
      </p>
      <div className="grid grid-cols-3 gap-4">
        <div className="text-center p-3 rounded-lg"
          style={{ background: 'rgba(239,68,68,0.06)', border: '1px solid rgba(239,68,68,0.15)' }}>
          <p className="text-slate-500 text-xs mb-1">Water Leakage Detected</p>
          <p className="text-2xl font-bold text-red-400">{waterLoss.toLocaleString()}</p>
          <p className="text-xs text-slate-500">liters (analysis window)</p>
          <p className="text-xs text-red-400 mt-2">approx. ₹{waterCost.toFixed(0)} loss</p>
        </div>
        <div className="text-center p-3 rounded-lg"
          style={{ background: 'rgba(249,115,22,0.06)', border: '1px solid rgba(249,115,22,0.15)' }}>
          <p className="text-slate-500 text-xs mb-1">After-Hours Energy Waste</p>
          <p className="text-2xl font-bold text-orange-400">{energyLoss.toFixed(1)}</p>
          <p className="text-xs text-slate-500">kWh (analysis window)</p>
          <p className="text-xs text-orange-400 mt-2">approx. ₹{energyCost.toFixed(0)} loss</p>
        </div>
        <div className="text-center p-3 rounded-lg"
          style={{ background: 'rgba(0,255,136,0.06)', border: '1px solid rgba(0,255,136,0.15)' }}>
          <p className="text-slate-500 text-xs mb-1">Recoverable Waste Value</p>
          <p className="text-2xl font-bold text-green-400">₹{(losses?.total_recoverable_inr || 0).toFixed(0)}</p>
          <p className="text-xs text-slate-500">est. potential</p>
          <p className="text-xs text-green-400 mt-2">Waste streams only</p>
        </div>
      </div>
    </div>
  )
}

function CampusRiskCard({ waterSev, energySev, anomalyCount, anomalyAvailable }) {
  const riskMap  = { critical: 4, high: 3, medium: 2, low: 1, none: 0 }
  const total    = (riskMap[waterSev] || 0) + (riskMap[energySev] || 0)
  const riskLabel = !anomalyAvailable ? 'UNASSESSED' : total >= 7 ? 'CRITICAL' : total >= 5 ? 'HIGH' : total >= 3 ? 'MODERATE' : 'LOW'
  const riskColor = !anomalyAvailable ? '#64748b' : total >= 7 ? '#ef4444' : total >= 5 ? '#f97316' : total >= 3 ? '#eab308' : '#22c55e'

  return (
    <div className="glass-card p-5" style={{ border: `1px solid ${riskColor}25` }}>
      <p className="text-xs text-slate-500 uppercase tracking-widest mb-3">Resource Risk Level</p>
      <p className="text-3xl font-black mb-3" style={{ color: riskColor }}>{riskLabel}</p>
      {!anomalyAvailable ? (
        <div className="space-y-2">
          <p className="text-xs text-slate-500 leading-relaxed">
            Risk classification requires anomaly detection. Provide hourly time-series data to enable leak detection and after-hours energy analysis.
          </p>
          <div className="text-xs px-3 py-2 rounded-lg mt-2" style={{ background: 'rgba(245,158,11,0.07)', border: '1px solid rgba(245,158,11,0.18)', color: '#f59e0b' }}>
            Requires Level 3 data (hourly, ≥3 days)
          </div>
        </div>
      ) : (
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-xs text-slate-400">Water leakage risk</span>
            <span className={`text-xs font-semibold badge-${waterSev}`}>{waterSev?.toUpperCase()}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-xs text-slate-400">Energy waste risk</span>
            <span className={`text-xs font-semibold badge-${energySev}`}>{energySev?.toUpperCase()}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-xs text-slate-400">Total anomaly events</span>
            <span className="text-xs font-bold" style={{ color: riskColor }}>{anomalyCount} detected</span>
          </div>
        </div>
      )}
    </div>
  )
}

function BeforeAfterCard({ before, after, improvement, targetRating }) {
  return (
    <div className="glass-card p-5">
      <p className="text-xs text-slate-500 uppercase tracking-widest mb-4">Before vs After Intervention</p>
      <div className="grid grid-cols-3 gap-3 items-center">
        <div className="text-center">
          <p className="text-xs text-slate-500 mb-2">Current State</p>
          <p className="text-3xl font-black text-red-400">{before}</p>
          <p className="text-xs text-slate-500 mt-1">RE:GEN Score</p>
          <span className="text-xs badge-critical mt-2 inline-block">Pre-Action</span>
        </div>
        <div className="text-center">
          <div className="flex items-center justify-center gap-1 mb-1">
            <div className="h-px w-6 bg-green-400" />
            <span className="text-green-400 font-bold text-sm">+{improvement}</span>
            <div className="h-px w-6 bg-green-400" />
          </div>
          <p className="text-xs text-slate-500">if all actions</p>
          <p className="text-xs text-slate-500">are implemented</p>
        </div>
        <div className="text-center">
          <p className="text-xs text-slate-500 mb-2">Post-Action Target</p>
          <p className="text-3xl font-black text-green-400">{after}</p>
          <p className="text-xs text-slate-500 mt-1">RE:GEN Score</p>
          <span className="text-xs badge-low mt-2 inline-block">{targetRating}</span>
        </div>
      </div>
    </div>
  )
}

function CO2EquivalencesCard({ impact }) {
  const vehicleKm     = impact?.vehicle_km_equivalent     || 0
  const householdDays = impact?.household_days_equivalent || 0
  const flightsFrac   = impact?.flights_offset_fraction   || 0
  const co2Kg         = impact?.total_co2_saved_kg        || 0

  if (!co2Kg) return null

  return (
    <div className="glass-card-green p-6">
      <div className="flex items-center gap-2 mb-4">
        <Leaf className="w-5 h-5 text-green-400" />
        <h3 className="text-sm font-bold text-green-400 uppercase tracking-wider">
          CO₂ Reduction — What {co2Kg} kg Means
        </h3>
        <span className="ml-auto text-xs text-slate-600">Estimated sustainability impact</span>
      </div>
      <p className="text-xs text-slate-500 mb-4 leading-relaxed">
        If all agent-recommended interventions are applied, the estimated weekly CO2 reduction is
        equivalent to the following real-world analogies. These are estimates for educational context.
      </p>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 rounded-xl text-center"
          style={{ background: 'rgba(0,229,255,0.06)', border: '1px solid rgba(0,229,255,0.15)' }}>
          <Car className="w-6 h-6 text-cyan-400 mx-auto mb-2" />
          <p className="text-2xl font-black text-cyan-400">{vehicleKm.toLocaleString()}</p>
          <p className="text-xs text-slate-400 mt-1">km of car travel offset</p>
          <p className="text-xs text-slate-600 mt-1">@ 0.167 kg CO2/km (avg vehicle)</p>
        </div>
        <div className="p-4 rounded-xl text-center"
          style={{ background: 'rgba(0,255,136,0.06)', border: '1px solid rgba(0,255,136,0.15)' }}>
          <Home className="w-6 h-6 text-green-400 mx-auto mb-2" />
          <p className="text-2xl font-black text-green-400">{householdDays.toLocaleString()}</p>
          <p className="text-xs text-slate-400 mt-1">household-days powered</p>
          <p className="text-xs text-slate-600 mt-1">@ 2.87 kg CO2/household-day</p>
        </div>
        <div className="p-4 rounded-xl text-center"
          style={{ background: 'rgba(167,139,250,0.06)', border: '1px solid rgba(167,139,250,0.15)' }}>
          <Plane className="w-6 h-6 text-purple-400 mx-auto mb-2" />
          <p className="text-2xl font-black text-purple-400">{(flightsFrac * 100).toFixed(1)}%</p>
          <p className="text-xs text-slate-400 mt-1">of a short-haul flight offset</p>
          <p className="text-xs text-slate-600 mt-1">@ 200 kg CO2/person/flight</p>
        </div>
      </div>
      <p className="text-xs text-slate-700 text-center mt-4">
        Estimated values only — actual emissions reductions depend on intervention execution and site-specific baselines.
      </p>
    </div>
  )
}

function FuelCard({ fuelCo2Kg, fuelSummary }) {
  if (!fuelCo2Kg) return null
  const breakdown = fuelSummary?.breakdown || {}
  const fuelRows  = Object.entries(breakdown)
  const source    = fuelSummary?.source === 'manual_entry' ? 'Manual entry' : 'Uploaded file'
  const co2Color  = fuelCo2Kg > 500 ? '#ef4444' : fuelCo2Kg > 200 ? '#f97316' : '#eab308'

  return (
    <div className="glass-card p-5 mb-8" style={{ border: `1px solid ${co2Color}22` }}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span style={{ fontSize: 18 }}>⛽</span>
          <h3 className="text-sm font-bold uppercase tracking-wider" style={{ color: co2Color }}>
            Fuel Consumption
          </h3>
          <span className="text-xs text-slate-600 ml-1">— {source}</span>
        </div>
        <span className="text-xs px-2 py-1 rounded-full"
          style={{ background: `${co2Color}12`, border: `1px solid ${co2Color}28`, color: co2Color }}>
          {fuelCo2Kg.toFixed(1)} kg CO₂
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="text-center p-3 rounded-lg" style={{ background: `${co2Color}07`, border: `1px solid ${co2Color}15` }}>
          <p className="text-slate-500 text-xs mb-1">Total CO₂ from Fuel</p>
          <p className="text-2xl font-black" style={{ color: co2Color }}>{fuelCo2Kg.toFixed(1)}</p>
          <p className="text-xs text-slate-500">kg CO₂ equivalent</p>
        </div>
        {fuelSummary?.total_liters > 0 && (
          <div className="text-center p-3 rounded-lg" style={{ background: 'rgba(249,115,22,0.06)', border: '1px solid rgba(249,115,22,0.15)' }}>
            <p className="text-slate-500 text-xs mb-1">Total Volume</p>
            <p className="text-2xl font-black text-orange-400">{fuelSummary.total_liters.toLocaleString()}</p>
            <p className="text-xs text-slate-500">
              {fuelSummary.fuel_type ? `liters (${fuelSummary.fuel_type})` : 'liters'}
            </p>
          </div>
        )}
        {fuelSummary?.emission_factor && (
          <div className="text-center p-3 rounded-lg" style={{ background: 'rgba(148,163,184,0.05)', border: '1px solid rgba(148,163,184,0.12)' }}>
            <p className="text-slate-500 text-xs mb-1">Emission Factor</p>
            <p className="text-xl font-black text-slate-300">{fuelSummary.emission_factor}</p>
            <p className="text-xs text-slate-500">kg CO₂ / liter</p>
          </div>
        )}
      </div>

      {fuelRows.length > 1 && (
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr style={{ color: '#475569' }}>
                <th className="pb-2 pr-4 text-left font-semibold uppercase tracking-wider">Fuel Type</th>
                <th className="pb-2 pr-4 text-left font-semibold uppercase tracking-wider">Volume (L)</th>
                <th className="pb-2 text-left font-semibold uppercase tracking-wider">CO₂ (kg)</th>
              </tr>
            </thead>
            <tbody>
              {fuelRows.map(([ftype, fdata]) => (
                <tr key={ftype} className="border-t" style={{ borderColor: 'rgba(255,255,255,0.04)' }}>
                  <td className="py-2 pr-4 text-slate-200 capitalize">{ftype}</td>
                  <td className="py-2 pr-4 text-slate-400">{(fdata.liters || 0).toLocaleString()}</td>
                  <td className="py-2 font-bold" style={{ color: co2Color }}>{(fdata.co2_kg || 0).toFixed(1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <p className="text-xs text-slate-700 mt-3">
        Fuel CO₂ is included in the total impact calculation. Reduce diesel generator use and transition to grid + solar to lower this footprint.
      </p>
    </div>
  )
}

function AnnualProjectionStrip({ projections }) {
  if (!projections?.water_liters) return null
  return (
    <div className="glass-card p-5">
      <div className="flex items-center gap-2 mb-4">
        <TrendingUp className="w-4 h-4 text-yellow-400" />
        <h3 className="text-xs font-bold text-yellow-400 uppercase tracking-widest">
          Annual Projection (52-Week Estimate)
        </h3>
        <span className="ml-auto text-xs text-slate-600">Assumes same weekly loss rate with no intervention applied</span>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Water at risk',   value: `${(projections.water_liters / 1000).toFixed(1)}k L`,    color: '#00e5ff' },
          { label: 'Energy wasted',   value: `${projections.energy_kwh?.toFixed(0)} kWh`,             color: '#eab308' },
          { label: 'CO2 avoidable',   value: `${projections.co2_kg?.toLocaleString()} kg`,            color: '#22c55e' },
          { label: 'Utility loss',    value: `₹${projections.financial_inr?.toLocaleString()}`,     color: '#ef4444' },
        ].map((item) => (
          <div key={item.label} className="text-center p-3 rounded-lg"
            style={{ background: `${item.color}06`, border: `1px solid ${item.color}15` }}>
            <p className="text-xs text-slate-500 mb-1">{item.label}</p>
            <p className="font-black text-sm" style={{ color: item.color }}>{item.value}</p>
            <p className="text-xs text-slate-600 mt-0.5">per year</p>
          </div>
        ))}
      </div>
      <p className="text-xs text-slate-700 text-center mt-3">{projections.note || ''}</p>
    </div>
  )
}

const LEVEL_COLORS = { level1: '#f59e0b', level2: '#00b4ff', level3: '#00ff88' }
const LEVEL_LABELS = {
  level1: 'Basic Assessment',
  level2: 'Operational Analysis',
  level3: 'Advanced AI Analysis',
}

function AnalysisLevelBadge({ metadata }) {
  if (!metadata) return null
  const code  = metadata.overall_code || 'level1'
  const color = LEVEL_COLORS[code] || '#f59e0b'
  const label = LEVEL_LABELS[code] || 'Basic Assessment'
  const conf  = metadata.confidence_pct || 0

  return (
    <div style={{
      marginBottom: 20, padding: '12px 16px',
      borderRadius: 12,
      background: `${color}08`,
      border: `1px solid ${color}28`,
      display: 'flex', flexWrap: 'wrap', gap: 12, alignItems: 'flex-start',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
        <div style={{
          width: 20, height: 20, borderRadius: '50%',
          background: color, display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 10, fontWeight: 900, color: '#000',
        }}>
          {metadata.overall_level || 1}
        </div>
        <div>
          <span style={{ fontSize: 12, fontWeight: 700, color }}>{label}</span>
          <span style={{ fontSize: 11, color: 'rgba(148,163,184,0.55)', marginLeft: 8 }}>
            Confidence: {conf}%
          </span>
        </div>
      </div>
      {metadata.skipped_modules?.length > 0 && (
        <div style={{ fontSize: 10.5, color: 'rgba(148,163,184,0.55)', lineHeight: 1.55, flex: 1 }}>
          <span style={{ color: '#f59e0b', fontWeight: 700 }}>Modules unavailable: </span>
          {metadata.skipped_modules.map(m => m.module).join(', ')}.
          {' '}Provide hourly operational logs to unlock advanced analysis.
        </div>
      )}
      {!metadata.anomaly_detection_available && (
        <div style={{
          fontSize: 10.5, color: 'rgba(148,163,184,0.55)',
          padding: '4px 8px', borderRadius: 6,
          background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.18)',
        }}>
          ⊘ Anomaly detection unavailable at this data resolution
        </div>
      )}
    </div>
  )
}

export default function CommandCenterDashboard({ data, planData, uploadResult }) {
  // Derive values before any early return — hooks must be called unconditionally
  const isUploadMode  = !!uploadResult
  const analysisMeta  = uploadResult?.analysis_metadata || null
  const anomalyAvailable = !isUploadMode || (analysisMeta?.anomaly_detection_available !== false)

  const silent_losses  = data?.silent_losses
  const water_summary  = data?.water_summary
  const energy_summary = data?.energy_summary
  const impact_summary = data?.impact_summary

  const totalSavings     = anomalyAvailable
    ? ((silent_losses?.water_cost_inr || 0) + (silent_losses?.energy_cost_inr || 0))
    : 0
  const waterLiters      = water_summary?.total_wasted_liters || 0
  const energyKwh        = energy_summary?.total_wasted_kwh || 0
  const waterConsumption = water_summary?.total_consumption_liters || 0
  const energyConsumption = energy_summary?.total_consumption_kwh || 0

  const animWater   = useCountUp(Math.round(anomalyAvailable ? waterLiters : waterConsumption))
  const animEnergy  = useCountUp(Math.round(anomalyAvailable ? energyKwh : energyConsumption))
  const animCO2     = useCountUp(Math.round((planData?.impact || data?.impact_summary)?.total_co2_saved_kg || 0))
  const animSavings = useCountUp(Math.round(totalSavings))

  if (!data) return null

  const { regen_score } = data
  const orgName     = uploadResult?.org_name || 'Organization'
  const orgType     = uploadResult?.org_type || ''
  const fuelCo2Kg   = data.fuel_co2_kg || uploadResult?.fuel_co2_kg || 0
  const fuelSummary = data.fuel_summary || uploadResult?.fuel_summary || null
  const impact      = planData?.impact || impact_summary || {}
  const annualProj  = impact?.annual_projections
  const anomalyTotal    = (water_summary?.anomaly_events || 0) + (energy_summary?.anomaly_events || 0)
  const waterCost       = silent_losses?.water_cost_inr || 0
  const energyCost      = silent_losses?.energy_cost_inr || 0

  return (
    <section className="px-6 py-16 max-w-7xl mx-auto fade-in" id="dashboard">
      <div className="mb-8">
        <h2 className="text-3xl font-black text-white mb-2">
          Command Center <span className="text-gradient-green">Dashboard</span>
        </h2>
        <p className="text-slate-400 text-sm">
          {isUploadMode
            ? `Sustainability impact analysis for ${orgName}${orgType ? ` (${orgType})` : ''}. All values derived by rule-based analysis from your uploaded data.`
            : 'Estimated sustainability impact from simulated 7-day resource logs. All values are derived by agent-prioritised rule-based analysis and clearly marked as simulated.'}
        </p>
      </div>

      {isUploadMode && <AnalysisLevelBadge metadata={analysisMeta} />}

      <ScanTimeline anomalyAvailable={anomalyAvailable} />

      {/* RE:GEN Score */}
      <div className="mb-8">
        <RegenScoreGauge
          before={regen_score?.before_score || 0}
          after={regen_score?.after_score   || 0}
          improvement={regen_score?.improvement || 0}
          rating={regen_score?.target_rating || 'N/A'}
          analysisMeta={analysisMeta}
        />
      </div>

      {/* Silent Loss / Hidden Resource Loss */}
      <div className="mb-8">
        <SilentLossCard
          losses={silent_losses}
          isUploadMode={isUploadMode}
          orgType={orgType}
          anomalyAvailable={anomalyAvailable}
          waterConsumption={waterConsumption}
          energyConsumption={energyConsumption}
        />
      </div>

      {/* Stat grid with storytelling */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
        {anomalyAvailable ? (
          <StatCard
            icon={<DollarSign className="w-5 h-5" />}
            label="Utility Loss (est.)"
            value={`₹${animSavings.toLocaleString()}`}
            unit=""
            color="#00ff88"
            sublabel="Water leakage + after-hours energy (analysis window)"
            trend="down"
            story={{
              what:   `Utilities losing an estimated ₹${totalSavings.toFixed(0)} during the analysis window.`,
              why:    'Anomaly detection flagged water leakage and after-hours energy consumption.',
              next:   'Dispatch maintenance; deploy smart timers within 7 days.',
              impact: `Addressing detected issues could recover ₹${totalSavings.toFixed(0)}/week.`,
            }}
          />
        ) : (
          <StatCard
            icon={<DollarSign className="w-5 h-5" />}
            label="Utility Cost Estimate"
            value="Unavailable"
            unit=""
            color="#64748b"
            sublabel="Requires anomaly detection (Level 3 hourly data)"
            trend={null}
          />
        )}
        <StatCard
          icon={<Droplets className="w-5 h-5" />}
          label={anomalyAvailable ? 'Water at Risk (Leakage)' : 'Water Consumption'}
          value={animWater.toLocaleString()}
          unit="L"
          color={anomalyAvailable ? '#00e5ff' : '#64748b'}
          sublabel={anomalyAvailable
            ? `Severity: ${water_summary?.severity?.toUpperCase() || 'N/A'} — anomaly detected`
            : 'Period total — leak detection unavailable at this resolution'}
          trend={anomalyAvailable ? 'down' : null}
          story={anomalyAvailable ? {
            what:   `${waterLiters.toLocaleString()} litres detected as anomalous flow.`,
            why:    'Night-flow anomalies signal pipe leak or valve failure.',
            next:   'Shut isolation valve; schedule pipe inspection this week.',
            impact: `Fixing leaks saves approx. ₹${waterCost.toFixed(0)}/week.`,
          } : null}
        />
        <StatCard
          icon={<Zap className="w-5 h-5" />}
          label={anomalyAvailable ? 'Energy Wasted (After-Hours)' : 'Energy Consumption'}
          value={anomalyAvailable ? animEnergy : animEnergy.toLocaleString()}
          unit="kWh"
          color={anomalyAvailable ? '#eab308' : '#64748b'}
          sublabel={anomalyAvailable
            ? `Severity: ${energy_summary?.severity?.toUpperCase() || 'N/A'} — after-hours anomaly`
            : 'Period total — after-hours detection unavailable at this resolution'}
          trend={anomalyAvailable ? 'down' : null}
          story={anomalyAvailable ? {
            what:   `${energyKwh.toFixed(1)} kWh consumed after-hours in unoccupied zones.`,
            why:    'HVAC and lighting running past operational hours.',
            next:   'Install smart timer switches and auto-off protocols.',
            impact: `After-hours shutdown saves approx. ₹${energyCost.toFixed(0)}/week.`,
          } : null}
        />
        <StatCard
          icon={<Leaf className="w-5 h-5" />}
          label="CO2 Reduction Potential"
          value={animCO2}
          unit="kg"
          color="#22c55e"
          sublabel="Estimated — if all interventions applied"
          trend="up"
          story={{
            what:   `${impact?.total_co2_saved_kg || impact_summary?.total_co2_saved_kg || 0} kg CO2 reduction achievable.`,
            why:    'Lower energy and water use reduces upstream grid emissions and treatment energy.',
            next:   'Prioritise energy fixes first — highest CO2 leverage per rupee spent.',
            impact: `Equivalent to ${impact?.vehicle_km_equivalent || 0} km of car travel avoided.`,
          }}
        />
        <StatCard
          icon={<TrendingUp className="w-5 h-5" />}
          label="Trees Equivalent"
          value={impact?.trees_equivalent || impact_summary?.trees_equivalent || 0}
          unit="trees"
          color="#a78bfa"
          sublabel="CO2 absorption analogy (educational estimate)"
          trend="up"
          story={{
            what:   `CO2 saving equals what ${impact?.trees_equivalent || impact_summary?.trees_equivalent || 0} trees absorb weekly.`,
            why:    'Tree-equivalent is a widely-understood sustainability communication metric.',
            next:   'Use in sustainability communications and SDG reports.',
            impact: 'Reinforces ESG commitments to stakeholders.',
          }}
        />
        {anomalyAvailable ? (
          <StatCard
            icon={<AlertTriangle className="w-5 h-5" />}
            label="Anomaly Events"
            value={anomalyTotal}
            unit="detected"
            color="#ef4444"
            sublabel="Agent-prioritised interventions required"
            trend="down"
            story={{
              what:   `${anomalyTotal} anomaly events flagged across water and energy domains.`,
              why:    'Each event is a measurable deviation from expected usage patterns.',
              next:   'Decision Engine has ranked these by urgency — see the Action Plan.',
              impact: 'Addressing all anomalies removes the primary drivers of resource waste.',
            }}
          />
        ) : (
          <StatCard
            icon={<AlertTriangle className="w-5 h-5" />}
            label="Anomaly Detection"
            value="Unavailable"
            unit=""
            color="#f59e0b"
            sublabel="Requires hourly data ≥ 3 days (Level 3)"
            trend={null}
          />
        )}
      </div>

      {/* Fuel section — shown only when fuel data is available */}
      {fuelCo2Kg > 0 && (
        <FuelCard fuelCo2Kg={fuelCo2Kg} fuelSummary={fuelSummary} />
      )}

      {/* Risk + Before/After */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
        <CampusRiskCard
          waterSev={water_summary?.severity}
          energySev={energy_summary?.severity}
          anomalyCount={anomalyTotal}
          anomalyAvailable={anomalyAvailable}
        />
        <BeforeAfterCard
          before={regen_score?.before_score || 0}
          after={regen_score?.after_score   || 0}
          improvement={regen_score?.improvement || 0}
          targetRating={regen_score?.target_rating}
        />
      </div>

      {/* CO2 Equivalences */}
      <div className="mb-8">
        <CO2EquivalencesCard impact={impact} />
      </div>

      {/* Annual Projection Strip */}
      {annualProj && (
        <div className="mb-8">
          <AnnualProjectionStrip projections={annualProj} />
        </div>
      )}

      {/* Score breakdown */}
      {regen_score?.score_breakdown && (
        <div className="glass-card p-6">
          <h3 className="text-xs font-bold text-cyan-400 uppercase tracking-widest mb-5">
            RE:GEN Score Breakdown — 6 Dimensions
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {Object.entries(regen_score.score_breakdown).map(([key, val]) => {
              const color = val >= 70 ? '#00ff88' : val >= 50 ? '#eab308' : '#ef4444'
              return (
                <div key={key} className="text-center">
                  <p className="text-xs text-slate-500 mb-2 capitalize">{key.replace(/_/g, ' ')}</p>
                  <div className="relative w-12 h-12 mx-auto mb-1">
                    <svg viewBox="0 0 36 36" className="w-12 h-12 -rotate-90">
                      <circle cx="18" cy="18" r="14" fill="none" stroke="#1e293b" strokeWidth="3" />
                      <circle cx="18" cy="18" r="14" fill="none" stroke={color} strokeWidth="3"
                        strokeDasharray={`${(val / 100) * 88} 88`} strokeLinecap="round"
                        style={{ transition: 'stroke-dasharray 1.5s ease-out' }} />
                    </svg>
                    <span className="absolute inset-0 flex items-center justify-center text-xs font-bold"
                      style={{ color }}>{val.toFixed(0)}</span>
                  </div>
                </div>
              )
            })}
          </div>
          <p className="text-xs text-slate-600 text-center mt-4">
            Scoring formula: waste × 0.20 + water × 0.20 + energy × 0.20 + CO₂ × 0.15 + urgency × 0.15 + feasibility × 0.10
          </p>
        </div>
      )}
    </section>
  )
}
