import { useState } from 'react'
import { Sliders, Droplets, Zap, Leaf, DollarSign, Sun, Flame } from 'lucide-react'

const WATER_COST  = 0.05
const ENERGY_COST = 8.0
const CO2_KWH     = 0.82

export default function InterventionSimulator({ waterData, energyData, dashData }) {
  const wastedLiters = waterData?.total_wasted_liters  || 678.8
  const wastedKwh    = energyData?.total_wasted_kwh    || 228.98
  const baseScore    = dashData?.regen_score?.before_score || 30

  const [toggles, setToggles] = useState({
    fixWater:    false,
    shutdownAC:  false,
    ledLights:   false,
    segregation: false,
    solar:       false,
    compost:     false,
  })

  const toggle = (key) => setToggles(t => ({ ...t, [key]: !t[key] }))

  /* Impact calculations */
  const waterSaved    = toggles.fixWater    ? wastedLiters * 0.85 : 0
  const acSaved       = toggles.shutdownAC  ? wastedKwh * 0.80   : 0
  const ledSaved      = toggles.ledLights   ? wastedKwh * 0.22   : 0   // 22% lighting share est
  const solarSaved    = toggles.solar       ? wastedKwh * 0.40   : 0   // 40% offset est
  const energySaved   = acSaved + ledSaved + solarSaved

  const segregGain    = toggles.segregation ? 4200 : 0   // ₹/month est
  const compostGain   = toggles.compost     ? 3200 : 0   // ₹/month est
  const waterINR      = waterSaved  * WATER_COST
  const energyINR     = energySaved * ENERGY_COST
  const co2Saved      = energySaved * CO2_KWH
  const totalFinancial= waterINR + energyINR + segregGain + compostGain

  const scoreGain =
    (toggles.fixWater    ? 6 : 0) +
    (toggles.shutdownAC  ? 7 : 0) +
    (toggles.ledLights   ? 5 : 0) +
    (toggles.segregation ? 4 : 0) +
    (toggles.solar       ? 9 : 0) +
    (toggles.compost     ? 3 : 0)
  const projectedScore = Math.min(100, baseScore + scoreGain)
  const activeCount    = Object.values(toggles).filter(Boolean).length

  const INTERVENTIONS = [
    {
      key: 'fixWater',
      icon: <Droplets className="w-4 h-4" />,
      label: 'Fix Water Leakage',
      sub: 'Repair pipes in Block-B Hostel and Lab Block',
      impact: `Saves ~${wastedLiters.toFixed(0)} L/week`,
      color: '#00e5ff',
      score: '+6 pts',
    },
    {
      key: 'shutdownAC',
      icon: <Zap className="w-4 h-4" />,
      label: 'Smart AC Scheduling',
      sub: 'Automated cutoff for Seminar Hall + Computer Lab',
      impact: `Saves ~${(wastedKwh * 0.80).toFixed(0)} kWh/week`,
      color: '#eab308',
      score: '+7 pts',
    },
    {
      key: 'ledLights',
      icon: <span className="text-sm">💡</span>,
      label: 'Replace Lights with LEDs',
      sub: 'Retrofit all common-area lighting campus-wide',
      impact: `Reduces lighting load ~22% (~${(wastedKwh * 0.22).toFixed(0)} kWh/wk)`,
      color: '#f59e0b',
      score: '+5 pts',
    },
    {
      key: 'segregation',
      icon: <Leaf className="w-4 h-4" />,
      label: 'Waste Segregation Drive',
      sub: 'Separate organic, dry, and recyclable waste streams',
      impact: 'Unlocks ≈ ₹4,200 estimated value/month',
      color: '#00ff88',
      score: '+4 pts',
    },
    {
      key: 'solar',
      icon: <Sun className="w-4 h-4" />,
      label: 'Install Rooftop Solar',
      sub: 'Offset ~40% of campus grid energy consumption',
      impact: `Avoids ~${(wastedKwh * 0.40).toFixed(0)} kWh grid load/week`,
      color: '#a78bfa',
      score: '+9 pts',
    },
    {
      key: 'compost',
      icon: <Flame className="w-4 h-4" />,
      label: 'Compost Food Waste',
      sub: 'On-site composting for canteen organic waste',
      impact: 'Reduces landfill + ≈ ₹3,200 est. value/month',
      color: '#22c55e',
      score: '+3 pts',
    },
  ]

  return (
    <section className="px-6 py-16 max-w-7xl mx-auto" id="simulator">
      <div className="mb-8">
        <h2 className="text-3xl font-black text-white mb-2">
          Intervention <span className="text-gradient-purple">Simulator</span>
        </h2>
        <p className="text-slate-400 text-sm">
          Toggle recommended interventions to model their projected impact on RE:GEN Score, resource savings,
          CO₂ reduction, and estimated financial gain. All calculations are frontend estimates based on
          simulated data — not backend predictions.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Intervention toggles */}
        <div className="lg:col-span-2 space-y-3">
          {INTERVENTIONS.map(({ key, icon, label, sub, impact, color, score }) => (
            <button key={key} onClick={() => toggle(key)}
              className={`w-full text-left toggle-btn ${toggles[key] ? 'active' : ''}`}
              style={toggles[key] ? { borderColor: color + '60', background: color + '0f', color } : {}}>
              <div className="flex items-center gap-3 flex-1">
                <div className="p-2 rounded-lg flex-shrink-0"
                  style={{ background: toggles[key] ? color + '20' : 'rgba(30,41,59,0.6)' }}>
                  <span style={{ color: toggles[key] ? color : '#64748b' }}>
                    {typeof icon === 'string' ? <span className="text-sm">{icon}</span> : icon}
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-bold text-sm" style={{ color: toggles[key] ? color : '#cbd5e1' }}>
                    {label}
                  </p>
                  <p className="text-xs mt-0.5 truncate" style={{ color: toggles[key] ? color + 'cc' : '#475569' }}>
                    {sub}
                  </p>
                  <p className="text-xs mt-1" style={{ color: toggles[key] ? '#94a3b8' : '#334155' }}>
                    {impact}
                  </p>
                </div>
                <div className="flex flex-col items-end gap-1 flex-shrink-0">
                  <div className={`w-10 h-5 rounded-full transition-all duration-300 relative`}
                    style={{ background: toggles[key] ? color + '80' : '#334155' }}>
                    <div className={`absolute top-0.5 w-4 h-4 rounded-full transition-all duration-300 ${
                      toggles[key] ? 'translate-x-5' : 'translate-x-0.5'
                    }`} style={{ background: toggles[key] ? color : '#4b5563' }} />
                  </div>
                  <span className="text-xs font-bold"
                    style={{ color: toggles[key] ? color : '#334155' }}>
                    {score}
                  </span>
                </div>
              </div>
            </button>
          ))}

          {activeCount === 0 && (
            <p className="text-xs text-slate-600 text-center pt-2">
              Toggle interventions above to model their projected impact
            </p>
          )}
        </div>

        {/* Live results panel */}
        <div className="space-y-4">
          <div className="glass-card p-5">
            <div className="flex items-center gap-2 mb-4">
              <Sliders className="w-4 h-4 text-cyan-400" />
              <h3 className="text-xs font-bold text-cyan-400 uppercase tracking-widest">Projected Impact</h3>
            </div>

            {/* RE:GEN Score */}
            <div className="text-center mb-5 p-4 rounded-xl" style={{
              background: 'rgba(0,255,136,0.04)', border: '1px solid rgba(0,255,136,0.15)',
            }}>
              <p className="text-xs text-slate-500 mb-1">RE:GEN Score</p>
              <div className="flex items-baseline justify-center gap-2">
                <span className="text-2xl font-black text-red-400">{baseScore}</span>
                <span className="text-slate-500">→</span>
                <span className={`text-3xl font-black transition-all duration-500 ${
                  projectedScore > baseScore ? 'text-green-400' : 'text-slate-400'
                }`}>{projectedScore}</span>
              </div>
              {scoreGain > 0 && (
                <span className="text-xs text-green-400 font-bold mt-1 inline-block">
                  +{scoreGain} pts from {activeCount} intervention{activeCount > 1 ? 's' : ''}
                </span>
              )}
            </div>

            {/* Metric rows */}
            <div className="space-y-3">
              {[
                { icon: <Droplets className="w-3 h-3 text-cyan-400" />, label: 'Water saved',
                  val: waterSaved > 0 ? `${waterSaved.toFixed(0)} L/wk` : '—', active: waterSaved > 0, color: 'text-cyan-400' },
                { icon: <Zap className="w-3 h-3 text-yellow-400" />, label: 'Energy saved',
                  val: energySaved > 0 ? `${energySaved.toFixed(1)} kWh/wk` : '—', active: energySaved > 0, color: 'text-yellow-400' },
                { icon: <Leaf className="w-3 h-3 text-green-400" />, label: 'CO₂ reduction',
                  val: co2Saved > 0 ? `${co2Saved.toFixed(1)} kg/wk` : '—', active: co2Saved > 0, color: 'text-green-400' },
                { icon: <DollarSign className="w-3 h-3 text-green-400" />, label: 'Financial gain',
                  val: totalFinancial > 0 ? `₹${totalFinancial.toFixed(0)}/wk` : '—', active: totalFinancial > 0, color: 'text-green-400' },
              ].map((row, i) => (
                <div key={i} className="flex justify-between items-center py-2 border-b last:border-0"
                  style={{ borderColor: 'rgba(255,255,255,0.05)' }}>
                  <div className="flex items-center gap-2 text-xs text-slate-400">
                    {row.icon} {row.label}
                  </div>
                  <span className={`text-xs font-bold ${row.active ? row.color : 'text-slate-600'}`}>
                    {row.val}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="p-3 rounded-lg text-xs text-slate-600 leading-relaxed"
            style={{ background: 'rgba(15,23,42,0.4)', border: '1px solid rgba(255,255,255,0.04)' }}>
            All projections are frontend estimates based on simulated 7-day data.
            Actual results depend on campus conditions, implementation quality,
            and real sensor readings not available in this prototype.
          </div>
        </div>
      </div>
    </section>
  )
}
