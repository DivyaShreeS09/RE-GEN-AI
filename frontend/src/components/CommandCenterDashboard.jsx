import { useEffect, useRef, useState } from 'react'
import { Droplets, Zap, Leaf, AlertTriangle, TrendingUp, DollarSign, TrendingDown, CheckCircle, Activity, Car, Home, Plane } from 'lucide-react'
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
  { label: 'Sensor data loaded',    icon: '📡' },
  { label: 'Anomalies detected',    icon: '🔍' },
  { label: 'Impact quantified',     icon: '📊' },
  { label: 'Interventions ranked',  icon: '🧠' },
  { label: 'Action plan generated', icon: '✅' },
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

function SilentLossCard({ losses }) {
  const waterLoss = losses?.water_leakage_liters || 0
  const energyLoss = losses?.energy_wasted_kwh   || 0
  const waterCost  = losses?.water_cost_inr       || 0
  const energyCost = losses?.energy_cost_inr      || 0
  const totalCost  = waterCost + energyCost

  return (
    <div className="glass-card-red p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-red-400" />
          <h3 className="text-red-400 font-bold uppercase tracking-wider text-sm">Hidden Resource Loss</h3>
        </div>
        <span className="text-xs px-2 py-1 rounded-full"
          style={{ background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.3)', color: '#ef4444' }}>
          Rs. {totalCost.toFixed(0)} estimated weekly loss
        </span>
      </div>
      <p className="text-xs text-slate-500 mb-4 leading-relaxed">
        Hidden resource loss detected from simulated smart-campus sensor logs across water, energy, and waste streams.
        Costs are estimates based on standard utility rates -- not real billing data.
      </p>
      <div className="grid grid-cols-3 gap-4">
        <div className="text-center p-3 rounded-lg"
          style={{ background: 'rgba(239,68,68,0.06)', border: '1px solid rgba(239,68,68,0.15)' }}>
          <p className="text-slate-500 text-xs mb-1">Water Leakage</p>
          <p className="text-2xl font-bold text-red-400">{waterLoss.toLocaleString()}</p>
          <p className="text-xs text-slate-500">liters (7 days)</p>
          <p className="text-xs text-red-400 mt-2">approx. Rs. {waterCost.toFixed(0)} loss</p>
        </div>
        <div className="text-center p-3 rounded-lg"
          style={{ background: 'rgba(249,115,22,0.06)', border: '1px solid rgba(249,115,22,0.15)' }}>
          <p className="text-slate-500 text-xs mb-1">Energy Waste</p>
          <p className="text-2xl font-bold text-orange-400">{energyLoss.toFixed(1)}</p>
          <p className="text-xs text-slate-500">kWh (7 days)</p>
          <p className="text-xs text-orange-400 mt-2">approx. Rs. {energyCost.toFixed(0)} loss</p>
        </div>
        <div className="text-center p-3 rounded-lg"
          style={{ background: 'rgba(0,255,136,0.06)', border: '1px solid rgba(0,255,136,0.15)' }}>
          <p className="text-slate-500 text-xs mb-1">Recoverable Waste Value</p>
          <p className="text-2xl font-bold text-green-400">Rs. {(losses?.total_recoverable_inr || 0).toFixed(0)}</p>
          <p className="text-xs text-slate-500">est. potential</p>
          <p className="text-xs text-green-400 mt-2">Waste streams only</p>
        </div>
      </div>
    </div>
  )
}

function CampusRiskCard({ waterSev, energySev, anomalyCount }) {
  const riskMap  = { critical: 4, high: 3, medium: 2, low: 1, none: 0 }
  const total    = (riskMap[waterSev] || 0) + (riskMap[energySev] || 0)
  const riskLabel = total >= 7 ? 'CRITICAL' : total >= 5 ? 'HIGH' : total >= 3 ? 'MODERATE' : 'LOW'
  const riskColor = total >= 7 ? '#ef4444' : total >= 5 ? '#f97316' : total >= 3 ? '#eab308' : '#22c55e'

  return (
    <div className="glass-card p-5" style={{ border: `1px solid ${riskColor}25` }}>
      <p className="text-xs text-slate-500 uppercase tracking-widest mb-3">Campus Risk Level</p>
      <p className="text-3xl font-black mb-3" style={{ color: riskColor }}>{riskLabel}</p>
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
          CO2 Reduction -- What {co2Kg} kg Means
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
        Simulated estimates only -- actual emissions reductions depend on intervention execution and campus baselines.
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
        <span className="ml-auto text-xs text-slate-600">Simulated -- assumes same weekly loss rate with no intervention</span>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Water at risk',   value: `${(projections.water_liters / 1000).toFixed(1)}k L`,    color: '#00e5ff' },
          { label: 'Energy wasted',   value: `${projections.energy_kwh?.toFixed(0)} kWh`,             color: '#eab308' },
          { label: 'CO2 avoidable',   value: `${projections.co2_kg?.toLocaleString()} kg`,            color: '#22c55e' },
          { label: 'Utility loss',    value: `Rs. ${projections.financial_inr?.toLocaleString()}`,     color: '#ef4444' },
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

export default function CommandCenterDashboard({ data, planData }) {
  if (!data) return null
  const { regen_score, silent_losses, water_summary, energy_summary, impact_summary } = data

  const impact       = planData?.impact || impact_summary || {}
  const annualProj   = impact?.annual_projections

  const totalSavings  = ((silent_losses?.water_cost_inr || 0) + (silent_losses?.energy_cost_inr || 0))
  const anomalyTotal  = (water_summary?.anomaly_events || 0) + (energy_summary?.anomaly_events || 0)
  const waterCost     = silent_losses?.water_cost_inr  || 0
  const energyCost    = silent_losses?.energy_cost_inr || 0
  const waterLiters   = water_summary?.total_wasted_liters || 0
  const energyKwh     = energy_summary?.total_wasted_kwh  || 0

  const animWater   = useCountUp(Math.round(waterLiters))
  const animEnergy  = useCountUp(Math.round(energyKwh))
  const animCO2     = useCountUp(Math.round(impact?.total_co2_saved_kg || impact_summary?.total_co2_saved_kg || 0))
  const animSavings = useCountUp(Math.round(totalSavings))

  return (
    <section className="px-6 py-16 max-w-7xl mx-auto fade-in" id="dashboard">
      <div className="mb-8">
        <h2 className="text-3xl font-black text-white mb-2">
          Command Center <span className="text-gradient-green">Dashboard</span>
        </h2>
        <p className="text-slate-400 text-sm">
          Estimated sustainability impact from simulated 7-day campus resource logs.
          All values are derived by agent-prioritised rule-based analysis and clearly marked as simulated.
        </p>
      </div>

      <ScanTimeline />

      {/* RE:GEN Score */}
      <div className="mb-8">
        <RegenScoreGauge
          before={regen_score?.before_score || 0}
          after={regen_score?.after_score   || 0}
          improvement={regen_score?.improvement || 0}
          rating={regen_score?.target_rating || 'N/A'}
        />
      </div>

      {/* Silent Loss / Hidden Resource Loss */}
      <div className="mb-8">
        <SilentLossCard losses={silent_losses} />
      </div>

      {/* Stat grid with storytelling */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
        <StatCard
          icon={<DollarSign className="w-5 h-5" />}
          label="Utility Loss (est.)"
          value={`Rs. ${animSavings.toLocaleString()}`}
          unit=""
          color="#00ff88"
          sublabel="Water + Energy combined (weekly)"
          trend="down"
          story={{
            what:   `Campus utilities lose an estimated Rs. ${totalSavings.toFixed(0)} per week.`,
            why:    'Night-flow water leaks and after-hours energy waste are running undetected.',
            next:   'Dispatch maintenance within 24 hours; deploy smart timers within 7 days.',
            impact: `Fixing both issues could recover Rs. ${totalSavings.toFixed(0)}/week in utility spend.`,
          }}
        />
        <StatCard
          icon={<Droplets className="w-5 h-5" />}
          label="Water at Risk"
          value={animWater.toLocaleString()}
          unit="L"
          color="#00e5ff"
          sublabel={`Severity: ${water_summary?.severity?.toUpperCase() || 'N/A'}`}
          trend="down"
          story={{
            what:   `${waterLiters.toLocaleString()} litres wasted in 7-day simulated scan window.`,
            why:    'Night-flow anomalies after midnight signal pipe rupture or valve failure.',
            next:   'Shut the suspected isolation valve; schedule pipe inspection this week.',
            impact: `Fixing leaks saves approx. Rs. ${waterCost.toFixed(0)}/week and prevents structural damage.`,
          }}
        />
        <StatCard
          icon={<Zap className="w-5 h-5" />}
          label="Energy Wasted"
          value={animEnergy}
          unit="kWh"
          color="#eab308"
          sublabel={`Severity: ${energy_summary?.severity?.toUpperCase() || 'N/A'}`}
          trend="down"
          story={{
            what:   `${energyKwh.toFixed(1)} kWh consumed after hours in unoccupied zones.`,
            why:    'HVAC and lighting running past 22:00 in seminar halls and computer labs.',
            next:   'Install smart timer switches and auto-off protocols on AC units this week.',
            impact: `After-hours shutdown saves approx. Rs. ${energyCost.toFixed(0)}/week in electricity bills.`,
          }}
        />
        <StatCard
          icon={<Leaf className="w-5 h-5" />}
          label="CO2 Reduction Potential"
          value={animCO2}
          unit="kg"
          color="#22c55e"
          sublabel="Estimated -- if all interventions applied"
          trend="up"
          story={{
            what:   `${impact?.total_co2_saved_kg || impact_summary?.total_co2_saved_kg || 0} kg CO2 reduction achievable per week.`,
            why:    'Lower energy and water use directly reduces upstream grid emissions and treatment energy.',
            next:   'Prioritise energy fixes first -- highest CO2 leverage per rupee spent.',
            impact: `Equivalent to ${impact?.vehicle_km_equivalent || 0} km of car travel avoided per week.`,
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
            what:   `The weekly CO2 saving equals what ${impact?.trees_equivalent || impact_summary?.trees_equivalent || 0} trees absorb per week.`,
            why:    'Tree-equivalent is a widely-understood metric for carbon literacy communications.',
            next:   'Use this metric in campus sustainability communications and SDG reports.',
            impact: 'Reinforces ESG commitments to students, faculty, and governing bodies.',
          }}
        />
        <StatCard
          icon={<AlertTriangle className="w-5 h-5" />}
          label="Anomaly Events"
          value={anomalyTotal}
          unit="detected"
          color="#ef4444"
          sublabel="Require agent-prioritised intervention"
          trend="down"
          story={{
            what:   `${anomalyTotal} anomaly events flagged across water and energy domains.`,
            why:    'Each event represents a measurable deviation from expected usage patterns.',
            next:   'Decision Engine has ranked these by urgency -- see the Action Plan below.',
            impact: 'Addressing all anomalies removes the primary drivers of resource waste.',
          }}
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
            RE:GEN Score Breakdown -- 6 Sub-Dimensions
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
            Formula: waste x 0.20 + water x 0.20 + energy x 0.20 + CO2 x 0.15 + urgency x 0.15 + feasibility x 0.10
          </p>
        </div>
      )}
    </section>
  )
}
