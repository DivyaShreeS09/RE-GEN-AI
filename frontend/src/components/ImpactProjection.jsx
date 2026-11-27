import { useState } from 'react'
import { DEMO_WATER_RATE, DEMO_ENERGY_RATE, DEMO_GRID_FACTOR } from '../projectionRates'
import { Droplets, Zap, Leaf, DollarSign, TrendingUp, Calendar } from 'lucide-react'

const FIX_RATE_WATER  = 0.85
const FIX_RATE_ENERGY = 0.80

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

function UploadedScenario({ waterData, energyData }) {
  const [reductions, setReductions] = useState({ water: '', energy: '' })
  return <section id="projection" className="max-w-7xl mx-auto px-6 py-12">
    <h2 className="text-3xl font-black text-white mb-3">Forecasts and scenarios</h2>
    <p className="text-sm text-slate-400 mb-4">Compare unchanged consumption with a reduction you specify for the same reporting window.</p>
    <div className="grid md:grid-cols-2 gap-4">
      {[['water', waterData, 'total_consumption_liters', 'L'], ['energy', energyData, 'total_consumption_kwh', 'kWh']].map(([resource, data, key, unit]) => {
        if (data?.[key] == null) return null
        const forecast = data.resource_profile?.forecast
        const value = reductions[resource]
        const valid = value !== '' && Number.isFinite(Number(value)) && Number(value) >= 0 && Number(value) <= 100
        const saved = valid ? data[key] * Number(value) / 100 : null
        const tariff = data.tariff?.inr_per_unit
        return <div className="glass-card p-5 space-y-3" key={resource}>
          <h3 className="capitalize font-bold text-white">{resource}</h3>
          <p>Observed reporting period · {data[key].toLocaleString()} {unit}</p>
          {data.intensity?.per_person != null && <p>{data.intensity.per_person} {unit}/person for the observed period</p>}
          {data.intensity?.per_square_metre != null && <p>{data.intensity.per_square_metre} {unit}/m² for the observed period</p>}
          <p>{forecast?.status === 'available'
            ? `${forecast.next_date} forecast · ${forecast.estimate} ${unit} (validation error range ${forecast.range.join('–')})`
            : forecast?.basis || 'Daily forecasting requires documented historical observations.'}</p>
          <label className="block">Assumed reduction (%)
            <input className="ml-3 bg-slate-900 rounded border border-slate-600 p-1 w-20" type="number" min="0" max="100"
              value={value} onChange={event => setReductions({ ...reductions, [resource]: event.target.value })} />
          </label>
          {saved != null && <p>Scenario consumption · {(data[key] - saved).toLocaleString()} {unit}. Estimated difference · {saved.toLocaleString()} {unit}.
            {tariff != null ? ` Variable tariff difference ₹${(saved * tariff).toLocaleString()}. ` : ' Financial estimate unavailable without a documented tariff. '}</p>}
        </div>
      })}
    </div>
  </section>
}

export default function ImpactProjection({ waterData, energyData, dashData, uploadResult }) {
  if (uploadResult) return <UploadedScenario waterData={waterData} energyData={energyData} />
  const WATER_COST = waterData?.tariff?.inr_per_unit ?? DEMO_WATER_RATE
  const ENERGY_COST = energyData?.tariff?.inr_per_unit ?? DEMO_ENERGY_RATE
  const CO2_PER_KWH = dashData?.impact_summary?.factor_metadata?.energy?.factor ?? DEMO_GRID_FACTOR
  if (!waterData || !energyData) return null

  const wasted7d    = waterData.total_wasted_liters  || 0
  const kwh7d       = energyData.total_wasted_kwh    || 0
  const regenBefore = dashData?.regen_score?.before_score   || 0
  const regenAfter  = dashData?.regen_score?.after_score    || 0
  const improvement = dashData?.regen_score?.improvement    || 0

  // 30-day projections (extrapolate 7-day window × 30/7)
  const waterDays = 7
  const energyDays = 7
  const waterSaved30    = Math.round(wasted7d * (waterDays ? 30 / waterDays : 0) * FIX_RATE_WATER)
  const energySaved30   = Math.round(kwh7d * (energyDays ? 30 / energyDays : 0) * FIX_RATE_ENERGY)
  const co2Reduced30    = (energySaved30 * CO2_PER_KWH + waterSaved30 * 0.001).toFixed(1)
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
          <ProgressRow label="Water savings potential" value={waterSaved30 / 1000} max={5} color="#00e5ff" unit="kL" />
          <ProgressRow label="Energy recovery potential" value={energySaved30} max={1000} color="#eab308" unit="kWh" />
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
          <p>• Water cost: ₹{WATER_COST}/litre (reference assumption)</p>
          <p>• Electricity cost: ₹{ENERGY_COST}/kWh (reference assumption)</p>
          <p>• CO₂ factor: {CO2_PER_KWH} kg/kWh (inherited reference assumption; vintage unverified)</p>
          <p>• All figures extrapolated from simulated 7-day data — not measured</p>
        </div>
      </div>
    </section>
  )
}
