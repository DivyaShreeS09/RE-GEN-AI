import { useState, useEffect, useCallback, useRef } from 'react'
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
import AnalysisModeSelector from './components/AnalysisModeSelector'
import UploadCenter from './components/UploadCenter'
import MissionSummary from './components/MissionSummary'
import { getDashboardSummary, analyzeWater, analyzeEnergy, getWarRoom, generateActionPlan, analyzeUpload } from './api'
import { CheckCircle } from 'lucide-react'

/* ── Mission sequence ─────────────────────────────── */
const MISSION_STEPS = [
  { phase: 'INIT',    text: 'Initializing RE:GEN intelligence layer' },
  { phase: 'AGENTS',  text: 'Connecting 7 specialized agents' },
  { phase: 'TWIN',    text: 'Loading digital twin visualization' },
  { phase: 'SCAN',    text: 'Scanning resource infrastructure' },
  { phase: 'WATER',   text: 'Detecting hidden water loss' },
  { phase: 'ENERGY',  text: 'Auditing energy anomalies' },
  { phase: 'CARBON',  text: 'Computing carbon footprint' },
  { phase: 'AI',      text: 'AI reasoning over findings' },
  { phase: 'REPORT',  text: 'Generating executive report' },
  { phase: 'DONE',    text: 'Mission complete' },
]

const RING_R    = 108
const RING_CIRC = 2 * Math.PI * RING_R

function MissionControlOverlay({ step, isComplete, label }) {
  const total   = MISSION_STEPS.length - 1
  const pct     = Math.round((Math.min(step, total) / total) * 100)
  const dashOff = RING_CIRC * (1 - pct / 100)
  const current = MISSION_STEPS[Math.min(step, total)]

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
          <svg className="absolute inset-0" width="256" height="256" style={{ transform: 'rotate(-90deg)' }}>
            <circle cx={128} cy={128} r={RING_R} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth={1.5} />
            <circle
              cx={128} cy={128} r={RING_R}
              fill="none" stroke="url(#missionGrad)" strokeWidth={2.5} strokeLinecap="round"
              strokeDasharray={RING_CIRC} strokeDashoffset={dashOff}
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
                src="/logo.jpeg" alt="RE:GEN AI"
                style={{
                  width: 92, height: 92, borderRadius: 14, objectFit: 'cover',
                  position: 'relative', zIndex: 10, boxShadow: '0 0 28px rgba(0,255,136,0.4)',
                }}
              />
            </div>
          </div>
        </div>

        {/* Percentage */}
        <div className="text-center mb-4">
          <p className="font-black text-gradient-green" style={{ fontSize: 52, lineHeight: 1 }}>
            {pct}%
          </p>
          <p className="text-xs uppercase mt-1" style={{ color: '#475569', letterSpacing: '0.22em' }}>
            {label || 'Analysis'}
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
            <div className={`w-1.5 h-1.5 rounded-full ${isComplete ? 'bg-green-400' : 'bg-cyan-400 animate-pulse'}`} />
            <span
              className={`text-xs font-bold uppercase ${isComplete ? 'text-green-400' : 'text-cyan-400'}`}
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
                    background: done ? 'rgba(0,255,136,0.14)' : active ? 'rgba(0,229,255,0.14)' : 'rgba(30,41,59,1)',
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

/* ── Toast ─────────────────────────────────────────── */
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
  /* ── Data state ─────────────────────────────────── */
  const [scanDone, setScanDone]               = useState(false)
  const [loading, setLoading]                 = useState(false)
  const [dashData, setDashData]               = useState(null)
  const [waterData, setWaterData]             = useState(null)
  const [energyData, setEnergyData]           = useState(null)
  const [warRoomData, setWarRoomData]         = useState(null)
  const [actionPlanData, setActionPlanData]   = useState(null)
  const [error, setError]                     = useState(null)
  const [toast, setToast]                     = useState(null)
  const [wasteResult, setWasteResult]         = useState(null)
  const [selectedBuilding, setSelectedBuilding] = useState(null)

  /* ── Mission overlay ────────────────────────────── */
  const [showMission, setShowMission]         = useState(false)
  const [missionStep, setMissionStep]         = useState(0)
  const [missionComplete, setMissionComplete] = useState(false)
  const [missionLabel, setMissionLabel]       = useState('Campus Scan')
  const [processingTimeSec, setProcessingTimeSec] = useState(null)
  const analysisStartRef = useRef(null)

  /* ── Mode flow ──────────────────────────────────── */
  const [showModeSelector, setShowModeSelector] = useState(false)
  const [showUploadCenter, setShowUploadCenter] = useState(false)
  const [showMissionSummary, setShowMissionSummary] = useState(false)
  const [uploadState, setUploadState]           = useState(null)
  const [launching, setLaunching]               = useState(false)

  /* ── Upload result (for Dashboard in upload mode) ─ */
  const [uploadResult, setUploadResult]         = useState(null)

  /* ── Keyboard: close mode selector on Escape ────── */
  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Escape') setShowModeSelector(false)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  /* ── Demo scan (existing pipeline, unchanged) ───── */
  const runScan = useCallback(async () => {
    setShowModeSelector(false)
    setLoading(true)
    setError(null)
    setShowMission(true)
    setMissionStep(0)
    setMissionComplete(false)
    setMissionLabel('Demo Analysis')
    analysisStartRef.current = Date.now()

    const STEP_TIMES = [0, 700, 1300, 1900, 2500, 3100, 3700, 5500]
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
      setUploadResult(null)
      setProcessingTimeSec(((Date.now() - (analysisStartRef.current || Date.now())) / 1000).toFixed(1))

      setTimeout(() => {
        setShowMission(false)
        setScanDone(true)
        setToast('Demo analysis complete — 7 agents, multi-domain analysis.')
        setTimeout(() => {
          document.getElementById('dashboard')?.scrollIntoView({ behavior: 'smooth' })
        }, 300)
      }, 2000)
    } catch {
      stepTimers.forEach(clearTimeout)
      setShowMission(false)
      setError(
        'Unable to reach the RE:GEN AI backend. The server may be warming up — please wait 30–60 seconds and try again.'
      )
    } finally {
      setLoading(false)
    }
  }, [])

  /* ── Upload scan (new pipeline) ─────────────────── */
  const runUploadScan = useCallback(async () => {
    if (!uploadState) return
    setLaunching(true)
    setShowMissionSummary(false)
    setShowMission(true)
    setMissionStep(0)
    setMissionComplete(false)
    setMissionLabel('Organization Analysis')
    setError(null)
    analysisStartRef.current = Date.now()

    const STEP_TIMES = [0, 800, 1500, 2100, 2700, 3300, 3900, 9000, 20000]
    const stepTimers = STEP_TIMES.map((t, i) =>
      setTimeout(() => setMissionStep(i), t)
    )

    try {
      const fd = new FormData()
      if (uploadState.orgName) fd.append('org_name', uploadState.orgName)
      if (uploadState.orgType) fd.append('org_type', uploadState.orgType)

      const w = uploadState.water
      if (w?.fileRaw)  fd.append('water_file', w.fileRaw)
      else if (parseFloat(w?.manual) > 0) {
        fd.append('manual_water_liters', w.manual)
        fd.append('manual_water_period', w.period || 'weekly')
      }

      const en = uploadState.energy
      if (en?.fileRaw) fd.append('energy_file', en.fileRaw)
      else if (parseFloat(en?.manual) > 0) {
        fd.append('manual_energy_kwh', en.manual)
        fd.append('manual_energy_period', en.period || 'weekly')
      }

      const f = uploadState.fuel
      if (f?.fileRaw)  fd.append('fuel_file', f.fileRaw)
      else if (f?.fuelType && parseFloat(f?.manual) > 0) {
        fd.append('manual_fuel_type',   f.fuelType)
        fd.append('manual_fuel_liters', f.manual)
      }

      const ws = uploadState.waste
      if (ws?.items?.length > 0) {
        const wasteItems = ws.items
          .filter(r => r.type && parseFloat(r.qty) > 0)
          .map(r => ({ type: r.type, quantity_kg: parseFloat(r.qty), unit: r.unit || 'kg' }))
        if (wasteItems.length > 0) {
          fd.append('waste_items', JSON.stringify(wasteItems))
        }
      }

      const res = await analyzeUpload(fd)
      const result = res.data

      stepTimers.forEach(clearTimeout)
      setMissionStep(MISSION_STEPS.length - 1)
      setMissionComplete(true)
      setUploadResult(result)
      setProcessingTimeSec(((Date.now() - (analysisStartRef.current || Date.now())) / 1000).toFixed(1))

      // Map upload result fields to existing component props
      setWaterData(result.water)
      setEnergyData(result.energy)
      setWarRoomData(result.war_room)
      setActionPlanData(result.report)
      setDashData({
        regen_score:    result.regen_score,
        silent_losses:  result.report?.silent_losses || {},
        water_summary: {
          total_wasted_liters:     result.water?.total_wasted_liters || 0,
          total_consumption_liters: result.water?.total_consumption_liters || 0,
          severity:                result.water?.severity || 'none',
          estimated_cost_inr:      result.water?.estimated_cost_inr || 0,
          anomaly_events:          result.water?.anomaly_events?.length || 0,
          anomaly_detection_available: result.water?.anomaly_detection_available,
          analysis_level:          result.water?.analysis_level,
        },
        energy_summary: {
          total_wasted_kwh:        result.energy?.total_wasted_kwh || 0,
          total_consumption_kwh:   result.energy?.total_consumption_kwh || 0,
          severity:                result.energy?.severity || 'none',
          estimated_cost_inr:      result.energy?.estimated_cost_inr || 0,
          anomaly_events:          result.energy?.anomaly_events?.length || 0,
          anomaly_detection_available: result.energy?.anomaly_detection_available,
          analysis_level:          result.energy?.analysis_level,
        },
        impact_summary: {
          total_co2_saved_kg:    result.impact?.total_co2_saved_kg || 0,
          trees_equivalent:      result.impact?.trees_equivalent || 0,
          sustainability_score:  result.impact?.sustainability_score || 0,
          sustainability_rating: result.impact?.sustainability_rating || '',
        },
        top_actions:  result.decision?.ranked_actions?.slice(0, 3) || [],
        fuel_co2_kg:  result.fuel_co2_kg || 0,
        fuel_summary: result.fuel_summary || null,
        waste_result: result.waste || null,
        disclaimer:   result.disclaimer || '',
        data_notice:  result.report?.data_notice || '',
      })

      setTimeout(() => {
        setShowMission(false)
        setShowUploadCenter(false)
        setScanDone(true)
        setToast(`Analysis complete — ${uploadState.orgName || 'Organization'} data processed.`)
        setTimeout(() => {
          document.getElementById('dashboard')?.scrollIntoView({ behavior: 'smooth' })
        }, 300)
      }, 2000)
    } catch (err) {
      stepTimers.forEach(clearTimeout)
      setShowMission(false)
      const isTimeout = err?.code === 'ECONNABORTED' || err?.message?.includes('timeout')
      setError(
        isTimeout
          ? 'The analysis is taking longer than expected. The backend server may be starting up (this can take 60–90 seconds on first use). Please wait and try again.'
          : 'Analysis failed. Please check your files and try again. If the server is warming up, wait 30–60 seconds and retry.'
      )
    } finally {
      setLaunching(false)
    }
  }, [uploadState])

  /* ── Open mode selector when hero button clicked ── */
  const handleStartAnalysis = useCallback(() => {
    setShowModeSelector(true)
  }, [])

  /* ── Nav button — opens mode selector in any state ── */
  const handleNavLaunch = useCallback(() => {
    setShowModeSelector(true)
  }, [])

  /* ── Mode selector handlers ─────────────────────── */
  const handlePickDemo   = useCallback(() => runScan(), [runScan])
  const handlePickUpload = useCallback(() => {
    setShowModeSelector(false)
    setShowUploadCenter(true)
  }, [])

  /* ── UploadCenter → MissionSummary ──────────────── */
  const handleUploadProceed = useCallback((state) => {
    setUploadState(state)
    setShowUploadCenter(false)
    setShowMissionSummary(true)
  }, [])

  const handleSummaryBack = useCallback(() => {
    setShowMissionSummary(false)
    setShowUploadCenter(true)
  }, [])

  /* ── Render ─────────────────────────────────────── */
  const inUploadFlow = showUploadCenter || showMissionSummary

  return (
    <div className="min-h-screen" style={{ background: '#030712' }}>

      {/* Mission overlay */}
      {showMission && (
        <MissionControlOverlay step={missionStep} isComplete={missionComplete} label={missionLabel} />
      )}

      {/* Mode selector modal */}
      <AnalysisModeSelector
        open={showModeSelector}
        onDemo={handlePickDemo}
        onUpload={handlePickUpload}
        onClose={() => setShowModeSelector(false)}
      />

      {/* Upload Center (full-page, replaces hero area) */}
      {showUploadCenter && (
        <div style={{ paddingTop: 64 }}>
          <UploadCenter
            onProceed={handleUploadProceed}
            onBack={() => { setShowUploadCenter(false) }}
          />
        </div>
      )}

      {/* Mission Summary (full-page) */}
      {showMissionSummary && (
        <MissionSummary
          uploadState={uploadState}
          onLaunch={runUploadScan}
          onBack={handleSummaryBack}
          launching={launching}
        />
      )}

      {/* ── Transparent hero nav (always visible) ── */}
      <nav
        className="fixed top-0 left-0 right-0 z-50 no-print"
        style={{
          background: (scanDone || inUploadFlow) ? 'rgba(3,7,18,0.88)' : 'transparent',
          backdropFilter: (scanDone || inUploadFlow) ? 'blur(20px)' : 'none',
          WebkitBackdropFilter: (scanDone || inUploadFlow) ? 'blur(20px)' : 'none',
          borderBottom: (scanDone || inUploadFlow) ? '1px solid rgba(255,255,255,0.05)' : 'none',
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

          {/* Logo */}
          <a href="#" style={{ display: 'flex', alignItems: 'center', gap: 9, textDecoration: 'none' }}>
            <img
              src="/logo.jpeg" alt="RE:GEN AI"
              style={{ width: 26, height: 26, borderRadius: 5, objectFit: 'cover', boxShadow: '0 0 8px rgba(0,255,136,0.30)' }}
            />
            <span className="text-sm font-black text-gradient-green">RE:GEN AI</span>
          </a>

          {/* Centre nav */}
          <div
            className="hidden md:flex items-center justify-center"
            style={{ gap: scanDone ? 5 : 22, overflow: 'hidden', minWidth: 0 }}
          >
            {!scanDone && !inUploadFlow && [
              { label: 'Mission',      href: '#' },
              { label: 'Digital Twin', href: '#twin' },
              { label: 'War Room',     href: '#warroom' },
              { label: 'Impact',       href: '#india' },
              { label: 'Reports',      href: '#action-plan' },
              { label: 'Global',       href: '#india' },
            ].map(l => (
              <a
                key={l.label} href={l.href}
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

          {/* Right controls */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, justifyContent: 'flex-end' }}>
            <button
              onClick={handleNavLaunch}
              disabled={loading || inUploadFlow}
              style={{
                display: 'inline-flex', alignItems: 'center', gap: 7,
                padding: '8px 18px',
                background: 'rgba(255,255,255,0.10)',
                border: '1px solid rgba(255,255,255,0.20)',
                borderRadius: 50,
                color: 'rgba(255,255,255,0.88)',
                fontSize: 13, fontWeight: 600,
                cursor: (loading || inUploadFlow) ? 'not-allowed' : 'pointer', fontFamily: 'inherit',
                transition: 'background 0.2s, border-color 0.2s, transform 0.15s',
                opacity: (loading || inUploadFlow) ? 0.4 : 1,
              }}
              onMouseEnter={e => {
                if (!loading && !inUploadFlow) {
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
              {scanDone ? 'New Analysis' : 'Start Analysis'}
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

      {/* ── Hero (hidden when in upload flow) ── */}
      {!inUploadFlow && (
        <HeroSection
          onScan={handleStartAnalysis}
          loading={loading}
          scanDone={scanDone}
          uploadResult={uploadResult}
          dashData={dashData}
          processingTimeSec={processingTimeSec}
        />
      )}

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
          <CommandCenterDashboard data={dashData} planData={actionPlanData} uploadResult={uploadResult} />

          <div className="section-divider" />
          <DigitalTwinCampus onBuildingSelect={setSelectedBuilding} uploadResult={uploadResult} />

          <div className="section-divider" />
          <WasteAnalyzer onResult={setWasteResult} uploadResult={uploadResult} />

          <div className="section-divider" />
          <WaterPanel data={waterData} uploadResult={uploadResult} />

          <div className="section-divider" />
          <EnergyPanel data={energyData} uploadResult={uploadResult} />

          <div className="section-divider" />
          <ResourceLossHeatmap waterData={waterData} energyData={energyData} uploadResult={uploadResult} />

          <div className="section-divider" />
          <ImpactProjection waterData={waterData} energyData={energyData} dashData={dashData} uploadResult={uploadResult} />

          <div className="section-divider" />
          <InterventionSimulator waterData={waterData} energyData={energyData} dashData={dashData} uploadResult={uploadResult} />

          <div className="section-divider" />
          <SustainabilityAchievements dashData={dashData} waterData={waterData} energyData={energyData} uploadResult={uploadResult} />

          <div className="section-divider" />
          <AgentWarRoom initialData={warRoomData} wasteResult={wasteResult} uploadResult={uploadResult} />

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
            src="/logo.jpeg" alt="RE:GEN AI"
            style={{
              width: 40, height: 40, borderRadius: 8, objectFit: 'cover',
              margin: '0 auto 14px', boxShadow: '0 0 16px rgba(0,255,136,0.22)',
            }}
          />
          <p className="font-black text-gradient-green mb-1" style={{ fontSize: 14 }}>
            RE:GEN AI
          </p>
          <p className="text-xs mb-6" style={{ color: '#94a3b8' }}>
            Sustainability Intelligence OS · Multi-Agent Resource Analysis Platform
          </p>
          <div className="h-px mb-6" style={{ background: 'rgba(255,255,255,0.04)' }} />
          <p className="text-xs leading-relaxed max-w-md mx-auto" style={{ color: '#64748b' }}>
            {uploadResult
              ? `Analysis derived from uploaded organizational data.`
              : 'Data is simulated for demonstration purposes. '}
            RE:GEN AI is a decision-support prototype — not professional regulatory, financial, or engineering advice.
            Designed for future integration with live IoT and building management systems.
          </p>
        </div>
      </footer>

      {toast && <Toast message={toast} onDone={() => setToast(null)} />}
    </div>
  )
}
