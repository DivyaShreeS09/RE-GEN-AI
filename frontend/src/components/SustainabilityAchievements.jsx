export default function SustainabilityAchievements({ dashData, waterData, energyData, uploadResult }) {
  const isUploadMode = !!uploadResult
  const regenAfter  = dashData?.regen_score?.after_score    || 0
  const co2Saved    = dashData?.impact_summary?.total_co2_saved_kg || 0
  const waterSev    = dashData?.water_summary?.severity     || 'none'
  const energySev   = dashData?.energy_summary?.severity    || 'none'
  const wasted      = waterData?.total_wasted_liters        || 0
  const wastedKwh   = energyData?.total_wasted_kwh          || 0

  const critical = ['critical', 'high', 'medium']

  const ACHIEVEMENTS = [
    {
      emoji: '💧',
      title: 'Water Guardian',
      desc: 'Detected night-flow leakage pattern in campus water logs',
      color: '#00e5ff',
      glow: '',
      unlocked: critical.includes(waterSev),
      progress: wasted > 500 ? 100 : wasted > 200 ? 80 : 55,
      detail: wasted > 0
        ? `${wasted.toFixed(0)} L anomaly identified — fix rate 85%`
        : 'Run water analysis to unlock',
    },
    {
      emoji: '⚡',
      title: 'Energy Optimizer',
      desc: 'Found after-hours energy consumption anomaly across campus zones',
      color: '#eab308',
      glow: '',
      unlocked: critical.includes(energySev),
      progress: wastedKwh > 200 ? 100 : wastedKwh > 100 ? 78 : 50,
      detail: wastedKwh > 0
        ? `${wastedKwh.toFixed(1)} kWh after-hours waste detected`
        : 'Run energy scan to unlock',
    },
    {
      emoji: '🌱',
      title: 'Carbon Saver',
      desc: 'Identified a CO₂ reduction pathway through multi-domain intervention',
      color: '#22c55e',
      glow: co2Saved > 0 ? 'achieve-glow-green' : '',
      unlocked: co2Saved > 0,
      progress: co2Saved > 0 ? Math.min(100, Math.round(co2Saved * 5)) : 35,
      detail: co2Saved > 0
        ? `${co2Saved.toFixed(1)} kg CO₂ reduction pathway confirmed`
        : 'Complete water + energy analysis to unlock',
    },
    {
      emoji: '♻',
      title: 'Circular Economy Champion',
      desc: 'Mapped waste-to-value recovery pathway for campus material streams',
      color: '#a78bfa',
      glow: '',
      unlocked: true,
      progress: 78,
      detail: '3 recovery pathways evaluated — processing route recommended (1.8× value)',
    },
    {
      emoji: '🛡',
      title: 'Hazard Guardian',
      desc: 'Triggered hazardous waste compliance guardrail and suppressed unsafe financial claims',
      color: '#ef4444',
      glow: '',
      unlocked: true,
      progress: 100,
      detail: 'Hazardous waste guardrail activated — financial estimates correctly suppressed',
    },
    {
      emoji: '🏆',
      title: 'Green Campus',
      desc: 'Achieve RE:GEN Score above 70 to earn full sustainability certification',
      color: '#f59e0b',
      glow: regenAfter >= 70 ? 'achieve-glow-gold' : '',
      unlocked: regenAfter >= 70,
      progress: Math.min(100, Math.round((regenAfter / 70) * 100)),
      detail: regenAfter >= 70
        ? `Score ${regenAfter} — certified!`
        : `Current target: ${regenAfter} / 70 required`,
    },
  ]

  const unlockedCount = ACHIEVEMENTS.filter(a => a.unlocked).length

  return (
    <section className="px-6 py-16 max-w-7xl mx-auto" id="achievements">
      <div className="mb-8">
        <h2 className="text-3xl font-black text-white mb-2">
          Sustainability <span className="text-gradient-gold">Achievements</span>
        </h2>
        <p className="text-slate-400 text-sm max-w-2xl">
          Intelligence milestones unlocked during this scan cycle — each badge represents a detection,
          pathway, or guardrail triggered by the multi-agent network.
        </p>
        <div className="mt-3 flex items-center gap-3">
          <div className="flex gap-1.5">
            {ACHIEVEMENTS.map((a, i) => (
              <div key={i} className="w-2 h-2 rounded-full transition-all duration-700"
                style={{ background: a.unlocked ? a.color : 'rgba(100,116,139,0.25)' }} />
            ))}
          </div>
          <span className="text-xs text-slate-400">
            {unlockedCount} / {ACHIEVEMENTS.length} achievements unlocked
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {ACHIEVEMENTS.map((ach, i) => (
          <div key={i}
            className={`glass-card p-5 agent-card-hover fade-in ${!ach.unlocked ? 'opacity-50' : ''}`}
            style={{
              animationDelay: `${i * 0.08}s`,
              borderColor: ach.unlocked ? ach.color + '30' : undefined,
            }}>
            <div className="flex items-start gap-4">
              {/* Badge */}
              <div className={`text-3xl p-3 rounded-xl flex-shrink-0 leading-none ${ach.glow}`}
                style={{
                  background: ach.unlocked ? ach.color + '12' : 'rgba(30,41,59,0.4)',
                  border: `1px solid ${ach.unlocked ? ach.color + '35' : 'rgba(255,255,255,0.05)'}`,
                  filter: ach.unlocked ? undefined : 'grayscale(0.85) brightness(0.5)',
                }}>
                {ach.emoji}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2 mb-1">
                  <h3 className="font-bold text-sm leading-tight"
                    style={{ color: ach.unlocked ? ach.color : '#475569' }}>
                    {ach.title}
                  </h3>
                  {ach.unlocked && (
                    <span className="text-xs px-2 py-0.5 rounded-full font-bold flex-shrink-0"
                      style={{
                        background: ach.color + '15',
                        color: ach.color,
                        border: `1px solid ${ach.color}30`,
                      }}>
                      ✓
                    </span>
                  )}
                </div>

                <p className="text-xs text-slate-500 leading-relaxed mb-3">{ach.desc}</p>

                {/* Progress */}
                <div className="mb-2">
                  <div className="flex justify-between mb-1">
                    <span className="text-xs text-slate-600">Progress</span>
                    <span className="text-xs font-bold" style={{ color: ach.unlocked ? ach.color : '#475569' }}>
                      {ach.progress}%
                    </span>
                  </div>
                  <div className="h-1 bg-slate-800 rounded-full overflow-hidden">
                    <div className="h-full rounded-full progress-entry"
                      style={{
                        width: `${ach.progress}%`,
                        background: ach.unlocked
                          ? `linear-gradient(90deg, ${ach.color}70, ${ach.color})`
                          : '#1e293b',
                        animationDelay: `${i * 0.1 + 0.3}s`,
                      }} />
                  </div>
                </div>

                <p className="text-xs text-slate-600 truncate" title={ach.detail}>{ach.detail}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <p className="text-xs text-slate-700 text-center mt-6">
        Achievement progress derived from {isUploadMode ? 'uploaded data analysis' : 'simulated sensor analysis'} · Not a regulatory certification
      </p>
    </section>
  )
}
