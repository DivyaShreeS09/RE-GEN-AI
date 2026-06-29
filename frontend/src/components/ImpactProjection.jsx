import { Droplets, Zap, Leaf, DollarSign, TrendingUp, Calendar } from 'lucide-react'

const FIX_RATE_WATER  = 0.85
const FIX_RATE_ENERGY = 0.80
const WATER_COST      = 0.05   // ₹/L
const ENERGY_COST     = 8.0    // ₹/kWh
const CO2_PER_KWH     = 0.82   // kg CO2/kWh

function ProjectionCard({ icon, label, value, unit, subvalue, sublabel, color }) {
  return (
    <div className="glass-card p-5 agent-card-hover fade-in text-center">
      <div className="p-2.5 rounded-xl w-fit mx-auto mb-3" style={{ background: `${color}15` }}>
        <div style={{ color }}>{icon}</div>
      </div>
      <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">{label}</p>
      <p className="text-2xl font-black mb-0.5" style={{ color }}>{value}</p>
      <p className="text-xs text-slate-400">{unit}</p>
      {subvalue && (
        <div className="mt-3 pt-3 border-t" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
          <p className="text-sm font-bold text-white">{subvalue}</p>
          <p className="text-xs text-slate-500">{sublabel}</p>
        </div>
      )}
    </div>
  )
}

function ProgressRow({ label, value, max, color, unit }) {
  const pct = Math.min(100, (value / max) * 100)
  return (
    <div>
      <div className="flex justify-between items-center mb-1.5">
        <span className="text-xs text-slate-400">{label}</span>
        <span className="text-xs font-bold" style={{ color }}>{value.toFixed(1)} {unit}</span>
      </div>
      <div className="h-2 rounded-full overflow-hidden" style={{ background: 'rgba(15,23,42,0.8)' }}>
        <div className="h-full rounded-full transition-all duration-1500" style={{
          width: `${pct}%`, background: `linear-gradient(90deg, ${color}aa, ${color})`
        }} />
      </div>
    </div>
  )
}

export default function ImpactProjection({ waterData, energyData, dashData }) {
  if (!waterData || !energyData) return null

  const wasted7d    = waterData.total_wasted_liters  || 0
  const kwh7d       = energyData.total_wasted_kwh    || 0
  const regenBefore = dashData?.regen_score?.before_score   || 0
  const regenAfter  = dashData?.regen_score?.after_score    || 0
  const improvement = dashData?.regen_score?.improvement    || 0

  // 30-day projections (extrapolate 7-day window × 30/7)
  const multiplier      = 30 / 7
  const waterSaved30    = Math.round(wasted7d  * multiplier * FIX_RATE_WATER)
  const energySaved30   = Math.round(kwh7d     * multiplier * FIX_RATE_ENERGY)
  const co2Reduced30    = (energySaved30 * CO2_PER_KWH).toFixed(1)
  const financialSaving = Math.round(waterSaved30 * WATER_COST + energySaved30 * ENERGY_COST)
  const treesEquiv      = Math.round(parseFloat(co2Reduced30) / 100 * 4.5 * 10) / 10

  return (
    <section className="px-6 py-16 max-w-7xl mx-auto" id="projection">
      <div className="mb-8">
        <h2 className="text-3xl font-black text-white mb-2">
          30-Day <span className="text-gradient-blue">Impact Projection</span>
        </h2>
        <p className="text-slate-400 text-sm">
          Estimated outcomes if all agent-recommended interventions are fully implemented.
          Projections extrapolate the 7-day simulation window using standard fix-efficiency rates
          (water: {Math.round(FIX_RATE_WATER*100)}%, energy: {Math.round(FIX_RATE_ENERGY*100)}%).
        </p>
      </div>

      {/* Main projection cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <ProjectionCard
          icon={<Droplets className="w-6 h-6" />}
          label="Water Saved"
          value={waterSaved30.toLocaleString()}
          unit="liters (30 days)"
          subvalue={`₹${Math.round(waterSaved30 * WATER_COST).toLocaleString()}`}
          sublabel="est. utility saving"
          color="#00e5ff"
        />
        <ProjectionCard
          icon={<Zap className="w-6 h-6" />}
          label="Energy Recovered"
          value={energySaved30.toLocaleString()}
          unit="kWh (30 days)"
          subvalue={`₹${Math.round(energySaved30 * ENERGY_COST).toLocaleString()}`}
          sublabel="est. electricity saving"
          color="#eab308"
        />
        <ProjectionCard
          icon={<Leaf className="w-6 h-6" />}
          label="CO₂ Reduced"
          value={co2Reduced30}
          unit="kg CO₂ equivalent"
          subvalue={`${treesEquiv} trees`}
          sublabel="absorption equivalent"
          color="#22c55e"
        />
        <ProjectionCard
          icon={<DollarSign className="w-6 h-6" />}
          label="Financial Saving"
          value={`₹${financialSaving.toLocaleString()}`}
          unit="est. (30 days)"
          subvalue={`₹${Math.round(financialSaving * 12).toLocaleString()}`}
          sublabel="annualised projection"
          color="#00ff88"
        />
      </div>

      {/* Score trajectory */}
      <div className="glass-card p-6 mb-6">
        <div className="flex items-center gap-2 mb-5">
          <TrendingUp className="w-4 h-4 text-green-400" />
          <h3 className="text-sm font-bold text-white">RE:GEN Score Trajectory</h3>
        </div>
        <div className="grid grid-cols-3 gap-4 items-center mb-6">
          <div className="text-center">
            <p className="text-xs text-slate-500 mb-1">Today (simulated)</p>
            <p className="text-3xl font-black text-red-400">{regenBefore}</p>
            <p className="text-xs text-slate-600 mt-1">Baseline state</p>
          </div>
          <div className="text-center">
            <div className="flex flex-col items-center gap-1">
              <span className="text-green-400 text-lg font-black">+{improvement} pts</span>
              <div className="flex items-center gap-1">
                <div className="h-px w-10 bg-green-400 opacity-50" />
                <span className="text-xs text-slate-500">30 days</span>
                <div className="h-px w-10 bg-green-400 opacity-50" />
              </div>
              <span className="text-xs text-slate-500">if all actions implemented</span>
            </div>
          </div>
          <div className="text-center">
            <p className="text-xs text-slate-500 mb-1">Post-action target</p>
            <p className="text-3xl font-black text-green-400">{regenAfter}</p>
            <p className="text-xs text-slate-600 mt-1">{dashData?.regen_score?.target_rating}</p>
          </div>
        </div>

        <div className="space-y-3">
          <ProgressRow label="Water savings potential" value={wasted7d * multiplier * FIX_RATE_WATER / 1000} max={5} color="#00e5ff" unit="kL" />
          <ProgressRow label="Energy recovery potential" value={kwh7d * multiplier * FIX_RATE_ENERGY} max={1000} color="#eab308" unit="kWh" />
          <ProgressRow label="CO₂ reduction potential" value={parseFloat(co2Reduced30)} max={200} color="#22c55e" unit="kg" />
          <ProgressRow label="Financial recovery" value={financialSaving} max={20000} color="#00ff88" unit="₹" />
        </div>
      </div>

      {/* Assumptions */}
      <div className="glass-card-yellow p-4">
        <div className="flex items-center gap-2 mb-3">
          <Calendar className="w-4 h-4 text-yellow-500" />
          <p className="text-xs font-bold text-yellow-500 uppercase tracking-wider">Projection Assumptions</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs text-slate-400">
          <p>• Water fix efficiency: {Math.round(FIX_RATE_WATER*100)}% of detected leakage addressed</p>
          <p>• Energy fix efficiency: {Math.round(FIX_RATE_ENERGY*100)}% of after-hours waste eliminated</p>
          <p>• Water cost: ₹{WATER_COST}/litre (standard campus utility rate)</p>
          <p>• Electricity cost: ₹{ENERGY_COST}/kWh (standard Indian grid tariff)</p>
          <p>• CO₂ factor: {CO2_PER_KWH} kg/kWh (India grid average 2024)</p>
          <p>• All figures extrapolated from simulated 7-day data — not measured</p>
        </div>
      </div>
    </section>
  )
}
