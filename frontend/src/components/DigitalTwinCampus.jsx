import { useState, useEffect } from 'react'

const RC  = { critical: '#ef4444', high: '#f97316', medium: '#eab308', low: '#22c55e', none: '#6b7280' }
const RL  = { critical: 'CRITICAL', high: 'HIGH', medium: 'MODERATE', low: 'LOW', none: 'CLEAR' }
const RLS = { critical: 'Critical', high: 'High', medium: 'Moderate', low: 'Healthy', none: 'Clear' }
const RLIcon = { critical: '!', high: '▲', medium: '→', low: '+', none: '+' }

const SCAN_STEPS = ['Acquiring', 'Scanning', 'Analyzing', 'Insights Ready']

const BUILDINGS = [
  {
    id: 'hostel', name: 'Hostel Block A', icon: '🏠', type: 'Residential',
    buildingId: 'HA-01', risk: 'medium', occupancy: '~240 students',
    hotX: 10, hotY: 45,
    water:  { level: 'high',   value: '142 L excess/day',   note: 'Night-flow anomaly detected (Jan 16, 2–4 AM)' },
    energy: { level: 'medium', value: '12 kWh after-hours', note: 'Moderate overnight consumption' },
    waste:  { level: 'low',    value: '8 kg/day',           note: 'Mostly organic — limited recyclables' },
    resources: {
      water: '5,240 L/day', waterDelta: 12,
      energy: '380 kWh/day', energyDelta: 8,
      waste: '8.2 kg/day', wasteDelta: 5,
      carbon: '0.9 tCO₂e/mo', carbonDelta: 6,
    },
    insights: 'Night-flow anomaly detected in plumbing network. Overnight energy consumption within expected range for residential capacity.',
    recommendations: [
      'Install flow monitoring at main entry point',
      'Inspect ground-floor pipe fittings for micro-leaks',
      'Deploy night auto-shutoff valve by Jan 22',
    ],
    impact: { water: -12, energy: -8, carbon: -6 },
    agent: 'Water Leakage Agent',
  },
  {
    id: 'seminar', name: 'Seminar Hall', icon: '🎓', type: 'Academic',
    buildingId: 'SH-01', risk: 'low', occupancy: 'Variable — event-driven',
    hotX: 37, hotY: 30,
    water:  { level: 'low',      value: 'Normal',           note: 'No anomalies in monitoring window' },
    energy: { level: 'critical', value: '68 kWh overnight', note: 'AC + lighting left on all night' },
    waste:  { level: 'low',      value: '3 kg/day',         note: 'Minimal — paper and packaging only' },
    resources: {
      water: '2,100 L/day', waterDelta: 3,
      energy: '845 kWh/day', energyDelta: 18,
      waste: '3.1 kg/day', wasteDelta: 2,
      carbon: '1.8 tCO₂e/mo', carbonDelta: 14,
    },
    insights: 'HVAC system continues operating 6.5 hrs post-occupancy. Occupancy sensor gap identified in main auditorium.',
    recommendations: [
      'Install occupancy-linked HVAC automation',
      'Schedule after-hours automated shutdown',
      'Estimated energy savings: ~34%',
    ],
    impact: { water: -4, energy: -34, carbon: -22 },
    agent: 'Energy Optimizer Agent',
  },
  {
    id: 'admin', name: 'Admin Block', icon: '🏢', type: 'Administrative',
    buildingId: 'AB-01', risk: 'low', occupancy: '~35 staff',
    hotX: 62, hotY: 30,
    water:  { level: 'none',   value: 'No anomalies',  note: 'All readings within normal range' },
    energy: { level: 'medium', value: '14 kWh/day',    note: 'Some computers left on after hours' },
    waste:  { level: 'low',    value: '5 kg/day',      note: 'Paper and dry waste — recyclable' },
    resources: {
      water: '890 L/day', waterDelta: 2,
      energy: '245 kWh/day', energyDelta: 9,
      waste: '5.2 kg/day', wasteDelta: 4,
      carbon: '0.5 tCO₂e/mo', carbonDelta: 3,
    },
    insights: 'Resource usage within expected operational baseline. Minor energy inefficiency from after-hours workstation usage.',
    recommendations: [
      'Default-off computer policy for all workstations',
      'Add paper recycling bins at each cluster',
      'Install motion-sensor lighting in corridors',
    ],
    impact: { water: -2, energy: -12, carbon: -5 },
    agent: 'Decision Engine',
  },
  {
    id: 'sports', name: 'Sports Complex', icon: '🏃', type: 'Recreation',
    buildingId: 'SC-01', risk: 'low', occupancy: '~200 students/day',
    hotX: 5, hotY: 66,
    water:  { level: 'low', value: 'Normal',         note: 'Usage within expected seasonal baseline' },
    energy: { level: 'low', value: '8 kWh/day',      note: 'Efficient LED lighting installed' },
    waste:  { level: 'low', value: '4 kg/day',       note: 'Minimal — packaging and sports waste' },
    resources: {
      water: '3,200 L/day', waterDelta: 5,
      energy: '280 kWh/day', energyDelta: 3,
      waste: '4.0 kg/day', wasteDelta: 2,
      carbon: '0.6 tCO₂e/mo', carbonDelta: 2,
    },
    insights: 'Facility operating efficiently. Roof area suitable for solar installation that could offset ~40% of energy demand.',
    recommendations: [
      'Solar panel installation on roof — est. 40% energy offset',
      'Rainwater harvesting system for field irrigation',
      'Install smart meters for granular monitoring',
    ],
    impact: { water: -8, energy: -40, carbon: -18 },
    agent: 'Impact Analyzer Agent',
  },
  {
    id: 'canteen', name: 'Canteen', icon: '🍽', type: 'Food Service',
    buildingId: 'CN-01', risk: 'medium', occupancy: '~500 meals/day',
    hotX: 63, hotY: 52,
    water:  { level: 'low',  value: 'Normal',    note: 'Operational usage within baseline' },
    energy: { level: 'low',  value: '8 kWh/day', note: 'Within expected operational range' },
    waste:  { level: 'high', value: '28 kg/day', note: 'High organic + packaging — high recovery potential' },
    resources: {
      water: '4,800 L/day', waterDelta: 7,
      energy: '520 kWh/day', energyDelta: 11,
      waste: '28.6 kg/day', wasteDelta: 11,
      carbon: '1.2 tCO₂e/mo', carbonDelta: 9,
    },
    insights: 'Organic waste load at 28 kg/day. Compost pathway yields ~1.8× vs raw disposal. High recovery potential identified.',
    recommendations: [
      'Route organic waste to biogas digester',
      'Transition to biodegradable packaging',
      'Est. ₹14,000/mo recovery from compost',
    ],
    impact: { water: -7, energy: -11, carbon: -9 },
    agent: 'Waste-to-Wealth Agent',
  },
  {
    id: 'computer', name: 'Computer Lab', icon: '💻', type: 'Technology',
    buildingId: 'CL-01', risk: 'critical', occupancy: '~60 users peak',
    hotX: 39, hotY: 66,
    water:  { level: 'medium', value: 'Slightly elevated',  note: 'Possible AC condensate drain issue' },
    energy: { level: 'high',   value: '39 kWh/day',        note: 'Workstation + AC anomaly (Jan 19)' },
    waste:  { level: 'medium', value: '12 kg/day',         note: 'E-waste and packaging — partly recoverable' },
    resources: {
      water: '12,850 L/day', waterDelta: 18,
      energy: '1,245 kWh/day', energyDelta: 24,
      waste: '28.6 kg/day', wasteDelta: 11,
      carbon: '3.2 tCO₂e/mo', carbonDelta: 16,
    },
    insights: 'High energy consumption due to extended equipment runtime and inefficient cooling. Water usage spike detected in restrooms.',
    recommendations: [
      'Implement smart power management on workstations',
      'Schedule HVAC based on occupancy sensors',
      'Fix leaking taps in Lab-3 & Restroom-2',
      'Install motion sensors in low-usage areas',
    ],
    impact: { water: -18, energy: -22, carbon: -15 },
    agent: 'Energy + Waste Agent',
  },
]

/* ─── Drone SVG ────────────────────────────────────────────────────────────── */
function DroneSVG({ isScanning, isComplete }) {
  const beamColor = isComplete ? '#00ff88' : '#00e5ff'
  return (
    <svg width="88" height="68" viewBox="0 0 88 68" style={{ display: 'block' }}>
      <ellipse cx="44" cy="60" rx="28" ry="5" fill="rgba(0,229,255,0.10)" />
      <line x1="44" y1="34" x2="11" y2="13" stroke="#00e5ff" strokeWidth="1.8" opacity="0.78"/>
      <line x1="44" y1="34" x2="77" y2="13" stroke="#00e5ff" strokeWidth="1.8" opacity="0.78"/>
      <line x1="44" y1="34" x2="11" y2="55" stroke="#00e5ff" strokeWidth="1.8" opacity="0.78"/>
      <line x1="44" y1="34" x2="77" y2="55" stroke="#00e5ff" strokeWidth="1.8" opacity="0.78"/>
      <ellipse cx="11" cy="13" rx="11" ry="3.5" fill="rgba(0,229,255,0.22)" stroke="#00e5ff" strokeWidth="0.8"
        style={{ animation: 'dtPropSpin 0.18s linear infinite', transformOrigin: '11px 13px' }}/>
      <ellipse cx="77" cy="13" rx="11" ry="3.5" fill="rgba(0,229,255,0.22)" stroke="#00e5ff" strokeWidth="0.8"
        style={{ animation: 'dtPropSpin 0.18s linear infinite reverse', transformOrigin: '77px 13px' }}/>
      <ellipse cx="11" cy="55" rx="11" ry="3.5" fill="rgba(0,229,255,0.22)" stroke="#00e5ff" strokeWidth="0.8"
        style={{ animation: 'dtPropSpin 0.22s linear infinite reverse', transformOrigin: '11px 55px' }}/>
      <ellipse cx="77" cy="55" rx="11" ry="3.5" fill="rgba(0,229,255,0.22)" stroke="#00e5ff" strokeWidth="0.8"
        style={{ animation: 'dtPropSpin 0.22s linear infinite', transformOrigin: '77px 55px' }}/>
      <rect x="32" y="27" width="24" height="14" rx="5" fill="rgba(0,8,28,0.95)" stroke="#00e5ff" strokeWidth="1.5"/>
      <circle cx="44" cy="27" r="2.5" fill={beamColor} opacity="0.95"
        style={{ animation: isScanning ? 'dtStatusBlink 0.55s ease-in-out infinite' : 'dtStatusBlink 1.8s ease-in-out infinite' }}/>
      <circle cx="44" cy="44" r="5" fill="rgba(0,229,255,0.10)" stroke="#00e5ff" strokeWidth="1"/>
      <circle cx="44" cy="44" r="2" fill={beamColor} opacity="0.72"/>
      <line x1="44" y1="49" x2="44" y2="68" stroke={beamColor} strokeWidth="1.5" opacity="0.85"/>
    </svg>
  )
}

/* ─── Drone System — smooth fly-to via CSS transition ──────────────────────── */
function DroneSystem({ hotX, hotY, scanPhase }) {
  const isScanning = scanPhase === 1 || scanPhase === 2
  const isComplete = scanPhase === 3

  return (
    <div style={{
      position: 'absolute',
      left: `${hotX}%`,
      top: `${hotY}%`,
      zIndex: 10,
      pointerEvents: 'none',
      transition: 'left 1.05s cubic-bezier(0.4,0,0.2,1), top 1.05s cubic-bezier(0.4,0,0.2,1)',
    }}>
      {/* Vertical beam — drone to ground target */}
      <div style={{
        position: 'absolute',
        left: '50%',
        top: -196,
        marginLeft: -1,
        width: 2,
        height: 196,
        background: isScanning
          ? 'linear-gradient(to bottom, transparent 0%, rgba(0,229,255,1) 55%, rgba(0,255,136,0.5))'
          : 'linear-gradient(to bottom, transparent 0%, rgba(0,229,255,0.8) 55%, rgba(0,229,255,0.45))',
        boxShadow: isScanning
          ? '0 0 28px rgba(0,229,255,0.9), 0 0 60px rgba(0,229,255,0.4)'
          : '0 0 14px rgba(0,229,255,0.5)',
        animation: 'dtBeamPulse 1.8s ease-in-out infinite',
        transition: 'box-shadow 0.5s ease, background 0.5s ease',
      }}/>

      {/* Cone spread */}
      <div style={{
        position: 'absolute',
        left: '50%',
        marginLeft: -56,
        top: -140,
        width: 112,
        height: 140,
        background: isScanning
          ? 'linear-gradient(to bottom, transparent, rgba(0,229,255,0.13))'
          : 'linear-gradient(to bottom, transparent, rgba(0,229,255,0.06))',
        clipPath: 'polygon(45% 0%, 55% 0%, 100% 100%, 0% 100%)',
        transition: 'background 0.5s ease',
      }}/>

      {/* Drone body — orbiting above the target */}
      <div style={{
        position: 'absolute',
        left: '50%',
        top: -196,
        animation: 'dtDroneOrbit 9s ease-in-out infinite',
        filter: `drop-shadow(0 0 ${isScanning ? '18px' : '10px'} rgba(0,229,255,0.75))`,
        transition: 'filter 0.5s ease',
      }}>
        <DroneSVG isScanning={isScanning} isComplete={isComplete} />
      </div>

      {/* Radar rings at ground target */}
      {[0, 0.6, 1.2].map((delay, i) => (
        <div key={i} style={{
          position: 'absolute',
          left: '50%',
          top: 0,
          width: 52 + i * 30,
          height: 52 + i * 30,
          borderRadius: '50%',
          border: `1px solid rgba(0,229,255,${isScanning ? 0.65 - i * 0.15 : 0.38 - i * 0.1})`,
          marginLeft: -(52 + i * 30) / 2,
          marginTop: -(52 + i * 30) / 2,
          animation: `dtRadarRing ${isScanning ? 1.3 : 1.9}s ${delay}s ease-out infinite`,
          transition: 'border-color 0.5s ease',
        }}/>
      ))}

      {/* Building scan grid */}
      <div style={{
        position: 'absolute',
        left: '50%',
        top: 0,
        width: 130,
        height: 75,
        marginLeft: -65,
        marginTop: -37,
        border: `1px solid rgba(0,229,255,${isComplete ? 0.7 : 0.42})`,
        boxShadow: `0 0 ${isComplete ? '32px' : '18px'} rgba(0,229,255,${isComplete ? 0.3 : 0.16}), inset 0 0 20px rgba(0,229,255,0.04)`,
        backgroundImage: [
          'linear-gradient(rgba(0,229,255,0.07) 1px, transparent 1px)',
          'linear-gradient(90deg, rgba(0,229,255,0.07) 1px, transparent 1px)',
        ].join(','),
        backgroundSize: '20px 13px',
        animation: 'dtGridBlink 3s ease-in-out infinite',
        transition: 'border-color 0.5s ease, box-shadow 0.5s ease',
      }}>
        {[0,1,2,3].map(i => (
          <div key={i} style={{
            position: 'absolute', width: 8, height: 8,
            ...(i===0 ? { top:0, left:0,  borderTop:'2px solid #00e5ff', borderLeft:'2px solid #00e5ff'  }
              :i===1 ? { top:0, right:0, borderTop:'2px solid #00e5ff', borderRight:'2px solid #00e5ff' }
              :i===2 ? { bottom:0, left:0,  borderBottom:'2px solid #00e5ff', borderLeft:'2px solid #00e5ff'  }
              :        { bottom:0, right:0, borderBottom:'2px solid #00e5ff', borderRight:'2px solid #00e5ff' }),
          }}/>
        ))}
      </div>
    </div>
  )
}

/* ─── Building hotspot label ─────────────────────────────────────────────── */
function Hotspot({ b, isSelected, onSelect, pulse }) {
  const color = RC[b.risk]
  const label = RLS[b.risk]
  const isCrit = b.risk === 'critical' || b.risk === 'high'

  return (
    <div
      onClick={() => onSelect(b.id)}
      style={{
        position: 'absolute',
        left: `${b.hotX}%`, top: `${b.hotY}%`,
        transform: 'translate(-50%, -50%)',
        zIndex: 12, cursor: 'pointer', userSelect: 'none',
      }}
    >
      <div style={{
        background: isSelected ? 'rgba(0,8,28,0.94)' : 'rgba(0,4,18,0.80)',
        border: `1px solid ${isSelected ? color + 'cc' : color + '55'}`,
        borderRadius: 8, padding: '6px 11px',
        backdropFilter: 'blur(14px)',
        boxShadow: isSelected
          ? `0 0 22px ${color}55, 0 0 50px ${color}22`
          : `0 0 10px ${color}22`,
        transition: 'all 0.3s ease',
        minWidth: 112, whiteSpace: 'nowrap',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 2 }}>
          <div style={{
            width: 6, height: 6, borderRadius: '50%', background: color,
            boxShadow: `0 0 7px ${color}`,
            animation: isCrit ? 'dtHotPulse 1.4s ease-in-out infinite' : 'none',
            flexShrink: 0,
          }}/>
          <span style={{ color: '#fff', fontSize: 11, fontWeight: 700, letterSpacing: '0.03em' }}>
            {b.name}
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 5, paddingLeft: 13 }}>
          <span style={{ color, fontSize: 9, fontWeight: 700 }}>{RLIcon[b.risk]}</span>
          <span style={{ color, fontSize: 9, fontWeight: 600 }}>{label}</span>
        </div>
      </div>
    </div>
  )
}

/* ─── Right analysis panel — compact, no internal scroll ────────────────── */
function BuildingPanel({ building, onClose }) {
  if (!building) return null
  const col = RC[building.risk]
  const r   = building.resources

  const resources = [
    { icon: '💧', label: 'Water',  value: r.water,  delta: r.waterDelta,  color: '#00e5ff' },
    { icon: '⚡', label: 'Energy', value: r.energy, delta: r.energyDelta, color: '#eab308' },
    { icon: '♻', label: 'Waste',  value: r.waste,  delta: r.wasteDelta,  color: '#22c55e' },
    { icon: '☁', label: 'Carbon', value: r.carbon, delta: r.carbonDelta, color: '#a78bfa' },
  ]

  return (
    <div style={{
      position: 'absolute', top: 0, right: 0, bottom: 0, width: 300,
      background: 'rgba(2,7,22,0.94)',
      backdropFilter: 'blur(24px)',
      borderLeft: '1px solid rgba(255,255,255,0.07)',
      zIndex: 20,
      display: 'flex',
      flexDirection: 'column',
      padding: '64px 18px 20px',
      gap: 0,
      animation: 'dtPanelIn 0.35s ease-out',
      overflowY: 'hidden',
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14, flexShrink: 0 }}>
        <span style={{ color: '#334155', fontSize: 9.5, fontWeight: 700, letterSpacing: '0.14em', textTransform: 'uppercase' }}>
          Building Analysis
        </span>
        <button
          onClick={onClose}
          style={{ color: '#475569', background: 'none', border: 'none', fontSize: 18, cursor: 'pointer', lineHeight: 1, padding: '0 3px', transition: 'color 0.2s' }}
          onMouseEnter={e => e.currentTarget.style.color = '#fff'}
          onMouseLeave={e => e.currentTarget.style.color = '#475569'}
        >×</button>
      </div>

      {/* Building identity */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16, flexShrink: 0 }}>
        <div style={{
          width: 44, height: 44, borderRadius: 8, flexShrink: 0,
          background: `linear-gradient(135deg, ${col}22, ${col}08)`,
          border: `1px solid ${col}44`,
          display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 20,
        }}>
          {building.icon}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 3, flexWrap: 'wrap' }}>
            <span style={{ color: '#fff', fontWeight: 800, fontSize: 13 }}>{building.name}</span>
            <span style={{
              background: col + '1e', border: `1px solid ${col}55`,
              color: col, fontSize: 8.5, fontWeight: 700,
              padding: '1px 7px', borderRadius: 10, letterSpacing: '0.07em', flexShrink: 0,
            }}>{RL[building.risk]}</span>
          </div>
          <div style={{ color: '#334155', fontSize: 9.5 }}>
            {building.buildingId} · {building.occupancy}
          </div>
        </div>
      </div>

      {/* Resource grid — 2×2 compact cards */}
      <PLabel>Resource Overview</PLabel>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 7, marginBottom: 14, flexShrink: 0 }}>
        {resources.map(row => (
          <div key={row.label} style={{
            background: `${row.color}08`,
            border: `1px solid ${row.color}1e`,
            borderRadius: 8,
            padding: '8px 10px',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 5, marginBottom: 4 }}>
              <span style={{ fontSize: 12 }}>{row.icon}</span>
              <span style={{ color: '#475569', fontSize: 8.5, fontWeight: 600, letterSpacing: '0.05em' }}>{row.label}</span>
            </div>
            <div style={{ color: '#e2e8f0', fontSize: 11.5, fontWeight: 700, marginBottom: 2 }}>{row.value}</div>
            <div style={{ color: '#ef4444', fontSize: 9, fontWeight: 700 }}>↑ {row.delta}%</div>
          </div>
        ))}
      </div>

      {/* AI Insights */}
      <PLabel>Gemini Insights</PLabel>
      <p style={{ color: '#94a3b8', fontSize: 11, lineHeight: 1.62, marginBottom: 14, flexShrink: 0 }}>
        {building.insights}
      </p>

      {/* Recommendations */}
      <PLabel>Recommendations</PLabel>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 14, flexShrink: 0 }}>
        {building.recommendations.map((rec, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 7 }}>
            <span style={{ color: '#22c55e', fontSize: 11, flexShrink: 0, marginTop: 1 }}>✓</span>
            <span style={{ color: '#cbd5e1', fontSize: 10.5, lineHeight: 1.55 }}>{rec}</span>
          </div>
        ))}
      </div>

      {/* Potential impact */}
      <PLabel>Estimated Impact</PLabel>
      <div style={{ display: 'flex', gap: 7, marginBottom: 16, flexShrink: 0 }}>
        {[
          { color: '#00e5ff', bg: 'rgba(0,229,255,0.06)', v: building.impact.water,  label: 'Water'  },
          { color: '#eab308', bg: 'rgba(234,179,8,0.06)', v: building.impact.energy, label: 'Energy' },
          { color: '#a78bfa', bg: 'rgba(167,139,250,0.06)', v: building.impact.carbon, label: 'Carbon' },
        ].map(p => (
          <div key={p.label} style={{
            flex: 1, textAlign: 'center',
            background: p.bg, border: `1px solid ${p.color}22`,
            borderRadius: 8, padding: '8px 4px',
          }}>
            <div style={{ color: p.color, fontSize: 16, fontWeight: 900, marginBottom: 2 }}>{p.v}%</div>
            <div style={{ color: '#475569', fontSize: 8.5 }}>{p.label}</div>
          </div>
        ))}
      </div>

      {/* View Action Plan — actually scrolls to the section */}
      <button
        onClick={() => document.getElementById('action-plan')?.scrollIntoView({ behavior: 'smooth' })}
        style={{
          width: '100%',
          background: 'linear-gradient(135deg, rgba(0,255,136,0.12), rgba(0,229,255,0.08))',
          border: '1px solid rgba(0,255,136,0.40)',
          borderRadius: 8, color: '#00ff88',
          fontWeight: 700, fontSize: 12, padding: '11px',
          cursor: 'pointer', letterSpacing: '0.04em',
          transition: 'all 0.22s ease',
          boxShadow: '0 0 14px rgba(0,255,136,0.10)',
          flexShrink: 0,
        }}
        onMouseEnter={e => {
          e.currentTarget.style.background = 'linear-gradient(135deg, rgba(0,255,136,0.22), rgba(0,229,255,0.14))'
          e.currentTarget.style.boxShadow = '0 0 24px rgba(0,255,136,0.22)'
          e.currentTarget.style.transform = 'translateY(-1px)'
        }}
        onMouseLeave={e => {
          e.currentTarget.style.background = 'linear-gradient(135deg, rgba(0,255,136,0.12), rgba(0,229,255,0.08))'
          e.currentTarget.style.boxShadow = '0 0 14px rgba(0,255,136,0.10)'
          e.currentTarget.style.transform = ''
        }}
      >
        View Action Plan →
      </button>

      <p style={{ color: '#1e293b', fontSize: 8.5, textAlign: 'center', marginTop: 10, lineHeight: 1.5, flexShrink: 0 }}>
        Simulated smart-campus resource logs · Decision-support prototype
      </p>
    </div>
  )
}

function PLabel({ children }) {
  return (
    <p style={{
      color: '#334155', fontSize: 8.5, fontWeight: 700,
      letterSpacing: '0.14em', textTransform: 'uppercase',
      marginBottom: 8, flexShrink: 0,
    }}>
      {children}
    </p>
  )
}

/* ─── Main export ────────────────────────────────────────────────────────── */
export default function DigitalTwinCampus({ onBuildingSelect }) {
  const [selected, setSelected] = useState('computer')
  const [pulse, setPulse]       = useState(true)
  const [scanStep, setScanStep] = useState(3)

  useEffect(() => {
    const t = setInterval(() => setPulse(p => !p), 700)
    return () => clearInterval(t)
  }, [])

  const handleSelect = (id) => {
    if (selected === id) {
      setSelected(null)
      onBuildingSelect?.(null)
      return
    }
    setSelected(id)
    const b = BUILDINGS.find(x => x.id === id)
    onBuildingSelect?.(b ?? null)
    setScanStep(0)
    setTimeout(() => setScanStep(1), 600)
    setTimeout(() => setScanStep(2), 1500)
    setTimeout(() => setScanStep(3), 2700)
  }

  const sel = BUILDINGS.find(b => b.id === selected)

  return (
    <section id="twin" style={{ position: 'relative', width: '100%', height: '100vh', overflow: 'hidden' }}>

      {/* CSS keyframes */}
      <style>{`
        @keyframes dtDroneOrbit {
          0%   { transform: translateX(-50%) translateX(26px)  translateY(0px)   rotate(4deg); }
          18%  { transform: translateX(-50%) translateX(10px)  translateY(-26px) rotate(11deg); }
          36%  { transform: translateX(-50%) translateX(-18px) translateY(-14px) rotate(1deg); }
          54%  { transform: translateX(-50%) translateX(-26px) translateY(-6px)  rotate(-7deg); }
          72%  { transform: translateX(-50%) translateX(-10px) translateY(-34px) rotate(-2deg); }
          88%  { transform: translateX(-50%) translateX(16px)  translateY(-20px) rotate(9deg); }
          100% { transform: translateX(-50%) translateX(26px)  translateY(0px)   rotate(4deg); }
        }
        @keyframes dtPropSpin    { from{transform:scaleX(1)} 25%{transform:scaleX(0.1)} 50%{transform:scaleX(-1)} 75%{transform:scaleX(-0.1)} to{transform:scaleX(1)} }
        @keyframes dtBeamPulse   { 0%,100%{opacity:0.72} 50%{opacity:1} }
        @keyframes dtRadarRing   { 0%{transform:translate(-50%,-50%) scale(0.4);opacity:0.9} 100%{transform:translate(-50%,-50%) scale(2.8);opacity:0} }
        @keyframes dtHotPulse    { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.3;transform:scale(1.5)} }
        @keyframes dtStatusBlink { 0%,100%{opacity:1} 50%{opacity:0.25} }
        @keyframes dtGridBlink   { 0%,100%{opacity:0.85} 50%{opacity:0.5} }
        @keyframes dtPanelIn     { from{opacity:0;transform:translateX(18px)} to{opacity:1;transform:translateX(0)} }
        @keyframes dtSweep       { 0%{opacity:0;transform:translateY(-100%)} 8%{opacity:1} 92%{opacity:0.6} 100%{opacity:0;transform:translateY(100vh)} }
      `}</style>

      {/* Campus background */}
      <img
        src="/twin-bg.jpg"
        alt="Campus aerial view"
        onError={e => { e.currentTarget.src = '/hero-campus.jpg' }}
        style={{
          position: 'absolute', inset: 0,
          width: '100%', height: '100%',
          objectFit: 'cover', objectPosition: 'center 35%',
          zIndex: 0,
        }}
      />

      {/* Dark overlay */}
      <div style={{ position:'absolute', inset:0, background:'rgba(0,3,16,0.45)', zIndex:1 }}/>
      {/* Vignette */}
      <div style={{ position:'absolute', inset:0, background:'radial-gradient(ellipse 85% 85% at 50% 50%, transparent 15%, rgba(0,0,0,0.58) 100%)', zIndex:1 }}/>
      {/* Top/bottom gradient */}
      <div style={{ position:'absolute', inset:0, background:'linear-gradient(0deg, rgba(0,2,14,0.75) 0%, transparent 20%, transparent 78%, rgba(0,2,14,0.6) 100%)', zIndex:1 }}/>
      {/* Cyan center tint */}
      <div style={{ position:'absolute', inset:0, background:'radial-gradient(ellipse 38% 38% at 42% 52%, rgba(0,229,255,0.04) 0%, transparent 70%)', zIndex:1 }}/>

      {/* Scan sweep */}
      <div style={{
        position:'absolute', left:0, right: sel ? 300 : 0, top:0, height:2, zIndex:4, pointerEvents:'none',
        background:'linear-gradient(90deg, transparent, rgba(0,229,255,0.55), rgba(0,255,136,0.22), transparent)',
        animation:'dtSweep 7s ease-in-out infinite',
        boxShadow:'0 0 18px rgba(0,229,255,0.4)',
      }}/>

      {/* Title block */}
      <div style={{ position:'absolute', left:48, top:84, zIndex:15, maxWidth:360, pointerEvents:'none' }}>
        <div style={{ display:'flex', alignItems:'center', gap:8, marginBottom:10 }}>
          <div style={{ width:7, height:7, borderRadius:'50%', background:'#00ff88', boxShadow:'0 0 8px #00ff88', animation:'dtStatusBlink 2s ease-in-out infinite' }}/>
          <span style={{ color:'#00ff88', fontSize:11, fontWeight:700, letterSpacing:'0.18em', textTransform:'uppercase' }}>Campus Intelligence</span>
        </div>
        <h2 style={{ color:'#fff', fontSize:52, fontWeight:900, lineHeight:1.05, margin:'0 0 12px', fontFamily:'Inter,sans-serif' }}>
          Digital <span style={{ color:'#00e5ff' }}>Twin</span>
        </h2>
        <p style={{ color:'rgba(148,163,184,0.82)', fontSize:12.5, lineHeight:1.65, margin:0 }}>
          AI-driven campus intelligence.<br/>
          Every resource. Every system. One connected view.
        </p>
      </div>

      {/* Building hotspots */}
      {BUILDINGS.map(b => (
        <Hotspot key={b.id} b={b} isSelected={selected === b.id} onSelect={handleSelect} pulse={pulse}/>
      ))}

      {/* Drone system — stays mounted, transitions on position */}
      {sel && (
        <DroneSystem hotX={sel.hotX} hotY={sel.hotY} scanPhase={scanStep} />
      )}

      {/* Right analysis panel */}
      <BuildingPanel building={sel} onClose={() => setSelected(null)}/>

      {/* Bottom status bar */}
      <div style={{
        position:'absolute', bottom:0, left:0, right: sel ? 300 : 0,
        zIndex:15, padding:'18px 48px',
        background:'linear-gradient(to top, rgba(0,2,14,0.90), transparent)',
        display:'flex', alignItems:'center', gap:36, flexWrap:'wrap',
      }}>
        <div style={{ display:'flex', alignItems:'center', gap:12, flexShrink:0 }}>
          <div style={{
            width:44, height:44, borderRadius:'50%', position:'relative',
            background:'rgba(0,229,255,0.07)',
            border:'1px solid rgba(0,229,255,0.28)',
            display:'flex', alignItems:'center', justifyContent:'center',
            boxShadow:'0 0 18px rgba(0,229,255,0.18)',
          }}>
            <span style={{ fontSize:19 }}>🛸</span>
            <div style={{ position:'absolute', inset:-5, borderRadius:'50%', border:'1px solid rgba(0,229,255,0.18)', animation:'dtRadarRing 2.2s 0s ease-out infinite' }}/>
            <div style={{ position:'absolute', inset:-10, borderRadius:'50%', border:'1px solid rgba(0,229,255,0.10)', animation:'dtRadarRing 2.2s 0.6s ease-out infinite' }}/>
          </div>
          <div>
            <div style={{ color:'#00e5ff', fontSize:11, fontWeight:700, letterSpacing:'0.08em', marginBottom:1 }}>DRONE STATUS</div>
            <div style={{ color:'#00e5ff', fontSize:13, fontWeight:800, marginBottom:1 }}>
              {scanStep < 3 ? SCAN_STEPS[scanStep] : 'Scanning Campus'}
            </div>
            <div style={{ color:'#334155', fontSize:9.5 }}>
              {sel ? `Focused: ${sel.name}` : 'Multi-layer data collection active'}
            </div>
          </div>
        </div>

        {/* Scan step pipeline */}
        <div style={{ display:'flex', alignItems:'center', gap:6 }}>
          {SCAN_STEPS.map((step, i) => (
            <div key={step} style={{ display:'flex', alignItems:'center', gap:6 }}>
              <div style={{ display:'flex', alignItems:'center', gap:6 }}>
                <div style={{
                  width:22, height:22, borderRadius:'50%', display:'flex', alignItems:'center', justifyContent:'center',
                  background: i <= scanStep ? 'rgba(0,229,255,0.18)' : 'rgba(255,255,255,0.03)',
                  border: `1px solid ${i <= scanStep ? 'rgba(0,229,255,0.5)' : 'rgba(255,255,255,0.07)'}`,
                  transition:'all 0.4s ease', flexShrink:0,
                }}>
                  {i < scanStep
                    ? <span style={{ color:'#00e5ff', fontSize:10 }}>✓</span>
                    : i === scanStep
                    ? <div style={{ width:6, height:6, borderRadius:'50%', background:'#00e5ff', animation:'dtStatusBlink 0.9s ease-in-out infinite' }}/>
                    : null}
                </div>
                <span style={{
                  color: i <= scanStep ? (i === scanStep ? '#fff' : '#64748b') : '#1e293b',
                  fontSize:11.5, fontWeight: i === scanStep ? 700 : 500,
                  transition:'color 0.3s ease',
                }}>
                  {step}
                </span>
              </div>
              {i < SCAN_STEPS.length - 1 && (
                <span style={{ color: i < scanStep ? '#00e5ff' : '#1e293b', fontSize:14, margin:'0 1px', transition:'color 0.3s ease' }}>→</span>
              )}
            </div>
          ))}
        </div>
      </div>

    </section>
  )
}
