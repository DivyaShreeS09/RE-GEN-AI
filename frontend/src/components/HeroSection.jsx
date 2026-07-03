import { useEffect, useState } from 'react'
import { Leaf, Zap, Droplets, ArrowRight, Shield, Activity, ChevronDown } from 'lucide-react'

const AGENTS = [
  { name: 'Waste-to-Wealth',   color: '#00ff88', delay: 0   },
  { name: 'Water Leakage',     color: '#00e5ff', delay: 0.4 },
  { name: 'Energy Optimizer',  color: '#eab308', delay: 0.8 },
  { name: 'Impact Analyzer',   color: '#a78bfa', delay: 1.2 },
  { name: 'Decision Engine',   color: '#f97316', delay: 1.6 },
  { name: 'RE:GEN Score',      color: '#3b82f6', delay: 2.0 },
  { name: 'Report Agent',      color: '#22c55e', delay: 2.4 },
]

const SCAN_STAGES = [
  'Connecting to campus data layer...',
  'Water Agent — scanning night-flow logs...',
  'Energy Agent — flagging anomalies...',
  'Waste Agent — mapping recovery pathways...',
  'Decision Engine — ranking interventions...',
  'RE:GEN Score — computing campus health...',
  'Report Agent — generating executive summary...',
]

const METRICS = [
  { value: '~678 L', label: 'water at risk',    color: '#00e5ff', bg: 'rgba(0,229,255,0.06)', border: 'rgba(0,229,255,0.15)' },
  { value: '~229 kWh', label: 'energy wasted',  color: '#eab308', bg: 'rgba(234,179,8,0.06)',  border: 'rgba(234,179,8,0.15)' },
  { value: '7 agents', label: 'in parallel',    color: '#00ff88', bg: 'rgba(0,255,136,0.06)',  border: 'rgba(0,255,136,0.15)' },
]

/* Agent network SVG — subtle animated pulse lines */
function AgentNetworkSVG({ pulseIdx }) {
  const nodes = [
    { x: 140, y: 40,  color: '#00ff88' },
    { x: 260, y: 80,  color: '#00e5ff' },
    { x: 60,  y: 120, color: '#eab308' },
    { x: 210, y: 150, color: '#a78bfa' },
    { x: 310, y: 190, color: '#f97316' },
    { x: 100, y: 210, color: '#3b82f6' },
    { x: 170, y: 280, color: '#22c55e' },
  ]
  const edges = [
    [0, 1], [0, 2], [1, 3], [2, 3], [3, 4], [3, 5], [4, 6], [5, 6],
  ]
  return (
    <svg width="370" height="320" className="opacity-40 pointer-events-none select-none" aria-hidden>
      {edges.map(([a, b], i) => (
        <line key={i}
          x1={nodes[a].x} y1={nodes[a].y} x2={nodes[b].x} y2={nodes[b].y}
          stroke="rgba(0,229,255,0.25)" strokeWidth="1"
          strokeDasharray="4 4"
          style={{ animation: `agentLinePulse ${2 + i * 0.4}s ease-in-out infinite`, animationDelay: `${i * 0.3}s` }}
        />
      ))}
      {nodes.map((n, i) => (
        <g key={i}>
          <circle cx={n.x} cy={n.y} r={i === pulseIdx ? 7 : 5} fill={n.color}
            style={{ transition: 'r 0.3s ease', filter: i === pulseIdx ? `drop-shadow(0 0 6px ${n.color})` : 'none' }} />
          {i === pulseIdx && (
            <circle cx={n.x} cy={n.y} r={12} fill="none" stroke={n.color} strokeWidth="1" opacity="0.4"
              style={{ animation: 'agentPulse 1.5s ease-out infinite' }} />
          )}
        </g>
      ))}
    </svg>
  )
}

export default function HeroSection({ onScan, loading }) {
  const [stageIdx,   setStageIdx]   = useState(0)
  const [agentPulse, setAgentPulse] = useState(0)

  useEffect(() => {
    if (!loading) { setStageIdx(0); return }
    const t = setInterval(() => setStageIdx(i => Math.min(i + 1, SCAN_STAGES.length - 1)), 900)
    return () => clearInterval(t)
  }, [loading])

  useEffect(() => {
    const t = setInterval(() => setAgentPulse(i => (i + 1) % AGENTS.length), 700)
    return () => clearInterval(t)
  }, [])

  return (
    <section className="relative min-h-screen flex flex-col items-center justify-center grid-bg overflow-hidden px-6 py-20">

      {/* Aurora background layers */}
      <div className="aurora-1" />
      <div className="aurora-2" />
      <div className="aurora-3" />

      {/* Scan line */}
      <div className="scan-sweep absolute left-0 right-0 h-px pointer-events-none"
        style={{ background: 'linear-gradient(90deg, transparent, rgba(0,229,255,0.3), transparent)' }} />

      <div className="relative z-10 w-full max-w-7xl mx-auto flex flex-col lg:flex-row items-center gap-12 lg:gap-16">

        {/* ── Left: Text + Logo + CTA ────────────────── */}
        <div className="flex-1 text-center lg:text-left fade-in">

          {/* One small capstone badge */}
          <div className="flex justify-center lg:justify-start mb-7">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full"
              style={{ background: 'rgba(0,229,255,0.06)', border: '1px solid rgba(0,229,255,0.15)' }}>
              <div className="w-1.5 h-1.5 rounded-full bg-green-400 status-dot-live" />
              <span className="text-cyan-500 text-xs font-medium tracking-wider">Google Kaggle AI Agents Capstone · 2025</span>
            </div>
          </div>

          {/* Logo */}
          <div className="flex justify-center lg:justify-start mb-7">
            <div className="relative">
              <div className="absolute -inset-4 rounded-3xl pointer-events-none hero-logo-ring" />
              <div className="absolute -inset-1 rounded-2xl pointer-events-none"
                style={{ boxShadow: '0 0 56px rgba(0,255,136,0.22), 0 0 112px rgba(0,229,255,0.10)' }} />
              <img
                src="/src/assets/logo.jpeg"
                alt="RE:GEN AI"
                style={{
                  width: '160px', height: '160px',
                  borderRadius: '16px',
                  objectFit: 'cover',
                  position: 'relative',
                  zIndex: 10,
                  boxShadow: '0 0 32px rgba(0,255,136,0.35), 0 0 64px rgba(0,229,255,0.18)',
                }}
              />
            </div>
          </div>

          {/* Title */}
          <h1 className="text-6xl lg:text-7xl font-black mb-2 leading-none tracking-tight">
            <span className="text-gradient-green">RE:GEN</span>
            <span className="text-white"> AI</span>
          </h1>

          <p className="text-xl text-cyan-300/80 font-semibold mb-2 tracking-wide">
            Sustainability Intelligence OS
          </p>
          <p className="text-sm text-slate-500 mb-8 tracking-wider uppercase">
            for Smart Campuses
          </p>

          {/* Product copy — clean, no "prototype" language */}
          <p className="text-slate-300 text-base mb-9 max-w-xl mx-auto lg:mx-0 leading-relaxed">
            Seven specialized AI agents monitor campus water, energy, and waste in parallel —
            surfacing hidden losses, mapping recovery pathways, and delivering ranked interventions
            with estimated financial and carbon impact.
          </p>

          {/* Feature pills */}
          <div className="flex flex-wrap justify-center lg:justify-start gap-2 mb-9">
            {[
              { icon: <Leaf     className="w-3.5 h-3.5" />, label: '7 Specialized Agents',   color: 'text-green-400'  },
              { icon: <Droplets className="w-3.5 h-3.5" />, label: 'Night-Flow Detection',   color: 'text-cyan-400'   },
              { icon: <Zap      className="w-3.5 h-3.5" />, label: 'After-Hours Energy Audit', color: 'text-yellow-400' },
              { icon: <Shield   className="w-3.5 h-3.5" />, label: 'Hazard Guardrails',       color: 'text-blue-400'   },
            ].map((item) => (
              <span key={item.label}
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium glass-card ${item.color}`}>
                {item.icon} {item.label}
              </span>
            ))}
          </div>

          {/* CTA group */}
          <div className="flex flex-col sm:flex-row items-center lg:items-start gap-3">
            <button className="btn-primary text-base glow-pulse-green" onClick={onScan} disabled={loading}>
              {loading ? (
                <>
                  <Activity className="w-4 h-4 animate-pulse" />
                  Scanning Campus Systems...
                </>
              ) : (
                <>
                  Launch Campus Scan
                  <ArrowRight className="w-5 h-5" />
                </>
              )}
            </button>

            <a href="#action-plan" className="btn-secondary">
              View Executive Report
            </a>
          </div>

          {loading && (
            <div className="mt-5 glass-card px-4 py-3 text-xs text-cyan-400 font-mono max-w-sm type-in" key={stageIdx}>
              <span className="text-green-400 mr-2">&rsaquo;</span>{SCAN_STAGES[stageIdx]}
              <span className="animate-pulse">_</span>
            </div>
          )}
        </div>

        {/* ── Right: Agent command card ──────────────── */}
        <div className="hidden lg:flex flex-col gap-4 w-[340px] flex-shrink-0 fade-in" style={{ animationDelay: '0.25s' }}>

          {/* Agent network visualizer */}
          <div className="depth-card p-5 overflow-hidden">
            <div className="flex items-center justify-between mb-3">
              <p className="text-xs font-bold text-cyan-400 uppercase tracking-widest">Agent Network</p>
              <div className="flex items-center gap-1.5">
                <div className="w-1.5 h-1.5 rounded-full bg-green-400 status-dot-live" />
                <span className="text-xs text-green-400 font-medium">7 Online</span>
              </div>
            </div>

            <div className="flex justify-center mb-2">
              <AgentNetworkSVG pulseIdx={agentPulse} />
            </div>

            <div className="space-y-2">
              {AGENTS.map((agent, i) => (
                <div key={agent.name} className="flex items-center justify-between"
                  style={{ animation: `fadeIn 0.4s ease-out ${agent.delay}s both` }}>
                  <div className="flex items-center gap-2">
                    <div className="relative w-2 h-2 rounded-full flex-shrink-0" style={{ background: agent.color }}>
                      {agentPulse === i && (
                        <div className="absolute inset-0 rounded-full agent-pulse" style={{ background: agent.color }} />
                      )}
                    </div>
                    <span className="text-xs text-slate-300">{agent.name}</span>
                  </div>
                  <span className="text-xs font-mono px-2 py-0.5 rounded font-bold"
                    style={{ background: `${agent.color}12`, color: agent.color }}>
                    {agentPulse === i ? 'ACTIVE' : 'READY'}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Estimated impact strip */}
          <div className="depth-card p-4">
            <p className="text-xs text-slate-500 uppercase tracking-widest mb-3 font-semibold">7-day campus scan estimate</p>
            <div className="grid grid-cols-3 gap-2">
              {METRICS.map((m) => (
                <div key={m.label} className="p-2.5 rounded-lg text-center"
                  style={{ background: m.bg, border: `1px solid ${m.border}` }}>
                  <p className="text-sm font-black mb-0.5" style={{ color: m.color }}>{m.value}</p>
                  <p className="text-xs text-slate-500">{m.label}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Scroll cue */}
      <a href="#dashboard" className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-1 opacity-30 hover:opacity-70 transition-opacity no-print"
        style={{ animationDelay: '2s' }}>
        <span className="text-xs text-slate-500 uppercase tracking-widest font-medium">Scroll</span>
        <ChevronDown className="w-4 h-4 text-slate-500 animate-bounce" />
      </a>
    </section>
  )
}
