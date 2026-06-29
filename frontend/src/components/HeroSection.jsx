import { useEffect, useState } from 'react'
import { Leaf, Zap, Droplets, ArrowRight, Shield, Activity } from 'lucide-react'

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
  'Water Agent scanning night-flow logs...',
  'Energy Agent flagging after-hours anomalies...',
  'Waste Agent cross-referencing knowledge base...',
  'Decision Engine ranking interventions...',
  'RE:GEN Score Agent computing composite metrics...',
  'Report Agent compiling executive summary...',
]

const IMPACT_BADGES = [
  { icon: '♻️', label: 'Waste Recovery',   sub: '30 material pathways'       },
  { icon: '💧', label: 'Water Defense',    sub: 'Night-flow leak detection'  },
  { icon: '⚡', label: 'Energy Autopilot', sub: 'After-hours anomaly flagging' },
]

export default function HeroSection({ onScan, loading }) {
  const [stageIdx,   setStageIdx]   = useState(0)
  const [agentPulse, setAgentPulse] = useState(0)

  useEffect(() => {
    if (!loading) { setStageIdx(0); return }
    const t = setInterval(() => setStageIdx(i => Math.min(i + 1, SCAN_STAGES.length - 1)), 900)
    return () => clearInterval(t)
  }, [loading])

  useEffect(() => {
    const t = setInterval(() => setAgentPulse(i => (i + 1) % AGENTS.length), 600)
    return () => clearInterval(t)
  }, [])

  return (
    <section className="relative min-h-screen flex items-center grid-bg overflow-hidden px-6 py-20">
      {/* Animated background orbs */}
      <div className="float-orb   absolute top-1/4  left-1/5  w-[500px] h-[500px] bg-green-500/4  rounded-full blur-3xl pointer-events-none" />
      <div className="float-orb-2 absolute bottom-1/4 right-1/5 w-[400px] h-[400px] bg-cyan-500/5  rounded-full blur-3xl pointer-events-none" />
      <div className="float-orb-3 absolute top-3/4  left-2/3  w-[300px] h-[300px] bg-blue-500/4  rounded-full blur-3xl pointer-events-none" />

      {/* Moving scan line */}
      <div className="scan-sweep absolute left-0 right-0 h-px pointer-events-none"
        style={{ background: 'linear-gradient(90deg, transparent, rgba(0,229,255,0.3), transparent)' }} />

      <div className="relative z-10 w-full max-w-7xl mx-auto flex flex-col lg:flex-row items-center gap-12 lg:gap-20">

        {/* ── Left — text content, logo as centrepiece ─────────────── */}
        <div className="flex-1 text-center fade-in">

          {/* Capstone badge */}
          <div className="flex justify-center mb-8">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full"
              style={{ background: 'rgba(0,229,255,0.08)', border: '1px solid rgba(0,229,255,0.2)' }}>
              <div className="w-2 h-2 rounded-full bg-green-400 pulse-ring" />
              <span className="text-cyan-400 text-sm font-medium tracking-wider uppercase">
                Google Kaggle AI Agents Capstone
              </span>
            </div>
          </div>

          {/* ── Logo — primary hero element ──────────────────────────── */}
          <div className="flex justify-center mb-8">
            <div className="relative">
              {/* Pulsing outer ring */}
              <div className="absolute -inset-4 rounded-3xl pointer-events-none hero-logo-ring" />
              {/* Soft ambient halo */}
              <div className="absolute -inset-1 rounded-2xl pointer-events-none"
                style={{
                  boxShadow: '0 0 48px rgba(0,255,136,0.25), 0 0 96px rgba(0,229,255,0.12)',
                  borderRadius: '18px',
                }} />
              <img
                src="/src/assets/logo.jpeg"
                alt="RE:GEN AI — Autonomous Sustainability Command Center"
                style={{
                  width:        '176px',
                  height:       '176px',
                  borderRadius: '16px',
                  objectFit:    'cover',
                  position:     'relative',
                  zIndex:       10,
                  boxShadow:    '0 0 28px rgba(0,255,136,0.4), 0 0 56px rgba(0,229,255,0.2)',
                }}
              />
            </div>
          </div>

          {/* Product title — immediately below logo */}
          <h1 className="text-6xl lg:text-7xl font-black mb-3 leading-none tracking-tight">
            <span className="text-gradient-green">RE:GEN</span>
            <span className="text-white"> AI</span>
          </h1>

          <p className="text-lg text-cyan-300/80 font-semibold mb-3 tracking-wide">
            Autonomous Sustainability Command Center
          </p>
          <p className="text-slate-400 text-sm mb-10 max-w-xl mx-auto leading-relaxed">
            A multi-agent decision-support prototype that detects hidden resource loss in simulated
            smart-campus sensor logs, maps waste-to-value pathways, and generates agent-prioritised
            sustainability interventions — all without live IoT or ML training.
          </p>

          {/* Impact badges */}
          <div className="flex flex-wrap justify-center gap-3 mb-10">
            {IMPACT_BADGES.map((b) => (
              <div key={b.label} className="glass-card px-4 py-3 flex items-center gap-3 agent-card-hover">
                <span className="text-xl">{b.icon}</span>
                <div>
                  <p className="text-xs font-bold text-white">{b.label}</p>
                  <p className="text-xs text-slate-500">{b.sub}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Feature pills */}
          <div className="flex flex-wrap justify-center gap-2 mb-10">
            {[
              { icon: <Leaf      className="w-3.5 h-3.5" />, label: '7 Specialised Agents',      color: 'text-green-400'  },
              { icon: <Droplets  className="w-3.5 h-3.5" />, label: 'Night-Flow Leak Detection', color: 'text-cyan-400'   },
              { icon: <Zap       className="w-3.5 h-3.5" />, label: 'After-Hours Energy Audit',  color: 'text-yellow-400' },
              { icon: <Shield    className="w-3.5 h-3.5" />, label: 'Hazard Guardrails',         color: 'text-blue-400'   },
            ].map((item) => (
              <span key={item.label}
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium glass-card ${item.color}`}>
                {item.icon} {item.label}
              </span>
            ))}
          </div>

          {/* CTA */}
          <div className="flex flex-col items-center gap-4">
            <button className="btn-primary text-base glow-pulse-green" onClick={onScan} disabled={loading}>
              {loading ? (
                <>
                  <Activity className="w-4 h-4 animate-pulse" />
                  Scanning Campus Systems...
                </>
              ) : (
                <>
                  Launch Campus Intelligence Scan
                  <ArrowRight className="w-5 h-5" />
                </>
              )}
            </button>

            {loading && (
              <div className="glass-card px-4 py-3 text-xs text-cyan-400 font-mono max-w-sm type-in" key={stageIdx}>
                <span className="text-green-400 mr-2">&rsaquo;</span>{SCAN_STAGES[stageIdx]}
                <span className="animate-pulse">_</span>
              </div>
            )}
          </div>

          <p className="text-slate-600 text-xs mt-8 max-w-md mx-auto leading-relaxed">
            All data is simulated for demonstration. RE:GEN AI is a prototype decision-support system
            and not professional regulatory, financial, or engineering advice.
          </p>
        </div>

        {/* ── Right — Agent network card ────────────────────────────── */}
        <div className="hidden lg:block w-80 flex-shrink-0 fade-in" style={{ animationDelay: '0.3s' }}>
          <div className="glass-card p-5 glow-cyan">
            <div className="flex items-center justify-between mb-5">
              <p className="text-xs font-bold text-cyan-400 uppercase tracking-widest">Agent Network</p>
              <div className="flex items-center gap-1.5">
                <div className="w-1.5 h-1.5 rounded-full bg-green-400 pulse-ring" />
                <span className="text-xs text-green-400">7 Active</span>
              </div>
            </div>

            <div className="space-y-3 mb-5">
              {AGENTS.map((agent, i) => (
                <div key={agent.name} className="flex items-center justify-between"
                  style={{ animation: `fadeIn 0.4s ease-out ${agent.delay}s both` }}>
                  <div className="flex items-center gap-2.5">
                    <div className="relative">
                      <div className="w-2 h-2 rounded-full" style={{ background: agent.color }} />
                      {agentPulse === i && (
                        <div className="absolute inset-0 rounded-full agent-pulse" style={{ background: agent.color }} />
                      )}
                    </div>
                    <span className="text-xs text-slate-300">{agent.name}</span>
                  </div>
                  <span className="text-xs font-mono px-2 py-0.5 rounded"
                    style={{ background: `${agent.color}15`, color: agent.color }}>
                    {agentPulse === i ? 'ACTIVE' : 'READY'}
                  </span>
                </div>
              ))}
            </div>

            <div className="border-t pt-4" style={{ borderColor: 'rgba(0,229,255,0.1)' }}>
              <p className="text-xs text-slate-500 mb-3">Estimated campus impact</p>
              <div className="grid grid-cols-2 gap-2">
                <div className="p-2 rounded-lg text-center"
                  style={{ background: 'rgba(0,255,136,0.06)', border: '1px solid rgba(0,255,136,0.15)' }}>
                  <p className="text-sm font-black text-green-400">~678 L</p>
                  <p className="text-xs text-slate-500">water at risk</p>
                </div>
                <div className="p-2 rounded-lg text-center"
                  style={{ background: 'rgba(234,179,8,0.06)', border: '1px solid rgba(234,179,8,0.15)' }}>
                  <p className="text-sm font-black text-yellow-400">~229 kWh</p>
                  <p className="text-xs text-slate-500">energy wasted</p>
                </div>
              </div>
            </div>

            <p className="text-xs text-slate-600 text-center mt-4">Simulated 7-day sensor window</p>
          </div>
        </div>
      </div>

      {/* Agent icons — bottom decoration */}
      <div className="absolute bottom-8 left-0 right-0 flex justify-center gap-8 opacity-20">
        {['♻️','💧','⚡','🌿','🧠','🏆','📋'].map((emoji, i) => (
          <span key={i} className="text-xl"
            style={{ animation: `fadeIn 0.5s ease-in-out ${i * 0.12}s both` }}>{emoji}</span>
        ))}
      </div>
    </section>
  )
}
