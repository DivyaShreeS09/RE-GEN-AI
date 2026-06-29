export default function RegenScoreGauge({ before, after, improvement, rating }) {
  const radius = 70
  const circumference = 2 * Math.PI * radius
  const beforeOffset = circumference - (before / 100) * circumference
  const afterOffset = circumference - (after / 100) * circumference

  const getColor = (score) => {
    if (score >= 80) return '#00ff88'
    if (score >= 60) return '#00e5ff'
    if (score >= 40) return '#eab308'
    if (score >= 20) return '#f97316'
    return '#ef4444'
  }

  return (
    <div className="glass-card p-6 glow-green flex flex-col items-center">
      <h3 className="text-sm font-semibold text-cyan-400 uppercase tracking-widest mb-4">
        RE:GEN Score
      </h3>

      <div className="relative flex items-center justify-center gap-8">
        {/* Before */}
        <div className="flex flex-col items-center">
          <p className="text-xs text-slate-500 mb-2">Current</p>
          <svg width="160" height="160" viewBox="0 0 160 160">
            <circle cx="80" cy="80" r={radius} fill="none" stroke="#1e293b" strokeWidth="10" />
            <circle
              cx="80" cy="80" r={radius} fill="none"
              stroke={getColor(before)} strokeWidth="10"
              strokeDasharray={circumference}
              strokeDashoffset={beforeOffset}
              strokeLinecap="round"
              transform="rotate(-90 80 80)"
              style={{ transition: 'stroke-dashoffset 2s ease-out' }}
            />
            <text x="80" y="74" textAnchor="middle" className="fill-white text-3xl font-black" fontSize="28" fontWeight="800" fill="white">
              {before}
            </text>
            <text x="80" y="94" textAnchor="middle" fontSize="11" fill="#94a3b8">out of 100</text>
          </svg>
          <span className="text-xs px-2 py-1 rounded-full mt-1" style={{
            background: 'rgba(239,68,68,0.15)', color: '#ef4444', border: '1px solid rgba(239,68,68,0.3)'
          }}>Before</span>
        </div>

        {/* Arrow + improvement */}
        <div className="flex flex-col items-center gap-2">
          <div className="text-2xl">→</div>
          {improvement > 0 && (
            <span className="text-green-400 font-bold text-sm">+{improvement} pts</span>
          )}
        </div>

        {/* After */}
        <div className="flex flex-col items-center">
          <p className="text-xs text-slate-500 mb-2">After Actions</p>
          <svg width="160" height="160" viewBox="0 0 160 160">
            <circle cx="80" cy="80" r={radius} fill="none" stroke="#1e293b" strokeWidth="10" />
            <circle
              cx="80" cy="80" r={radius} fill="none"
              stroke={getColor(after)} strokeWidth="10"
              strokeDasharray={circumference}
              strokeDashoffset={afterOffset}
              strokeLinecap="round"
              transform="rotate(-90 80 80)"
              style={{ transition: 'stroke-dashoffset 2s ease-out' }}
            />
            <text x="80" y="74" textAnchor="middle" fontSize="28" fontWeight="800" fill="white">
              {after}
            </text>
            <text x="80" y="94" textAnchor="middle" fontSize="11" fill="#94a3b8">out of 100</text>
          </svg>
          <span className="text-xs px-2 py-1 rounded-full mt-1" style={{
            background: 'rgba(0,255,136,0.1)', color: '#00ff88', border: '1px solid rgba(0,255,136,0.3)'
          }}>{rating}</span>
        </div>
      </div>
    </div>
  )
}
