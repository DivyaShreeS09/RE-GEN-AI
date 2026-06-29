import { getWarRoom } from '../api'
import { useState, useEffect, useRef } from 'react'
import { RefreshCw, Clock, MessageSquare, CheckCircle, Cpu, Zap, Brain } from 'lucide-react'

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

const PIPELINE_PHASES = [
  {
    id: 'rules',
    label: 'Rule Engine',
    icon: <Cpu className="w-3.5 h-3.5" />,
    color: '#00e5ff',
    description: 'Deterministic threshold analysis',
    agentRange: [1, 3],
  },
  {
    id: 'impact',
    label: 'Impact & Decision',
    icon: <Brain className="w-3.5 h-3.5" />,
    color: '#a78bfa',
    description: 'Cross-domain scoring & ranking',
    agentRange: [4, 5],
  },
  {
    id: 'report',
    label: 'AI Reasoning & Report',
    icon: <Zap className="w-3.5 h-3.5" />,
    color: '#00ff88',
    description: 'Gemini narrative + executive summary',
    agentRange: [6, 7],
  },
]

const EXTRA_FEED = [
  { agent: 'Decision Engine',       message: 'Energy intervention promoted to Priority 1 — highest combined urgency and financial impact.', color: '#f97316' },
  { agent: 'Impact Analyzer',       message: 'Cross-domain opportunity: combining water + energy fixes amplifies CO2 reduction by ~35%.', color: '#a78bfa' },
  { agent: 'Water Leakage Agent',   message: 'Leakage confidence increased to 92% — night-flow signature matches known pipe pressure failure pattern.', color: '#00e5ff' },
  { agent: 'RE:GEN Score Agent',    message: 'Composite score finalised. Campus Health Grade computed from 6-dimension weighted formula.', color: '#3b82f6' },
  { agent: 'Waste-to-Wealth Agent', message: 'Processing pathway confirmed as highest-value route: 1.8x estimated recovery versus raw sale.', color: '#00ff88' },
  { agent: 'Report Agent',          message: 'Executive sustainability report finalised. AI reasoning layer enriched narrative with Gemini.', color: '#22c55e' },
  { agent: 'Energy Optimizer',      message: 'After-hours AC anomaly correlation confirmed: Seminar Hall (Jan 16) and Computer Lab (Jan 19).', color: '#eab308' },
]

function StatusChip({ status }) {
  const s = STATUS_CHIP[status] || STATUS_CHIP.idle
  return (
    <span className="text-xs px-2 py-0.5 rounded-full font-bold"
      style={{ background: s.bg, border: `1px solid ${s.border}`, color: s.color }}>
      {s.label}
    </span>
  )
}

/* Mini 3-phase progress per card */
function AgentPhaseBar({ visible, agentIdx }) {
  const [phase, setPhase] = useState(0)
  const phases = ['Loading data', 'Running rules', 'Finalising output']

  useEffect(() => {
    if (!visible) return
    if (phase >= phases.length - 1) return
    const delay = agentIdx * 180 + phase * 500
    const t = setTimeout(() => setPhase(p => Math.min(p + 1, phases.length - 1)), delay)
    return () => clearTimeout(t)
  }, [visible, phase, agentIdx])

  return (
    <div className="mt-3 pt-3" style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}>
      <div className="flex items-center gap-2">
        {phases.map((label, i) => (
          <div key={i} className="flex items-center gap-1">
            <div className={`w-1.5 h-1.5 rounded-full transition-all duration-500 ${
              i < phase  ? 'bg-green-400' :
              i === phase ? 'bg-cyan-400 animate-pulse' :
              'bg-slate-700'
            }`} />
            <span className={`text-xs transition-colors duration-300 ${
              i < phase  ? 'text-green-500' :
              i === phase ? 'text-cyan-400' :
              'text-slate-700'
            }`}>{label}</span>
            {i < phases.length - 1 && (
              <div className={`w-4 h-px transition-all duration-500 ${i < phase ? 'bg-green-600' : 'bg-slate-800'}`} />
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

function AgentCard({ agent, animDelay, cardIdx, visible }) {
  const urgency = agent.severity === 'critical' ? 95 : agent.severity === 'high' ? 75 :
                  agent.severity === 'medium'   ? 55 : agent.severity === 'low'   ? 30 : 15

  return (
    <div
      className="glass-card p-5 agent-card-hover"
      style={{
        opacity:    visible ? 1 : 0,
        transform:  visible ? 'translateY(0)' : 'translateY(16px)',
        transition: `opacity 0.45s ease ${animDelay}s, transform 0.45s ease ${animDelay}s`,
      }}
    >
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

      <div className="mb-3">
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
              width:      `${urgency}%`,
              background: urgency > 70
                ? 'linear-gradient(90deg,#ef4444,#f97316)'
                : 'linear-gradient(90deg,#eab308,#f97316)',
              transition: 'width 1.2s ease-out 0.3s',
            }} />
          </div>
        </div>
      </div>

      <AgentPhaseBar visible={visible} agentIdx={cardIdx} />
    </div>
  )
}

function PipelineHeader({ visibleCount }) {
  return (
    <div className="glass-card p-4 mb-6">
      <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3">
        Agent Pipeline — 3-Phase Execution
      </p>
      <div className="flex items-center gap-2 flex-wrap">
        {PIPELINE_PHASES.map((phase, i) => {
          const agentsInPhase = phase.agentRange[1] - phase.agentRange[0] + 1
          const phaseStart    = phase.agentRange[0] - 1
          const phaseDone     = visibleCount >= phase.agentRange[1]
          const phaseActive   = visibleCount >= phaseStart && !phaseDone

          return (
            <div key={phase.id} className="flex items-center gap-2">
              <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-500 ${
                phaseDone   ? 'bg-green-500/10 border border-green-500/25' :
                phaseActive ? 'border animate-pulse' :
                              'bg-slate-800/50 border border-slate-700/40'
              }`}
                style={phaseActive ? { borderColor: `${phase.color}60`, background: `${phase.color}08` } : {}}>
                <span style={{ color: phaseDone ? '#22c55e' : phaseActive ? phase.color : '#374151' }}>
                  {phaseDone ? <CheckCircle className="w-3.5 h-3.5" /> : phase.icon}
                </span>
                <span style={{ color: phaseDone ? '#22c55e' : phaseActive ? phase.color : '#374151' }}>
                  {phase.label}
                </span>
                <span className="text-xs opacity-60" style={{ color: phaseDone ? '#22c55e' : phaseActive ? phase.color : '#374151' }}>
                  ({agentsInPhase} agents)
                </span>
              </div>
              {i < PIPELINE_PHASES.length - 1 && (
                <div className={`w-6 h-px transition-all duration-500 ${phaseDone ? 'bg-green-600' : 'bg-slate-700'}`} />
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

function AgentFeed({ agents }) {
  const feedRef    = useRef(null)
  const [extraMsgs, setExtraMsgs] = useState([])
  const counterRef = useRef(0)

  const allMsgs = [
    ...agents.map((a, i) => ({
      agent:   a.agent,
      message: a.finding,
      color:   ['#00e5ff','#eab308','#00ff88','#a78bfa','#f97316','#3b82f6','#22c55e'][i % 7],
      time:    `00:0${String(i + 1).padStart(2, '0')}`,
    })),
    ...extraMsgs,
  ]

  useEffect(() => {
    if (feedRef.current) feedRef.current.scrollTop = feedRef.current.scrollHeight
  }, [allMsgs.length])

  useEffect(() => {
    const interval = setInterval(() => {
      const idx    = counterRef.current % EXTRA_FEED.length
      const baseIdx = agents.length + counterRef.current
      const pad    = n => String(n).padStart(2, '0')
      const min    = Math.floor(baseIdx / 60)
      const sec    = baseIdx % 60
      setExtraMsgs(prev => [...prev, { ...EXTRA_FEED[idx], time: `${pad(min)}:${pad(sec + 10)}` }])
      counterRef.current += 1
    }, 2800)
    return () => clearInterval(interval)
  }, [agents.length])

  return (
    <div className="glass-card p-5 mb-6">
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
  const [data,    setData]    = useState(initialData)
  const [loading, setLoading] = useState(false)
  const [visible, setVisible] = useState(0)   // how many cards are revealed

  /* Sequential card reveal — one every 280 ms */
  const agents = data || []
  useEffect(() => {
    if (!agents.length) return
    setVisible(0)
    const timers = agents.map((_, i) =>
      setTimeout(() => setVisible(v => Math.max(v, i + 1)), i * 280)
    )
    return () => timers.forEach(clearTimeout)
  }, [agents.length])

  const refresh = async () => {
    setLoading(true)
    try {
      const res = await getWarRoom()
      setData(res.data.war_room)
      setVisible(0)
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  return (
    <section className="px-6 py-16 max-w-7xl mx-auto" id="warroom">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-3xl font-black text-white mb-2">
            Agent <span className="text-gradient-green">War Room</span>
          </h2>
          <p className="text-slate-400 text-sm">
            7 autonomous agents — each analysing a distinct resource domain and escalating
            prioritised findings through a 3-phase execution pipeline.
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
          <PipelineHeader visibleCount={visible} />
          <AgentFeed agents={agents} />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
            {agents.map((agent, i) => (
              <AgentCard
                key={i}
                agent={agent}
                cardIdx={i}
                animDelay={0}
                visible={i < visible}
              />
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
