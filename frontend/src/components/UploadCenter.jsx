import { useState, useRef, useCallback } from 'react'
import { validateUpload, BASE_URL } from '../api'

const CARD_STYLE = {
  background: 'rgba(3,9,20,0.72)',
  backdropFilter: 'blur(22px)',
  WebkitBackdropFilter: 'blur(22px)',
  border: '1px solid rgba(255,255,255,0.07)',
  borderRadius: 18,
  padding: '22px 22px 20px',
}

const ORG_TYPES = [
  'University / College',
  'Hotel / Hospitality',
  'Hospital / Healthcare',
  'Office / Corporate',
  'Industrial Facility',
  'Government Building',
  'Retail / Mall',
  'Research Institution',
  'Other',
]

const PERIOD_OPTIONS = [
  { value: 'hourly',  label: 'per Hour' },
  { value: 'daily',   label: 'per Day'  },
  { value: 'weekly',  label: 'per Week' },
  { value: 'monthly', label: 'per Month'},
]

const DATASETS = [
  {
    id: 'water',
    icon: '💧',
    label: 'Water Usage',
    color: '#00b4ff',
    description: 'Water consumption logs — hourly smart-meter exports unlock leak detection.',
    requiredCols: 'date / hour / usage_liters / location (optional)',
    fileExamples: [
      'Hourly smart-meter export (CSV / Excel)',
      'Daily meter readings from facilities team',
      'Building Management System (BMS) log export',
      'Monthly utility statement (Level 1 analysis only)',
    ],
    manualLabel: 'Water consumption (liters)',
    manualKey: 'manual_water_liters',
    manualUnit: 'liters',
    manualPlaceholder: 'e.g. 50000',
    hasPeriod: true,
  },
  {
    id: 'energy',
    icon: '⚡',
    label: 'Energy Usage',
    color: '#eab308',
    description: 'Electricity consumption by hour or zone — hourly data enables after-hours waste detection.',
    requiredCols: 'date / hour / usage_kwh / zone (optional)',
    fileExamples: [
      'Smart meter hourly export (CSV)',
      'Zonal electricity sub-meter logs',
      'Energy Management System (EMS) export',
      'Monthly electricity invoice data (Level 1 only)',
    ],
    manualLabel: 'Electricity consumption (kWh)',
    manualKey: 'manual_energy_kwh',
    manualUnit: 'kWh',
    manualPlaceholder: 'e.g. 8000',
    hasPeriod: true,
  },
  {
    id: 'fuel',
    icon: '⛽',
    label: 'Fuel Usage',
    color: '#f97316',
    description: 'Diesel, petrol, CNG, or LPG for carbon footprint calculation.',
    requiredCols: 'date / fuel_type / quantity_liters / location (optional)',
    fileExamples: [
      'DG set fuel log (diesel / petrol)',
      'Fleet fuel consumption register',
      'Monthly fuel purchase invoice',
      'Generator logbook export',
    ],
    manualLabel: 'Weekly fuel consumption (liters)',
    manualKey: 'manual_fuel_liters',
    manualUnit: 'liters / week',
    manualPlaceholder: 'e.g. 200',
    manualExtra: 'fuel_type',
  },
  {
    id: 'waste',
    icon: '♻️',
    label: 'Waste Inventory',
    color: '#00ff88',
    description: 'List all waste streams — the agent analyses each for recovery pathways and recovery value.',
    manualOnly: true,
  },
]

const WASTE_UNIT_OPTIONS = ['kg', 'g', 'tons']

const WASTE_SUGGESTIONS = [
  'Food Waste', 'Plastic Bottles', 'Paper & Cardboard', 'Metal / Aluminium',
  'E-waste', 'Glass', 'Wood Waste', 'Garden Waste', 'Textile Waste',
  'Biomedical Waste', 'Construction Debris', 'Rubber Tyres', 'Battery Waste',
  'Cooking Oil', 'Organic Waste', 'Sawdust', 'Cotton Waste',
]

// ── Analysis Quality Guide ──────────────────────────────────────────────────
const ANALYSIS_LEVELS = [
  {
    level: 1,
    name: 'Basic Assessment',
    badge: 'LOW–MEDIUM CONFIDENCE',
    color: '#f59e0b',
    borderColor: 'rgba(245,158,11,0.25)',
    bg: 'rgba(245,158,11,0.06)',
    data: ['Monthly utility bills', 'Manual total entry', 'Single-period aggregate'],
    features: ['Sustainability Score', 'Carbon estimation', 'Cost benchmarking', 'Efficiency comparison', 'General recommendations'],
    notAvailable: ['Anomaly detection', 'Leak detection', 'Predictive maintenance', 'Night-flow analysis'],
  },
  {
    level: 2,
    name: 'Operational Analysis',
    badge: 'MEDIUM–HIGH CONFIDENCE',
    color: '#00b4ff',
    borderColor: 'rgba(0,180,255,0.25)',
    bg: 'rgba(0,180,255,0.06)',
    data: ['Daily / weekly meter exports', 'Building-wise usage logs', 'Multi-week CSV files'],
    features: ['Trend analysis', 'Building comparison', 'Consumption hotspots', 'Targeted recommendations'],
    notAvailable: ['Anomaly detection', 'Leak detection', 'Night-flow analysis'],
  },
  {
    level: 3,
    name: 'Advanced AI Analysis',
    badge: 'HIGH–VERY HIGH CONFIDENCE',
    color: '#00ff88',
    borderColor: 'rgba(0,255,136,0.25)',
    bg: 'rgba(0,255,136,0.06)',
    data: ['Hourly smart-meter logs', 'IoT / BMS / SCADA data', 'EMS / SCADA time-series'],
    features: ['Anomaly detection', 'Leak detection', 'Night-flow analysis', 'Predictive insights', 'Full War Room intelligence'],
    notAvailable: [],
  },
]

function AnalysisQualityGuide() {
  return (
    <div style={{
      ...CARD_STYLE,
      marginBottom: 20,
      borderTop: '2px solid rgba(148,163,184,0.20)',
    }}>
      <div style={{ marginBottom: 16 }}>
        <div style={{ fontWeight: 800, fontSize: 15, color: '#fff', marginBottom: 4 }}>
          Analysis Quality Guide
        </div>
        <div style={{ fontSize: 11.5, color: 'rgba(148,163,184,0.65)', lineHeight: 1.6 }}>
          The system automatically detects what analysis level your data supports.
          Higher-resolution data unlocks more advanced modules. Manual entry always produces Level 1.
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 10 }}>
        {ANALYSIS_LEVELS.map(lv => (
          <div key={lv.level} style={{
            borderRadius: 12,
            background: lv.bg,
            border: `1px solid ${lv.borderColor}`,
            padding: '14px 14px 12px',
          }}>
            {/* Header */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
              <div style={{
                width: 22, height: 22, borderRadius: '50%', flexShrink: 0,
                background: lv.color,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 10, fontWeight: 900, color: '#000',
              }}>
                {lv.level}
              </div>
              <div>
                <div style={{ fontWeight: 700, fontSize: 12, color: '#fff' }}>{lv.name}</div>
                <div style={{ fontSize: 9, color: lv.color, fontWeight: 700, letterSpacing: '0.08em', marginTop: 1 }}>
                  {lv.badge}
                </div>
              </div>
            </div>

            {/* Required data */}
            <div style={{ marginBottom: 8 }}>
              <div style={{ fontSize: 9, fontWeight: 700, color: 'rgba(255,255,255,0.32)', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: 4 }}>
                Required Data
              </div>
              {lv.data.map((d, i) => (
                <div key={i} style={{ fontSize: 10.5, color: 'rgba(148,163,184,0.75)', marginBottom: 2, display: 'flex', gap: 5 }}>
                  <span style={{ color: lv.color, flexShrink: 0 }}>·</span>{d}
                </div>
              ))}
            </div>

            {/* Available features */}
            <div style={{ marginBottom: lv.notAvailable.length ? 8 : 0 }}>
              <div style={{ fontSize: 9, fontWeight: 700, color: 'rgba(255,255,255,0.32)', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: 4 }}>
                Available Features
              </div>
              {lv.features.map((f, i) => (
                <div key={i} style={{ fontSize: 10.5, color: '#94a3b8', marginBottom: 2, display: 'flex', gap: 5 }}>
                  <span style={{ color: '#00ff88', flexShrink: 0 }}>✓</span>{f}
                </div>
              ))}
            </div>

            {/* Unavailable */}
            {lv.notAvailable.length > 0 && (
              <div>
                <div style={{ fontSize: 9, fontWeight: 700, color: 'rgba(255,255,255,0.32)', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: 4 }}>
                  Not Available
                </div>
                {lv.notAvailable.map((f, i) => (
                  <div key={i} style={{ fontSize: 10.5, color: 'rgba(100,116,139,0.6)', marginBottom: 2, display: 'flex', gap: 5 }}>
                    <span style={{ flexShrink: 0 }}>–</span>{f}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

const COMING_SOON = [
  { icon: '📄', label: 'PDF Reports' },
  { icon: '🖼️', label: 'Images / Photos' },
  { icon: '📡', label: 'IoT API' },
  { icon: '🏢', label: 'ERP Integration' },
  { icon: '🏗️', label: 'BMS Systems' },
]

// ── Drag-drop zone ──────────────────────────────────────────────────────────
function DropZone({ datasetId: _datasetId, color, onFile, validating, validationInfo, error }) {
  const [dragging, setDragging] = useState(false)
  const inputRef = useRef(null)

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) onFile(file)
  }, [onFile])

  const handleChange = (e) => {
    const file = e.target.files[0]
    if (file) onFile(file)
    e.target.value = ''
  }

  const borderColor = error
    ? 'rgba(239,68,68,0.50)'
    : validationInfo?.valid
    ? `${color}60`
    : dragging
    ? `${color}88`
    : 'rgba(255,255,255,0.09)'

  const bg = error
    ? 'rgba(239,68,68,0.06)'
    : validationInfo?.valid
    ? `${color}08`
    : dragging
    ? `${color}0c`
    : 'rgba(255,255,255,0.02)'

  return (
    <div>
      <div
        onDragOver={e => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        style={{
          border: `1.5px dashed ${borderColor}`,
          borderRadius: 12,
          background: bg,
          padding: '20px 16px',
          textAlign: 'center',
          cursor: 'pointer',
          transition: 'all 0.2s ease',
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".csv,.xlsx,.xls"
          onChange={handleChange}
          style={{ display: 'none' }}
        />
        {validating ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, color: color }}>
            <span style={{ width: 12, height: 12, border: `2px solid ${color}`, borderTopColor: 'transparent', borderRadius: '50%', display: 'inline-block', animation: 'upSpin 0.75s linear infinite' }} />
            <span style={{ fontSize: 12 }}>Validating…</span>
          </div>
        ) : validationInfo?.valid ? (
          <div>
            <span style={{ fontSize: 13, color, fontWeight: 700 }}>✓ {validationInfo.filename}</span>
            <div style={{ fontSize: 11, color: 'rgba(148,163,184,0.65)', marginTop: 4 }}>
              {validationInfo.record_count} records · {validationInfo.date_range || '—'}
            </div>
          </div>
        ) : (
          <>
            <div style={{ fontSize: 22, marginBottom: 6 }}>📁</div>
            <div style={{ fontSize: 12.5, color: 'rgba(203,213,225,0.65)', fontWeight: 500 }}>
              Drop CSV / Excel here
            </div>
            <div style={{ fontSize: 11, color: 'rgba(100,116,139,0.6)', marginTop: 3 }}>
              or{' '}
              <span style={{ color, fontWeight: 600, textDecoration: 'underline' }}>browse files</span>
            </div>
          </>
        )}
      </div>

      {/* Validation errors */}
      {error && (
        <div style={{ marginTop: 8, fontSize: 11, color: '#f87171', lineHeight: 1.55 }}>
          ⚠ {error}
        </div>
      )}

      {/* Warnings */}
      {validationInfo?.warnings?.length > 0 && (
        <div style={{ marginTop: 6, fontSize: 10.5, color: '#fbbf24', lineHeight: 1.55 }}>
          {validationInfo.warnings.map((w, i) => <div key={i}>⚡ {w}</div>)}
        </div>
      )}

      {/* Detected info */}
      {validationInfo?.valid && (
        <div style={{ marginTop: 8, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {validationInfo.buildings_detected && (
            <span style={{
              padding: '2px 8px', borderRadius: 50,
              background: `${color}12`, border: `1px solid ${color}30`,
              fontSize: 10, color, fontWeight: 600,
            }}>
              {validationInfo.buildings_detected.slice(0, 3).join(', ')}
              {validationInfo.buildings_detected.length > 3 && ` +${validationInfo.buildings_detected.length - 3}`}
            </span>
          )}
          {validationInfo.zones_detected && (
            <span style={{
              padding: '2px 8px', borderRadius: 50,
              background: `${color}12`, border: `1px solid ${color}30`,
              fontSize: 10, color, fontWeight: 600,
            }}>
              {validationInfo.zones_detected.slice(0, 3).join(', ')}
            </span>
          )}
          {validationInfo.anomaly_pre_labeled === false && (
            <span style={{
              padding: '2px 8px', borderRadius: 50,
              background: 'rgba(251,191,36,0.10)', border: '1px solid rgba(251,191,36,0.25)',
              fontSize: 10, color: '#fbbf24', fontWeight: 600,
            }}>
              Auto anomaly detection
            </span>
          )}
        </div>
      )}
    </div>
  )
}

// ── Single dataset card ─────────────────────────────────────────────────────
function DatasetCard({ ds, state, onFile, onManualChange, onFuelTypeChange, onPeriodChange }) {
  const [showManual, setShowManual] = useState(ds.manualOnly || false)

  return (
    <div style={{
      ...CARD_STYLE,
      borderTop: `2px solid ${ds.color}44`,
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
        <div style={{
          width: 40, height: 40, borderRadius: 11, flexShrink: 0,
          background: `radial-gradient(circle at 35% 32%, ${ds.color}22, rgba(3,9,20,0.9))`,
          border: `1px solid ${ds.color}33`,
          display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18,
        }}>
          {ds.icon}
        </div>
        <div>
          <div style={{ fontWeight: 700, fontSize: 14, color: '#fff' }}>{ds.label}</div>
          <div style={{ fontSize: 11, color: 'rgba(148,163,184,0.65)', marginTop: 1 }}>
            {ds.description}
          </div>
        </div>

        {/* Status badge */}
        {state.file?.valid && (
          <div style={{
            marginLeft: 'auto', flexShrink: 0,
            padding: '3px 9px', borderRadius: 50,
            background: `${ds.color}12`, border: `1px solid ${ds.color}35`,
            fontSize: 9.5, fontWeight: 700, color: ds.color, letterSpacing: '0.09em', textTransform: 'uppercase',
          }}>
            Ready
          </div>
        )}
        {((state.manual && parseFloat(state.manual) > 0) || (state.items && state.items.some(r => r.type && parseFloat(r.qty) > 0))) && !state.file?.valid && (
          <div style={{
            marginLeft: 'auto', flexShrink: 0,
            padding: '3px 9px', borderRadius: 50,
            background: 'rgba(251,191,36,0.10)', border: '1px solid rgba(251,191,36,0.25)',
            fontSize: 9.5, fontWeight: 700, color: '#fbbf24', letterSpacing: '0.09em', textTransform: 'uppercase',
          }}>
            Manual
          </div>
        )}
      </div>

      {/* For waste: multi-row inventory table */}
      {ds.manualOnly ? (
        <WasteInventoryTable onManualChange={onManualChange} color={ds.color} state={state} />
      ) : (
        <>
          {/* Toggle: file vs manual */}
          <div style={{ display: 'flex', gap: 6, marginBottom: 14 }}>
            {['file', 'manual'].map(mode => (
              <button
                key={mode}
                onClick={() => setShowManual(mode === 'manual')}
                style={{
                  flex: 1,
                  padding: '7px 0',
                  borderRadius: 8,
                  border: `1px solid ${showManual === (mode === 'manual')
                    ? `${ds.color}55`
                    : 'rgba(255,255,255,0.07)'}`,
                  background: showManual === (mode === 'manual')
                    ? `${ds.color}10`
                    : 'rgba(255,255,255,0.02)',
                  color: showManual === (mode === 'manual') ? ds.color : 'rgba(148,163,184,0.65)',
                  fontSize: 11, fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit',
                  transition: 'all 0.18s ease',
                }}
              >
                {mode === 'file' ? '📁 Upload File' : '✏️ Manual Entry'}
              </button>
            ))}
          </div>

          {!showManual ? (
            <>
              {ds.fileExamples && (
                <div style={{ marginBottom: 10 }}>
                  <div style={{ fontSize: 9.5, fontWeight: 700, color: 'rgba(255,255,255,0.28)', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: 5 }}>
                    Accepted file types
                  </div>
                  {ds.fileExamples.map((ex, i) => (
                    <div key={i} style={{ fontSize: 10.5, color: 'rgba(148,163,184,0.60)', marginBottom: 2, display: 'flex', gap: 5 }}>
                      <span style={{ color: ds.color, flexShrink: 0, opacity: 0.7 }}>›</span>{ex}
                    </div>
                  ))}
                  <div style={{ fontSize: 10, color: 'rgba(100,116,139,0.55)', fontFamily: 'monospace', marginTop: 6 }}>
                    Columns: {ds.requiredCols}
                  </div>
                </div>
              )}
              <DropZone
                datasetId={ds.id}
                color={ds.color}
                onFile={onFile}
                validating={state.validating}
                validationInfo={state.file}
                error={state.fileError}
              />
              {/* Demo data download link */}
              <div style={{ marginTop: 10, textAlign: 'right' }}>
                <a
                  href={`${BASE_URL}/demo-data/${ds.id}`}
                  download
                  style={{ fontSize: 10.5, color: ds.color, opacity: 0.7, textDecoration: 'none', fontWeight: 600 }}
                  onMouseEnter={e => e.currentTarget.style.opacity = 1}
                  onMouseLeave={e => e.currentTarget.style.opacity = 0.7}
                >
                  ↓ Download template / demo data
                </a>
              </div>
            </>
          ) : (
            <div>
              <div style={{
                marginBottom: 10, padding: '7px 10px', borderRadius: 8,
                background: 'rgba(245,158,11,0.07)', border: '1px solid rgba(245,158,11,0.22)',
                display: 'flex', alignItems: 'flex-start', gap: 7,
              }}>
                <span style={{ fontSize: 12, flexShrink: 0, marginTop: 1 }}>⚡</span>
                <div>
                  <span style={{ fontSize: 10.5, fontWeight: 700, color: '#f59e0b' }}>Quick Sustainability Assessment — </span>
                  <span style={{ fontSize: 10.5, color: 'rgba(148,163,184,0.65)' }}>
                    Manual entry produces Level 1 analysis only. Anomaly detection, leak detection, and predictive maintenance are not available without operational logs.
                  </span>
                </div>
              </div>
              <label style={{ display: 'block', fontSize: 11.5, color: 'rgba(148,163,184,0.75)', marginBottom: 8 }}>
                {ds.manualLabel}
              </label>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <input
                  type="number"
                  min="0"
                  placeholder={ds.manualPlaceholder}
                  value={state.manual || ''}
                  onChange={e => onManualChange(e.target.value)}
                  style={{
                    flex: 1, padding: '9px 12px', borderRadius: 9,
                    background: 'rgba(255,255,255,0.04)',
                    border: '1px solid rgba(255,255,255,0.10)',
                    color: '#fff', fontSize: 13, fontFamily: 'inherit',
                    outline: 'none',
                  }}
                  onFocus={e => e.target.style.borderColor = ds.color + '66'}
                  onBlur={e => e.target.style.borderColor = 'rgba(255,255,255,0.10)'}
                />
                <span style={{ fontSize: 11, color: 'rgba(100,116,139,0.7)', whiteSpace: 'nowrap' }}>
                  {ds.manualUnit}
                </span>
              </div>

              {/* Period selector for water / energy */}
              {ds.hasPeriod && (
                <div style={{ marginTop: 10 }}>
                  <label style={{ display: 'block', fontSize: 11, color: 'rgba(100,116,139,0.6)', marginBottom: 6 }}>
                    Time period
                  </label>
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    {PERIOD_OPTIONS.map(opt => {
                      const active = (state.period || 'weekly') === opt.value
                      return (
                        <button
                          key={opt.value}
                          onClick={() => onPeriodChange(opt.value)}
                          style={{
                            padding: '5px 11px', borderRadius: 50,
                            border: `1px solid ${active ? ds.color + '55' : 'rgba(255,255,255,0.07)'}`,
                            background: active ? `${ds.color}10` : 'rgba(255,255,255,0.02)',
                            color: active ? ds.color : 'rgba(148,163,184,0.5)',
                            fontSize: 10.5, fontWeight: active ? 700 : 500,
                            cursor: 'pointer', fontFamily: 'inherit',
                            transition: 'all 0.15s ease',
                          }}
                        >
                          {opt.label}
                        </button>
                      )
                    })}
                  </div>
                </div>
              )}

              {/* Fuel type selector */}
              {ds.id === 'fuel' && (
                <div style={{ marginTop: 10 }}>
                  <label style={{ display: 'block', fontSize: 11.5, color: 'rgba(148,163,184,0.75)', marginBottom: 6 }}>
                    Fuel type
                  </label>
                  <select
                    value={state.fuelType || 'diesel'}
                    onChange={e => onFuelTypeChange(e.target.value)}
                    style={{
                      width: '100%', padding: '9px 12px', borderRadius: 9,
                      background: 'rgba(255,255,255,0.04)',
                      border: '1px solid rgba(255,255,255,0.10)',
                      color: '#fff', fontSize: 12, fontFamily: 'inherit',
                      outline: 'none',
                    }}
                  >
                    {['diesel', 'petrol', 'cng', 'lpg', 'natural gas'].map(t => (
                      <option key={t} value={t} style={{ background: '#0a1220' }}>
                        {t.charAt(0).toUpperCase() + t.slice(1)}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}

let _wasteIdCounter = 1

function WasteInventoryTable({ onManualChange, color, state }) {
  const items = state.items || []

  const addRow = () => {
    onManualChange({ key: 'items', val: [...items, { id: _wasteIdCounter++, type: '', qty: '', unit: 'kg' }] })
  }

  const updateRow = (id, field, val) => {
    onManualChange({ key: 'items', val: items.map(r => r.id === id ? { ...r, [field]: val } : r) })
  }

  const removeRow = (id) => {
    onManualChange({ key: 'items', val: items.filter(r => r.id !== id) })
  }

  const inputStyle = {
    padding: '7px 10px', borderRadius: 8,
    background: 'rgba(255,255,255,0.04)',
    border: '1px solid rgba(255,255,255,0.09)',
    color: '#fff', fontSize: 12, fontFamily: 'inherit',
    outline: 'none', width: '100%', boxSizing: 'border-box',
  }

  const hasRows = items.length > 0

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {/* Column headers */}
      {hasRows && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 90px 64px 28px', gap: 8, padding: '0 2px' }}>
          {['Waste Type', 'Quantity', 'Unit', ''].map((h, i) => (
            <span key={i} style={{ fontSize: 9.5, fontWeight: 700, color: 'rgba(100,116,139,0.55)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
              {h}
            </span>
          ))}
        </div>
      )}

      {/* Rows */}
      {items.map(row => (
        <div key={row.id} style={{ display: 'grid', gridTemplateColumns: '1fr 90px 64px 28px', gap: 8, alignItems: 'center' }}>
          <input
            list={`waste-suggestions-${row.id}`}
            type="text"
            placeholder='e.g. "food waste"'
            value={row.type}
            onChange={e => updateRow(row.id, 'type', e.target.value)}
            style={inputStyle}
            onFocus={e => e.target.style.borderColor = color + '66'}
            onBlur={e => e.target.style.borderColor = 'rgba(255,255,255,0.09)'}
          />
          <datalist id={`waste-suggestions-${row.id}`}>
            {WASTE_SUGGESTIONS.map(s => <option key={s} value={s} />)}
          </datalist>
          <input
            type="number"
            min="0"
            placeholder="e.g. 50"
            value={row.qty}
            onChange={e => updateRow(row.id, 'qty', e.target.value)}
            style={inputStyle}
            onFocus={e => e.target.style.borderColor = color + '66'}
            onBlur={e => e.target.style.borderColor = 'rgba(255,255,255,0.09)'}
          />
          <select
            value={row.unit}
            onChange={e => updateRow(row.id, 'unit', e.target.value)}
            style={{ ...inputStyle, padding: '7px 6px', cursor: 'pointer' }}
          >
            {WASTE_UNIT_OPTIONS.map(u => (
              <option key={u} value={u} style={{ background: '#0a1220' }}>{u}</option>
            ))}
          </select>
          <button
            onClick={() => removeRow(row.id)}
            style={{
              width: 26, height: 26, borderRadius: '50%', border: '1px solid rgba(239,68,68,0.30)',
              background: 'rgba(239,68,68,0.08)', color: '#ef4444',
              fontSize: 14, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontFamily: 'inherit', flexShrink: 0,
            }}
            title="Remove row"
          >×</button>
        </div>
      ))}

      {/* Empty state */}
      {!hasRows && (
        <div style={{
          padding: '16px 14px', borderRadius: 10, textAlign: 'center',
          background: 'rgba(0,255,136,0.03)', border: '1.5px dashed rgba(0,255,136,0.15)',
        }}>
          <div style={{ fontSize: 20, marginBottom: 6 }}>♻️</div>
          <div style={{ fontSize: 11.5, color: 'rgba(100,116,139,0.7)', lineHeight: 1.55 }}>
            No waste streams added yet.<br />
            Click <strong style={{ color }}>+ Add Waste Stream</strong> to begin.
          </div>
        </div>
      )}

      {/* Add row button */}
      <button
        onClick={addRow}
        style={{
          display: 'flex', alignItems: 'center', gap: 6,
          padding: '8px 14px', borderRadius: 8,
          background: `${color}0a`, border: `1px solid ${color}28`,
          color, fontSize: 11.5, fontWeight: 600, cursor: 'pointer',
          fontFamily: 'inherit', transition: 'all 0.18s ease', alignSelf: 'flex-start',
        }}
        onMouseEnter={e => { e.currentTarget.style.background = `${color}14`; e.currentTarget.style.borderColor = `${color}44` }}
        onMouseLeave={e => { e.currentTarget.style.background = `${color}0a`; e.currentTarget.style.borderColor = `${color}28` }}
      >
        <span style={{ fontSize: 14, lineHeight: 1 }}>+</span>
        Add Waste Stream
      </button>

      {hasRows && (
        <div style={{ fontSize: 10.5, color: 'rgba(100,116,139,0.55)', lineHeight: 1.5 }}>
          The Waste-to-Wealth agent analyses each stream against a 97-material knowledge base and estimates recovery value, CO₂ savings, and compliance guidance per pathway.
        </div>
      )}
    </div>
  )
}

// ── Main component ──────────────────────────────────────────────────────────
export default function UploadCenter({ onProceed, onBack }) {
  const [orgName, setOrgName] = useState('')
  const [orgType, setOrgType] = useState(ORG_TYPES[0])

  // Per-dataset state
  const [datasetStates, setDatasetStates] = useState({
    water:  { file: null, fileRaw: null, fileError: null, validating: false, manual: '', period: 'weekly' },
    energy: { file: null, fileRaw: null, fileError: null, validating: false, manual: '', period: 'weekly' },
    fuel:   { file: null, fileRaw: null, fileError: null, validating: false, manual: '', fuelType: 'diesel' },
    waste:  { items: [] },
  })

  const updateDs = (id, patch) => {
    setDatasetStates(prev => ({ ...prev, [id]: { ...prev[id], ...patch } }))
  }

  const handleFile = async (dsId, file) => {
    // Basic client-side check
    const ext = file.name.split('.').pop().toLowerCase()
    if (!['csv', 'xlsx', 'xls'].includes(ext)) {
      updateDs(dsId, { fileError: 'Only CSV and Excel (.xlsx / .xls) files are supported.' })
      return
    }
    if (file.size > 20 * 1024 * 1024) {
      updateDs(dsId, { fileError: 'File size exceeds 20 MB.' })
      return
    }
    updateDs(dsId, { validating: true, fileError: null, fileRaw: file })

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('dataset_type', dsId)
      const res = await validateUpload(formData)
      const info = res.data
      if (!info.valid) {
        updateDs(dsId, { validating: false, fileError: (info.errors || []).join(' | '), file: null })
      } else {
        updateDs(dsId, { validating: false, file: info, fileError: null })
      }
    } catch (err) {
      const detail = err.response?.data?.detail || err.message || 'Validation failed.'
      updateDs(dsId, { validating: false, fileError: detail, file: null })
    }
  }

  const handleManual = (dsId, val) => updateDs(dsId, { manual: val })
  const handlePeriod = (dsId, val) => updateDs(dsId, { period: val })
  const handleFuelType = (val) => updateDs('fuel', { fuelType: val })
  const handleWasteManual = ({ key, val }) => updateDs('waste', { [key]: val })

  const wasteHasData = (datasetStates.waste.items || []).some(
    r => r.type && parseFloat(r.qty) > 0
  )

  // Check if anything has been entered
  const anyData = (
    datasetStates.water.file?.valid  || parseFloat(datasetStates.water.manual)  > 0 ||
    datasetStates.energy.file?.valid || parseFloat(datasetStates.energy.manual) > 0 ||
    datasetStates.fuel.file?.valid   || parseFloat(datasetStates.fuel.manual)   > 0 ||
    wasteHasData
  )

  const handleProceed = () => {
    onProceed({
      orgName:  orgName || 'My Organization',
      orgType,
      water:    datasetStates.water,
      energy:   datasetStates.energy,
      fuel:     datasetStates.fuel,
      waste:    datasetStates.waste,
    })
  }

  return (
    <section style={{
      width: '100%',
      minHeight: '100vh',
      paddingTop: 80,
      paddingBottom: 80,
      background: 'linear-gradient(180deg, rgba(0,10,20,1) 0%, rgba(2,6,18,1) 100%)',
      position: 'relative',
    }}>
      {/* Grid background */}
      <div style={{
        position: 'absolute', inset: 0, zIndex: 0, pointerEvents: 'none',
        backgroundImage: [
          'linear-gradient(rgba(0,229,255,0.012) 1px, transparent 1px)',
          'linear-gradient(90deg, rgba(0,229,255,0.012) 1px, transparent 1px)',
        ].join(','),
        backgroundSize: '52px 52px',
      }} />

      <div style={{ position: 'relative', zIndex: 1, maxWidth: 900, margin: '0 auto', padding: '0 24px' }}>

        {/* Back + title row */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 36 }}>
          <button
            onClick={onBack}
            style={{
              display: 'flex', alignItems: 'center', gap: 6,
              padding: '7px 14px', borderRadius: 50,
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.10)',
              color: 'rgba(255,255,255,0.65)', fontSize: 12, fontWeight: 600,
              cursor: 'pointer', fontFamily: 'inherit',
              transition: 'all 0.18s ease',
            }}
            onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.09)'}
            onMouseLeave={e => e.currentTarget.style.background = 'rgba(255,255,255,0.05)'}
          >
            ← Back
          </button>
          <div>
            <h1 style={{ fontSize: 'clamp(22px, 3vw, 32px)', fontWeight: 900, color: '#fff', margin: 0 }}>
              Upload Your Data
            </h1>
            <p style={{ fontSize: 12, color: 'rgba(100,116,139,0.7)', margin: '4px 0 0', lineHeight: 1.5 }}>
              No dataset is mandatory — the platform analyses whatever you provide.
            </p>
          </div>
        </div>

        {/* Org info */}
        <div style={{ ...CARD_STYLE, marginBottom: 20, borderTop: '2px solid rgba(0,229,255,0.25)' }}>
          <div style={{ fontWeight: 700, fontSize: 14, color: '#fff', marginBottom: 16 }}>
            Organization Details
          </div>
          <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
            <div style={{ flex: '2 1 200px' }}>
              <label style={{ display: 'block', fontSize: 11.5, color: 'rgba(148,163,184,0.75)', marginBottom: 6 }}>
                Organization name
              </label>
              <input
                type="text"
                placeholder="e.g. St. Joseph's University"
                value={orgName}
                onChange={e => setOrgName(e.target.value)}
                style={{
                  width: '100%', padding: '9px 12px', borderRadius: 9, boxSizing: 'border-box',
                  background: 'rgba(255,255,255,0.04)',
                  border: '1px solid rgba(255,255,255,0.10)',
                  color: '#fff', fontSize: 13, fontFamily: 'inherit', outline: 'none',
                }}
                onFocus={e => e.target.style.borderColor = 'rgba(0,229,255,0.45)'}
                onBlur={e => e.target.style.borderColor = 'rgba(255,255,255,0.10)'}
              />
            </div>
            <div style={{ flex: '1 1 160px' }}>
              <label style={{ display: 'block', fontSize: 11.5, color: 'rgba(148,163,184,0.75)', marginBottom: 6 }}>
                Organization type
              </label>
              <select
                value={orgType}
                onChange={e => setOrgType(e.target.value)}
                style={{
                  width: '100%', padding: '9px 12px', borderRadius: 9,
                  background: 'rgba(255,255,255,0.04)',
                  border: '1px solid rgba(255,255,255,0.10)',
                  color: '#fff', fontSize: 12, fontFamily: 'inherit', outline: 'none',
                }}
              >
                {ORG_TYPES.map(t => (
                  <option key={t} value={t} style={{ background: '#0a1220' }}>{t}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Analysis Quality Guide */}
        <AnalysisQualityGuide />

        {/* Carbon auto-notice */}
        <div style={{
          marginBottom: 20,
          padding: '10px 16px',
          borderRadius: 10,
          background: 'rgba(0,255,136,0.05)',
          border: '1px solid rgba(0,255,136,0.16)',
          display: 'flex', alignItems: 'flex-start', gap: 10,
        }}>
          <span style={{ fontSize: 14, flexShrink: 0 }}>🌿</span>
          <div>
            <span style={{ fontSize: 11.5, fontWeight: 700, color: '#00cc77' }}>Carbon is Automatic — </span>
            <span style={{ fontSize: 11.5, color: 'rgba(148,163,184,0.75)' }}>
              You never upload carbon data. CO₂ is calculated deterministically from electricity, fuel, water, and waste data using certified emission factors. No AI is used in carbon calculations.
            </span>
          </div>
        </div>

        {/* Dataset cards — 2 column grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: 16, marginBottom: 24 }}>
          {DATASETS.map(ds => (
            <DatasetCard
              key={ds.id}
              ds={ds}
              state={datasetStates[ds.id]}
              onFile={file => handleFile(ds.id, file)}
              onManualChange={ds.manualOnly
                ? handleWasteManual
                : val => handleManual(ds.id, val)
              }
              onFuelTypeChange={handleFuelType}
              onPeriodChange={val => handlePeriod(ds.id, val)}
            />
          ))}
        </div>

        {/* Coming Soon */}
        <div style={{ ...CARD_STYLE, marginBottom: 28 }}>
          <div style={{ fontWeight: 600, fontSize: 12, color: 'rgba(100,116,139,0.7)', marginBottom: 12, textTransform: 'uppercase', letterSpacing: '0.12em' }}>
            Coming Soon — Future Input Sources
          </div>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            {COMING_SOON.map(cs => (
              <div key={cs.label} style={{
                display: 'flex', alignItems: 'center', gap: 7,
                padding: '6px 12px', borderRadius: 50,
                background: 'rgba(255,255,255,0.03)',
                border: '1px solid rgba(255,255,255,0.07)',
              }}>
                <span style={{ fontSize: 13 }}>{cs.icon}</span>
                <span style={{ fontSize: 11, color: 'rgba(100,116,139,0.65)', fontWeight: 500 }}>{cs.label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Launch button */}
        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <button
            onClick={handleProceed}
            disabled={!anyData}
            style={{
              display: 'inline-flex', alignItems: 'center', gap: 10,
              padding: '14px 36px',
              background: anyData ? 'rgba(0,255,136,0.12)' : 'rgba(255,255,255,0.04)',
              border: `1.5px solid ${anyData ? 'rgba(0,255,136,0.40)' : 'rgba(255,255,255,0.08)'}`,
              borderRadius: 50,
              color: anyData ? '#00ff88' : 'rgba(100,116,139,0.5)',
              fontSize: 14, fontWeight: 700, letterSpacing: '0.01em',
              cursor: anyData ? 'pointer' : 'not-allowed',
              fontFamily: 'inherit',
              transition: 'all 0.22s ease',
            }}
            onMouseEnter={e => {
              if (anyData) {
                e.currentTarget.style.background = 'rgba(0,255,136,0.18)'
                e.currentTarget.style.borderColor = 'rgba(0,255,136,0.60)'
                e.currentTarget.style.transform = 'translateY(-1px)'
              }
            }}
            onMouseLeave={e => {
              e.currentTarget.style.background = anyData ? 'rgba(0,255,136,0.12)' : 'rgba(255,255,255,0.04)'
              e.currentTarget.style.borderColor = anyData ? 'rgba(0,255,136,0.40)' : 'rgba(255,255,255,0.08)'
              e.currentTarget.style.transform = ''
            }}
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M2 7h10M8 4l3 3-3 3" stroke="currentColor" strokeWidth="1.6"
                strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            {anyData ? 'Review Mission Summary →' : 'Add at least one dataset above'}
          </button>
        </div>
      </div>

      <style>{`
        @keyframes upSpin { to { transform: rotate(360deg); } }
      `}</style>
    </section>
  )
}
