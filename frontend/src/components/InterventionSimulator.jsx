import { useState, useMemo } from 'react'
import { Sliders, Droplets, Zap, Leaf, DollarSign, Sun, Flame, Database } from 'lucide-react'

const WATER_COST  = 0.05  // ₹/litre (standard municipal rate)
const ENERGY_COST = 8.0   // ₹/kWh  (standard commercial rate)
const CO2_KWH     = 0.82  // kg CO2/kWh (India grid factor)

export default function InterventionSimulator({ waterData, energyData, dashData, uploadResult }) {
  const isUploadMode     = !!uploadResult
  const analysisMeta     = uploadResult?.analysis_metadata || null
  const anomalyAvailable = !isUploadMode || (analysisMeta?.anomaly_detection_available !== false)

  // Only use real detected values — never fall back to hardcoded demo numbers
  const wastedLiters     = waterData?.total_wasted_liters || 0
  const wastedKwh        = energyData?.total_wasted_kwh   || 0
  const totalConsumptionL = waterData?.total_consumption_liters || 0
  const totalConsumptionKwh = energyData?.total_consumption_kwh || 0
  const waterAnomalies   = waterData?.anomaly_events || []
  const energyAnomalies  = energyData?.anomaly_events || []
  const waterSeverity    = waterData?.severity || 'none'
  const energySeverity   = energyData?.severity || 'none'
  const baseScore        = dashData?.regen_score?.before_score || 30

  // Evidence strings for each intervention
  const waterEvidence = waterAnomalies.length > 0
    ? `${wastedLiters.toFixed(0)} L anomalous flow detected across ${waterAnomalies.length} event(s). Severity: ${waterSeverity.toUpperCase()}.`
    : totalConsumptionL > 0
      ? `Water consumption ${totalConsumptionL.toLocaleString()} L (period total). Usage vs benchmark analysis available.`
      : null

  const energyEvidence = energyAnomalies.length > 0
    ? `${wastedKwh.toFixed(1)} kWh after-hours waste detected across ${energyAnomalies.length} event(s). Severity: ${energySeverity.toUpperCase()}.`
    : totalConsumptionKwh > 0
      ? `Energy consumption ${totalConsumptionKwh.toFixed(1)} kWh (period total). Benchmark comparison available.`
      : null

  // Build only evidence-supported interventions
  const INTERVENTIONS = useMemo(() => {
    const list = []

    // Fix Water Leakage — only if anomalies detected
    if (!isUploadMode || (anomalyAvailable && wastedLiters > 0)) {
      list.push({
        key: 'fixWater',
        icon: <Droplets className="w-4 h-4" />,
        label: 'Fix Water Leakage',
        evidence: isUploadMode
          ? waterEvidence || 'Water anomaly data not available'
          : 'Night-flow anomaly detected: 678.8 L wasted in 7-day demo dataset. 2 events flagged.',
        sub: isUploadMode ? 'Repair identified pipe anomaly locations' : 'Repair pipes in Block-B Hostel and Lab Block',
        impact: `Saves ~${Math.max(wastedLiters, 0).toFixed(0)} L/analysis window`,
        color: '#00e5ff',
        scoreGain: 6,
        energySaving: 0,
        waterSaving: wastedLiters * 0.85,
        financialGain: wastedLiters * 0.85 * WATER_COST,
      })
    }

    // Smart AC Scheduling — only if after-hours energy anomaly detected
    if (!isUploadMode || (anomalyAvailable && wastedKwh > 0)) {
      list.push({
        key: 'shutdownAC',
        icon: <Zap className="w-4 h-4" />,
        label: 'Smart AC Scheduling',
        evidence: isUploadMode
          ? energyEvidence || 'Energy anomaly data not available'
          : 'HVAC ran 6.5 hrs post-occupancy in Seminar Hall (Jan 16). 68 kWh overnight with zero occupants.',
        sub: isUploadMode ? 'Automated after-hours cutoff for high-use zones' : 'Automated cutoff for Seminar Hall + Computer Lab',
        impact: `Saves ~${(Math.max(wastedKwh, 0) * 0.80).toFixed(0)} kWh/analysis window`,
        color: '#eab308',
        scoreGain: 7,
        energySaving: wastedKwh * 0.80,
        waterSaving: 0,
        financialGain: wastedKwh * 0.80 * ENERGY_COST,
      })
    }

    // LED Retrofit — benchmark-based, always available if energy data exists
    if (!isUploadMode || (totalConsumptionKwh > 0)) {
      const ledSaving = (isUploadMode ? totalConsumptionKwh : 228.98) * 0.22
      list.push({
        key: 'ledLights',
        icon: <span style={{ fontSize: 16 }}>💡</span>,
        label: 'Replace Lights with LEDs',
        evidence: totalConsumptionKwh > 0
          ? `Total energy consumption: ${totalConsumptionKwh.toFixed(1)} kWh. Industry benchmark: 22% of energy is lighting load.`
          : 'Energy consumption data not provided — estimate based on industry benchmarks.',
        sub: 'Retrofit all common-area lighting (22% of energy load, industry benchmark)',
        impact: `Reduces lighting load ~22% (est. ${ledSaving.toFixed(0)} kWh)`,
        color: '#f59e0b',
        scoreGain: 5,
        energySaving: ledSaving,
        waterSaving: 0,
        financialGain: ledSaving * ENERGY_COST,
      })
    }

    // Waste Segregation — available if waste data or as best-practice
    list.push({
      key: 'segregation',
      icon: <Leaf className="w-4 h-4" />,
      label: 'Waste Segregation Programme',
      evidence: 'Best-practice recommendation: segregating organic, dry, and recyclable streams unlocks material recovery value. No waste data was analysed — estimate based on typical institutional waste profiles.',
      sub: 'Separate organic, dry, and recyclable waste streams',
      impact: 'Unlocks material recovery potential (est. ₹3,000–₹5,000/month for mid-size institutions)',
      color: '#00ff88',
      scoreGain: 4,
      energySaving: 0,
      waterSaving: 0,
      financialGain: 4200,
    })

    // Solar — always a strategic recommendation, not anomaly-based
    const solarBase = isUploadMode ? (totalConsumptionKwh || 200) : 228.98
    list.push({
      key: 'solar',
      icon: <Sun className="w-4 h-4" />,
      label: 'Install Rooftop Solar',
      evidence: totalConsumptionKwh > 0
        ? `Total energy consumption ${totalConsumptionKwh.toFixed(1)} kWh. Rooftop solar can offset ~40% of grid consumption (industry benchmark for institutions).`
        : 'Strategic recommendation based on India MNRE guidelines for institutional solar adoption.',
      sub: 'Offset ~40% of facility grid energy (India MNRE benchmark for institutions)',
      impact: `Avoids ~${(solarBase * 0.40).toFixed(0)} kWh grid load per analysis window`,
      color: '#a78bfa',
      scoreGain: 9,
      energySaving: solarBase * 0.40,
      waterSaving: 0,
      financialGain: solarBase * 0.40 * ENERGY_COST,
    })

    // Compost — always a best-practice recommendation
    list.push({
      key: 'compost',
      icon: <Flame className="w-4 h-4" />,
      label: 'Compost Organic Waste',
      evidence: 'Best-practice recommendation. Institutional food waste is typically 60–75% organic, compostable fraction. No waste tonnage data was provided.',
      sub: 'On-site composting for organic waste streams',
      impact: 'Reduces landfill cost + est. ₹2,500–₹4,000/month compost/biogas value',
      color: '#22c55e',
      scoreGain: 3,
      energySaving: 0,
      waterSaving: 0,
      financialGain: 3200,
    })

    // If Level 1/2 upload: add "Upgrade Data Resolution" as a priority intervention
    if (isUploadMode && !anomalyAvailable) {
      list.unshift({
        key: 'upgradeData',
        icon: <Database className="w-4 h-4" />,
        label: 'Upgrade Data Resolution',
        evidence: `Current data level: ${analysisMeta?.overall_label || 'Basic Assessment'}. Hourly time-series data would unlock leak detection, after-hours energy analysis, and zone-level risk mapping.`,
        sub: 'Provide hourly CSV exports from smart meters or BMS for Level 3 analysis',
        impact: 'Unlocks: Leak Detection · Anomaly Events · Zone Heatmap · Predictive Maintenance',
        color: '#00b4ff',
        scoreGain: 0,
        energySaving: 0,
        waterSaving: 0,
        financialGain: 0,
      })
    }

    return list
  }, [isUploadMode, anomalyAvailable, wastedLiters, wastedKwh, totalConsumptionKwh, waterEvidence, energyEvidence, analysisMeta, waterAnomalies.length, energyAnomalies.length, waterSeverity, energySeverity])

  const initialToggles = useMemo(() =>
    Object.fromEntries(INTERVENTIONS.map(i => [i.key, false])),
  [INTERVENTIONS])

  const [toggles, setToggles] = useState(initialToggles)
  const toggle = (key) => setToggles(t => ({ ...t, [key]: !t[key] }))

  const waterSaved     = INTERVENTIONS.filter(i => toggles[i.key]).reduce((s, i) => s + (i.waterSaving || 0), 0)
  const energySaved    = INTERVENTIONS.filter(i => toggles[i.key]).reduce((s, i) => s + (i.energySaving || 0), 0)
  const co2Saved       = energySaved * CO2_KWH
  const totalFinancial = INTERVENTIONS.filter(i => toggles[i.key]).reduce((s, i) => s + (i.financialGain || 0), 0)
  const scoreGain      = INTERVENTIONS.filter(i => toggles[i.key]).reduce((s, i) => s + (i.scoreGain || 0), 0)
  const projectedScore = Math.min(100, baseScore + scoreGain)
  const activeCount    = Object.values(toggles).filter(Boolean).length

  return (
    <section className="px-6 py-16 max-w-7xl mx-auto" id="simulator">
      <div className="mb-8">
        <h2 className="text-3xl font-black text-white mb-2">
          Intervention <span className="text-gradient-purple">Simulator</span>
        </h2>
        <p className="text-slate-400 text-sm">
          {isUploadMode
            ? `Interventions are generated from evidence found in your uploaded data. ${!anomalyAvailable ? 'Some interventions are best-practice recommendations because anomaly detection was unavailable at this data resolution.' : 'Anomaly-based interventions reference actual detected events.'} All financial projections are estimates.`
            : 'Interventions are generated from the simulated 7-day demo analysis. Toggle each to model projected impact on RE:GEN Score, resource savings, CO₂ reduction, and estimated financial gain. All calculations are estimates.'}
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Intervention toggles */}
        <div className="lg:col-span-2 space-y-3">
          {INTERVENTIONS.map(({ key, icon, label, evidence, sub, impact, color, scoreGain: sg }) => (
            <button key={key} onClick={() => toggle(key)}
              className={`w-full text-left toggle-btn ${toggles[key] ? 'active' : ''}`}
              style={toggles[key] ? { borderColor: color + '60', background: color + '0f', color } : {}}>
              <div className="flex items-center gap-3 flex-1">
                <div className="p-2 rounded-lg flex-shrink-0"
                  style={{ background: toggles[key] ? color + '20' : 'rgba(30,41,59,0.6)' }}>
                  <span style={{ color: toggles[key] ? color : '#64748b' }}>
                    {icon}
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-bold text-sm" style={{ color: toggles[key] ? color : '#cbd5e1' }}>
                    {label}
                  </p>
                  <p className="text-xs mt-0.5" style={{ color: toggles[key] ? color + 'cc' : '#475569' }}>
                    {sub}
                  </p>
                  {/* Evidence field */}
                  <p className="text-xs mt-1 leading-relaxed" style={{ color: toggles[key] ? 'rgba(148,163,184,0.8)' : '#374151' }}>
                    <span style={{ color: toggles[key] ? color + '99' : '#4b5563', fontWeight: 600 }}>Evidence: </span>
                    {evidence}
                  </p>
                  <p className="text-xs mt-1 font-medium" style={{ color: toggles[key] ? '#94a3b8' : '#334155' }}>
                    → {impact}
                  </p>
                </div>
                <div className="flex flex-col items-end gap-1 flex-shrink-0">
                  <div className="w-10 h-5 rounded-full transition-all duration-300 relative"
                    style={{ background: toggles[key] ? color + '80' : '#334155' }}>
                    <div className={`absolute top-0.5 w-4 h-4 rounded-full transition-all duration-300 ${
                      toggles[key] ? 'translate-x-5' : 'translate-x-0.5'
                    }`} style={{ background: toggles[key] ? color : '#4b5563' }} />
                  </div>
                  {sg > 0 && (
                    <span className="text-xs font-bold" style={{ color: toggles[key] ? color : '#334155' }}>
                      +{sg} pts
                    </span>
                  )}
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
                  val: waterSaved > 0 ? `${waterSaved.toFixed(0)} L` : '—', active: waterSaved > 0, color: 'text-cyan-400' },
                { icon: <Zap className="w-3 h-3 text-yellow-400" />, label: 'Energy saved',
                  val: energySaved > 0 ? `${energySaved.toFixed(1)} kWh` : '—', active: energySaved > 0, color: 'text-yellow-400' },
                { icon: <Leaf className="w-3 h-3 text-green-400" />, label: 'CO₂ reduction',
                  val: co2Saved > 0 ? `${co2Saved.toFixed(1)} kg` : '—', active: co2Saved > 0, color: 'text-green-400' },
                { icon: <DollarSign className="w-3 h-3 text-green-400" />, label: 'Financial gain (est.)',
                  val: totalFinancial > 0 ? `₹${totalFinancial.toFixed(0)}` : '—', active: totalFinancial > 0, color: 'text-green-400' },
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
            All projections are estimates. Anomaly-based savings reference detected events.
            Best-practice items use industry benchmarks. Actual results depend on site conditions and implementation quality.
          </div>
        </div>
      </div>
    </section>
  )
}
