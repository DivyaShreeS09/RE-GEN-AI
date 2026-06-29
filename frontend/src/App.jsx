import { useState, useEffect } from 'react'
import HeroSection from './components/HeroSection'
import CommandCenterDashboard from './components/CommandCenterDashboard'
import WasteAnalyzer from './components/WasteAnalyzer'
import WaterPanel from './components/WaterPanel'
import EnergyPanel from './components/EnergyPanel'
import AgentWarRoom from './components/AgentWarRoom'
import ActionPlan from './components/ActionPlan'
import CapstoneMappingSection from './components/CapstoneMappingSection'
import ResourceLossHeatmap from './components/ResourceLossHeatmap'
import ImpactProjection from './components/ImpactProjection'
import InterventionSimulator from './components/InterventionSimulator'
import WhyThisMatters from './components/WhyThisMatters'
import DigitalTwinCampus from './components/DigitalTwinCampus'
import SustainabilityAchievements from './components/SustainabilityAchievements'
import { getDashboardSummary, analyzeWater, analyzeEnergy, getWarRoom, generateActionPlan } from './api'
import { CheckCircle, Cpu } from 'lucide-react'

/* ── Mission Control sequence ─────────────────────────────── */
const MISSION_STEPS = [
  { icon: '🛰', text: 'Connecting to Campus Resource Network...' },
  { icon: '♻️', text: 'Waste Agent Online — Knowledge base loaded' },
  { icon: '💧', text: 'Water Agent Online — Night-flow logs indexed' },
  { icon: '⚡', text: 'Energy Agent Online — Anomaly detection active' },
  { icon: '🌿', text: 'Environmental Intelligence — Impact models ready' },
  { icon: '🧠', text: 'Decision Engine — Interventions ranked by priority' },
  { icon: '📊', text: 'RE:GEN Score Calculated — Executive report generated' },
  { icon: '✅', text: 'Campus Intelligence Scan Complete' },
]

function MissionControlOverlay({ step, isComplete }) {
  const pct = Math.round(
    (Math.min(step, MISSION_STEPS.length - 1) / (MISSION_STEPS.length - 1)) * 100
  )

  return (
    <div className="mission-overlay">
      <div className="absolute inset-0 grid-bg opacity-20 pointer-events-none" />
      <div className="scan-sweep absolute left-0 right-0 h-px pointer-events-none"
        style={{ background: 'linear-gradient(90deg, transparent, rgba(0,229,255,0.35), transparent)' }} />

      <div className="relative z-10 max-w-lg w-full px-6 sm:px-10">
        {/* Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 mb-5">
            <Cpu className="w-5 h-5 text-cyan-400" />
            <span className="text-xs text-cyan-400 uppercase tracking-[0.35em] font-bold">Mission Control</span>
          </div>
          <h1 className="text-5xl font-black text-gradient-green mb-2">RE:GEN AI</h1>
          <p className="text-slate-500 text-sm">Autonomous Sustainability Command Center</p>
        </div>

        {/* Progress bar */}
        <div className="mb-8">
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
        <div className="space-y-2.5 mb-8">
          {MISSION_STEPS.map((s, i) => {
            const done    = i < step || isComplete
            const active  = i === step && !isComplete
            const pending = i > step && !isComplete
            return (
              <div key={i} className={`flex items-center gap-3 transition-all duration-500 ${pending ? 'opacity-25' : ''}`}>
                <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs flex-shrink-0 transition-all duration-500 ${
                  done   ? 'bg-green-500/20' :
                  active ? 'bg-cyan-500/20 ring-1 ring-cyan-400/50' :
                           'bg-slate-800'
                }`}>
                  {done   ? <span className="text-green-400">✓</span> :
                   active ? <span className="text-cyan-400 animate-pulse">→</span> :
                            <span className="text-slate-600">○</span>}
                </div>
                <span className={`text-sm transition-all duration-300 ${
                  done   ? 'text-green-400' :
                  active ? 'text-cyan-300 font-semibold mission-step-active' :
                           'text-slate-600'
                }`}>
                  <span className="mr-2">{s.icon}</span>
                  {s.text}
                </span>
              </div>
            )
          })}
        </div>

        {/* Status chip */}
        <div className={`p-4 rounded-xl text-center border transition-all duration-700 ${
          isComplete
            ? 'bg-green-500/8 border-green-500/30'
            : 'bg-cyan-500/5 border-cyan-500/20'
        }`}>
          <div className="flex items-center justify-center gap-2 mb-1">
            <div className={`w-2 h-2 rounded-full ${isComplete ? 'bg-green-400' : 'bg-cyan-400 animate-pulse'}`} />
            <span className={`text-xs uppercase tracking-widest font-bold ${isComplete ? 'text-green-400' : 'text-cyan-400'}`}>
              {isComplete ? 'Scan Complete — Loading Dashboard...' : 'Scanning Campus Systems'}
            </span>
          </div>
          {isComplete && (
            <p className="text-xs text-slate-400 fade-in mt-1">
              7 agents — multi-domain analysis finished
            </p>
          )}
        </div>

        <p className="text-center text-xs text-slate-700 mt-6">
          Simulated smart-campus sensor logs · Decision-support prototype · Not live IoT
        </p>
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

const NAV_LINKS = [
  { href: '#dashboard',    label: 'Dashboard' },
  { href: '#twin',         label: 'Digital Twin' },
  { href: '#waste',        label: 'Waste' },
  { href: '#water',        label: 'Water' },
  { href: '#energy',       label: 'Energy' },
  { href: '#heatmap',      label: 'Heatmap' },
  { href: '#projection',   label: 'Projection' },
  { href: '#simulator',    label: 'Simulate' },
  { href: '#achievements', label: 'Badges' },
  { href: '#warroom',      label: 'War Room' },
  { href: '#action-plan',  label: 'Actions' },
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

  // Mission control
  const [showMission, setShowMission]       = useState(false)
  const [missionStep, setMissionStep]       = useState(0)
  const [missionComplete, setMissionComplete] = useState(false)

  const runScan = async () => {
    setLoading(true)
    setError(null)
    setShowMission(true)
    setMissionStep(0)
    setMissionComplete(false)

    // Advance steps while API runs in parallel
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

      // Show "complete" state briefly, then transition
      setTimeout(() => {
        setShowMission(false)
        setScanDone(true)
        setToast('7 agents completed sustainability scan.')
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

  const Divider = () => (
    <div style={{ borderTop: '1px solid rgba(0,229,255,0.06)' }} />
  )

  return (
    <div className="min-h-screen" style={{ background: '#030712' }}>
      {/* Mission Control full-screen overlay */}
      {showMission && (
        <MissionControlOverlay step={missionStep} isComplete={missionComplete} />
      )}

      {/* Fixed nav */}
      <nav className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 py-3"
        style={{
          background: 'rgba(3,7,18,0.92)',
          backdropFilter: 'blur(14px)',
          borderBottom: '1px solid rgba(0,229,255,0.07)',
        }}>
        <div className="flex items-center gap-3">
          <span className="text-lg font-black text-gradient-green">RE:GEN AI</span>
          <span className="text-xs text-slate-600 hidden sm:block">Sustainability Command Center</span>
        </div>
        <div className="flex items-center gap-1 overflow-x-auto">
          {scanDone && NAV_LINKS.map(l => (
            <a key={l.href} href={l.href}
              className="px-3 py-1 text-xs text-slate-400 hover:text-cyan-400 transition-colors rounded whitespace-nowrap hidden md:block">
              {l.label}
            </a>
          ))}
          <div className="ml-3 flex items-center gap-2 px-3 py-1 rounded-full flex-shrink-0"
            style={{ background: 'rgba(0,255,136,0.07)', border: '1px solid rgba(0,255,136,0.18)' }}>
            <div className="w-1.5 h-1.5 rounded-full bg-green-400 pulse-ring" />
            <span style={{ color: '#00ff88' }} className="text-xs font-medium">v1.0.0</span>
          </div>
        </div>
      </nav>

      <div className="pt-14">
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
          <Divider />
          <CommandCenterDashboard data={dashData} planData={actionPlanData} />

          <Divider />
          <DigitalTwinCampus />

          <Divider />
          <WasteAnalyzer />

          <Divider />
          <WaterPanel data={waterData} />

          <Divider />
          <EnergyPanel data={energyData} />

          <Divider />
          <ResourceLossHeatmap />

          <Divider />
          <ImpactProjection waterData={waterData} energyData={energyData} dashData={dashData} />

          <Divider />
          <InterventionSimulator waterData={waterData} energyData={energyData} dashData={dashData} />

          <Divider />
          <SustainabilityAchievements dashData={dashData} waterData={waterData} energyData={energyData} />

          <Divider />
          <AgentWarRoom initialData={warRoomData} />

          <Divider />
          <ActionPlan data={actionPlanData} />

          <Divider />
          <WhyThisMatters />

          <Divider />
          <CapstoneMappingSection />
        </div>
      )}

      <footer className="mt-16 py-8 text-center" style={{ borderTop: '1px solid rgba(255,255,255,0.04)' }}>
        <p className="text-xs" style={{ color: '#334155' }}>
          RE:GEN AI — Google Kaggle AI Agents Capstone Project
          <br />
          All data is simulated for demonstration. Not professional regulatory, financial, or engineering advice.
        </p>
      </footer>

      {toast && <Toast message={toast} onDone={() => setToast(null)} />}
    </div>
  )
}
