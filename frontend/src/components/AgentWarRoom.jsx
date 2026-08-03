import { getWarRoom } from '../api'
import { useState, useEffect, useRef, useCallback, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { RefreshCw } from 'lucide-react'

/* ── Agent definitions ─────────────────────────────── */
const AGENT_META = [
  { id: 'water',    label: 'Water',    sub: 'Leakage Detection',  color: '#00b4ff', icon: '💧', angle: -90,
    observation: 'Night-flow anomaly detected at 03:14 — 380 L in 2 hrs. Hostel Block A plumbing shows sustained pressure differential.',
    reasoning: 'Flow rate exceeds normal baseline by 3.2×. Pattern matches known micro-crack burst signature in ground-floor supply lines.',
    impact: 'Est. 1,420 L/week hidden loss. Potential structural water damage if unaddressed.',
    recommendation: 'Inspect ground-floor pipe fittings. Deploy auto-shutoff valve at main entry by Jan 22.',
    confidence: 0.92, priority: 1, urgency: 'HIGH',
    metric: '1,420 L/wk', metricLabel: 'Hidden Water Loss',
  },
  { id: 'energy',   label: 'Energy',   sub: 'Grid Optimizer',     color: '#eab308', icon: '⚡', angle: -38,
    observation: 'HVAC continues running 6.5 hrs post-occupancy in Seminar Hall (Jan 16). 68 kWh overnight with zero occupants.',
    reasoning: 'Occupancy sensor gap in main auditorium. HVAC schedule not linked to event calendar. Workstation power plans set to "never sleep".',
    impact: 'Est. 68 kWh/night × 22 working days = 1,496 kWh/mo in wasted cooling energy.',
    recommendation: 'Install occupancy-linked HVAC automation. Enforce default-off workstation policy campus-wide.',
    confidence: 0.88, priority: 1, urgency: 'HIGH',
    metric: '68 kWh', metricLabel: 'Nightly Waste',
  },
  { id: 'waste',    label: 'Waste',    sub: 'Wealth Agent',       color: '#00ff88', icon: '♻',  angle:  14,
    observation: 'Canteen generates 28 kg organic waste/day. Currently routed to mixed disposal. High-value compostable fraction identified.',
    reasoning: 'Organic fraction at 71% of total waste stream. Biogas pathway yields ~1.8× vs raw sale. Zero capital required for initial compost setup.',
    impact: 'Est. resource recovery potential from compost + biogas pathway. Mixed disposal forfeits recovery opportunity.',
    recommendation: 'Route organic waste to biogas digester. Transition to biodegradable packaging. Segregation bins at canteen entry.',
    confidence: 0.81, priority: 2, urgency: 'MEDIUM',
    metric: '28 kg/day', metricLabel: 'Organic Load',
  },
  { id: 'impact',   label: 'Impact',   sub: 'Analyzer',           color: '#f472b6', icon: '✦',  angle:  66,
    observation: 'Cross-domain analysis: simultaneous water + energy interventions create compounding sustainability gains vs addressing each independently.',
    reasoning: 'Energy-water nexus: fixing HVAC reduces condensate drain load (water). Fixing leaks reduces pump energy. Combined CO₂ reduction ~35% better than sequential fixes.',
    impact: 'Campus carbon footprint reduction est. 4.8 tCO₂e/year with full intervention stack. SDG 6, 7, 13 alignment confirmed.',
    recommendation: 'Prioritize Energy fix first (fastest payback), then Water (structural risk), then Waste (ongoing recovery).',
    confidence: 0.79, priority: 2, urgency: 'MEDIUM',
    metric: '~35%', metricLabel: 'CO₂ Synergy Gain',
  },
  { id: 'score',    label: 'Score',    sub: 'Campus Health',      color: '#a78bfa', icon: '◈',  angle: 118,
    observation: 'Composite campus health index computed across 6 dimensions: water, energy, waste, carbon, compliance, infrastructure. Score: 61/100.',
    reasoning: 'Energy dimension scores lowest (38/100) due to overnight consumption anomalies. Water at 52/100. Waste at 48/100. Carbon at 55/100.',
    impact: 'Current grade: C. Target: B+ (75/100) achievable within 60 days with Priority 1 and 2 interventions.',
    recommendation: 'Address Priority 1 items (Energy + Water) to lift score to ~74. Then target waste pathway for B+ territory.',
    confidence: 0.85, priority: 3, urgency: 'LOW',
    metric: '61/100', metricLabel: 'Campus Health Index',
  },
  { id: 'report',   label: 'Report',   sub: 'Narrative Engine',   color: '#22d3ee', icon: '◻',  angle: 170,
    observation: 'All agent findings consolidated. Executive narrative layer generated via AI reasoning. Report is multi-domain and action-ready.',
    reasoning: 'Findings from 7 agents cross-validated. Conflicting signals reconciled. Priority stack confirmed by Decision Agent. AI narrative layer applied.',
    impact: 'Decision-support report ready for campus administration and sustainability office. Action plan covers 13 prioritized interventions.',
    recommendation: 'Distribute report to Facilities, Electrical, and Sustainability teams. Schedule monthly re-run to track intervention progress.',
    confidence: 0.95, priority: 3, urgency: 'LOW',
    metric: '13 items', metricLabel: 'Action Plan',
  },
  { id: 'decision', label: 'Decision', sub: 'Priority Engine',    color: '#e2e8f0', icon: '◆',  angle: 222,
    observation: 'Priority engine ranked all interventions by urgency × estimated impact × implementation cost. Final stack dispatched to Report Agent.',
    reasoning: 'Energy intervention: high urgency, low cost, fast payback → Priority 1. Water: structural risk escalation → Priority 1 co-ranked. Waste: medium urgency, medium payback → Priority 2.',
    impact: 'Optimized intervention order minimizes time-to-impact while respecting available budget and team capacity constraints.',
    recommendation: 'Begin with Seminar Hall HVAC automation (Week 1). Hostel plumbing inspection (Week 2). Canteen compost setup (Month 2).',
    confidence: 0.90, priority: 1, urgency: 'HIGH',
    metric: 'Priority 1', metricLabel: 'Decision Rank',
  },
]

const REASONING_STREAM = [
  { agent: 'water',    color: '#00b4ff', msg: 'Night-flow anomaly at 03:14 — 380 L in 2 hrs. Burst pattern confirmed.' },
  { agent: 'energy',   color: '#eab308', msg: 'AC runtime +6.5 hrs post-occupancy. Seminar Hall Jan 16 correlation: 68 kWh.' },
  { agent: 'waste',    color: '#00ff88', msg: 'Organic load 28 kg/day at Canteen. Compost pathway yields 1.8× vs raw sale.' },
  { agent: 'impact',   color: '#f472b6', msg: 'Cross-domain synergy: water + energy co-fix amplifies CO₂ reduction ~35%.' },
  { agent: 'score',    color: '#a78bfa', msg: 'Composite health grade computed from 6-dimension weighted formula. Score: 61/100.' },
  { agent: 'decision', color: '#e2e8f0', msg: 'Energy intervention promoted to Priority 1 — highest urgency × financial impact.' },
  { agent: 'report',   color: '#22d3ee', msg: 'Executive summary enriched. AI narrative layer finalised.' },
  { agent: 'water',    color: '#00b4ff', msg: 'Leakage confidence escalated to 92% — matches known pipe pressure failure pattern.' },
  { agent: 'impact',   color: '#f472b6', msg: 'Water loss estimated: ₹12,400–₹18,600 annually if unaddressed.' },
  { agent: 'decision', color: '#e2e8f0', msg: 'Final priority stack: [1] Energy [2] Water [3] Waste. Dispatching to Report Agent.' },
  { agent: 'report',   color: '#22d3ee', msg: 'Mission complete. All agent findings consolidated into decision-support report.' },
]

/* ── Coordinate system ─────────────────────────────── */
const AW = 680, AH = 680          // logical artboard size
const CX = AW / 2, CY = AH / 2   // core center
const ORBIT_R = 270               // agent orbit radius (+35% scale)

function agentCoord(meta) {
  const r = (meta.angle * Math.PI) / 180
  return { x: CX + ORBIT_R * Math.cos(r), y: CY + ORBIT_R * Math.sin(r) }
}

/* Full path for animateMotion (core → exact node center) */
function buildFullPath(meta) {
  const a = agentCoord(meta)
  return `M ${CX},${CY} L ${a.x},${a.y}`
}

/* Visible path: core → just outside node edge (stops 50 logical units before center) */
function buildPath(meta) {
  const a = agentCoord(meta)
  const dx = a.x - CX, dy = a.y - CY
  const len = Math.sqrt(dx * dx + dy * dy)  // = ORBIT_R = 270
  const stop = (len - 50) / len
  return `M ${CX},${CY} L ${CX + dx * stop},${CY + dy * stop}`
}

/* ── Background floating particles ────────────────── */
const PARTICLE_COLORS = ['#00e5ff', '#00ff88', '#a78bfa', '#f472b6', '#eab308']
function BackgroundParticles() {
  const pts = useMemo(() => Array.from({ length: 48 }, (_, i) => ({
    id: i,
    x: ((i * 7919 + 3571) % 10000) / 100,
    y: ((i * 6271 + 1999) % 10000) / 100,
    size: 1.0 + ((i * 2311) % 1000) / 500,
    dur: 6 + ((i * 1999) % 10),
    delay: -((i * 3211) % 13),
    opacity: 0.10 + ((i * 1777) % 1000) / 4000,
    color: PARTICLE_COLORS[i % PARTICLE_COLORS.length],
  })), [])

  return (
    <div style={{ position: 'absolute', inset: 0, overflow: 'hidden', pointerEvents: 'none', zIndex: 2 }}>
      {pts.map(p => (
        <div
          key={p.id}
          style={{
            position: 'absolute',
            left: `${p.x}%`,
            top: `${p.y}%`,
            width: p.size,
            height: p.size,
            borderRadius: '50%',
            background: p.color,
            opacity: p.opacity,
            boxShadow: `0 0 ${p.size * 3}px ${p.color}`,
            animation: `warParticleFloat ${p.dur}s ${p.delay}s linear infinite`,
          }}
        />
      ))}
    </div>
  )
}

/* ── AI Core (CSS-only, no canvas) ─────────────────── */
function AICore() {
  const RAY_ANGLES = [0, 22.5, 45, 67.5, 90, 112.5, 135, 157.5, 180, 202.5, 225, 247.5, 270, 292.5, 315, 337.5]
  return (
    <div style={{
      position: 'absolute',
      left: `${(CX / AW) * 100}%`,
      top:  `${(CY / AH) * 100}%`,
      width: 0, height: 0,
      zIndex: 5,
      pointerEvents: 'none',
    }}>
      {/* Outer halo bloom */}
      <div className="war-core-halo" />

      {/* Concentric rings */}
      <div className="war-ring war-ring-1" />
      <div className="war-ring war-ring-2" />
      <div className="war-ring war-ring-3" />
      <div className="war-ring war-ring-4" />

      {/* 16 light rays — longer alternating pattern */}
      {RAY_ANGLES.map((deg, i) => (
        <div
          key={deg}
          className="war-ray"
          style={{
            height: i % 2 === 0 ? 68 : 46,
            opacity: i % 2 === 0 ? 0.75 : 0.42,
            transform: `rotate(${deg}deg) translateY(-100%)`,
            animation: `warRayFlicker 3.8s ${deg * 8}ms ease-in-out infinite alternate`,
          }}
        />
      ))}

      {/* Core reactor sphere */}
      <div className="war-core-sphere">
        <div className="war-core-inner">
          <span style={{ letterSpacing: '0.22em', fontSize: 12, fontWeight: 900, color: '#00ff88', opacity: 0.98, textShadow: '0 0 14px #00ff88, 0 0 28px #00ff8877' }}>AI</span>
          <span style={{ letterSpacing: '0.18em', fontSize: 15, fontWeight: 900, color: '#00e5ff', opacity: 1, textShadow: '0 0 18px #00e5ff, 0 0 36px #00e5ff88' }}>CORE</span>
        </div>
      </div>
    </div>
  )
}

/* ── SVG connection layer ───────────────────────────── */
function ConnectionsSVG({ focused }) {
  return (
    <svg
      viewBox={`0 0 ${AW} ${AH}`}
      style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', overflow: 'visible', zIndex: 3, pointerEvents: 'none' }}
    >
      <defs>
        <filter id="war-glow-filter">
          <feGaussianBlur stdDeviation="3.5" result="blur" />
          <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
        <filter id="war-glow-lg">
          <feGaussianBlur stdDeviation="6" result="blur" />
          <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
      </defs>

      {/* Orbit reference rings — more visible */}
      <circle cx={CX} cy={CY} r={ORBIT_R + 8}  stroke="rgba(0,229,255,0.05)" strokeWidth="0.5" fill="none" />
      <circle cx={CX} cy={CY} r={ORBIT_R}       stroke="rgba(0,229,255,0.15)" strokeWidth="1"   fill="none" />
      <circle cx={CX} cy={CY} r={ORBIT_R - 22}  stroke="rgba(0,229,255,0.07)" strokeWidth="0.5" fill="none" strokeDasharray="4 9" />

      {/* Hidden paths for animateMotion — full length so dots reach node center */}
      {AGENT_META.map(meta => (
        <path key={meta.id} id={`wcp-${meta.id}`} d={buildFullPath(meta)} fill="none" stroke="none" />
      ))}

      {/* Connection paths + pulses per agent */}
      {AGENT_META.map((meta, idx) => {
        const isFocused = focused === meta.id
        const isDimmed  = focused !== null && !isFocused
        const baseOpacity = isDimmed ? 0.30 : isFocused ? 1 : 0.68
        const dotDur = isFocused ? '0.95s' : '2.0s'
        const staggerBegin = `-${Math.round(idx * (2000 / AGENT_META.length))}ms`

        return (
          <g key={meta.id} style={{ opacity: baseOpacity, transition: 'opacity 0.4s ease' }}>
            {/* Wide soft glow underneath for focused state */}
            {isFocused && (
              <path
                d={buildPath(meta)}
                stroke={meta.color}
                strokeWidth="8"
                fill="none"
                strokeOpacity="0.15"
                filter="url(#war-glow-lg)"
              />
            )}
            {/* Base static path */}
            <path
              d={buildPath(meta)}
              stroke={meta.color}
              strokeWidth={isFocused ? 2 : 0.9}
              fill="none"
              strokeOpacity={isFocused ? 0.7 : 0.5}
            />
            {/* Animated dash — energy flow */}
            <path
              d={buildPath(meta)}
              stroke={meta.color}
              strokeWidth={isFocused ? 3 : 1.6}
              fill="none"
              strokeDasharray="8 26"
              style={{
                animation: `warDashOut ${isFocused ? '1.2s' : '1.8s'} linear infinite`,
                animationDelay: `${-idx * 257}ms`,
                filter: isFocused ? `drop-shadow(0 0 6px ${meta.color})` : `drop-shadow(0 0 2px ${meta.color}88)`,
              }}
            />
            {/* Traveling glow dot */}
            <circle
              r={isFocused ? 5.5 : 3}
              fill={meta.color}
              opacity={isFocused ? 1 : 0.8}
              filter={isFocused ? 'url(#war-glow-lg)' : 'url(#war-glow-filter)'}
            >
              <animateMotion dur={dotDur} repeatCount="indefinite" begin={staggerBegin}>
                <mpath href={`#wcp-${meta.id}`} />
              </animateMotion>
            </circle>
            {/* Second + third dots for focused — rapid bidirectional pulses */}
            {isFocused && (
              <>
                <circle r="3.5" fill={meta.color} opacity="0.65" filter="url(#war-glow-filter)">
                  <animateMotion dur="1.4s" repeatCount="indefinite" begin="-700ms" keyPoints="1;0" keyTimes="0;1" calcMode="linear">
                    <mpath href={`#wcp-${meta.id}`} />
                  </animateMotion>
                </circle>
                <circle r="2.5" fill={meta.color} opacity="0.45">
                  <animateMotion dur="0.95s" repeatCount="indefinite" begin="-340ms">
                    <mpath href={`#wcp-${meta.id}`} />
                  </animateMotion>
                </circle>
              </>
            )}
            {/* Periodic energy burst — fires every ~4s from core to node */}
            <circle r="11" fill={meta.color} filter="url(#war-glow-lg)">
              <animateMotion
                dur="4.2s"
                repeatCount="indefinite"
                begin={`-${(idx * 0.58).toFixed(2)}s`}
                keyPoints="0;0.85;1;1"
                keyTimes="0;0.22;0.27;1"
                calcMode="linear"
              >
                <mpath href={`#wcp-${meta.id}`} />
              </animateMotion>
              <animate
                attributeName="opacity"
                values="0.92;0.92;0;0;0.92"
                keyTimes="0;0.20;0.27;0.99;1"
                dur="4.2s"
                repeatCount="indefinite"
                begin={`-${(idx * 0.58).toFixed(2)}s`}
              />
            </circle>
          </g>
        )
      })}
    </svg>
  )
}

/* ── Individual agent node ─────────────────────────── */
function AgentNode({ meta, isActive, isHovered, isAnyFocused, onClick, onMouseEnter, onMouseLeave, agentData, isAnalyzed }) {
  const isDimmed  = isAnyFocused && !isActive && !isHovered
  const isLit     = isActive || isHovered
  const coord     = agentCoord(meta)
  const conf      = agentData?.confidence != null ? Math.round(agentData.confidence * 100) : null
  const floatDur  = 2.6 + Math.abs(meta.angle % 7) * 0.28
  const baseSize  = 75
  const litSize   = isActive ? 100 : 88

  // currentSize: what the circle actually renders at
  const cSize = isActive ? litSize : isHovered ? litSize : baseSize
  const half  = cSize / 2

  return (
    /* Zero-size anchor — sits exactly at the SVG coordinate point */
    <motion.div
      animate={{
        scale: isActive ? 1.18 : isHovered ? 1.12 : isDimmed ? 0.94 : [1, 1.038, 1],
        opacity: isDimmed ? 0.65 : 1,
      }}
      transition={{
        scale: isActive || isHovered || isDimmed
          ? { duration: 0.25, ease: [0.34, 1.56, 0.64, 1] }
          : { duration: floatDur, repeat: Infinity, ease: 'easeInOut' },
        opacity: { duration: 0.38 },
      }}
      onClick={() => onClick(meta.id)}
      onMouseEnter={() => onMouseEnter(meta.id)}
      onMouseLeave={onMouseLeave}
      style={{
        position: 'absolute',
        left: `${(coord.x / AW) * 100}%`,
        top:  `${(coord.y / AH) * 100}%`,
        width: 0, height: 0,
        zIndex: 10,
        cursor: 'crosshair',
        userSelect: 'none',
      }}
    >
      {/* Soft halo bloom — centered on anchor */}
      <div style={{
        position: 'absolute',
        width: cSize + 44,
        height: cSize + 44,
        top: -(cSize + 44) / 2,
        left: -(cSize + 44) / 2,
        borderRadius: '50%',
        background: `radial-gradient(circle, ${meta.color}${isLit ? '18' : '08'} 0%, transparent 70%)`,
        pointerEvents: 'none',
        transition: 'all 0.3s ease',
      }} />

      {/* Node circle — centered exactly on anchor */}
      <div style={{
        position: 'absolute',
        width: cSize,
        height: cSize,
        top: -half,
        left: -half,
        borderRadius: '50%',
        background: isLit
          ? `radial-gradient(circle at 35% 30%, ${meta.color}55, ${meta.color}18 50%, rgba(3,7,18,0.88))`
          : `radial-gradient(circle at 38% 32%, ${meta.color}20, rgba(3,7,18,0.92))`,
        border: isLit ? `2px solid ${meta.color}ee` : `1.5px solid ${meta.color}88`,
        boxShadow: isActive
          ? `0 0 30px ${meta.color}88, 0 0 70px ${meta.color}44, 0 0 130px ${meta.color}22, inset 0 0 26px ${meta.color}28`
          : isHovered
          ? `0 0 20px ${meta.color}66, 0 0 48px ${meta.color}28, inset 0 0 18px ${meta.color}14`
          : `0 0 14px ${meta.color}44, 0 0 32px ${meta.color}22, inset 0 0 10px ${meta.color}0a`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: isLit ? (isActive ? 42 : 34) : 30,
        transition: 'all 0.25s ease',
      }}>
        {meta.icon}
      </div>

      {/* Label — hangs below circle */}
      <div style={{
        position: 'absolute',
        top: half + 6,
        left: '50%',
        transform: 'translateX(-50%)',
        textAlign: 'center',
        lineHeight: 1.3,
        whiteSpace: 'nowrap',
        pointerEvents: 'none',
      }}>
        <div style={{
          fontSize: 11,
          fontWeight: 800,
          letterSpacing: '0.13em',
          textTransform: 'uppercase',
          color: isLit ? meta.color : 'rgba(255,255,255,0.72)',
          textShadow: isLit ? `0 0 14px ${meta.color}` : 'none',
          transition: 'all 0.25s ease',
        }}>
          {meta.label}
        </div>
        {isAnalyzed && !isLit && (
          <div style={{
            fontSize: 9, fontWeight: 700, letterSpacing: '0.12em',
            color: '#00ff88', marginTop: 2, textShadow: '0 0 10px #00ff88',
          }}>
            ✓ ANALYZED
          </div>
        )}
        <AnimatePresence>
          {isLit && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              style={{ fontSize: 10, color: meta.color + 'cc', letterSpacing: '0.06em', overflow: 'hidden', textShadow: `0 0 10px ${meta.color}` }}
            >
              {isAnalyzed ? '✓ Analyzed' : (conf != null ? `${conf}% conf` : '—')}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Exploding pulse rings for active state */}
      {isActive && [0, 0.4, 0.8].map((delay) => (
        <motion.div
          key={delay}
          initial={{ scale: 1, opacity: 0.65 }}
          animate={{ scale: 3.2, opacity: 0 }}
          transition={{ duration: 1.6, delay, repeat: Infinity, ease: 'easeOut' }}
          style={{
            position: 'absolute',
            width: litSize, height: litSize,
            top: -litSize / 2, left: -litSize / 2,
            borderRadius: '50%',
            border: `1.5px solid ${meta.color}`,
            pointerEvents: 'none',
          }}
        />
      ))}

      {/* Subtle hover ring */}
      {isHovered && !isActive && (
        <motion.div
          initial={{ scale: 1, opacity: 0.5 }}
          animate={{ scale: 2.6, opacity: 0 }}
          transition={{ duration: 1.2, repeat: Infinity, ease: 'easeOut' }}
          style={{
            position: 'absolute',
            width: litSize, height: litSize,
            top: -litSize / 2, left: -litSize / 2,
            borderRadius: '50%',
            border: `1px solid ${meta.color}88`,
            pointerEvents: 'none',
          }}
        />
      )}
    </motion.div>
  )
}

/* ── Live reasoning feed ────────────────────────────── */
function buildUploadStream(agents) {
  if (!agents?.length) return REASONING_STREAM
  const idMap = {
    'water':    { id: 'water',    color: '#00b4ff' },
    'energy':   { id: 'energy',   color: '#eab308' },
    'waste':    { id: 'waste',    color: '#00ff88' },
    'impact':   { id: 'impact',   color: '#f472b6' },
    'decision': { id: 'decision', color: '#e2e8f0' },
    'score':    { id: 'score',    color: '#a78bfa' },
    'report':   { id: 'report',   color: '#22d3ee' },
  }
  function agentMeta(agentName) {
    const n = (agentName || '').toLowerCase()
    if (n.includes('water'))    return idMap.water
    if (n.includes('energy'))   return idMap.energy
    if (n.includes('waste'))    return idMap.waste
    if (n.includes('impact') || n.includes('pollution')) return idMap.impact
    if (n.includes('decision')) return idMap.decision
    if (n.includes('score') || n.includes('regen'))      return idMap.score
    if (n.includes('report'))   return idMap.report
    return { id: 'report', color: '#22d3ee' }
  }
  const lines = []
  agents.forEach(a => {
    const m = agentMeta(a.agent)
    if (a.status === 'skipped') {
      lines.push({ agent: m.id, color: m.color, msg: `${a.agent}: ⊘ Skipped — ${a.skip_reason || 'No data provided.'}` })
    } else {
      if (a.finding) lines.push({ agent: m.id, color: m.color, msg: `${a.agent}: ${a.finding}` })
      if (a.reasoning && a.reasoning !== a.finding) lines.push({ agent: m.id, color: m.color, msg: a.reasoning })
      if (a.recommendation) lines.push({ agent: m.id, color: m.color, msg: `Recommendation: ${a.recommendation}` })
    }
  })
  /* In upload mode never fall back to hardcoded demo stream */
  return lines.length ? lines : []
}

function LiveReasoningFeed({ filterAgent, isUploadMode, agents }) {
  const stream = useMemo(
    () => isUploadMode ? buildUploadStream(agents) : REASONING_STREAM,
    [isUploadMode, agents]
  )
  const [lines, setLines] = useState(stream.length ? [stream[0]] : [])
  const ref = useRef(null)
  const idx = useRef(1)

  useEffect(() => {
    setLines(stream.length ? [stream[0]] : [])
    idx.current = 1
  }, [isUploadMode, stream])

  useEffect(() => {
    if (!stream.length) return
    const t = setInterval(() => {
      setLines(prev => [...prev.slice(-10), stream[idx.current % stream.length]])
      idx.current++
    }, 2600)
    return () => clearInterval(t)
  }, [stream])

  useEffect(() => {
    if (ref.current) ref.current.scrollTop = ref.current.scrollHeight
  }, [lines])

  const visible = filterAgent ? lines.filter(l => l.agent === filterAgent) : lines

  return (
    <div ref={ref} style={{ flex: 1, overflowY: 'auto', scrollbarWidth: 'none' }}>
      <AnimatePresence initial={false}>
        {visible.map((line, i) => {
          const m = AGENT_META.find(a => a.id === line.agent)
          return (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              style={{ display: 'flex', gap: 9, marginBottom: 10, alignItems: 'flex-start' }}
            >
              <div style={{
                width: 5, height: 5, borderRadius: '50%',
                background: line.color, flexShrink: 0, marginTop: 5,
                boxShadow: `0 0 6px ${line.color}`,
              }} />
              <div>
                <span style={{ fontSize: 11.5, fontWeight: 700, color: line.color }}>{m?.label ?? line.agent}</span>
                <span style={{ fontSize: 11, color: 'rgba(226,232,240,0.62)', marginLeft: 7, lineHeight: 1.75 }}>{line.msg}</span>
              </div>
            </motion.div>
          )
        })}
      </AnimatePresence>
      {visible.length === 0 && (
        <p style={{ fontSize: 11, color: 'rgba(255,255,255,0.2)', textAlign: 'center', paddingTop: 16 }}>
          {stream.length === 0
            ? 'No agent reasoning data returned for this analysis.'
            : 'No activity for this agent yet.'}
        </p>
      )}
    </div>
  )
}

/* ── Pipeline status ────────────────────────────────── */
function PipelinePanel() {
  const phases = [
    { label: 'Rule Engine',  color: '#00b4ff' },
    { label: 'Impact Layer', color: '#a78bfa' },
    { label: 'Report Layer', color: '#00ff88' },
  ]
  return (
    <div style={{
      background: 'rgba(3,7,18,0.75)',
      backdropFilter: 'blur(18px)',
      border: '1px solid rgba(255,255,255,0.05)',
      borderRadius: 16,
      padding: '16px 18px',
    }}>
      <p style={{ fontSize: 9, fontWeight: 700, letterSpacing: '0.18em', color: 'rgba(255,255,255,0.28)', textTransform: 'uppercase', marginBottom: 14 }}>
        Pipeline
      </p>
      {phases.map((ph, i) => (
        <div key={i} style={{ marginBottom: i < phases.length - 1 ? 12 : 0 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <div style={{ width: 5, height: 5, borderRadius: '50%', background: ph.color, boxShadow: `0 0 4px ${ph.color}` }} />
              <span style={{ fontSize: 11, color: ph.color }}>{ph.label}</span>
            </div>
            <span style={{ fontSize: 10, color: '#4ade80', fontWeight: 600 }}>✓ Done</span>
          </div>
          <div style={{ height: 2, background: 'rgba(255,255,255,0.05)', borderRadius: 1, overflow: 'hidden' }}>
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: '100%' }}
              transition={{ duration: 1.2, delay: i * 0.35, ease: 'easeOut' }}
              style={{ height: '100%', background: `linear-gradient(90deg, ${ph.color}55, ${ph.color})`, borderRadius: 1 }}
            />
          </div>
        </div>
      ))}
    </div>
  )
}

/* ── Agent detail panel (right panel content) ──────── */
function AgentDetailPanel({ agentId, agents, wasteResult, isUploadMode }) {
  const meta = AGENT_META.find(m => m.id === agentId)
  if (!meta) return null

  const backendData = agents?.find?.(a =>
    a.agent?.toLowerCase().includes(meta.label.toLowerCase()) ||
    (agentId === 'decision' && a.agent?.toLowerCase().includes('decision'))
  )

  /* In upload mode use only live backend data — never fall back to hardcoded demo text */
  const liveObservation    = backendData?.finding        || null
  const liveReasoning      = backendData?.reasoning      || null
  const liveImpact         = backendData?.impact         || null
  const liveRecommendation = backendData?.recommendation || null
  const liveMetric         = backendData?.metric         || null
  const isSkipped          = backendData?.status === 'skipped'
  const anomalyGated       = isUploadMode && backendData?.anomaly_detection_available === false

  /* Waste agent: merge live wasteResult — in upload mode never fall back to demo text */
  const wasteOverride = agentId === 'waste' && wasteResult ? {
    observation:     wasteResult.finding             || (isUploadMode ? null : meta.observation),
    recommendation:  wasteResult.recommended_pathway || (isUploadMode ? null : meta.recommendation),
    metric: wasteResult.hidden_value_score != null
      ? `Score: ${wasteResult.hidden_value_score}/100`
      : (isUploadMode ? null : meta.metric),
    severity:      wasteResult.hazard_warning ? 'HIGH' : meta.urgency,
    confidence:    wasteResult.confidence ?? meta.confidence,
    hazard_warning: wasteResult.hazard_warning,
    waste_type:    wasteResult.waste_type,
  } : null

  const conf    = wasteOverride?.confidence ?? backendData?.confidence ?? meta.confidence
  const confPct = Math.round((typeof conf === 'number' && conf <= 1 ? conf * 100 : conf))
  const urgencyPct = meta.urgency === 'HIGH' ? 82 : meta.urgency === 'MEDIUM' ? 56 : 28
  const urgencyColor = urgencyPct > 70 ? '#ef4444' : urgencyPct > 45 ? '#eab308' : '#22c55e'

  const now = new Date()
  const timestamp = `${now.toLocaleDateString('en-IN', { day:'2-digit', month:'short' })} · ${now.toLocaleTimeString('en-IN', { hour:'2-digit', minute:'2-digit' })}`

  return (
    <motion.div
      key={agentId}
      initial={{ x: 50, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: 50, opacity: 0 }}
      transition={{ type: 'spring', damping: 26, stiffness: 220 }}
      style={{
        flex: 1, display: 'flex', flexDirection: 'column',
        background: 'rgba(3,7,18,0.84)',
        backdropFilter: 'blur(28px)',
        border: `1px solid ${meta.color}1e`,
        borderTop: `2px solid ${meta.color}`,
        borderRadius: 20, padding: '20px 20px 16px',
        overflowY: 'auto', scrollbarWidth: 'none',
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
        <div style={{
          width: 48, height: 48, borderRadius: 13, flexShrink: 0,
          background: `radial-gradient(circle at 35% 32%, ${meta.color}25, rgba(3,7,18,0.9))`,
          border: `1px solid ${meta.color}44`,
          display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 22,
          boxShadow: `0 0 20px ${meta.color}28`,
        }}>
          {meta.icon}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontWeight: 800, fontSize: 16, color: '#fff', marginBottom: 2 }}>
            {meta.label} Agent
          </div>
          <div style={{ fontSize: 11.5, color: meta.color, opacity: 0.92 }}>
            {wasteOverride?.waste_type ? `Analyzing: ${wasteOverride.waste_type}` : meta.sub}
          </div>
        </div>
        <div style={{ textAlign: 'right', flexShrink: 0 }}>
          <div style={{
            padding: '3px 9px', borderRadius: 20, marginBottom: 4,
            background: meta.color + '18', border: `1px solid ${meta.color}40`,
            fontSize: 8.5, fontWeight: 800, textTransform: 'uppercase',
            letterSpacing: '0.10em', color: meta.color,
          }}>
            {meta.urgency}
          </div>
          <div style={{ fontSize: 8.5, color: 'rgba(255,255,255,0.25)' }}>P{meta.priority}</div>
        </div>
      </div>

      {/* Hazard warning */}
      {wasteOverride?.hazard_warning && (
        <motion.div
          initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }}
          style={{
            marginBottom: 12, padding: '9px 13px', borderRadius: 8,
            background: 'rgba(239,68,68,0.10)', border: '1px solid rgba(239,68,68,0.35)',
            display: 'flex', gap: 8, alignItems: 'flex-start',
          }}
        >
          <span style={{ fontSize: 13, flexShrink: 0 }}>⚠</span>
          <span style={{ fontSize: 10.5, color: '#fca5a5', lineHeight: 1.65 }}>
            <strong>Hazard Warning:</strong> {wasteOverride.hazard_warning}
          </span>
        </motion.div>
      )}

      {/* Key metric */}
      <motion.div
        initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.12 }}
        style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 14 }}
      >
        <span style={{ fontSize: 32, fontWeight: 900, color: meta.color, lineHeight: 1, letterSpacing: '-0.02em' }}>
          {wasteOverride?.metric ?? liveMetric ?? (isUploadMode ? '—' : meta.metric)}
        </span>
        <span style={{ fontSize: 10.5, color: 'rgba(255,255,255,0.35)', lineHeight: 1.4 }}>
          {meta.metricLabel}
        </span>
      </motion.div>

      {/* Skipped badge for upload mode */}
      {isSkipped && (
        <div style={{
          marginBottom: 12, padding: '7px 12px', borderRadius: 8,
          background: 'rgba(71,85,105,0.12)', border: '1px solid rgba(71,85,105,0.25)',
          fontSize: 11, color: '#94a3b8',
        }}>
          ⊘ {backendData?.skip_reason || 'No data provided for this agent — analysis skipped.'}
        </div>
      )}

      {/* Anomaly gating notice */}
      {anomalyGated && (
        <div style={{
          marginBottom: 12, padding: '8px 12px', borderRadius: 8,
          background: 'rgba(245,158,11,0.07)', border: '1px solid rgba(245,158,11,0.22)',
          fontSize: 11, color: '#fbbf24', lineHeight: 1.6,
        }}>
          <strong>Advanced detection unavailable.</strong>{' '}
          {backendData?.anomaly_detection_reason ||
            'Provide hourly operational logs or smart-meter exports to enable leak detection and predictive analytics.'}
        </div>
      )}

      {/* Reasoning blocks — in upload mode never show hardcoded demo text */}
      {[
        {
          label: 'Observation',
          text:  wasteOverride?.observation ?? liveObservation ?? (isUploadMode ? null : meta.observation),
          color: meta.color,
        },
        {
          label: 'Reasoning',
          text:  wasteOverride?.reasoning ?? liveReasoning ?? (isUploadMode ? null : meta.reasoning),
          color: 'rgba(226,232,240,0.6)',
        },
        {
          label: 'Impact',
          text:  wasteOverride?.impact ?? liveImpact ?? (isUploadMode ? null : meta.impact),
          color: '#a78bfa',
        },
        {
          label: 'Recommendation',
          text:  wasteOverride?.recommendation ?? liveRecommendation ?? (isUploadMode ? null : meta.recommendation),
          color: '#4ade80',
        },
      ].filter(({ text }) => text != null).map(({ label, text, color }, i) => (
        <motion.div
          key={label}
          initial={{ opacity: 0, x: -8 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.25 + i * 0.14 }}
          style={{ marginBottom: 11 }}
        >
          <p style={{ fontSize: 9, fontWeight: 700, letterSpacing: '0.13em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.38)', marginBottom: 5 }}>
            {label}
          </p>
          <p style={{ fontSize: 12, color, lineHeight: 1.7 }}>
            {text}
          </p>
        </motion.div>
      ))}

      {/* Confidence + Urgency bars */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 4, marginBottom: 14 }}>
        {[
          { label: 'Confidence', value: confPct, color: meta.color },
          { label: 'Urgency',    value: urgencyPct, color: urgencyColor },
        ].map(({ label, value, color }) => (
          <div key={label}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
              <span style={{ fontSize: 8.5, color: 'rgba(255,255,255,0.32)', textTransform: 'uppercase', letterSpacing: '0.12em' }}>{label}</span>
              <span style={{ fontSize: 11, fontWeight: 700, color }}>{value}%</span>
            </div>
            <div style={{ height: 3, background: 'rgba(255,255,255,0.06)', borderRadius: 2, overflow: 'hidden' }}>
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${value}%` }}
                transition={{ duration: 1.1, ease: 'easeOut', delay: 0.5 }}
                style={{ height: '100%', borderRadius: 2, background: `linear-gradient(90deg, ${color}55, ${color})` }}
              />
            </div>
          </div>
        ))}
      </div>

      {/* Timestamp + AI attribution */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: 10 }}>
        <span style={{ fontSize: 8.5, color: 'rgba(255,255,255,0.22)' }}>Last run: {timestamp}</span>
        <span style={{ fontSize: 8.5, color: '#00e5ff', opacity: 0.6, fontWeight: 600 }}>Powered by AI Core</span>
      </div>
    </motion.div>
  )
}

/* ── Right column ───────────────────────────────────── */
function RightColumn({ focusedAgent, agents, wasteResult, isUploadMode, uploadResult: _uploadResult }) {
  return (
    <div style={{
      height: '100%', display: 'flex', flexDirection: 'column',
      padding: '8px 0 8px 0', gap: 12,
      maxHeight: 'calc(100vh - 140px)',
      overflowY: 'auto',
      scrollbarWidth: 'none',
    }}>
      <AnimatePresence mode="wait">
        {focusedAgent ? (
          <AgentDetailPanel key={focusedAgent} agentId={focusedAgent} agents={agents} wasteResult={wasteResult} isUploadMode={isUploadMode} />
        ) : (
          <motion.div
            key="idle"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 14 }}
          >
            {/* Live reasoning */}
            <div style={{
              flex: 1,
              background: 'rgba(3,7,18,0.78)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(255,255,255,0.06)',
              borderRadius: 20,
              padding: 20,
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                <div className="war-dot-pulse" style={{ width: 6, height: 6, borderRadius: '50%', background: '#00e5ff' }} />
                <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.16em', color: '#00e5ff', textTransform: 'uppercase' }}>
                  Live Reasoning
                </span>
              </div>
              <LiveReasoningFeed filterAgent={null} isUploadMode={isUploadMode} agents={agents} />
            </div>
            <PipelinePanel />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

/* ── Left column ────────────────────────────────────── */
function LeftColumn({ loading, onRefresh, replayPhase, wasteResult, activeAgent, onSelectAgent, agents, isUploadMode }) {
  return (
    <div style={{
      height: '100%', display: 'flex', flexDirection: 'column',
      padding: '8px 0 8px 0', gap: 8,
      overflowY: 'auto', scrollbarWidth: 'none',
    }}>
      {/* Mission title area */}
      <div style={{ flexShrink: 0 }}>
        <h2 style={{ fontSize: 'clamp(24px, 2.8vw, 52px)', fontWeight: 900, lineHeight: 0.95, color: '#fff', marginBottom: 6 }}>
          Agent<br />
          <span className="text-gradient-green">War Room</span>
        </h2>
        <p style={{ fontSize: 11, color: 'rgba(226,232,240,0.48)', lineHeight: 1.55, maxWidth: 220 }}>
          7 autonomous agents — parallel analysis, priority escalation,
          reasoning through {isUploadMode ? 'your uploaded organizational data.' : 'simulated smart-campus resource logs.'}
        </p>
      </div>

      {/* System Status */}
      <div style={{
        background: 'rgba(3,7,18,0.75)',
        backdropFilter: 'blur(18px)',
        border: '1px solid rgba(255,255,255,0.06)',
        borderRadius: 16,
        padding: '12px 14px',
        flexShrink: 0,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
            <div
              className="war-dot-pulse"
              style={{
                width: 5, height: 5, borderRadius: '50%',
                background: replayPhase === 'resetting' ? '#475569' : replayPhase === 'done' ? '#4ade80' : '#00ff88',
                transition: 'background 0.3s ease',
              }}
            />
            <span style={{
              fontSize: 10, fontWeight: 600,
              color: replayPhase === 'resetting' ? '#475569' : replayPhase === 'done' ? '#4ade80' : '#00ff88',
              transition: 'color 0.3s ease',
            }}>
              {replayPhase === 'resetting'  ? 'Resetting System'    :
               replayPhase === 'sequencing' ? 'Running Sequence'    :
               replayPhase === 'done'       ? 'Sequence Complete'   :
               'System Online'}
            </span>
          </div>
          <span style={{ fontSize: 9, color: 'rgba(255,255,255,0.22)' }}>
            {replayPhase ? 'Multi-agent pipeline' : 'All systems operational'}
          </span>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
          {AGENT_META.map((meta, i) => {
            const currentIdx = AGENT_META.findIndex(m => m.id === activeAgent)
            let statusLabel = 'Active'
            let statusColor = meta.color

            // Check if this agent was skipped in an upload run
            const agentEntry = agents?.find?.(a =>
              a.agent?.toLowerCase().includes(meta.label.toLowerCase()) ||
              (meta.id === 'decision' && a.agent?.toLowerCase().includes('decision'))
            )
            const isSkipped = agentEntry?.status === 'skipped'

            if (replayPhase === 'resetting') {
              statusLabel = '— Queued'
              statusColor = '#334155'
            } else if (replayPhase === 'sequencing') {
              if (currentIdx === -1 || i > currentIdx) {
                statusLabel = '— Queued'
                statusColor = '#334155'
              } else if (i === currentIdx) {
                statusLabel = '⟳ Running'
                statusColor = meta.color
              } else {
                statusLabel = '✓ Done'
                statusColor = '#00ff88'
              }
            } else if (replayPhase === 'done') {
              statusLabel = '✓ Completed'
              statusColor = '#00ff88'
            } else if (isSkipped) {
              statusLabel = '⊘ Skipped'
              statusColor = '#475569'
            } else {
              const isWasteAnalyzed = meta.id === 'waste' && !!wasteResult
              const isSelected = meta.id === activeAgent
              if (isSelected) {
                statusLabel = '◉ Active'
                statusColor = meta.color
              } else if (isWasteAnalyzed) {
                statusLabel = '✓ Done'
                statusColor = '#00ff88'
              } else {
                statusLabel = 'Online'
                statusColor = meta.color + '99'
              }
            }

            return (
              <div key={meta.id} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <div style={{
                  width: 4, height: 4, borderRadius: '50%', background: statusColor,
                  boxShadow: `0 0 5px ${statusColor}`, flexShrink: 0,
                  transition: 'background 0.3s ease, box-shadow 0.3s ease',
                }} />
                <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.45)', flex: 1 }}>{meta.label}</span>
                <span style={{ fontSize: 9, color: statusColor, fontWeight: 600, transition: 'color 0.3s ease' }}>
                  {statusLabel}
                </span>
              </div>
            )
          })}
        </div>
      </div>

      {/* Agent selector — directly below System Status, ABOVE Re-run */}
      <div style={{
        background: 'rgba(3,7,18,0.75)',
        backdropFilter: 'blur(18px)',
        border: '1px solid rgba(255,255,255,0.06)',
        borderRadius: 16,
        padding: '10px 12px',
        flexShrink: 0,
      }}>
        <p style={{ fontSize: 9, fontWeight: 700, letterSpacing: '0.18em', color: 'rgba(255,255,255,0.28)', textTransform: 'uppercase', marginBottom: 8 }}>
          Agent Controls
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
          {AGENT_META.map(meta => {
            const isActive = activeAgent === meta.id
            return (
              <button
                key={meta.id}
                onClick={() => onSelectAgent(isActive ? null : meta.id)}
                style={{
                  display: 'flex', alignItems: 'center', gap: 6,
                  padding: '6px 8px',
                  borderRadius: 8,
                  background: isActive ? `${meta.color}14` : 'rgba(255,255,255,0.03)',
                  border: `1px solid ${isActive ? meta.color + '55' : 'rgba(255,255,255,0.07)'}`,
                  color: isActive ? meta.color : 'rgba(255,255,255,0.60)',
                  fontSize: 10.5, fontWeight: isActive ? 700 : 500,
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  textAlign: 'left',
                  boxShadow: isActive ? `0 0 12px ${meta.color}22` : 'none',
                  gridColumn: meta.id === 'decision' ? 'span 2' : undefined,
                }}
                onMouseEnter={e => { if (!isActive) { e.currentTarget.style.background = 'rgba(255,255,255,0.07)'; e.currentTarget.style.color = '#fff' } }}
                onMouseLeave={e => { if (!isActive) { e.currentTarget.style.background = 'rgba(255,255,255,0.03)'; e.currentTarget.style.color = 'rgba(255,255,255,0.60)' } }}
              >
                <div style={{
                  width: 6, height: 6, borderRadius: '50%', flexShrink: 0,
                  background: meta.color,
                  boxShadow: isActive ? `0 0 8px ${meta.color}` : `0 0 4px ${meta.color}88`,
                }} />
                {meta.label}
              </button>
            )
          })}
        </div>
      </div>

      {/* Re-run button */}
      <button
        onClick={onRefresh}
        disabled={loading}
        style={{
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 7,
          padding: '10px 18px',
          borderRadius: 10,
          background: loading ? 'rgba(0,229,255,0.10)' : 'rgba(0,229,255,0.06)',
          border: `1px solid rgba(0,229,255,${loading ? '0.40' : '0.22'})`,
          color: '#00e5ff',
          fontSize: 12, fontWeight: 600,
          cursor: loading ? 'not-allowed' : 'pointer',
          transition: 'all 0.25s ease',
          backdropFilter: 'blur(12px)',
          boxShadow: loading ? '0 0 18px rgba(0,229,255,0.18)' : 'none',
          flexShrink: 0,
        }}
        onMouseEnter={e => { if (!loading) e.currentTarget.style.background = 'rgba(0,229,255,0.12)' }}
        onMouseLeave={e => { if (!loading) e.currentTarget.style.background = 'rgba(0,229,255,0.06)' }}
      >
        <RefreshCw size={13} style={{ animation: loading ? 'missionSpin 1s linear infinite' : 'none' }} />
        {replayPhase === 'resetting'   ? 'Resetting…'   :
         replayPhase === 'sequencing'  ? 'Activating…'  :
         replayPhase === 'done'        ? 'Complete'     :
         'Re-run Agents'}
      </button>

      {/* Hint glass badge */}
      <div style={{
        padding: '6px 10px',
        borderRadius: 10,
        background: 'rgba(0,229,255,0.04)',
        border: '1px solid rgba(0,229,255,0.18)',
        backdropFilter: 'blur(12px)',
        flexShrink: 0,
      }}>
        <p style={{ fontSize: 10, color: 'rgba(0,229,255,0.70)', lineHeight: 1.55, letterSpacing: '0.04em' }}>
          Click an agent node or control above to inspect AI reasoning.
        </p>
      </div>
    </div>
  )
}

/* ── Center stage ───────────────────────────────────── */
function CenterStage({ agents, activeAgent, setActiveAgent, wasteResult }) {
  const [hovered, setHovered] = useState(null)
  const focused = hovered || activeAgent   // hovered takes visual priority

  const handleClick = useCallback((id) => {
    setActiveAgent(prev => prev === id ? null : id)
  }, [setActiveAgent])

  return (
    <div style={{ height: '100%', position: 'relative' }}>
      {/* Positioning anchor: top=43% moves network UP onto the stage circle */}
      <div style={{
        position: 'absolute',
        top: '40%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        width: `min(${AW}px, 60vh)`,
        aspectRatio: '1 / 1',
      }}>
      {/* Scale wrapper for "focus" zoom */}
      <motion.div
        animate={{ scale: activeAgent ? 1.03 : 1 }}
        transition={{ duration: 0.8, ease: 'easeOut' }}
        style={{
          position: 'relative',
          width: '100%',
          height: '100%',
        }}
      >
        {/* Scanning sweep line — always animating */}
        <div style={{
          position: 'absolute', left: 0, right: 0, top: 0, height: 2, zIndex: 4, pointerEvents: 'none',
          background: 'linear-gradient(90deg, transparent, rgba(0,229,255,0.55), rgba(0,255,136,0.35), transparent)',
          animation: 'warScan 6s ease-in-out infinite',
          boxShadow: '0 0 20px rgba(0,229,255,0.4), 0 2px 40px rgba(0,229,255,0.15)',
        }} />

        {/* SVG connections */}
        <ConnectionsSVG focused={focused} />

        {/* AI Core rings + sphere */}
        <AICore />

        {/* Agent nodes */}
        {AGENT_META.map(meta => (
          <AgentNode
            key={meta.id}
            meta={meta}
            isActive={activeAgent === meta.id}
            isHovered={hovered === meta.id}
            isAnyFocused={!!(activeAgent || hovered)}
            onClick={handleClick}
            onMouseEnter={setHovered}
            onMouseLeave={() => setHovered(null)}
            agentData={agents?.find?.(a =>
              a.agent?.toLowerCase().includes(meta.label.toLowerCase()) ||
              (meta.id === 'decision' && a.agent?.toLowerCase().includes('decision'))
            )}
            isAnalyzed={meta.id === 'waste' && !!wasteResult}
          />
        ))}

      </motion.div>
      </div>
    </div>
  )
}

/* ── Main export ────────────────────────────────────── */
export default function AgentWarRoom({ initialData, wasteResult, uploadResult }) {
  const [agents,       setAgents]      = useState(uploadResult?.war_room || initialData)
  const [loading,      setLoading]     = useState(false)
  const [activeAgent,  setActiveAgent] = useState(null)
  const [replayPhase,  setReplayPhase] = useState(null) // null | 'resetting' | 'sequencing' | 'done'

  useEffect(() => {
    if (uploadResult?.war_room) setAgents(uploadResult.war_room)
  }, [uploadResult])

  const delay = (ms) => new Promise(r => setTimeout(r, ms))

  const replayAll = useCallback(async () => {
    if (loading) return
    setLoading(true)
    setActiveAgent(null)
    setReplayPhase('resetting')
    await delay(500)

    setReplayPhase('sequencing')
    for (const meta of AGENT_META) {
      setActiveAgent(meta.id)
      await delay(680)
    }

    setActiveAgent(null)
    setReplayPhase('done')
    await delay(300)
    setReplayPhase(null)

    if (uploadResult?.war_room) {
      setAgents(uploadResult.war_room)
    } else {
      try {
        const res = await getWarRoom()
        setAgents(res.data.war_room)
      } catch { /* war room reload failed silently */ }
    }
    setLoading(false)
  }, [loading, uploadResult])

  const isEmpty = !agents?.length

  const rightFocused = activeAgent

  return (
    <section
      id="warroom"
      style={{
        width: '100%',
        height: 'calc(100vh - 72px)',
        position: 'relative',
        overflow: 'hidden',
        '--warroom-core-size': 'min(520px, 62vh)',
        '--warroom-core-x': '50%',
        '--warroom-core-y': '43%',
      }}
    >
      {/* ── Background: provided war-room image + dark overlay ── */}
      <div style={{
        position: 'absolute', inset: 0, zIndex: 0,
        backgroundImage: 'url(/war-room-bg.jpg)',
        backgroundSize: 'cover',
        backgroundPosition: 'center center',
        backgroundRepeat: 'no-repeat',
      }} />
      {/* Dark overlay for readability */}
      <div style={{
        position: 'absolute', inset: 0, zIndex: 1,
        background: 'rgba(1,4,14,0.40)',
      }} />
      {/* Fine grid overlay */}
      <div style={{
        position: 'absolute', inset: 0, zIndex: 1,
        backgroundImage: [
          'linear-gradient(rgba(0,229,255,0.016) 1px, transparent 1px)',
          'linear-gradient(90deg, rgba(0,229,255,0.016) 1px, transparent 1px)',
        ].join(','),
        backgroundSize: '54px 54px',
        pointerEvents: 'none',
      }} />
      {/* Radial vignette */}
      <div style={{
        position: 'absolute', inset: 0, zIndex: 1, pointerEvents: 'none',
        background: 'radial-gradient(ellipse 80% 80% at 50% 50%, transparent 25%, rgba(0,0,0,0.55) 100%)',
      }} />
      {/* Top + bottom fog */}
      <div style={{
        position: 'absolute', inset: 0, zIndex: 1, pointerEvents: 'none',
        background: 'linear-gradient(0deg, rgba(0,2,8,0.55) 0%, transparent 12%, transparent 88%, rgba(0,2,8,0.50) 100%)',
      }} />
      {/* Central cyan reactor glow */}
      <div style={{
        position: 'absolute', inset: 0, zIndex: 1, pointerEvents: 'none',
        background: 'radial-gradient(ellipse 38% 38% at 50% 50%, rgba(0,229,255,0.045) 0%, transparent 70%)',
      }} />

      {/* Ambient particles */}
      <BackgroundParticles />

      {/* ── Content ── */}
      {isEmpty ? (
        <div style={{
          position: 'relative', zIndex: 10,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          height: '100vh',
        }}>
          <div style={{
            background: 'rgba(3,7,18,0.88)', backdropFilter: 'blur(20px)',
            border: '1px solid rgba(0,229,255,0.1)', borderRadius: 20,
            padding: '44px 64px', textAlign: 'center',
          }}>
            <p style={{ color: 'rgba(226,232,240,0.38)', fontSize: 14 }}>
              Run an analysis to activate the command center.
            </p>
          </div>
        </div>
      ) : (
        <div style={{
          position: 'relative', zIndex: 10,
          maxWidth: 1440, margin: '0 auto',
          display: 'grid',
          gridTemplateColumns: 'clamp(200px, 20vw, 270px) 1fr clamp(260px, 27vw, 380px)',
          gap: 'clamp(12px, 1.6vw, 24px)',
          height: '100%',
          alignItems: 'stretch',
          padding: 'clamp(66px, 9vh, 88px) clamp(16px, 3.5vw, 48px) 16px',
        }}>
          <LeftColumn loading={loading} onRefresh={replayAll} replayPhase={replayPhase} wasteResult={wasteResult} activeAgent={activeAgent} onSelectAgent={setActiveAgent} agents={agents} isUploadMode={!!uploadResult} />
          <CenterStage agents={agents} activeAgent={activeAgent} setActiveAgent={setActiveAgent} wasteResult={wasteResult} />
          <RightColumn focusedAgent={rightFocused} agents={agents} wasteResult={wasteResult} isUploadMode={!!uploadResult} uploadResult={uploadResult} />
        </div>
      )}
    </section>
  )
}
