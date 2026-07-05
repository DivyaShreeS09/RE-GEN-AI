import { useState, useEffect } from 'react'
import HeroSection from './components/HeroSection'
import CommandCenterDashboard from './components/CommandCenterDashboard'
import WasteAnalyzer from './components/WasteAnalyzer'
import WaterPanel from './components/WaterPanel'
import EnergyPanel from './components/EnergyPanel'
import AgentWarRoom from './components/AgentWarRoom'
import ActionPlan from './components/ActionPlan'
import ResourceLossHeatmap from './components/ResourceLossHeatmap'
import ImpactProjection from './components/ImpactProjection'
import InterventionSimulator from './components/InterventionSimulator'
import WhyThisMatters from './components/WhyThisMatters'
import DigitalTwinCampus from './components/DigitalTwinCampus'
import SustainabilityAchievements from './components/SustainabilityAchievements'
import IndiaGlobalSection from './components/IndiaGlobalSection'
import { getDashboardSummary, analyzeWater, analyzeEnergy, getWarRoom, generateActionPlan } from './api'
import { CheckCircle } from 'lucide-react'

/* ── Mission sequence ─────────────────────────────── */
const MISSION_STEPS = [
  { phase: 'INIT',    text: 'Initializing RE:GEN intelligence layer' },
  { phase: 'AGENTS',  text: 'Connecting 7 specialized agents' },
  { phase: 'TWIN',    text: 'Loading campus digital twin' },
  { phase: 'SCAN',    text: 'Scanning building infrastructure' },
  { phase: 'WATER',   text: 'Detecting hidden water loss' },
  { phase: 'ENERGY',  text: 'Auditing energy anomalies' },
  { phase: 'CARBON',  text: 'Estimating carbon footprint' },
  { phase: 'GEMINI',  text: 'Gemini reasoning over findings' },
  { phase: 'REPORT',  text: 'Generating executive report' },
  { phase: 'DONE',    text: 'Mission complete' },
]

const RING_R    = 108
const RING_CIRC = 2 * Math.PI * RING_R

function MissionControlOverlay({ step, isComplete }) {
  const total     = MISSION_STEPS.length - 1
  const pct       = Math.round((Math.min(step, total) / total) * 100)
  const dashOff   = RING_CIRC * (1 - pct / 100)
  const current   = MISSION_STEPS[Math.min(step, total)]

  return (
    <div className="mission-overlay">
      <div className="aurora-1" style={{ opacity: 0.25 }} />
      <div className="aurora-2" style={{ opacity: 0.15 }} />
      <div className="absolute inset-0 grid-bg pointer-events-none" style={{ opacity: 0.06 }} />
      <div
        className="scan-sweep absolute inset-x-0 h-px pointer-events-none"
        style={{ background: 'linear-gradient(90deg, transparent, rgba(0,229,255,0.4), transparent)' }}
      />

      <div className="relative z-10 flex flex-col items-center px-6 max-w-md w-full">

        {/* Circular progress ring + logo */}
        <div className="relative mb-5" style={{ width: 256, height: 256 }}>
          <svg
            className="absolute inset-0"
            width="256"
            height="256"
            style={{ transform: 'rotate(-90deg)' }}
          >
            <circle
              cx={128} cy={128} r={RING_R}
              fill="none"
              stroke="rgba(255,255,255,0.05)"
              strokeWidth={1.5}
            />
            <circle
              cx={128} cy={128} r={RING_R}
              fill="none"
              stroke="url(#missionGrad)"
              strokeWidth={2.5}
              strokeLinecap="round"
              strokeDasharray={RING_CIRC}
              strokeDashoffset={dashOff}
              style={{
                transition: 'stroke-dashoffset 0.75s cubic-bezier(0.4,0,0.2,1)',
                filter: 'drop-shadow(0 0 8px rgba(0,255,136,0.5))',
              }}
            />
            <defs>
              <linearGradient id="missionGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%"   stopColor="#00ff88" />
                <stop offset="100%" stopColor="#00e5ff" />
              </linearGradient>
            </defs>
          </svg>

          <div className="absolute inset-0 flex items-center justify-center">
            <div className="relative">
              <div className="absolute hero-logo-ring" style={{ inset: -5, borderRadius: 18 }} />
              <img
                src="/src/assets/logo.jpeg"
                alt="RE:GEN AI"
                style={{
                  width: 92, height: 92,
                  borderRadius: 14,
                  objectFit: 'cover',
                  position: 'relative',
                  zIndex: 10,
                  boxShadow: '0 0 28px rgba(0,255,136,0.4)',
                }}
              />
            </div>
          </div>
        </div>

        {/* Percentage */}
        <div className="text-center mb-4">
          <p
            className="font-black text-gradient-green"
            style={{ fontSize: 52, lineHeight: 1 }}
          >
            {pct}%
          </p>
          <p
            className="text-xs uppercase mt-1"
            style={{ color: '#475569', letterSpacing: '0.22em' }}
          >
            Campus Scan
          </p>
        </div>

        {/* Phase chip + current step */}
        <div className="text-center mb-5">
          <div
            className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full mb-2"
            style={
              isComplete
                ? { background: 'rgba(0,255,136,0.08)', border: '1px solid rgba(0,255,136,0.22)' }
                : { background: 'rgba(0,229,255,0.05)', border: '1px solid rgba(0,229,255,0.18)' }
            }
          >
            <div
              className={`w-1.5 h-1.5 rounded-full ${
                isComplete ? 'bg-green-400' : 'bg-cyan-400 animate-pulse'
              }`}
            />
            <span
              className={`text-xs font-bold uppercase ${
                isComplete ? 'text-green-400' : 'text-cyan-400'
              }`}
              style={{ letterSpacing: '0.2em' }}
            >
              {current.phase}
            </span>
          </div>
          <p className="text-sm font-medium" style={{ color: '#cbd5e1' }}>
            {current.text}
            {!isComplete && <span className="terminal-cursor" />}
          </p>
        </div>

        {/* Step list */}
        <div className="w-full space-y-1">
          {MISSION_STEPS.slice(0, -1).map((s, i) => {
            const done   = i < step || isComplete
            const active = i === step && !isComplete
            return (
              <div
                key={i}
                className="flex items-center gap-2.5 px-3 py-1 rounded-lg transition-all duration-500"
                style={{
                  opacity: i > step && !isComplete ? 0.2 : 1,
                  background: active ? 'rgba(0,229,255,0.05)' : 'transparent',
                }}
              >
                <div
                  className="w-3.5 h-3.5 rounded-full flex-shrink-0 flex items-center justify-center"
                  style={{
                    background: done
                      ? 'rgba(0,255,136,0.14)'
                      : active
                      ? 'rgba(0,229,255,0.14)'
                      : 'rgba(30,41,59,1)',
                    boxShadow: active ? '0 0 0 1px rgba(0,229,255,0.35)' : 'none',
                    fontSize: 9,
                    color: done ? '#00ff88' : active ? '#00e5ff' : '#475569',
                  }}
                >
                  {done ? '✓' : active ? '→' : '·'}
                </div>
                <span
                  className="text-xs"
                  style={{
                    color: done ? '#00ff88' : active ? '#7dd3fc' : '#475569',
                    fontWeight: active ? 600 : 400,
                  }}
                >
                  {s.text}
                </span>
              </div>
            )
          })}
        </div>

        {isComplete && (
          <p className="fade-in text-xs font-medium mt-4" style={{ color: '#4ade80' }}>
            Loading dashboard...
          </p>
        )}
      </div>
    </div>
  )
}

/* ── Toast ──────────────────────────────────────────── */
function Toast({ message, onDone }) {
  useEffect(() => {
    const t = setTimeout(onDone, 4000)
    return () => clearTimeout(t)
  }, [onDone])
  return (
    <div className="toast">
      <CheckCircle className="w-4 h-4" />
      {message}
    </div>
  )
}

const NAV_MODULES = [
  { href: '#dashboard',   label: 'Dashboard' },
  { href: '#twin',        label: 'Twin'      },
  { href: '#heatmap',     label: 'Loss Map'  },
  { href: '#warroom',     label: 'War Room'  },
  { href: '#action-plan', label: 'Report'    },
  { href: '#india',       label: 'Global'    },
]

export default function App() {
  const [scanDone, setScanDone]               = useState(false)
  const [loading, setLoading]                 = useState(false)
  const [dashData, setDashData]               = useState(null)
  const [waterData, setWaterData]             = useState(null)
  const [energyData, setEnergyData]           = useState(null)
  const [warRoomData, setWarRoomData]         = useState(null)
  const [actionPlanData, setActionPlanData]   = useState(null)
  const [error, setError]                     = useState(null)
  const [toast, setToast]                     = useState(null)
  const [showMission, setShowMission]         = useState(false)
  const [missionStep, setMissionStep]         = useState(0)
  const [missionComplete, setMissionComplete] = useState(false)
  const [wasteResult, setWasteResult]         = useState(null)
  const [selectedBuilding, setSelectedBuilding] = useState(null)

  const runScan = async () => {
    setLoading(true)
    setError(null)
    setShowMission(true)
    setMissionStep(0)
    setMissionComplete(false)

    const STEP_TIMES = [0, 700, 1300, 1900, 2500, 3100, 3700]
    const stepTimers = STEP_TIMES.map((t, i) =>
      setTimeout(() => setMissionStep(i), t)
    )

    try {
      const [dash, water, energy, warRoom, plan] = await Promise.all([
        getDashboardSummary(),
        analyzeWater(),
        analyzeEnergy(),
        getWarRoom(),
        generateActionPlan({ include_waste: false }),
      ])

      stepTimers.forEach(clearTimeout)
      setMissionStep(MISSION_STEPS.length - 1)
      setMissionComplete(true)

      setDashData(dash.data)
      setWaterData(water.data)
      setEnergyData(energy.data)
      setWarRoomData(warRoom.data.war_room)
      setActionPlanData(plan.data)

      setTimeout(() => {
        setShowMission(false)
        setScanDone(true)
        setToast('Campus scan complete — 7 agents, multi-domain analysis.')
        setTimeout(() => {
          document.getElementById('dashboard')?.scrollIntoView({ behavior: 'smooth' })
        }, 300)
      }, 2000)
    } catch (err) {
      console.error(err)
      stepTimers.forEach(clearTimeout)
      setShowMission(false)
      setError(
        'Unable to reach RE:GEN AI backend. Ensure the FastAPI server is running on port 8000.'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen" style={{ background: '#030712' }}>
      {showMission && (
        <MissionControlOverlay step={missionStep} isComplete={missionComplete} />
      )}

      {/* ── Transparent hero nav (always visible) ── */}
      <nav
        className="fixed top-0 left-0 right-0 z-50 no-print"
        style={{
          background: scanDone ? 'rgba(3,7,18,0.88)' : 'transparent',
          backdropFilter: scanDone ? 'blur(20px)' : 'none',
          WebkitBackdropFilter: scanDone ? 'blur(20px)' : 'none',
          borderBottom: scanDone ? '1px solid rgba(255,255,255,0.05)' : 'none',
          transition: 'background 0.5s ease, backdrop-filter 0.5s ease',
        }}
      >
        <div style={{
          maxWidth: 1440, margin: '0 auto',
          display: 'grid', gridTemplateColumns: '1fr auto 1fr',
          alignItems: 'center',
          padding: '0 28px', height: 64,
          gap: 16,
        }}>

          {/* Logo — left cell */}
          <a href="#" style={{ display: 'flex', alignItems: 'center', gap: 9, textDecoration: 'none' }}>
            <img
              src="/src/assets/logo.jpeg"
              alt="RE:GEN AI"
              style={{ width: 26, height: 26, borderRadius: 5, objectFit: 'cover', boxShadow: '0 0 8px rgba(0,255,136,0.30)' }}
            />
            <span className="text-sm font-black text-gradient-green">RE:GEN AI</span>
          </a>

          {/* Centre nav links — pre-scan: 6 anchors; post-scan: module pills only */}
          <div
            className="hidden md:flex items-center justify-center"
            style={{ gap: scanDone ? 5 : 22, overflow: 'hidden', minWidth: 0 }}
          >
            {!scanDone && [
              { label: 'Mission',      href: '#' },
              { label: 'Digital Twin', href: '#twin' },
              { label: 'War Room',     href: '#warroom' },
              { label: 'Impact',       href: '#india' },
              { label: 'Reports',      href: '#action-plan' },
              { label: 'Global',       href: '#india' },
            ].map(l => (
              <a
                key={l.label}
                href={l.href}
                style={{
                  fontSize: 12.5, fontWeight: 500,
                  color: 'rgba(255,255,255,0.62)',
                  textDecoration: 'none', letterSpacing: '0.01em',
                  position: 'relative', paddingBottom: 2,
                  transition: 'color 0.2s', whiteSpace: 'nowrap',
                }}
                onMouseEnter={e => e.currentTarget.style.color = 'rgba(255,255,255,0.95)'}
                onMouseLeave={e => e.currentTarget.style.color = 'rgba(255,255,255,0.62)'}
              >
                {l.label}
              </a>
            ))}
            {scanDone && NAV_MODULES.map(l => (
              <a key={l.href} href={l.href} className="nav-module" style={{ whiteSpace: 'nowrap' }}>{l.label}</a>
            ))}
          </div>

          {/* Right controls — right cell, justify to end */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, justifyContent: 'flex-end' }}>
            {/* Launch Mission CTA */}
            <button
              onClick={runScan}
              disabled={loading}
              style={{
                display: 'inline-flex', alignItems: 'center', gap: 7,
                padding: '8px 18px',
                background: 'rgba(255,255,255,0.10)',
                border: '1px solid rgba(255,255,255,0.20)',
                borderRadius: 50,
                color: 'rgba(255,255,255,0.88)',
                fontSize: 13, fontWeight: 600,
                cursor: loading ? 'not-allowed' : 'pointer', fontFamily: 'inherit',
                transition: 'background 0.2s, border-color 0.2s, transform 0.15s',
                opacity: loading ? 0.6 : 1,
              }}
              onMouseEnter={e => {
                if (!loading) {
                  e.currentTarget.style.background = 'rgba(255,255,255,0.16)'
                  e.currentTarget.style.borderColor = 'rgba(255,255,255,0.34)'
                  e.currentTarget.style.transform = 'translateY(-1px)'
                }
              }}
              onMouseLeave={e => {
                e.currentTarget.style.background = 'rgba(255,255,255,0.10)'
                e.currentTarget.style.borderColor = 'rgba(255,255,255,0.20)'
                e.currentTarget.style.transform = ''
              }}
            >
              Launch Mission
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                <path d="M2 6h8M7 3l3 3-3 3" stroke="currentColor" strokeWidth="1.6"
                  strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>

            {/* LIVE badge */}
            <div style={{
              display: 'flex', alignItems: 'center', gap: 6,
              padding: '5px 10px', borderRadius: 50,
              background: 'rgba(0,255,136,0.08)',
              border: '1px solid rgba(0,255,136,0.18)',
            }}>
              <div className="w-1.5 h-1.5 rounded-full status-dot-live" style={{ background: '#4ade80' }} />
              <span style={{ color: '#00cc77', fontSize: 11, fontWeight: 700, letterSpacing: '0.06em' }}>LIVE</span>
            </div>
          </div>
        </div>
      </nav>

      {/* ── Hero ── */}
      <HeroSection onScan={runScan} loading={loading} />

      {error && (
        <div
          className="mx-6 my-4 p-4 rounded-lg text-sm text-center"
          style={{
            background: 'rgba(239,68,68,0.08)',
            border: '1px solid rgba(239,68,68,0.25)',
            color: '#ef4444',
          }}
        >
          {error}
        </div>
      )}

      {scanDone && (
        <div className="fade-in">
          <div className="section-divider" />
          <CommandCenterDashboard data={dashData} planData={actionPlanData} />

          <div className="section-divider" />
          <DigitalTwinCampus onBuildingSelect={setSelectedBuilding} />

          <div className="section-divider" />
          <WasteAnalyzer onResult={setWasteResult} />

          <div className="section-divider" />
          <WaterPanel data={waterData} />

          <div className="section-divider" />
          <EnergyPanel data={energyData} />

          <div className="section-divider" />
          <ResourceLossHeatmap />

          <div className="section-divider" />
          <ImpactProjection waterData={waterData} energyData={energyData} dashData={dashData} />

          <div className="section-divider" />
          <InterventionSimulator waterData={waterData} energyData={energyData} dashData={dashData} />

          <div className="section-divider" />
          <SustainabilityAchievements dashData={dashData} waterData={waterData} energyData={energyData} />

          <div className="section-divider" />
          <AgentWarRoom initialData={warRoomData} wasteResult={wasteResult} />

          <div className="section-divider" />
          <ActionPlan data={actionPlanData} selectedBuilding={selectedBuilding} />

          <div className="section-divider" />
          <WhyThisMatters />

          <div className="section-divider" />
          <IndiaGlobalSection />
        </div>
      )}

      <footer
        className="mt-20 py-14 text-center no-print"
        style={{ borderTop: '1px solid rgba(255,255,255,0.04)' }}
      >
        <div className="max-w-lg mx-auto px-6">
          <img
            src="/src/assets/logo.jpeg"
            alt="RE:GEN AI"
            style={{
              width: 40, height: 40,
              borderRadius: 8,
              objectFit: 'cover',
              margin: '0 auto 14px',
              boxShadow: '0 0 16px rgba(0,255,136,0.22)',
            }}
          />
          <p className="font-black text-gradient-green mb-1" style={{ fontSize: 14 }}>
            RE:GEN AI
          </p>
          <p className="text-xs mb-6" style={{ color: '#94a3b8' }}>
            Sustainability Intelligence OS · Google Kaggle AI Agents: Intensive Vibe Coding Capstone Project 2026
          </p>
          <div className="h-px mb-6" style={{ background: 'rgba(255,255,255,0.04)' }} />
          <p
            className="text-xs leading-relaxed max-w-md mx-auto"
            style={{ color: '#64748b' }}
          >
            Data is simulated for demonstration purposes. RE:GEN AI is a decision-support
            prototype — not professional regulatory, financial, or engineering advice.
            Designed for future integration with live campus IoT infrastructure.
          </p>
        </div>
      </footer>

      {toast && <Toast message={toast} onDone={() => setToast(null)} />}
    </div>
  )
}
