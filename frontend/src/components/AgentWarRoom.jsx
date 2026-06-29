import { getWarRoom } from '../api'
import { useState, useEffect, useRef } from 'react'
import { RefreshCw, Clock, MessageSquare } from 'lucide-react'

const STATUS_CHIP = {
  active:    { label: 'ACTIVE',    bg: 'rgba(0,255,136,0.12)',  border: 'rgba(0,255,136,0.4)',   color: '#00ff88' },
  reasoning: { label: 'REASONING', bg: 'rgba(0,229,255,0.1)',   border: 'rgba(0,229,255,0.4)',   color: '#00e5ff' },
  escalated: { label: 'ESCALATED', bg: 'rgba(239,68,68,0.12)',  border: 'rgba(239,68,68,0.4)',   color: '#ef4444' },
  standby:   { label: 'STANDBY',   bg: 'rgba(59,130,246,0.1)',  border: 'rgba(59,130,246,0.35)', color: '#3b82f6' },
  completed: { label: 'COMPLETED', bg: 'rgba(34,197,94,0.1)',   border: 'rgba(34,197,94,0.3)',   color: '#22c55e' },
  idle:      { label: 'IDLE',      bg: 'rgba(107,114,128,0.08)',border: 'rgba(107,114,128,0.2)', color: '#6b7280' },
}

const BADGE_CLS = {
  critical: 'badge-critical', high: 'badge-high', medium: 'badge-medium',
  low: 'badge-low', none: 'badge-none', info: 'badge-info',
}

/* Extra messages that replay on a timer to make the feed feel alive */
const EXTRA_FEED = [
  { agent: 'Decision Engine',      message: 'Energy intervention promoted to Priority 1 — highest combined urgency and financial impact.', color: '#f97316' },
  { agent: 'Impact Analyzer',      message: 'Cross-domain opportunity: combining water + energy fixes amplifies CO₂ reduction by ~35%.', color: '#a78bfa' },
  { agent: 'Water Leakage Agent',  message: 'Leakage confidence increased to 92% — night-flow signature matches known pipe pressure failure pattern.', color: '#00e5ff' },
  { agent: 'RE:GEN Score Agent',   message: 'Composite score finalized. Waste recovery pathway adds +8 pts to circular economy dimension.', color: '#3b82f6' },
  { agent: 'Waste-to-Wealth Agent',message: 'Processing pathway confirmed as highest-value route: 1.8× estimated recovery versus raw sale.', color: '#00ff88' },
  { agent: 'Report Agent',         message: 'Executive sustainability report finalized. Action plan exported to Priority Actions section.', color: '#22c55e' },
  { agent: 'Energy Optimizer',     message: 'After-hours AC anomaly correlation confirmed across Seminar Hall (Jan 16) and Computer Lab (Jan 19).', color: '#eab308' },
]

function StatusChip({ status }) {
  const s = STATUS_CHIP[status] || STATUS_CHIP.idle
  return (
    <span className="text-xs px-2 py-0.5 rounded-full font-bold" style={{
      background: s.bg, border: `1px solid ${s.border}`, color: s.color,
    }}>{s.label}</span>
  )
}

function AgentCard({ agent, animDelay }) {
  const urgency = agent.severity === 'critical' ? 95 : agent.severity === 'high' ? 75 :
    agent.severity === 'medium' ? 55 : agent.severity === 'low' ? 30 : 15

  return (
    <div className="glass-card p-5 agent-card-hover fade-in" style={{ animationDelay: `${animDelay}s` }}>
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="relative">
            <span className="text-2xl">{agent.icon}</span>
            {agent.status === 'active' && (
              <div className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-green-400 agent-pulse" />
            )}
          </div>
          <div>
            <h3 className="font-bold text-white text-sm leading-tight">{agent.agent}</h3>
            <div className="mt-1"><StatusChip status={agent.status} /></div>
          </div>
        </div>
        {agent.severity && (
          <span className={`text-xs px-2 py-1 rounded-full font-medium ${BADGE_CLS[agent.severity] || 'badge-info'}`}>
            {agent.severity?.toUpperCase()}
          </span>
        )}
      </div>

      {agent.key_metric && (
        <div className="mb-3 p-2.5 rounded-lg text-center"
          style={{ background: 'rgba(0,229,255,0.06)', border: '1px solid rgba(0,229,255,0.12)' }}>
          <p className="text-cyan-400 font-black text-lg">{agent.key_metric}</p>
          <p className="text-xs text-slate-500 mt-0.5">key metric</p>
        </div>
      )}

      <div className="mb-3">
        <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Finding</p>
        <p className="text-xs text-slate-300 leading-relaxed">{agent.finding}</p>
      </div>

      <div className="mb-4">
        <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Recommendation</p>
        <p className="text-xs text-green-400 leading-relaxed">{agent.recommendation}</p>
      </div>

      <div className="space-y-2.5">
        {agent.confidence != null && (
          <div>
            <div className="flex justify-between items-center mb-1">
              <p className="text-xs text-slate-500">Confidence</p>
              <p className="text-xs text-cyan-400 font-bold">{Math.round(agent.confidence * 100)}%</p>
            </div>
            <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
              <div className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-green-400"
                style={{ width: `${agent.confidence * 100}%`, transition: 'width 1.2s ease-out' }} />
            </div>
          </div>
        )}
        <div>
          <div className="flex justify-between items-center mb-1">
            <p className="text-xs text-slate-500">Urgency</p>
            <p className="text-xs font-bold" style={{
              color: urgency > 70 ? '#ef4444' : urgency > 50 ? '#f97316' : '#eab308',
            }}>{urgency}%</p>
          </div>
          <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
            <div className="h-full rounded-full" style={{
              width: `${urgency}%`,
              background: urgency > 70
                ? 'linear-gradient(90deg,#ef4444,#f97316)'
                : 'linear-gradient(90deg,#eab308,#f97316)',
              transition: 'width 1.2s ease-out 0.3s',
            }} />
          </div>
        </div>
      </div>
    </div>
  )
}

function AgentFeed({ agents }) {
  const feedRef = useRef(null)
  const [extraMsgs, setExtraMsgs] = useState([])
  const counterRef = useRef(0)

  /* Auto-scroll on new messages */
  const allMsgs = [
    ...agents.map((a, i) => ({
      agent: a.agent,
      message: a.finding,
      color: ['#00e5ff','#eab308','#00ff88','#a78bfa','#f97316','#3b82f6','#22c55e'][i % 7],
      time: `00:0${String(i + 1).padStart(2, '0')}`,
    })),
    ...extraMsgs,
  ]

  useEffect(() => {
    if (feedRef.current) feedRef.current.scrollTop = feedRef.current.scrollHeight
  }, [allMsgs.length])

  /* Add a new extra message every 2.8 s */
  useEffect(() => {
    const interval = setInterval(() => {
      const idx = counterRef.current % EXTRA_FEED.length
      const baseIdx = agents.length + counterRef.current
      const pad = n => String(n).padStart(2, '0')
      const min = Math.floor(baseIdx / 60)
      const sec = baseIdx % 60
      setExtraMsgs(prev => [
        ...prev,
        { ...EXTRA_FEED[idx], time: `${pad(min)}:${pad(sec + 10)}` },
      ])
      counterRef.current += 1
    }, 2800)
    return () => clearInterval(interval)
  }, [agents.length])

  return (
    <div className="glass-card p-5 mb-8">
      <div className="flex items-center gap-2 mb-4">
        <MessageSquare className="w-4 h-4 text-cyan-400" />
        <h3 className="text-xs font-bold text-cyan-400 uppercase tracking-widest">
          Agent Collaboration Feed
        </h3>
        <div className="ml-auto flex items-center gap-1.5">
          <div className="w-1.5 h-1.5 rounded-full bg-green-400 pulse-ring" />
          <span className="text-xs text-green-400">Live</span>
        </div>
      </div>

      <div ref={feedRef} className="space-y-2 max-h-52 overflow-y-auto pr-1"
        style={{ scrollbarWidth: 'thin' }}>
        {allMsgs.map((m, i) => (
          <div key={i} className="flex items-start gap-3 type-in"
            style={{ animationDelay: `${Math.min(i, 8) * 0.1}s` }}>
            <span className="text-xs text-slate-600 font-mono flex-shrink-0 mt-0.5">{m.time}</span>
            <div className="flex-1 p-2 rounded-lg"
              style={{ background: 'rgba(15,23,42,0.6)', border: `1px solid ${m.color}18` }}>
              <span className="text-xs font-bold mr-2" style={{ color: m.color }}>{m.agent}:</span>
              <span className="text-xs text-slate-400">{m.message}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function AgentWarRoom({ initialData }) {
  const [data, setData]     = useState(initialData)
  const [loading, setLoading] = useState(false)

  const refresh = async () => {
    setLoading(true)
    try {
      const res = await getWarRoom()
      setData(res.data.war_room)
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  const agents = data || []

  return (
    <section className="px-6 py-16 max-w-7xl mx-auto" id="warroom">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-3xl font-black text-white mb-2">
            Agent <span className="text-gradient-green">War Room</span>
          </h2>
          <p className="text-slate-400 text-sm">
            7 autonomous agents — each analyzing a distinct resource domain and escalating
            prioritized findings to the decision engine.
          </p>
        </div>
        <button onClick={refresh} disabled={loading}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm text-cyan-400 font-medium glass-card hover:border-cyan-400/40 transition-all">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Re-run Agents
        </button>
      </div>

      {agents.length === 0 ? (
        <div className="glass-card p-16 text-center">
          <Clock className="w-12 h-12 text-slate-600 mx-auto mb-4" />
          <p className="text-slate-400">Run a sustainability scan to activate the agent war room.</p>
        </div>
      ) : (
        <>
          <AgentFeed agents={agents} />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
            {agents.map((agent, i) => (
              <AgentCard key={i} agent={agent} animDelay={i * 0.08} />
            ))}
          </div>
        </>
      )}

      <div className="mt-6 flex flex-wrap items-center gap-5 text-xs text-slate-600">
        {Object.entries(STATUS_CHIP).map(([k, v]) => (
          <div key={k} className="flex items-center gap-1.5">
            <div className="w-1.5 h-1.5 rounded-full" style={{ background: v.color }} />
            <span style={{ color: v.color }}>{v.label}</span>
          </div>
        ))}
      </div>
    </section>
  )
}
