import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import { Droplets, AlertTriangle } from 'lucide-react'

function CustomTooltip({ active, payload, label }) {
  if (active && payload && payload.length) {
    return (
      <div className="glass-card p-3 text-xs">
        <p className="text-slate-400">Hour: {label}:00</p>
        <p className="text-cyan-400 font-bold">{payload[0]?.value} L avg</p>
      </div>
    )
  }
  return null
}

function ConsumptionSummary({ data }) {
  const total = data?.total_consumption_liters || 0
  const costEst = data?.estimated_cost_inr || 0

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
        Hourly time-series data was not provided. The chart below requires hourly resolution (Level 3).
        Showing period consumption total derived from the provided summary data.
      </p>
      <div className="grid grid-cols-2 gap-4 mb-5">
        <div className="p-4 rounded-xl text-center" style={{ background: 'rgba(0,229,255,0.06)', border: '1px solid rgba(0,229,255,0.15)' }}>
          <p className="text-xs text-slate-500 mb-1">Period Total</p>
          <p className="text-3xl font-black text-cyan-400">{total.toLocaleString()}</p>
          <p className="text-xs text-slate-400 mt-1">liters consumed</p>
        </div>
        <div className="p-4 rounded-xl text-center" style={{ background: 'rgba(239,68,68,0.06)', border: '1px solid rgba(239,68,68,0.15)' }}>
          <p className="text-xs text-slate-500 mb-1">Estimated Cost</p>
          <p className="text-3xl font-black text-red-400">₹{costEst.toFixed(0)}</p>
          <p className="text-xs text-slate-400 mt-1">period (standard rates)</p>
        </div>
      </div>
      <div className="p-3 rounded-lg text-xs leading-relaxed"
        style={{ background: 'rgba(245,158,11,0.06)', border: '1px solid rgba(245,158,11,0.15)', color: '#f59e0b' }}>
        ⊘ Leak detection, night-flow analysis, and anomaly events require hourly data over ≥ 3 days.
        Provide smart-meter CSV exports to unlock this panel.
      </div>
    </div>
  )
}

export default function WaterPanel({ data, uploadResult }) {
  if (!data) return null

  const anomalyAvailable = !uploadResult || (data?.anomaly_detection_available !== false)
  const hasHourlyData = anomalyAvailable && Array.isArray(data?.hourly_chart_data) && data.hourly_chart_data.length > 0

  const { anomaly_events, total_wasted_liters, severity, estimated_cost_inr, hourly_chart_data, recommendations } = data

  const severityColors = {
    critical: '#ef4444', high: '#f97316', medium: '#eab308', low: '#22c55e', none: '#6b7280'
  }
  const color = severityColors[severity] || '#00e5ff'

  // Detect which anomaly hours to highlight (only real ones from data)
  const anomalyHours = new Set(
    (anomaly_events || []).flatMap(ev => ev.anomaly_hours || [])
  )

  return (
    <section className="px-6 py-16 max-w-7xl mx-auto" id="water">
      <div className="mb-8">
        <h2 className="text-3xl font-black text-white mb-2">
          {anomalyAvailable ? 'Silent Water' : 'Water'}{' '}
          <span className="text-gradient-blue">{anomalyAvailable ? 'Loss Panel' : 'Consumption Panel'}</span>
        </h2>
        <p className="text-slate-400">
          {anomalyAvailable
            ? 'Detecting invisible water leakage from hourly time-series data'
            : 'Water consumption summary — upgrade to hourly data for leak detection'}
        </p>
      </div>

      {!anomalyAvailable ? (
        <ConsumptionSummary data={data} />
      ) : (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
            {/* Stats */}
            <div className="glass-card p-6 flex flex-col justify-between">
              <div className="flex items-center gap-2 mb-4">
                <Droplets className="w-5 h-5 text-cyan-400" />
                <h3 className="text-sm font-semibold text-cyan-400 uppercase tracking-wider">Water Loss Summary</h3>
              </div>

              <div className="space-y-4">
                <div>
                  <p className="text-xs text-slate-500 mb-1">Total Wasted (Detected)</p>
                  <p className="text-4xl font-black text-cyan-400">{total_wasted_liters?.toLocaleString()}</p>
                  <p className="text-xs text-slate-400">liters (analysis window)</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 mb-1">Estimated Loss</p>
                  <p className="text-2xl font-bold text-red-400">₹{estimated_cost_inr?.toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 mb-1">Severity</p>
                  <span className={`text-sm font-bold px-3 py-1 rounded-full badge-${severity}`}>
                    {severity?.toUpperCase()}
                  </span>
                </div>
                <div>
                  <p className="text-xs text-slate-500 mb-1">Anomaly Events</p>
                  <p className="text-xl font-bold" style={{ color }}>{anomaly_events?.length}</p>
                </div>
              </div>
            </div>

            {/* Chart */}
            <div className="lg:col-span-2 glass-card p-6">
              <p className="text-sm font-semibold text-slate-300 mb-4">Avg Hourly Water Usage (liters)</p>
              {hasHourlyData ? (
                <>
                  <ResponsiveContainer width="100%" height={220}>
                    <AreaChart data={hourly_chart_data} margin={{ top: 5, right: 10, bottom: 5, left: 0 }}>
                      <defs>
                        <linearGradient id="waterGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#00e5ff" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="#00e5ff" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                      <XAxis dataKey="hour" stroke="#475569" tick={{ fontSize: 10 }}
                        tickFormatter={(h) => `${h}h`} />
                      <YAxis stroke="#475569" tick={{ fontSize: 10 }} />
                      <Tooltip content={<CustomTooltip />} />
                      {/* Only draw reference lines for hours with actual detected anomalies */}
                      {[...anomalyHours].slice(0, 3).map(h => (
                        <ReferenceLine key={h} x={h} stroke="#ef4444" strokeDasharray="4 4"
                          label={{ value: '⚠', fill: '#ef4444', fontSize: 10 }} />
                      ))}
                      <Area type="monotone" dataKey="avg_usage" stroke="#00e5ff" fill="url(#waterGrad)" strokeWidth={2} dot={false} />
                    </AreaChart>
                  </ResponsiveContainer>
                  <p className="text-xs text-slate-600 mt-2 text-center">
                    {anomalyHours.size > 0
                      ? `Red markers = detected anomaly hours (${[...anomalyHours].join(', ')}:00)`
                      : 'Hourly consumption pattern — no anomaly hours detected'}
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
                <AlertTriangle className="w-4 h-4 text-red-400" />
                <h3 className="text-sm font-semibold text-red-400 uppercase tracking-wider">Anomaly Events Detected</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-xs text-slate-500 uppercase tracking-wider border-b border-slate-800">
                      <th className="pb-2 pr-4">Date</th>
                      <th className="pb-2 pr-4">Location</th>
                      <th className="pb-2 pr-4">Hours</th>
                      <th className="pb-2 pr-4">Duration</th>
                      <th className="pb-2 pr-4">Total Flow</th>
                      <th className="pb-2">Est. Waste</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/50">
                    {anomaly_events.map((ev, i) => (
                      <tr key={i} className="text-slate-300">
                        <td className="py-2 pr-4 text-slate-400">{ev.date}</td>
                        <td className="py-2 pr-4 text-red-400 font-medium">{ev.location}</td>
                        <td className="py-2 pr-4">{ev.anomaly_hours?.join(', ')}:00</td>
                        <td className="py-2 pr-4">{ev.duration_hours}h</td>
                        <td className="py-2 pr-4 text-cyan-400">{ev.total_flow_liters} L</td>
                        <td className="py-2 text-red-400">{ev.estimated_waste_liters} L</td>
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

      {/* Always show recommendations if available (even for Level 1) */}
      {!anomalyAvailable && recommendations?.length > 0 && (
        <div className="glass-card-green p-5 mt-6">
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
    </section>
  )
}
