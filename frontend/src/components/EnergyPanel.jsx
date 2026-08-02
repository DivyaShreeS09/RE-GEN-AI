import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { Zap, AlertTriangle } from 'lucide-react'

function CustomTooltip({ active, payload, label }) {
  if (active && payload && payload.length) {
    return (
      <div className="glass-card p-3 text-xs">
        <p className="text-slate-400">Hour: {label}:00</p>
        <p className="text-yellow-400 font-bold">{payload[0]?.value?.toFixed(2)} kWh avg</p>
      </div>
    )
  }
  return null
}

function EnergyConsumptionSummary({ data }) {
  const total  = data?.total_consumption_kwh || 0
  const cost   = data?.estimated_cost_inr    || 0
  const co2    = data?.co2_equivalent_kg      || 0
  const recs   = data?.recommendations        || []

  return (
    <div className="glass-card p-6" style={{ border: '1px solid rgba(245,158,11,0.18)' }}>
      <div className="flex items-center gap-2 mb-3">
        <span style={{ fontSize: 11, color: '#f59e0b', fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase' }}>
          Consumption Summary
        </span>
        <span className="text-xs px-2 py-0.5 rounded-full"
          style={{ background: 'rgba(245,158,11,0.10)', border: '1px solid rgba(245,158,11,0.25)', color: '#f59e0b' }}>
          ESTIMATED
        </span>
      </div>
      <p className="text-xs text-slate-500 mb-5 leading-relaxed">
        Hourly time-series data was not provided. After-hours energy waste detection requires hourly resolution (Level 3).
        Showing period consumption total derived from the provided summary data.
      </p>
      <div className="grid grid-cols-3 gap-4 mb-5">
        <div className="p-4 rounded-xl text-center" style={{ background: 'rgba(234,179,8,0.06)', border: '1px solid rgba(234,179,8,0.15)' }}>
          <p className="text-xs text-slate-500 mb-1">Period Total</p>
          <p className="text-3xl font-black text-yellow-400">{total.toFixed(1)}</p>
          <p className="text-xs text-slate-400 mt-1">kWh consumed</p>
        </div>
        <div className="p-4 rounded-xl text-center" style={{ background: 'rgba(239,68,68,0.06)', border: '1px solid rgba(239,68,68,0.15)' }}>
          <p className="text-xs text-slate-500 mb-1">Estimated Cost</p>
          <p className="text-3xl font-black text-red-400">₹{cost.toFixed(0)}</p>
          <p className="text-xs text-slate-400 mt-1">period (₹8/kWh est.)</p>
        </div>
        <div className="p-4 rounded-xl text-center" style={{ background: 'rgba(249,115,22,0.06)', border: '1px solid rgba(249,115,22,0.15)' }}>
          <p className="text-xs text-slate-500 mb-1">CO₂ Equivalent</p>
          <p className="text-3xl font-black text-orange-400">{co2.toFixed(1)}</p>
          <p className="text-xs text-slate-400 mt-1">kg (0.82 kg/kWh)</p>
        </div>
      </div>
      <div className="p-3 rounded-lg text-xs leading-relaxed"
        style={{ background: 'rgba(245,158,11,0.06)', border: '1px solid rgba(245,158,11,0.15)', color: '#f59e0b' }}>
        ⊘ After-hours waste detection, zone-level breakdown, and equipment anomalies require hourly data over ≥ 3 days.
        Provide smart-meter CSV exports to unlock this panel.
      </div>
      {recs.length > 0 && (
        <div className="mt-5">
          <p className="text-sm font-semibold text-green-400 uppercase tracking-wider mb-3">Agent Recommendations</p>
          <div className="space-y-2">
            {recs.map((r, i) => (
              <div key={i} className="flex items-start gap-2">
                <span className="text-green-400 mt-0.5">›</span>
                <p className="text-sm text-slate-300">{r}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default function EnergyPanel({ data, uploadResult }) {
  if (!data) return null

  const anomalyAvailable = !uploadResult || (data?.anomaly_detection_available !== false)
  const hasHourlyData = anomalyAvailable && Array.isArray(data?.hourly_chart_data) && data.hourly_chart_data.length > 0

  const { anomaly_events, total_wasted_kwh, severity, estimated_cost_inr, co2_equivalent_kg, hourly_chart_data, recommendations } = data

  // Identify after-hours from actual anomaly events, not a hardcoded set
  const anomalyHourSet = new Set(
    (anomaly_events || []).flatMap(ev => ev.anomaly_hours || [])
  )

  return (
    <section className="px-6 py-16 max-w-7xl mx-auto" id="energy">
      <div className="mb-8">
        <h2 className="text-3xl font-black text-white mb-2">
          {anomalyAvailable ? 'Energy Waste' : 'Energy'}{' '}
          <span className="text-gradient-green">{anomalyAvailable ? 'Panel' : 'Consumption Panel'}</span>
        </h2>
        <p className="text-slate-400">
          {anomalyAvailable
            ? 'After-hours energy waste detection from hourly time-series data'
            : 'Energy consumption summary — upgrade to hourly data for after-hours waste detection'}
        </p>
      </div>

      {!anomalyAvailable ? (
        <EnergyConsumptionSummary data={data} />
      ) : (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
            {/* Stats */}
            <div className="glass-card p-6 flex flex-col justify-between">
              <div className="flex items-center gap-2 mb-4">
                <Zap className="w-5 h-5 text-yellow-400" />
                <h3 className="text-sm font-semibold text-yellow-400 uppercase tracking-wider">Energy Waste Summary</h3>
              </div>
              <div className="space-y-4">
                <div>
                  <p className="text-xs text-slate-500 mb-1">After-Hours kWh Wasted</p>
                  <p className="text-4xl font-black text-yellow-400">{total_wasted_kwh?.toFixed(1)}</p>
                  <p className="text-xs text-slate-400">detected anomalous consumption</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 mb-1">Cost Impact</p>
                  <p className="text-2xl font-bold text-red-400">₹{estimated_cost_inr?.toFixed(0)}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 mb-1">CO₂ Equivalent</p>
                  <p className="text-xl font-bold text-orange-400">{co2_equivalent_kg} kg</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 mb-1">Severity</p>
                  <span className={`text-sm font-bold px-3 py-1 rounded-full badge-${severity}`}>
                    {severity?.toUpperCase()}
                  </span>
                </div>
              </div>
            </div>

            {/* Chart */}
            <div className="lg:col-span-2 glass-card p-6">
              <p className="text-sm font-semibold text-slate-300 mb-4">
                Avg Hourly Energy Usage (kWh)
                {anomalyHourSet.size > 0 && ' — Orange = Detected After-Hours Anomaly'}
              </p>
              {hasHourlyData ? (
                <>
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart data={hourly_chart_data} margin={{ top: 5, right: 10, bottom: 5, left: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                      <XAxis dataKey="hour" stroke="#475569" tick={{ fontSize: 10 }} tickFormatter={(h) => `${h}h`} />
                      <YAxis stroke="#475569" tick={{ fontSize: 10 }} />
                      <Tooltip content={<CustomTooltip />} />
                      <Bar dataKey="avg_kwh" radius={[3, 3, 0, 0]}>
                        {hourly_chart_data.map((entry, index) => (
                          <Cell
                            key={index}
                            fill={anomalyHourSet.has(entry.hour) ? '#f97316' : '#3b82f6'}
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                  <p className="text-xs text-slate-600 mt-2 text-center">
                    {anomalyHourSet.size > 0
                      ? `Orange bars = detected anomaly hours (${[...anomalyHourSet].join(', ')}:00) — after-hours waste confirmed`
                      : 'Hourly energy pattern — no anomaly hours detected in this period'}
                  </p>
                </>
              ) : (
                <div className="flex items-center justify-center h-48 text-slate-600 text-sm">
                  Hourly chart data not available for this analysis
                </div>
              )}
            </div>
          </div>

          {/* Anomaly Events */}
          {anomaly_events?.length > 0 && (
            <div className="glass-card p-6 mb-6">
              <div className="flex items-center gap-2 mb-4">
                <AlertTriangle className="w-4 h-4 text-orange-400" />
                <h3 className="text-sm font-semibold text-orange-400 uppercase tracking-wider">After-Hours Waste Events</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-xs text-slate-500 uppercase tracking-wider border-b border-slate-800">
                      <th className="pb-2 pr-4">Date</th>
                      <th className="pb-2 pr-4">Zone</th>
                      <th className="pb-2 pr-4">Equipment</th>
                      <th className="pb-2 pr-4">Hours</th>
                      <th className="pb-2 pr-4">Total kWh</th>
                      <th className="pb-2">Wasted kWh</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/50">
                    {anomaly_events.map((ev, i) => (
                      <tr key={i} className="text-slate-300">
                        <td className="py-2 pr-4 text-slate-400">{ev.date}</td>
                        <td className="py-2 pr-4 text-orange-400 font-medium">{ev.zone}</td>
                        <td className="py-2 pr-4 text-xs text-slate-400">{ev.equipment?.join(', ')}</td>
                        <td className="py-2 pr-4">{ev.anomaly_hours?.join(', ')}:00</td>
                        <td className="py-2 pr-4 text-yellow-400">{ev.total_kwh} kWh</td>
                        <td className="py-2 text-red-400">{ev.wasted_kwh} kWh</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Recommendations */}
          {recommendations?.length > 0 && (
            <div className="glass-card-green p-5">
              <p className="text-sm font-semibold text-green-400 uppercase tracking-wider mb-3">Agent Recommendations</p>
              <div className="space-y-2">
                {recommendations.map((r, i) => (
                  <div key={i} className="flex items-start gap-2">
                    <span className="text-green-400 mt-0.5">›</span>
                    <p className="text-sm text-slate-300">{r}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </section>
  )
}
