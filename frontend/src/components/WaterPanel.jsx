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

export default function WaterPanel({ data }) {
  if (!data) return null

  const { anomaly_events, total_wasted_liters, severity, estimated_cost_inr, hourly_chart_data, recommendations } = data

  const severityColors = {
    critical: '#ef4444', high: '#f97316', medium: '#eab308', low: '#22c55e', none: '#6b7280'
  }
  const color = severityColors[severity] || '#00e5ff'

  return (
    <section className="px-6 py-16 max-w-7xl mx-auto" id="water">
      <div className="mb-8">
        <h2 className="text-3xl font-black text-white mb-2">
          Silent Water <span className="text-gradient-blue">Loss Panel</span>
        </h2>
        <p className="text-slate-400">Detecting invisible water leakage across campus zones</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/* Stats */}
        <div className="glass-card p-6 flex flex-col justify-between">
          <div className="flex items-center gap-2 mb-4">
            <Droplets className="w-5 h-5 text-cyan-400" />
            <h3 className="text-sm font-semibold text-cyan-400 uppercase tracking-wider">Water Loss Summary</h3>
          </div>

          <div className="space-y-4">
            <div>
              <p className="text-xs text-slate-500 mb-1">Total Wasted</p>
              <p className="text-4xl font-black text-cyan-400">{total_wasted_liters?.toLocaleString()}</p>
              <p className="text-xs text-slate-400">liters (7-day period)</p>
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
              <ReferenceLine x={3} stroke="#ef4444" strokeDasharray="4 4" label={{ value: '⚠ Anomaly', fill: '#ef4444', fontSize: 10 }} />
              <Area type="monotone" dataKey="avg_usage" stroke="#00e5ff" fill="url(#waterGrad)" strokeWidth={2} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
          <p className="text-xs text-slate-600 mt-2 text-center">
            Red dashed line marks detected anomaly window (night-hour continuous flow)
          </p>
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
      <div className="glass-card-green p-5">
        <p className="text-sm font-semibold text-green-400 uppercase tracking-wider mb-3">Agent Recommendations</p>
        <div className="space-y-2">
          {recommendations?.map((r, i) => (
            <div key={i} className="flex items-start gap-2">
              <span className="text-green-400 mt-0.5">›</span>
              <p className="text-sm text-slate-300">{r}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
