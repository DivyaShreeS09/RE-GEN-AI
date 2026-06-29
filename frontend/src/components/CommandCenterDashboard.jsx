import { useEffect, useRef, useState } from 'react'
import { Droplets, Zap, Leaf, AlertTriangle, TrendingUp, DollarSign, TrendingDown, CheckCircle, Activity } from 'lucide-react'
import RegenScoreGauge from './RegenScoreGauge'

/* ── Animated counter hook ─── */
function useCountUp(target, duration = 1400) {
  const [val, setVal] = useState(0)
  useEffect(() => {
    if (!target) return
    let current = 0
    const step = target / (duration / 16)
    const timer = setInterval(() => {
      current += step
      if (current >= target) { setVal(target); clearInterval(timer) }
      else setVal(Math.floor(current))
    }, 16)
    return () => clearInterval(timer)
  }, [target, duration])
  return val
}

const SCAN_STAGES = [
  { label: 'Sensor data loaded',         icon: '📡' },
  { label: 'Anomalies detected',         icon: '🔍' },
  { label: 'Impact quantified',          icon: '📊' },
  { label: 'Interventions ranked',       icon: '🧠' },
  { label: 'Action plan generated',      icon: '✅' },
]

function ScanTimeline() {
  const [active, setActive] = useState(0)
  useEffect(() => {
    if (active >= SCAN_STAGES.length - 1) return
    const t = setTimeout(() => setActive(i => i + 1), 500)
    return () => clearTimeout(t)
  }, [active])
  return (
    <div className="glass-card p-5 mb-8">
      <p className="text-xs font-bold text-cyan-400 uppercase tracking-widest mb-4">Scan Pipeline</p>
      <div className="flex items-center gap-1 flex-wrap">
        {SCAN_STAGES.map((s, i) => (
          <div key={i} className="flex items-center gap-1">
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-500 ${
              i < active ? 'bg-green-500/10 text-green-400 border border-green-500/25' :
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

function StatCard({ icon, label, value, unit, color, sublabel, trend }) {
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
    </div>
  )
}

function SilentLossCard({ losses }) {
  const waterLoss = losses?.water_leakage_liters || 0
  const energyLoss = losses?.energy_wasted_kwh || 0
  const waterCost  = losses?.water_cost_inr || 0
  const energyCost = losses?.energy_cost_inr || 0
  const totalCost  = waterCost + energyCost

  return (
    <div className="glass-card-red p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-red-400" />
          <h3 className="text-red-400 font-bold uppercase tracking-wider text-sm">Silent Loss Detector</h3>
        </div>
        <span className="text-xs px-2 py-1 rounded-full" style={{
          background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.3)', color: '#ef4444'
        }}>
          ₹{totalCost.toFixed(0)} estimated weekly loss
        </span>
      </div>
      <p className="text-xs text-slate-500 mb-4 leading-relaxed">
        Resource losses identified from simulated campus sensor logs. Costs are estimates based on standard utility rates.
      </p>
      <div className="grid grid-cols-3 gap-4">
        <div className="text-center p-3 rounded-lg" style={{ background: 'rgba(239,68,68,0.06)', border: '1px solid rgba(239,68,68,0.15)' }}>
          <p className="text-slate-500 text-xs mb-1">Water Leakage</p>
          <p className="text-2xl font-bold text-red-400">{waterLoss.toLocaleString()}</p>
          <p className="text-xs text-slate-500">liters (7 days)</p>
          <p className="text-xs text-red-400 mt-2">≈ ₹{waterCost.toFixed(0)} loss</p>
        </div>
        <div className="text-center p-3 rounded-lg" style={{ background: 'rgba(249,115,22,0.06)', border: '1px solid rgba(249,115,22,0.15)' }}>
          <p className="text-slate-500 text-xs mb-1">Energy Waste</p>
          <p className="text-2xl font-bold text-orange-400">{energyLoss.toFixed(1)}</p>
          <p className="text-xs text-slate-500">kWh (7 days)</p>
          <p className="text-xs text-orange-400 mt-2">≈ ₹{energyCost.toFixed(0)} loss</p>
        </div>
        <div className="text-center p-3 rounded-lg" style={{ background: 'rgba(0,255,136,0.06)', border: '1px solid rgba(0,255,136,0.15)' }}>
          <p className="text-slate-500 text-xs mb-1">Recoverable Waste Value</p>
          <p className="text-2xl font-bold text-green-400">₹{(losses?.total_recoverable_inr || 0).toFixed(0)}</p>
          <p className="text-xs text-slate-500">est. potential</p>
          <p className="text-xs text-green-400 mt-2">Waste streams only</p>
        </div>
      </div>
    </div>
  )
}

function CampusRiskCard({ waterSev, energySev, anomalyCount }) {
  const riskMap = { critical: 4, high: 3, medium: 2, low: 1, none: 0 }
  const total = (riskMap[waterSev] || 0) + (riskMap[energySev] || 0)
  const riskLabel = total >= 7 ? 'CRITICAL' : total >= 5 ? 'HIGH' : total >= 3 ? 'MODERATE' : 'LOW'
  const riskColor = total >= 7 ? '#ef4444' : total >= 5 ? '#f97316' : total >= 3 ? '#eab308' : '#22c55e'

  return (
    <div className="glass-card p-5" style={{ border: `1px solid ${riskColor}25` }}>
      <p className="text-xs text-slate-500 uppercase tracking-widest mb-3">Campus Risk Level</p>
      <div className="flex items-end gap-3 mb-3">
        <p className="text-3xl font-black" style={{ color: riskColor }}>{riskLabel}</p>
      </div>
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
    </div>
  )
}

function BeforeAfterCard({ before, after, improvement, currentRating, targetRating }) {
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
          <div className="text-slate-400 mb-2">
            <div className="flex items-center justify-center gap-1">
              <div className="h-px w-6 bg-green-400" />
              <span className="text-green-400 font-bold text-sm">+{improvement}</span>
              <div className="h-px w-6 bg-green-400" />
            </div>
          </div>
          <p className="text-xs text-slate-500">if recommendations</p>
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

export default function CommandCenterDashboard({ data }) {
  if (!data) return null
  const { regen_score, silent_losses, water_summary, energy_summary, impact_summary } = data

  const totalSavings = ((silent_losses?.water_cost_inr || 0) + (silent_losses?.energy_cost_inr || 0))
  const anomalyTotal = (water_summary?.anomaly_events || 0) + (energy_summary?.anomaly_events || 0)

  const animWater   = useCountUp(Math.round(water_summary?.total_wasted_liters || 0))
  const animEnergy  = useCountUp(Math.round(energy_summary?.total_wasted_kwh || 0))
  const animCO2     = useCountUp(Math.round(impact_summary?.total_co2_saved_kg || 0))
  const animSavings = useCountUp(Math.round(totalSavings))

  return (
    <section className="px-6 py-16 max-w-7xl mx-auto fade-in" id="dashboard">
      <div className="mb-8">
        <h2 className="text-3xl font-black text-white mb-2">
          Command Center <span className="text-gradient-green">Dashboard</span>
        </h2>
        <p className="text-slate-400 text-sm">
          Estimated sustainability metrics from simulated 7-day campus resource logs.
          All values are agent-derived from rule-based analysis.
        </p>
      </div>

      <ScanTimeline />

      {/* RE:GEN Score */}
      <div className="mb-8">
        <RegenScoreGauge
          before={regen_score?.before_score || 0}
          after={regen_score?.after_score || 0}
          improvement={regen_score?.improvement || 0}
          rating={regen_score?.target_rating || 'N/A'}
        />
      </div>

      {/* Silent Loss Detector */}
      <div className="mb-8">
        <SilentLossCard losses={silent_losses} />
      </div>

      {/* Stat grid + Risk + Before/After */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
        <StatCard
          icon={<DollarSign className="w-5 h-5" />}
          label="Utility Loss (est.)"
          value={`₹${animSavings.toLocaleString()}`}
          unit=""
          color="#00ff88"
          sublabel="Water + Energy combined"
          trend="down"
        />
        <StatCard
          icon={<Droplets className="w-5 h-5" />}
          label="Water at Risk"
          value={animWater.toLocaleString()}
          unit="L"
          color="#00e5ff"
          sublabel={`Severity: ${water_summary?.severity?.toUpperCase() || 'N/A'}`}
          trend="down"
        />
        <StatCard
          icon={<Zap className="w-5 h-5" />}
          label="Energy Wasted"
          value={animEnergy.toFixed ? animEnergy : animEnergy}
          unit="kWh"
          color="#eab308"
          sublabel={`Severity: ${energy_summary?.severity?.toUpperCase() || 'N/A'}`}
          trend="down"
        />
        <StatCard
          icon={<Leaf className="w-5 h-5" />}
          label="CO₂ Reduction Potential"
          value={animCO2}
          unit="kg"
          color="#22c55e"
          sublabel="If all interventions applied"
          trend="up"
        />
        <StatCard
          icon={<TrendingUp className="w-5 h-5" />}
          label="Trees Equivalent"
          value={impact_summary?.trees_equivalent || 0}
          unit="trees"
          color="#a78bfa"
          sublabel="CO₂ absorption analogy"
          trend="up"
        />
        <StatCard
          icon={<AlertTriangle className="w-5 h-5" />}
          label="Anomaly Events"
          value={anomalyTotal}
          unit="detected"
          color="#ef4444"
          sublabel="Require immediate action"
          trend="down"
        />
      </div>

      {/* Risk + Before/After */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
        <CampusRiskCard
          waterSev={water_summary?.severity}
          energySev={energy_summary?.severity}
          anomalyCount={anomalyTotal}
        />
        <BeforeAfterCard
          before={regen_score?.before_score || 0}
          after={regen_score?.after_score || 0}
          improvement={regen_score?.improvement || 0}
          currentRating={regen_score?.current_rating}
          targetRating={regen_score?.target_rating}
        />
      </div>

      {/* Score breakdown */}
      {regen_score?.score_breakdown && (
        <div className="glass-card p-6">
          <h3 className="text-xs font-bold text-cyan-400 uppercase tracking-widest mb-5">
            RE:GEN Score Breakdown — 6 Sub-Dimensions
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
                    <span className="absolute inset-0 flex items-center justify-center text-xs font-bold" style={{ color }}>
                      {val.toFixed(0)}
                    </span>
                  </div>
                </div>
              )
            })}
          </div>
          <p className="text-xs text-slate-600 text-center mt-4">
            Formula: waste×0.20 + water×0.20 + energy×0.20 + CO₂×0.15 + urgency×0.15 + feasibility×0.10
          </p>
        </div>
      )}
    </section>
  )
}
