import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { interpretDatasets } from '../api'

const DATASET_LABELS = {
  water:     { icon: '💧', label: 'Water Usage',   color: '#00b4ff' },
  energy:    { icon: '⚡', label: 'Energy Usage',  color: '#eab308' },
  fuel:      { icon: '⛽', label: 'Fuel Usage',    color: '#f97316' },
  waste:     { icon: '♻️', label: 'Waste Inventory', color: '#00ff88' },
  occupancy: { icon: '👥', label: 'Occupancy',     color: '#a78bfa' },
}

function GaugeArc({ value, color, size = 80 }) {
  const r = size * 0.38
  const circ = 2 * Math.PI * r
  const pct = Math.min(100, Math.max(0, value))
  const offset = circ * (1 - pct / 100)
  const cx = size / 2, cy = size / 2

  return (
    <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth={5} />
      <circle
        cx={cx} cy={cy} r={r}
        fill="none"
        stroke={color}
        strokeWidth={5}
        strokeLinecap="round"
        strokeDasharray={circ}
        strokeDashoffset={offset}
        style={{ transition: 'stroke-dashoffset 1.2s cubic-bezier(0.16,1,0.3,1)', filter: `drop-shadow(0 0 5px ${color}88)` }}
      />
    </svg>
  )
}

function MetricGauge({ value, label, color, description, onClick, expanded }) {
  return (
    <div
      onClick={onClick}
      style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6, flex: 1, cursor: onClick ? 'pointer' : 'default' }}
    >
      <div style={{ position: 'relative', width: 80, height: 80 }}>
        <GaugeArc value={value} color={color} size={80} />
        <div style={{
          position: 'absolute', inset: 0,
          display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        }}>
          <span style={{ fontSize: 16, fontWeight: 800, color, fontVariantNumeric: 'tabular-nums', lineHeight: 1 }}>
            {value}
          </span>
          <span style={{ fontSize: 8, color: 'rgba(255,255,255,0.35)', letterSpacing: '0.06em' }}>%</span>
        </div>
      </div>
      <div style={{ textAlign: 'center' }}>
        <div style={{ fontSize: 11.5, fontWeight: 700, color: '#fff' }}>
          {label}
          {onClick && <span style={{ marginLeft: 4, fontSize: 9, color: 'rgba(255,255,255,0.25)' }}>{expanded ? '▲' : '▼'}</span>}
        </div>
        <div style={{ fontSize: 10, color: 'rgba(100,116,139,0.7)', lineHeight: 1.4, maxWidth: 110 }}>{description}</div>
      </div>
    </div>
  )
}

// ── Data Intelligence Panel (Step 3) ─────────────────────────────────────────
function DataIntelligencePanel({ uploadState, available }) {
  const [result, setResult]   = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState(false)

  useEffect(() => {
    const { water, energy, fuel, waste, orgName, orgType } = uploadState || {}

    const payload = {
      org_name: orgName || 'My Organization',
      org_type: orgType || 'University',
      water_records:      water?.file?.record_count || 0,
      water_buildings:    water?.file?.buildings_detected || [],
      water_date_range:   water?.file?.date_range || '',
      water_warnings:     water?.file?.warnings || [],
      energy_records:     energy?.file?.record_count || 0,
      energy_zones:       energy?.file?.zones_detected || [],
      energy_date_range:  energy?.file?.date_range || '',
      energy_warnings:    energy?.file?.warnings || [],
      fuel_records:       fuel?.file?.record_count || 0,
      waste_type:         (function() {
        const wi = (waste?.items || []).filter(r => r.type && parseFloat(r.qty) > 0)
        if (!wi.length) return ''
        return wi.length === 1 ? wi[0].type : `${wi.length} waste streams`
      })(),
      waste_qty_kg:       (waste?.items || []).filter(r => r.type && parseFloat(r.qty) > 0).reduce((s, r) => s + parseFloat(r.qty || 0), 0),
      manual_water_liters:  parseFloat(water?.manual) || 0,
      manual_water_period:  water?.period || 'weekly',
      manual_energy_kwh:    parseFloat(energy?.manual) || 0,
      manual_energy_period: energy?.period || 'weekly',
      available_datasets: available,
    }

    interpretDatasets(payload)
      .then(res => { setResult(res.data); setLoading(false) })
      .catch(() => { setError(true); setLoading(false) })
  }, [])

  // Fallback deterministic display when API fails
  const fallbackFacts = []
  const { water, energy, fuel, waste } = uploadState || {}
  if (water?.file?.record_count) fallbackFacts.push(`${water.file.record_count.toLocaleString()} Water Records`)
  if (water?.file?.buildings_detected?.length) fallbackFacts.push(`${water.file.buildings_detected.length} Water Locations`)
  if (energy?.file?.record_count) fallbackFacts.push(`${energy.file.record_count.toLocaleString()} Energy Records`)
  if (energy?.file?.zones_detected?.length) fallbackFacts.push(`${energy.file.zones_detected.length} Energy Zones`)
  if (parseFloat(water?.manual) > 0) fallbackFacts.push(`Water: Manual Entry (${water.manual} L/${water.period || 'weekly'})`)
  if (parseFloat(energy?.manual) > 0) fallbackFacts.push(`Energy: Manual Entry (${energy.manual} kWh/${energy.period || 'weekly'})`)
  if (fuel?.file?.record_count) fallbackFacts.push(`${fuel.file.record_count.toLocaleString()} Fuel Records`)
  const wItems = (waste?.items || []).filter(r => r.type && parseFloat(r.qty) > 0)
  if (wItems.length > 0) {
    const totalKg = wItems.reduce((s, r) => s + parseFloat(r.qty || 0), 0)
    fallbackFacts.push(`Waste: ${wItems.length} stream${wItems.length !== 1 ? 's' : ''} (${Math.round(totalKg)} kg total)`)
  }
  fallbackFacts.push(`Carbon: Automatic (from ${available.length} dataset${available.length !== 1 ? 's' : ''})`)

  const facts = result?.facts || fallbackFacts
  const qualityNote = result?.quality_note || ''
  const aiEnhanced = result?.ai_enhanced || false

  return (
    <div style={{
      background: 'rgba(3,9,20,0.72)',
      backdropFilter: 'blur(22px)',
      border: '1px solid rgba(255,255,255,0.07)',
      borderTop: '2px solid rgba(0,229,255,0.22)',
      borderRadius: 18, padding: '18px 22px',
      marginBottom: 16,
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 9, marginBottom: 14 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
          {loading ? (
            <span style={{ width: 10, height: 10, border: '1.5px solid rgba(0,229,255,0.5)', borderTopColor: '#00e5ff', borderRadius: '50%', display: 'inline-block', animation: 'mssSpin 0.75s linear infinite' }} />
          ) : (
            <div style={{ width: 6, height: 6, borderRadius: '50%', background: aiEnhanced ? '#00ff88' : '#00e5ff', boxShadow: `0 0 8px ${aiEnhanced ? '#00ff88' : '#00e5ff'}` }} />
          )}
          <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.16em', color: '#00e5ff', textTransform: 'uppercase' }}>
            Data Intelligence
          </span>
        </div>
        {!loading && (
          <span style={{ marginLeft: 'auto', fontSize: 9, color: aiEnhanced ? '#00ff8888' : 'rgba(100,116,139,0.5)', fontWeight: 600 }}>
            {aiEnhanced ? '✦ AI-Enhanced' : 'Deterministic'}
          </span>
        )}
      </div>

      {loading ? (
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {[1,2,3,4].map(i => (
            <div key={i} style={{ height: 22, borderRadius: 50, background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)', width: 100 + i * 20, animation: 'mssPulse 1.5s ease-in-out infinite' }} />
          ))}
        </div>
      ) : (
        <>
          {/* Fact chips */}
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: qualityNote ? 12 : 0 }}>
            {facts.map((fact, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.06 }}
                style={{
                  padding: '4px 10px', borderRadius: 50,
                  background: 'rgba(0,229,255,0.07)',
                  border: '1px solid rgba(0,229,255,0.18)',
                  fontSize: 11, color: '#94a3b8', fontWeight: 500,
                  whiteSpace: 'nowrap',
                }}
              >
                {fact}
              </motion.div>
            ))}
          </div>

          {/* AI quality note */}
          {qualityNote && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.4 }}
              style={{
                marginTop: 10, padding: '8px 12px', borderRadius: 8,
                background: 'rgba(0,229,255,0.04)',
                border: '1px solid rgba(0,229,255,0.10)',
                fontSize: 11.5, color: 'rgba(148,163,184,0.75)', lineHeight: 1.6,
              }}
            >
              {qualityNote}
            </motion.div>
          )}
        </>
      )}
    </div>
  )
}

// ── Coverage formula breakdown (Step 4) ─────────────────────────────────────
function CoverageBreakdown({ available, coverage, confidence, readiness, WEIGHTS, PENALTIES }) {
  const ALL_DS = ['water', 'energy', 'fuel', 'waste', 'occupancy']

  return (
    <motion.div
      initial={{ height: 0, opacity: 0 }}
      animate={{ height: 'auto', opacity: 1 }}
      exit={{ height: 0, opacity: 0 }}
      transition={{ duration: 0.3, ease: 'easeInOut' }}
      style={{ overflow: 'hidden' }}
    >
      <div style={{
        marginTop: 12, padding: '14px 16px', borderRadius: 10,
        background: 'rgba(0,0,0,0.25)',
        border: '1px solid rgba(255,255,255,0.06)',
      }}>
        <p style={{ fontSize: 9.5, fontWeight: 700, color: 'rgba(255,255,255,0.28)', letterSpacing: '0.14em', textTransform: 'uppercase', marginBottom: 10 }}>
          Formula Breakdown
        </p>

        {/* Coverage */}
        <div style={{ marginBottom: 10 }}>
          <div style={{ fontSize: 10, color: '#a78bfa', fontWeight: 700, marginBottom: 5 }}>
            Data Coverage = sum of present dataset weights
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
            {ALL_DS.map(ds => {
              const w = WEIGHTS[ds] || 0
              const present = available.includes(ds)
              return (
                <div key={ds} style={{
                  padding: '2px 8px', borderRadius: 4, fontSize: 10,
                  background: present ? 'rgba(167,139,250,0.12)' : 'rgba(255,255,255,0.03)',
                  border: `1px solid ${present ? 'rgba(167,139,250,0.3)' : 'rgba(255,255,255,0.06)'}`,
                  color: present ? '#a78bfa' : '#475569',
                  textDecoration: !present ? 'line-through' : 'none',
                }}>
                  {ds} {w}%
                </div>
              )
            })}
            <div style={{ padding: '2px 8px', borderRadius: 4, fontSize: 10, fontWeight: 700, color: '#a78bfa' }}>= {coverage}%</div>
          </div>
        </div>

        {/* Confidence */}
        <div style={{ marginBottom: 10 }}>
          <div style={{ fontSize: 10, color: '#00e5ff', fontWeight: 700, marginBottom: 5 }}>
            Analysis Confidence = 100% minus penalties for missing datasets
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, alignItems: 'center' }}>
            <div style={{ padding: '2px 8px', borderRadius: 4, fontSize: 10, background: 'rgba(0,229,255,0.08)', border: '1px solid rgba(0,229,255,0.18)', color: '#00e5ff' }}>100%</div>
            {ALL_DS.map(ds => {
              const penalty = PENALTIES[ds] || 0
              const missing = !available.includes(ds) && penalty > 0
              if (!missing) return null
              return (
                <div key={ds} style={{ padding: '2px 8px', borderRadius: 4, fontSize: 10, background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.18)', color: '#f87171' }}>
                  − {ds} {penalty}%
                </div>
              )
            })}
            <div style={{ padding: '2px 8px', borderRadius: 4, fontSize: 10, fontWeight: 700, color: '#00e5ff' }}>= {confidence}%</div>
          </div>
        </div>

        {/* Readiness */}
        <div>
          <div style={{ fontSize: 10, color: '#00ff88', fontWeight: 700, marginBottom: 5 }}>
            Analysis Readiness = (Coverage × 60%) + (Confidence × 40%)
          </div>
          <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', alignItems: 'center' }}>
            <div style={{ padding: '2px 8px', borderRadius: 4, fontSize: 10, background: 'rgba(167,139,250,0.08)', border: '1px solid rgba(167,139,250,0.18)', color: '#a78bfa' }}>{coverage}% × 0.6</div>
            <span style={{ fontSize: 10, color: '#475569' }}>+</span>
            <div style={{ padding: '2px 8px', borderRadius: 4, fontSize: 10, background: 'rgba(0,229,255,0.08)', border: '1px solid rgba(0,229,255,0.18)', color: '#00e5ff' }}>{confidence}% × 0.4</div>
            <div style={{ padding: '2px 8px', borderRadius: 4, fontSize: 10, fontWeight: 700, color: '#00ff88' }}>= {readiness}%</div>
          </div>
        </div>
      </div>
    </motion.div>
  )
}

export default function MissionSummary({ uploadState, onLaunch, onBack, launching }) {
  const { orgName, orgType, water, energy, fuel, waste } = uploadState || {}
  const [coverageExpanded, setCoverageExpanded] = useState(false)

  // Determine which datasets are available
  const available = []
  const missing   = []

  const check = (id, ds) => {
    const hasFile   = ds?.file?.valid
    const hasManual = parseFloat(ds?.manual) > 0
    if (hasFile || hasManual) available.push(id)
    else missing.push(id)
  }

  check('water',  water)
  check('energy', energy)
  check('fuel',   fuel)
  const wasteItems = (waste?.items || []).filter(r => r.type && parseFloat(r.qty) > 0)
  if (wasteItems.length > 0) available.push('waste')
  else missing.push('waste')

  // Coverage formula — mirrors backend compute_coverage() exactly
  const WEIGHTS    = { water: 30, energy: 30, fuel: 15, waste: 15, occupancy: 0 }
  const PENALTIES  = { water: 20, energy: 20, fuel: 8,  waste: 8,  occupancy: 4 }
  const ALL_DS     = ['water', 'energy', 'fuel', 'waste', 'occupancy']
  const coverage   = Math.round(available.reduce((s, d) => s + (WEIGHTS[d] || 0), 0))
  const confidence = Math.round(Math.max(0,
    100 - ALL_DS.reduce((s, d) => s + (available.includes(d) ? 0 : PENALTIES[d]), 0)
  ))
  const readiness  = Math.round(coverage * 0.6 + confidence * 0.4)

  const readinessColor = readiness >= 70 ? '#00ff88' : readiness >= 40 ? '#eab308' : '#ef4444'
  const confColor      = confidence >= 70 ? '#00e5ff' : confidence >= 40 ? '#eab308' : '#f97316'
  const covColor       = coverage >= 60 ? '#a78bfa' : coverage >= 30 ? '#eab308' : '#94a3b8'

  return (
    <section style={{
      width: '100%', minHeight: '100vh',
      paddingTop: 90, paddingBottom: 80,
      background: 'linear-gradient(180deg, rgba(0,10,20,1) 0%, rgba(2,6,18,1) 100%)',
      position: 'relative',
    }}>
      <div style={{
        position: 'absolute', inset: 0, zIndex: 0, pointerEvents: 'none',
        backgroundImage: [
          'linear-gradient(rgba(0,229,255,0.012) 1px, transparent 1px)',
          'linear-gradient(90deg, rgba(0,229,255,0.012) 1px, transparent 1px)',
        ].join(','),
        backgroundSize: '52px 52px',
      }} />

      <div style={{ position: 'relative', zIndex: 1, maxWidth: 760, margin: '0 auto', padding: '0 24px' }}>

        {/* Back */}
        <button
          onClick={onBack}
          disabled={launching}
          style={{
            display: 'flex', alignItems: 'center', gap: 6,
            padding: '7px 14px', borderRadius: 50,
            background: 'rgba(255,255,255,0.05)',
            border: '1px solid rgba(255,255,255,0.10)',
            color: 'rgba(255,255,255,0.65)', fontSize: 12, fontWeight: 600,
            cursor: launching ? 'not-allowed' : 'pointer', fontFamily: 'inherit',
            marginBottom: 28,
            transition: 'all 0.18s ease',
            opacity: launching ? 0.4 : 1,
          }}
        >
          ← Edit Datasets
        </button>

        {/* Title */}
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 8,
            padding: '4px 14px', borderRadius: 50,
            background: 'rgba(0,255,136,0.07)',
            border: '1px solid rgba(0,255,136,0.18)',
            marginBottom: 14,
          }}>
            <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#00ff88', boxShadow: '0 0 8px #00ff88', animation: 'mssPulse 2s ease-in-out infinite' }} />
            <span style={{ fontSize: 10.5, fontWeight: 700, letterSpacing: '0.18em', color: '#00cc77', textTransform: 'uppercase' }}>
              Analysis Summary
            </span>
          </div>
          <h2 style={{ fontSize: 'clamp(22px, 3vw, 30px)', fontWeight: 900, color: '#fff', margin: '0 0 8px' }}>
            Pre-Analysis Summary
          </h2>
          <p style={{ fontSize: 13, color: 'rgba(148,163,184,0.55)', margin: 0 }}>
            Review your datasets and estimated analysis coverage before launching.
          </p>
        </div>

        {/* Org info */}
        <div style={{
          background: 'rgba(3,9,20,0.72)',
          backdropFilter: 'blur(22px)',
          border: '1px solid rgba(255,255,255,0.07)',
          borderTop: '2px solid rgba(0,229,255,0.30)',
          borderRadius: 18, padding: '20px 22px',
          marginBottom: 16,
        }}>
          <div style={{ fontWeight: 600, fontSize: 11, color: 'rgba(100,116,139,0.7)', marginBottom: 14, textTransform: 'uppercase', letterSpacing: '0.12em' }}>
            Organization
          </div>
          <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
            {[
              { label: 'Name',         value: orgName || 'My Organization' },
              { label: 'Type',         value: orgType || '—' },
              { label: 'Analysis Source', value: 'Uploaded Data' },
              { label: 'Carbon Source', value: 'Automatic — from resource data' },
            ].map(({ label, value }) => (
              <div key={label}>
                <div style={{ fontSize: 10, color: 'rgba(100,116,139,0.6)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 3 }}>
                  {label}
                </div>
                <div style={{ fontSize: 13, fontWeight: 600, color: '#e2e8f0' }}>{value}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Data Intelligence Panel (Step 3) */}
        <DataIntelligencePanel uploadState={uploadState} available={available} />

        {/* Gauges row — click to expand formula */}
        <div style={{
          background: 'rgba(3,9,20,0.72)',
          backdropFilter: 'blur(22px)',
          border: '1px solid rgba(255,255,255,0.07)',
          borderRadius: 18, padding: '22px',
          marginBottom: 16,
        }}>
          <div style={{ display: 'flex', gap: 16, justifyContent: 'space-around', flexWrap: 'wrap' }}>
            <MetricGauge value={readiness}   color={readinessColor} label="Analysis Readiness"   description="Click to expand formula" onClick={() => setCoverageExpanded(p => !p)} expanded={coverageExpanded} />
            <MetricGauge value={confidence}  color={confColor}      label="Analysis Confidence"  description="Confidence given available data" />
            <MetricGauge value={coverage}    color={covColor}       label="Data Coverage"        description="Weighted % of optimal datasets" />
          </div>

          {/* Expandable breakdown (Step 4) */}
          <AnimatePresence>
            {coverageExpanded && (
              <CoverageBreakdown
                available={available}
                coverage={coverage}
                confidence={confidence}
                readiness={readiness}
                WEIGHTS={WEIGHTS}
                PENALTIES={PENALTIES}
              />
            )}
          </AnimatePresence>
        </div>

        {/* Datasets found / missing */}
        <div style={{
          background: 'rgba(3,9,20,0.72)',
          backdropFilter: 'blur(22px)',
          border: '1px solid rgba(255,255,255,0.07)',
          borderRadius: 18, padding: '20px 22px',
          marginBottom: 24,
        }}>
          <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
            <div style={{ flex: 1, minWidth: 200 }}>
              <div style={{ fontSize: 10, fontWeight: 700, color: '#00ff88', textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: 12 }}>
                ✓ Datasets Found ({available.length})
              </div>
              {available.length === 0 ? (
                <div style={{ fontSize: 12, color: 'rgba(100,116,139,0.55)' }}>No datasets provided yet.</div>
              ) : available.map(id => {
                const meta = DATASET_LABELS[id] || { icon: '📊', label: id, color: '#94a3b8' }
                const isWaste = id === 'waste'
                const wasteDetail = isWaste && wasteItems.length > 0
                  ? wasteItems.slice(0, 4).map(r => r.type).join(', ') + (wasteItems.length > 4 ? ` +${wasteItems.length - 4} more` : '')
                  : null
                return (
                  <div key={id} style={{ marginBottom: 9 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 9 }}>
                      <div style={{
                        width: 28, height: 28, borderRadius: 8,
                        background: `${meta.color}14`, border: `1px solid ${meta.color}30`,
                        display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 13, flexShrink: 0,
                      }}>
                        {meta.icon}
                      </div>
                      <span style={{ fontSize: 12.5, color: '#e2e8f0', fontWeight: 600 }}>
                        {isWaste ? `Waste Inventory (${wasteItems.length} stream${wasteItems.length !== 1 ? 's' : ''})` : meta.label}
                      </span>
                      <span style={{ fontSize: 10, color: '#00ff88', marginLeft: 'auto', fontWeight: 700 }}>Will run ✓</span>
                    </div>
                    {wasteDetail && (
                      <div style={{ marginLeft: 37, marginTop: 3, fontSize: 10.5, color: 'rgba(148,163,184,0.55)', lineHeight: 1.5 }}>
                        {wasteDetail}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>

            <div style={{ width: 1, background: 'rgba(255,255,255,0.06)', flexShrink: 0 }} />

            <div style={{ flex: 1, minWidth: 200 }}>
              <div style={{ fontSize: 10, fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: 12 }}>
                ⊘ Missing Datasets ({missing.length})
              </div>
              {missing.length === 0 ? (
                <div style={{ fontSize: 12, color: '#00ff88' }}>All datasets provided!</div>
              ) : missing.map(id => {
                const meta = DATASET_LABELS[id] || { icon: '📊', label: id, color: '#64748b' }
                return (
                  <div key={id} style={{ display: 'flex', alignItems: 'center', gap: 9, marginBottom: 9, opacity: 0.55 }}>
                    <div style={{
                      width: 28, height: 28, borderRadius: 8,
                      background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 13, flexShrink: 0,
                      filter: 'grayscale(1)',
                    }}>
                      {meta.icon}
                    </div>
                    <span style={{ fontSize: 12.5, color: '#94a3b8' }}>{meta.label}</span>
                    <span style={{ fontSize: 10, color: '#64748b', marginLeft: 'auto', fontWeight: 600 }}>Skipped</span>
                  </div>
                )
              })}

              {missing.length > 0 && (
                <div style={{
                  marginTop: 10, padding: '8px 11px', borderRadius: 8,
                  background: 'rgba(100,116,139,0.06)',
                  border: '1px solid rgba(100,116,139,0.12)',
                  fontSize: 10.5, color: 'rgba(100,116,139,0.65)', lineHeight: 1.55,
                }}>
                  Missing datasets are skipped — not estimated or invented.
                  The report documents exactly which analyses ran and which were absent.
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Launch button */}
        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <motion.button
            onClick={onLaunch}
            disabled={launching || available.length === 0}
            whileHover={!launching ? { scale: 1.03, y: -2 } : {}}
            whileTap={!launching ? { scale: 0.98 } : {}}
            style={{
              display: 'inline-flex', alignItems: 'center', gap: 12,
              padding: '16px 44px',
              background: launching ? 'rgba(255,255,255,0.08)' : 'rgba(255,255,255,0.95)',
              color: launching ? 'rgba(255,255,255,0.55)' : '#0d1f12',
              border: 'none', borderRadius: 50,
              fontSize: 15, fontWeight: 700, letterSpacing: '0.01em',
              cursor: launching || available.length === 0 ? 'not-allowed' : 'pointer',
              fontFamily: 'inherit',
              boxShadow: launching ? 'none' : '0 6px 32px rgba(0,0,0,0.35)',
              transition: 'all 0.22s ease',
              opacity: available.length === 0 ? 0.5 : 1,
            }}
          >
            {launching ? (
              <>
                <span style={{
                  width: 16, height: 16,
                  border: '2.5px solid rgba(255,255,255,0.3)',
                  borderTopColor: 'rgba(255,255,255,0.8)',
                  borderRadius: '50%',
                  display: 'inline-block',
                  animation: 'mssSpin 0.75s linear infinite',
                }} />
                Launching Analysis…
              </>
            ) : (
              <>
                <span style={{
                  width: 30, height: 30, background: '#0d1f12', borderRadius: '50%',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', marginLeft: -6,
                }}>
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                    <path d="M2 6h8M7 3l3 3-3 3" stroke="white" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </span>
                Launch Analysis
              </>
            )}
          </motion.button>
        </div>
      </div>

      <style>{`
        @keyframes mssPulse { 0%, 100% { box-shadow: 0 0 4px #00ff88; } 50% { box-shadow: 0 0 12px #00ff88; } }
        @keyframes mssSpin  { to { transform: rotate(360deg); } }
      `}</style>
    </section>
  )
}
