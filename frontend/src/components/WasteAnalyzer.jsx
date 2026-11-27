import RecoveryPathwayGrid from './RecoveryPathwayGrid'
import { useState, useEffect, useRef } from 'react'
import { signIn } from '../api'
import { Trash2 } from 'lucide-react'

function BatchResultPanel({ batchResult }) {
  if (!batchResult || batchResult.status === 'no_waste') {
    return (
      <section className="px-6 py-16 max-w-7xl mx-auto" id="waste">
        <div className="mb-8">
          <h2 className="text-3xl font-black text-white mb-2">
            Waste-to-<span className="text-gradient-green">Wealth</span>
          </h2>
          <p className="text-slate-400 text-sm max-w-2xl">
            Recovery pathway analysis — no waste inventory was submitted.
          </p>
        </div>
        <div className="glass-card p-10 flex flex-col items-center justify-center text-center"
          style={{ border: '1px solid rgba(245,158,11,0.18)' }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>♻️</div>
          <p className="text-white font-bold text-base mb-2">No Waste Inventory Submitted</p>
          <p className="text-slate-400 text-sm leading-relaxed max-w-md">
            Upload or enter your waste streams in the Upload Center to unlock Waste-to-Wealth analysis —
            recovery pathways, estimated value, circularity scoring, and compliance guidance.
          </p>
          <div className="mt-4 px-4 py-2 rounded-lg text-xs" style={{ background: 'rgba(245,158,11,0.07)', border: '1px solid rgba(245,158,11,0.18)', color: '#f59e0b' }}>
            Use the waste inventory table in Upload Center to add waste streams.
          </div>
        </div>
      </section>
    )
  }

  const comp  = batchResult.composition || {}
  const items = batchResult.items       || []
  const plannedItems = items.filter(item => item.recovery_intelligence?.pathways?.length)


  const compBars = [
    { label: 'Organic',      pct: comp.organic_pct      || 0, color: '#22c55e' },
    { label: 'Paper',        pct: comp.paper_pct        || 0, color: '#a3e635' },
    { label: 'Plastic',      pct: comp.plastic_pct      || 0, color: '#3b82f6' },
    { label: 'Metal',        pct: comp.metal_pct        || 0, color: '#94a3b8' },
    { label: 'Glass',        pct: comp.glass_pct        || 0, color: '#67e8f9' },
    { label: 'Construction', pct: comp.construction_pct || 0, color: '#d97706' },
    { label: 'Hazardous',    pct: comp.hazardous_pct    || 0, color: '#ef4444' },
    { label: 'Other',        pct: comp.other_pct        || 0, color: '#64748b' },
  ].filter(b => b.pct > 0)

  return (
    <section className="px-6 py-16 max-w-7xl mx-auto" id="waste">
      <div className="mb-8">
        <h2 className="text-3xl font-black text-white mb-2">
          Waste-to-<span className="text-gradient-green">Wealth</span>
        </h2>
        <p className="text-slate-400 text-sm max-w-2xl">
          Agent analysis of {batchResult.total_items} waste stream{batchResult.total_items !== 1 ? 's' : ''} — recovery pathways, estimated value, and circularity scoring.
        </p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {[
          { label: 'Total Inventory',  value: `${batchResult.total_kg.toLocaleString()} kg`,  color: '#00ff88' },
          { label: 'Streams Analysed', value: `${batchResult.analyzed_items} / ${batchResult.total_items}`, color: '#00e5ff' },
          { label: 'Est. Recovery',    value: batchResult.total_recovery_max_inr == null ? "Unavailable" : `₹${Math.round(batchResult.total_recovery_max_inr).toLocaleString()}`, color: '#eab308', sub: 'max estimate' },
          { label: 'Circularity Score', value: batchResult.circularity_score == null ? "Unavailable" : `${batchResult.circularity_score}/100`, color: batchResult.circularity_score >= 70 ? '#00ff88' : batchResult.circularity_score >= 50 ? '#eab308' : '#ef4444' },
        ].map(c => (
          <div key={c.label} className="glass-card p-4 text-center">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">{c.label}</p>
            <p className="text-xl font-black" style={{ color: c.color }}>{c.value}</p>
            {c.sub && <p className="text-xs text-slate-600 mt-1">{c.sub}</p>}
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Composition */}
        {compBars.length > 0 && (
          <div className="glass-card p-5">
            <h3 className="text-sm font-bold text-cyan-400 uppercase tracking-wider mb-4">Waste Composition</h3>
            <div className="space-y-3">
              {compBars.map(b => (
                <div key={b.label}>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-xs text-slate-400">{b.label}</span>
                    <span className="text-sm font-bold" style={{ color: b.color }}>{b.pct}%</span>
                  </div>
                  <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                    <div className="h-full rounded-full" style={{ width: `${b.pct}%`, background: b.color, transition: 'width 1s ease' }} />
                  </div>
                </div>
              ))}
            </div>
            {batchResult.top_opportunity && (
              <div className="mt-4 p-3 rounded-lg" style={{ background: 'rgba(0,255,136,0.06)', border: '1px solid rgba(0,255,136,0.15)' }}>
                <p className="text-xs text-slate-500 mb-1">Highest-Value Opportunity</p>
                <p className="text-sm font-bold text-green-400 capitalize">{batchResult.top_opportunity}</p>
                <p className="text-xs text-slate-500 mt-0.5">{batchResult.top_opportunity_pathway} · est. ₹{Math.round(batchResult.top_opportunity_value_max_inr).toLocaleString()} max</p>
              </div>
            )}
          </div>
        )}

        {/* Per-stream table */}
        <div className="glass-card p-5">
          <h3 className="text-sm font-bold text-cyan-400 uppercase tracking-wider mb-4">Stream Breakdown</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr style={{ color: '#475569' }}>
                  <th className="pb-2 pr-3 text-left font-semibold uppercase tracking-wider">Material</th>
                  <th className="pb-2 pr-3 text-left font-semibold uppercase tracking-wider">Qty (kg)</th>
                  <th className="pb-2 pr-3 text-left font-semibold uppercase tracking-wider hidden sm:table-cell">Pathway</th>
                  <th className="pb-2 pr-3 text-left font-semibold uppercase tracking-wider">Est. Value</th>
                  <th className="pb-2 text-left font-semibold uppercase tracking-wider">Status</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item, i) => {
                  const isHazard  = item.hazard_warning
                  const isUnknown = item.status === 'unknown_material'
                  const maxVal    = item.estimated_recovery?.max_inr || 0
                  return (
                    <tr key={i} className="border-t" style={{ borderColor: 'rgba(255,255,255,0.04)' }}>
                      <td className="py-2.5 pr-3 font-medium text-slate-200 capitalize">{item.waste_type || '—'}</td>
                      <td className="py-2.5 pr-3 text-slate-400">{(item.quantity_kg || 0).toLocaleString()}</td>
                      <td className="py-2.5 pr-3 text-slate-500 hidden sm:table-cell">
                        {isUnknown ? <span className="text-amber-500">Not in knowledge base</span> : (item.recommended_pathway || '—')}
                      </td>
                      <td className="py-2.5 pr-3">
                        {isUnknown
                          ? <span className="text-slate-600">N/A</span>
                          : isHazard
                            ? <span className="text-red-400 font-semibold">Regulated</span>
                            : maxVal > 0
                              ? <span style={{ color: '#00ff88' }} className="font-bold">₹{Math.round(maxVal).toLocaleString()}</span>
                              : <span className="text-slate-600">—</span>
                        }
                      </td>
                      <td className="py-2.5">
                        {isUnknown
                          ? <span className="px-1.5 py-0.5 rounded text-xs font-bold" style={{ background: 'rgba(245,158,11,0.12)', color: '#f59e0b', border: '1px solid rgba(245,158,11,0.3)' }}>Unknown ⚠</span>
                          : isHazard
                            ? <span className="px-1.5 py-0.5 rounded text-xs font-bold" style={{ background: 'rgba(239,68,68,0.12)', color: '#ef4444', border: '1px solid rgba(239,68,68,0.3)' }}>Hazardous</span>
                            : <span className="px-1.5 py-0.5 rounded text-xs font-bold" style={{ background: 'rgba(0,255,136,0.08)', color: '#00ff88', border: '1px solid rgba(0,255,136,0.25)' }}>Analyzed ✓</span>
                        }
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
            {items.filter(i => i.status === 'unknown_material').map((item, idx) => (
              <div key={idx} className="mt-3 p-3 rounded-lg text-xs" style={{ background: 'rgba(245,158,11,0.06)', border: '1px solid rgba(245,158,11,0.18)' }}>
                <p className="font-bold mb-1" style={{ color: '#f59e0b' }}>⚠ Unknown: {item.waste_type}</p>
                {item.inferred_category && (
                  <p className="text-slate-400 mb-0.5"><span className="text-slate-500">Inferred category: </span>{item.inferred_category}</p>
                )}
                {item.inferred_handling && (
                  <p className="text-slate-400 mb-0.5"><span className="text-slate-500">Interim handling: </span>{item.inferred_handling}</p>
                )}
                {item.suggestions?.length > 0 && (
                  <p className="text-slate-500 mt-1">Similar known materials: {item.suggestions.join(', ')}</p>
                )}
                <p className="text-slate-600 mt-1">{item.next_step || 'Contact your waste handler for classification.'}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Compliance warnings */}
      {batchResult.compliance_warnings?.length > 0 && (
        <div className="mt-6 glass-card p-4" style={{ border: '1px solid rgba(239,68,68,0.25)' }}>
          <p className="text-sm font-bold text-red-400 mb-2">⚠ Compliance Warnings</p>
          <ul className="space-y-1">
            {batchResult.compliance_warnings.map((w, i) => (
              <li key={i} className="text-xs text-red-300/80">{w}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Enriched per-stream intelligence */}
      {plannedItems.map((item, index) => <details key={index} className="glass-card p-4">
        <summary className="cursor-pointer">Recovery pathways for {item.waste_type}</summary>
        <RecoveryPathwayGrid item={{material:item.waste_type, quantity:item.quantity_kg, unit:'kg',
          condition:item.recovery_intelligence.material_identity?.condition || 'as submitted',
          intelligence:item.recovery_intelligence}} />
      </details>)}

      {items.some(i => i.status === 'analyzed' && (i.compliance_notes || i.preparation_before_sale)) && (
        <div className="mt-6 glass-card p-5">
          <h3 className="text-sm font-bold text-cyan-400 uppercase tracking-wider mb-4">Compliance & Handling Guidance</h3>
          <div className="space-y-5">
            {items.filter(i => i.status === 'analyzed' && (i.compliance_notes || i.preparation_before_sale)).map((item, idx) => (
              <div key={idx} className="border-l-2 pl-4" style={{ borderColor: item.hazard_warning ? '#ef4444' : '#00ff88' }}>
                <p className="text-sm font-bold text-slate-200 capitalize mb-2">{item.waste_type}</p>
                <div className="space-y-1.5 text-xs">
                  {item.compliance_notes && (
                    <div>
                      <span className="text-slate-500 uppercase tracking-wider">Compliance: </span>
                      <span className="text-slate-300">{item.compliance_notes}</span>
                    </div>
                  )}
                  {item.required_handling && (
                    <div>
                      <span className="text-slate-500 uppercase tracking-wider">Handling: </span>
                      <span className="text-slate-300">{item.required_handling}</span>
                    </div>
                  )}
                  {item.preparation_before_sale && (
                    <div>
                      <span className="text-slate-500 uppercase tracking-wider">Preparation: </span>
                      <span className="text-slate-300">{item.preparation_before_sale}</span>
                    </div>
                  )}
                  {item.collection_frequency && (
                    <div>
                      <span className="text-slate-500 uppercase tracking-wider">Collection: </span>
                      <span className="text-slate-300">{item.collection_frequency}</span>
                    </div>
                  )}
                  {item.co2_savings_kg_per_tonne && (
                    <div>
                      <span className="text-slate-500 uppercase tracking-wider">CO₂ Savings: </span>
                      <span style={{ color: '#00ff88' }} className="font-bold">{item.co2_savings_kg_per_tonne.toLocaleString()} kg CO₂/tonne vs landfill</span>
                    </div>
                  )}
                  {item.knowledge_source && (
                    <div>
                      <span className="text-slate-500 uppercase tracking-wider">Source: </span>
                      <span className="text-slate-600">{item.knowledge_source}</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <p className="text-xs text-slate-700 mt-4 text-center">
        Recovery values are knowledge base estimates. Actual market prices vary by location and material grade. Not financial advice.
      </p>
    </section>
  )
}


import { streamInventory } from '../api'

const emptyItem = () => ({
  material: '',
  quantity: '',
  unit: 'kg',
  condition: 'used',
  contaminated: false
})

export default function WasteAnalyzer({ onResult, uploadResult }) {
  const [items, setItems] = useState([emptyItem()])
  const [pin, setPin] = useState('')
  const [result, setResult] = useState(null)
  const [active, setActive] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const running = useRef(null)
  useEffect(() => () => running.current?.abort(), [])

  const field = 'w-full rounded-lg bg-slate-900 border border-slate-700 p-3 text-sm text-white'

  function clearResult() { setResult(null); onResult?.(null) }

  function update(index, key, value) {
    setItems(previous => previous.map((item, i) =>
      i === index ? { ...item, [key]: value } : item
    ))
    clearResult()
  }

  async function analyze(evidenceOnly = false) {
    if (running.current) return
    const controller = new AbortController()
    running.current = controller
    setLoading(true)
    setError('')
    if (!evidenceOnly) { clearResult(); setActive(0) }
    try {
      if (items.some(i => !i.material.trim() || !(Number(i.quantity) > 0)))
        throw new Error('Enter a material and valid quantity for every row.')
      if (pin && !/^[1-9][0-9]{5}$/.test(pin))
        throw new Error('Enter a valid six-digit PIN.')
      if (!(await signIn()) || controller.signal.aborted) return
      const streamStarted = performance.now()
      let firstPathwaysMs
      await streamInventory({
        evidence_only: evidenceOnly,
        items: items.map((i, index) => ({
          ...i, material: i.material.trim(), quantity: Number(i.quantity),
          research_pathways: evidenceOnly ? result.items[index].intelligence.pathways.filter(route => !route.conditional_completion).map(route => route.category) : [],
          contaminated: ['contaminated', 'spoiled'].includes(i.condition),
        })),
        service_pin: pin || null,
      }, snapshot => {
        if (running.current !== controller || controller.signal.aborted) return
        if (evidenceOnly) {
          if (!snapshot.researched_items) return
          snapshot.items = snapshot.items.map((row, index) => {
            const original = result.items[index]
            if (index >= snapshot.researched_items) return original
            return {...row, intelligence: {...original.intelligence,
              local_discovery: row.intelligence.local_discovery,
              research_status: row.intelligence.research_status,
              events: [...original.intelligence.events.filter(event => event.action !== 'public_service_discovery'),
                ...row.intelligence.events.filter(event => event.action === 'public_service_discovery')],
              pathways: row.intelligence.pathways.map(route => {
                const originalRoute = original.intelligence.pathways.find(before => before.category === route.category)
                return originalRoute ? {...route, title: originalRoute.title, action: originalRoute.action,
                  preparation: originalRoute.preparation, benefit: originalRoute.benefit} : route
              })}}
          })
          snapshot.ai_enhanced = result.ai_enhanced
        }
        const receivedMs = Math.round(performance.now() - streamStarted)
        if (firstPathwaysMs == null && snapshot.items.some(row => row.intelligence.pathways.length)) firstPathwaysMs = receivedMs
        snapshot.research_timings_ms = { ...snapshot.research_timings_ms, first_pathways_received_ms: firstPathwaysMs, received_ms: receivedMs }
        setResult(snapshot)
        onResult?.(snapshot)
      }, controller.signal)
    } catch (err) {
      if (!controller.signal.aborted)
        setError(err.response?.status === 422 ? 'Check material descriptions, quantities and PIN.' : err.message)
    } finally {
      if (running.current === controller) {
        running.current = null
        setLoading(false)
      }
    }
  }

  if (uploadResult)
    return <BatchResultPanel batchResult={uploadResult.waste} />

  const selected = result?.items?.[active]

  return (
    <section id="waste" className="px-6 py-16 max-w-[1500px] mx-auto">
      <h2 className="text-3xl font-black text-white mb-2">
        Waste-to-<span className="text-gradient-green">Wealth</span>
      </h2>

      <p className="text-sm text-slate-400 mb-6">
        Investigate materials, compare recovery opportunities
        and identify practical next actions.
      </p>

      <div className="glass-card p-6 space-y-4">
        <h3 className="text-cyan-400 font-bold uppercase text-sm">
          Waste Stream Input
        </h3>

        <fieldset disabled={loading} className="space-y-3">
          {items.map((item, index) => (
            <div key={index} className="grid grid-cols-1 md:grid-cols-12 gap-3 items-center">
              <input className={field + ' md:col-span-4'}
                aria-label="Material description"
                placeholder="e.g. old mobile, cotton clothes"
                value={item.material}
                onChange={e => update(index, 'material', e.target.value)} />

              <input className={field + ' md:col-span-2'}
                aria-label="Quantity"
                type="number" min="0.001" step="any"
                placeholder="Quantity"
                value={item.quantity}
                onChange={e => update(index, 'quantity', e.target.value)} />

              <select className={field + ' md:col-span-2'}
                aria-label="Unit" value={item.unit}
                onChange={e => update(index, 'unit', e.target.value)}>
                {['kg','g','pcs','L','tonnes'].map(unit =>
                  <option key={unit}>{unit}</option>
                )}
              </select>

              <select className={field + ' md:col-span-3'}
                aria-label="Condition" value={item.condition}
                onChange={e => update(index, 'condition', e.target.value)}>
                {['good','used','working','not working','damaged','mixed','contaminated','spoiled','unsure'].map(c =>
                  <option key={c}>{c}</option>
                )}
              </select>



              <button type="button" disabled={loading || items.length === 1}
                className="text-slate-400 text-xl"
                aria-label="Remove material"
                onClick={() => {
                  setItems(items.filter((_, i) => i !== index))
                  clearResult()
                }}><Trash2 size={18} /></button>
            </div>
          ))}

          <button type="button" disabled={loading || items.length >= 20}
            className="text-cyan-400 text-sm font-semibold"
            onClick={() => {
              setItems([...items, emptyItem()])
              clearResult()
            }}>+ Add material</button>

          <div className="grid md:grid-cols-2 gap-4">
            <input className={field} value={pin}
              maxLength={6} inputMode="numeric"
              placeholder="Service PIN (optional)"
              onChange={e => setPin(e.target.value)} />

            <button className="btn-primary justify-center"
              onClick={() => analyze()} disabled={loading}>
              {loading ? 'Investigating recovery options...' : 'Analyze Waste Streams'}
            </button>
          </div>


          {result?.completed_items === items.length && pin && <button type="button" onClick={() => analyze(true)}>
            Refresh PIN evidence
          </button>}
        </fieldset>

        {loading && <button type="button" onClick={() => {
          running.current?.abort()
          running.current = null
          setLoading(false)
          setError('Analysis cancelled. Completed results are available below.')
        }}>Cancel analysis</button>}
        {error && <p role="status" className="text-red-400 text-sm">{error}</p>}
      </div>

      {result && (
        <div className="space-y-5 mt-6">
          <div className="grid grid-cols-2 gap-3">
            {[
              ['Materials reviewed', `${result.completed_items} / ${result.total_items}`],
              ['Recovery pathways', result.pathway_count]
            ].map(([label,value]) => (
              <div key={label} className="glass-card p-4">
                <p className="text-xs text-slate-400">{label}</p>
                <p className="text-xl font-bold text-white mt-2">{value}</p>
              </div>
            ))}
          </div>

          <div className="flex flex-wrap gap-2">
            {result.items.map((item,index) => (
              <button key={index}
                onClick={() => setActive(index)}
                className={'px-4 py-2 rounded-lg text-sm border ' +
                  (active === index
                    ? 'border-cyan-400 text-cyan-400'
                    : 'border-slate-700 text-slate-400')}>
                {item.material} - {item.quantity} {item.unit}
              </button>
            ))}
          </div>

          {selected && (
            <RecoveryPathwayGrid item={selected} />
          )}


        </div>
      )}
    </section>
  )
}
