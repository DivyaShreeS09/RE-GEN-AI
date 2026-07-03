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
import { CheckCircle, Cpu } from 'lucide-react'

/* ── Mission Control sequence ─────────────────────────────── */
const MISSION_STEPS = [
  { icon: '🛰', text: 'Connecting to Campus Resource Network' },
  { icon: '♻️', text: 'Waste Agent Online — Knowledge base loaded' },
  { icon: '💧', text: 'Water Agent Online — Night-flow logs indexed' },
  { icon: '⚡', text: 'Energy Agent Online — Anomaly detection active' },
  { icon: '🌿', text: 'Environmental Intelligence — Impact models ready' },
  { icon: '🧠', text: 'Decision Engine — Interventions ranked by priority' },
  { icon: '📊', text: 'RE:GEN Score Calculated — Executive report ready' },
  { icon: '✅', text: 'Campus Scan Complete' },
]

function MissionControlOverlay({ step, isComplete }) {
  const pct = Math.round(
    (Math.min(step, MISSION_STEPS.length - 1) / (MISSION_STEPS.length - 1)) * 100
  )

  return (
    <div className="mission-overlay">
      {/* Aurora inside overlay */}
      <div className="aurora-1" style={{ opacity: 0.3 }} />
      <div className="aurora-2" style={{ opacity: 0.2 }} />

      <div className="absolute inset-0 grid-bg opacity-10 pointer-events-none" />
      <div className="scan-sweep absolute left-0 right-0 h-px pointer-events-none"
        style={{ background: 'linear-gradient(90deg, transparent, rgba(0,229,255,0.35), transparent)' }} />

      <div className="relative z-10 max-w-lg w-full px-6 sm:px-10">

        {/* Logo + header */}
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <div className="relative">
              <div className="absolute -inset-3 rounded-2xl hero-logo-ring" />
              <img src="/src/assets/logo.jpeg" alt="RE:GEN AI"
                style={{ width: 72, height: 72, borderRadius: 12, objectFit: 'cover', position: 'relative', zIndex: 10,
                  boxShadow: '0 0 20px rgba(0,255,136,0.3)' }} />
            </div>
          </div>
          <div className="inline-flex items-center gap-2 mb-3">
            <Cpu className="w-4 h-4 text-cyan-400" />
            <span className="text-xs text-cyan-400 uppercase tracking-[0.3em] font-bold">Mission Control</span>
          </div>
          <h1 className="text-4xl font-black text-gradient-green">RE:GEN AI</h1>
          <p className="text-slate-500 text-xs mt-1">Sustainability Intelligence OS · Campus Scan Initializing</p>
        </div>

        {/* Progress bar */}
        <div className="mb-7">
          <div className="flex justify-between items-center mb-2">
            <span className="text-xs text-slate-500 uppercase tracking-wider">Scan Progress</span>
            <span className="text-xs font-bold" style={{ color: isComplete ? '#00ff88' : '#00e5ff' }}>
              {pct}%
            </span>
          </div>
          <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
            <div className="h-full rounded-full transition-all duration-700 ease-out" style={{
              width: `${pct}%`,
              background: isComplete
                ? 'linear-gradient(90deg, #00ff88, #00e5ff)'
                : 'linear-gradient(90deg, #00e5ff, #3b82f6)',
              boxShadow: isComplete
                ? '0 0 14px rgba(0,255,136,0.55)'
                : '0 0 12px rgba(0,229,255,0.4)',
            }} />
          </div>
        </div>

        {/* Step list */}
        <div className="space-y-2 mb-7">
          {MISSION_STEPS.map((s, i) => {
            const done    = i < step || isComplete
            const active  = i === step && !isComplete
            const pending = i > step && !isComplete
            return (
              <div key={i} className={`flex items-center gap-3 transition-all duration-500 ${pending ? 'opacity-20' : ''}`}>
                <div className={`w-5 h-5 rounded-full flex items-center justify-center text-xs flex-shrink-0 transition-all duration-500 ${
                  done   ? 'bg-green-500/20' :
                  active ? 'bg-cyan-500/20 ring-1 ring-cyan-400/50' :
                           'bg-slate-800'
                }`}>
                  {done   ? <span className="text-green-400 text-xs">✓</span> :
                   active ? <span className="text-cyan-400 animate-pulse">→</span> :
                            <span className="text-slate-600 text-xs">○</span>}
                </div>
                <span className={`text-sm transition-all duration-300 ${
                  done   ? 'text-green-400' :
                  active ? 'text-cyan-300 font-semibold mission-step-active' :
                           'text-slate-700'
                }`}>
                  <span className="mr-2">{s.icon}</span>{s.text}
                </span>
              </div>
            )
          })}
        </div>

        {/* Status chip */}
        <div className={`p-4 rounded-xl text-center border transition-all duration-700 ${
          isComplete
            ? 'bg-green-500/8 border-green-500/30'
            : 'bg-cyan-500/5 border-cyan-500/18'
        }`}>
          <div className="flex items-center justify-center gap-2">
            <div className={`w-2 h-2 rounded-full ${isComplete ? 'bg-green-400' : 'bg-cyan-400 animate-pulse'}`} />
            <span className={`text-xs uppercase tracking-widest font-bold ${isComplete ? 'text-green-400' : 'text-cyan-400'}`}>
              {isComplete ? 'Scan Complete — Loading Dashboard...' : 'Scanning Campus Systems'}
            </span>
          </div>
          {isComplete && (
            <p className="text-xs text-slate-400 fade-in mt-1">
              7 agents — multi-domain analysis complete
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

/* ── Toast ──────────────────────────────────────────────────── */
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
  { href: '#dashboard',   label: 'Dashboard'     },
  { href: '#twin',        label: 'Digital Twin'  },
  { href: '#waste',       label: 'Waste Intel'   },
  { href: '#water',       label: 'Water'         },
  { href: '#energy',      label: 'Energy'        },
  { href: '#heatmap',     label: 'Loss Map'      },
  { href: '#warroom',     label: 'War Room'      },
  { href: '#action-plan', label: 'Action Plan'   },
  { href: '#india',       label: 'India / Global'},
]

export default function App() {
  const [scanDone, setScanDone]             = useState(false)
  const [loading, setLoading]               = useState(false)
  const [dashData, setDashData]             = useState(null)
  const [waterData, setWaterData]           = useState(null)
  const [energyData, setEnergyData]         = useState(null)
  const [warRoomData, setWarRoomData]       = useState(null)
  const [actionPlanData, setActionPlanData] = useState(null)
  const [error, setError]                   = useState(null)
  const [toast, setToast]                   = useState(null)

  const [showMission, setShowMission]         = useState(false)
  const [missionStep, setMissionStep]         = useState(0)
  const [missionComplete, setMissionComplete] = useState(false)

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
        setToast('7 agents completed campus sustainability scan.')
        setTimeout(() => {
          document.getElementById('dashboard')?.scrollIntoView({ behavior: 'smooth' })
        }, 300)
      }, 2000)
    } catch (err) {
      console.error(err)
      stepTimers.forEach(clearTimeout)
      setShowMission(false)
      setError('Unable to reach RE:GEN AI backend. Ensure the FastAPI server is running on port 8000.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen" style={{ background: '#030712' }}>

      {showMission && (
        <MissionControlOverlay step={missionStep} isComplete={missionComplete} />
      )}

      {/* Fixed nav */}
      <nav className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-5 py-2.5 no-print"
        style={{
          background: 'rgba(3,7,18,0.93)',
          backdropFilter: 'blur(16px)',
          borderBottom: '1px solid rgba(0,229,255,0.07)',
        }}>

        {/* Logo + brand */}
        <a href="#" className="flex items-center gap-2.5 flex-shrink-0">
          <img src="/src/assets/logo.jpeg" alt="RE:GEN AI"
            style={{ width: 28, height: 28, borderRadius: 6, objectFit: 'cover',
              boxShadow: '0 0 10px rgba(0,255,136,0.3)' }} />
          <span className="text-sm font-black text-gradient-green">RE:GEN AI</span>
          <span className="text-xs text-slate-600 hidden sm:block font-medium">Sustainability OS</span>
        </a>

        {/* Module nav */}
        <div className="flex items-center gap-0.5 overflow-x-auto">
          {scanDone && NAV_MODULES.map(l => (
            <a key={l.href} href={l.href} className="nav-module hidden md:inline-flex">
              {l.label}
            </a>
          ))}
          <div className="ml-2 flex items-center gap-1.5 px-3 py-1 rounded-full flex-shrink-0"
            style={{ background: 'rgba(0,255,136,0.07)', border: '1px solid rgba(0,255,136,0.18)' }}>
            <div className="w-1.5 h-1.5 rounded-full bg-green-400 status-dot-live" />
            <span style={{ color: '#00ff88' }} className="text-xs font-bold">v1.0</span>
          </div>
        </div>
      </nav>

      <div className="pt-12">
        <HeroSection onScan={runScan} loading={loading} />
      </div>

      {error && (
        <div className="mx-6 my-4 p-4 rounded-lg text-sm text-center" style={{
          background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.25)', color: '#ef4444',
        }}>
          {error}
        </div>
      )}

      {scanDone && (
        <div className="fade-in">

          <div className="section-divider" />
          <CommandCenterDashboard data={dashData} planData={actionPlanData} />

          <div className="section-divider" />
          <DigitalTwinCampus />

          <div className="section-divider" />
          <WasteAnalyzer />

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
          <AgentWarRoom initialData={warRoomData} />

          <div className="section-divider" />
          <ActionPlan data={actionPlanData} />

          <div className="section-divider" />
          <WhyThisMatters />

          <div className="section-divider" />
          <IndiaGlobalSection />

        </div>
      )}

      <footer className="mt-16 py-10 text-center no-print" style={{ borderTop: '1px solid rgba(255,255,255,0.04)' }}>
        <div className="max-w-2xl mx-auto px-6">
          <img src="/src/assets/logo.jpeg" alt="RE:GEN AI"
            style={{ width: 36, height: 36, borderRadius: 8, objectFit: 'cover', margin: '0 auto 12px',
              boxShadow: '0 0 12px rgba(0,255,136,0.2)' }} />
          <p className="text-sm font-black text-gradient-green mb-1">RE:GEN AI</p>
          <p className="text-xs text-slate-600 mb-4">Sustainability Intelligence OS · Google Kaggle AI Agents Capstone 2025</p>
          <div className="h-px bg-slate-800 mb-4" />
          <p className="text-xs text-slate-700 leading-relaxed">
            All data used is simulated for capstone demonstration purposes.
            RE:GEN AI is a decision-support prototype and not professional regulatory, financial, or engineering advice.
            Architecture is designed for future integration with live IoT data sources.
            No ML training was used — all analysis is rule-based with Gemini AI reasoning augmentation.
          </p>
        </div>
      </footer>

      {toast && <Toast message={toast} onDone={() => setToast(null)} />}
    </div>
  )
}
