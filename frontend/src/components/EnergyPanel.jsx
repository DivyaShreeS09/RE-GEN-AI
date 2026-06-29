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

const AFTER_HOURS = new Set([0, 1, 2, 3, 4, 5, 22, 23])

export default function EnergyPanel({ data }) {
  if (!data) return null
  const { anomaly_events, total_wasted_kwh, severity, estimated_cost_inr, co2_equivalent_kg, hourly_chart_data, recommendations } = data

  return (
    <section className="px-6 py-16 max-w-7xl mx-auto" id="energy">
      <div className="mb-8">
        <h2 className="text-3xl font-black text-white mb-2">
          Energy Waste <span className="text-gradient-green">Panel</span>
        </h2>
        <p className="text-slate-400">After-hours energy waste detection across campus zones</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/* Stats */}
        <div className="glass-card p-6 flex flex-col justify-between">
          <div className="flex items-center gap-2 mb-4">
            <Zap className="w-5 h-5 text-yellow-400" />
            <h3 className="text-sm font-semibold text-yellow-400 uppercase tracking-wider">Energy Waste Summary</h3>
          </div>
          <div className="space-y-4">
            <div>
              <p className="text-xs text-slate-500 mb-1">Total kWh Wasted</p>
              <p className="text-4xl font-black text-yellow-400">{total_wasted_kwh?.toFixed(1)}</p>
              <p className="text-xs text-slate-400">after-hours (7-day)</p>
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
          <p className="text-sm font-semibold text-slate-300 mb-4">Avg Hourly Energy Usage (kWh) — Yellow = After-Hours Anomaly</p>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={hourly_chart_data} margin={{ top: 5, right: 10, bottom: 5, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="hour" stroke="#475569" tick={{ fontSize: 10 }} tickFormatter={(h) => `${h}h`} />
              <YAxis stroke="#475569" tick={{ fontSize: 10 }} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="avg_kwh" radius={[3, 3, 0, 0]}>
                {hourly_chart_data?.map((entry, index) => (
                  <Cell
                    key={index}
                    fill={AFTER_HOURS.has(entry.hour) && entry.avg_kwh > 10 ? '#f97316' : '#3b82f6'}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <p className="text-xs text-slate-600 mt-2 text-center">
            Orange bars = detected after-hours anomaly (non-essential equipment active 10PM–6AM)
          </p>
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
