import { useState } from 'react'
import { analyzeWaste } from '../api'
import { AlertTriangle, CheckCircle, Search, Package, Star, TrendingUp, BarChart3 } from 'lucide-react'

/* ── Waste Market Intelligence (static reference data) ────── */
const MARKET_INTEL = [
  { material: 'Organic / Food Waste',  pathway: 'Composting · Biogas',    buyer: 'Farm co-ops · Municipal plants', range: '₹2 – 8 /kg',   feasibility: 'High',   confidence: 85, risk: 'Low'  },
  { material: 'Paper & Cardboard',     pathway: 'Recycled pulp',           buyer: 'Paper mills · Kabadiwala',       range: '₹8 – 15 /kg',  feasibility: 'High',   confidence: 90, risk: 'Low'  },
  { material: 'PET / Plastic Bottles', pathway: 'Recycled pellets',        buyer: 'Plastic recyclers',              range: '₹5 – 20 /kg',  feasibility: 'Medium', confidence: 80, risk: 'Med'  },
  { material: 'Metal & Aluminium',     pathway: 'Foundry scrap',           buyer: 'Scrap dealers · Foundries',      range: '₹30 – 80 /kg', feasibility: 'High',   confidence: 92, risk: 'Low'  },
  { material: 'Coconut Shell',         pathway: 'Activated carbon / fuel', buyer: 'Industrial buyers',              range: '₹10 – 35 /kg', feasibility: 'High',   confidence: 88, risk: 'Low'  },
  { material: 'E-waste',               pathway: 'Certified recycler',      buyer: 'CPCB-authorized vendors',        range: 'Regulated',     feasibility: 'Low',    confidence: 70, risk: 'High' },
]

const FEASIBILITY_COLOR = { High: '#00ff88', Medium: '#eab308', Low: '#ef4444' }
const RISK_COLOR        = { Low: '#00ff88',  Med: '#eab308',    High: '#ef4444' }

function MarketIntelPanel() {
  return (
    <div className="glass-card p-5 mb-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-cyan-400" />
          <h3 className="text-sm font-bold text-cyan-400 uppercase tracking-wider">Waste Market Intelligence</h3>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <div className="w-1.5 h-1.5 rounded-full bg-yellow-400" />
          Estimated market reference · Not live pricing · AI-compiled from public data
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="text-left" style={{ color: '#475569' }}>
              <th className="pb-2 pr-4 font-semibold uppercase tracking-wider">Material</th>
              <th className="pb-2 pr-4 font-semibold uppercase tracking-wider hidden sm:table-cell">Recovery Pathway</th>
              <th className="pb-2 pr-4 font-semibold uppercase tracking-wider hidden lg:table-cell">Buyer Type</th>
              <th className="pb-2 pr-4 font-semibold uppercase tracking-wider">Est. Value Range</th>
              <th className="pb-2 pr-4 font-semibold uppercase tracking-wider">Feasibility</th>
              <th className="pb-2 font-semibold uppercase tracking-wider hidden sm:table-cell">Confidence</th>
            </tr>
          </thead>
          <tbody>
            {MARKET_INTEL.map((row, i) => (
              <tr key={i} className="border-t" style={{ borderColor: 'rgba(255,255,255,0.04)' }}>
                <td className="py-2.5 pr-4 font-medium text-slate-200">{row.material}</td>
                <td className="py-2.5 pr-4 text-slate-400 hidden sm:table-cell">{row.pathway}</td>
                <td className="py-2.5 pr-4 text-slate-500 hidden lg:table-cell">{row.buyer}</td>
                <td className="py-2.5 pr-4 font-bold" style={{ color: row.risk === 'High' ? '#ef4444' : '#00ff88' }}>
                  {row.range}
                </td>
                <td className="py-2.5 pr-4">
                  <span className="px-2 py-0.5 rounded-full font-bold"
                    style={{ background: FEASIBILITY_COLOR[row.feasibility] + '15', color: FEASIBILITY_COLOR[row.feasibility], border: `1px solid ${FEASIBILITY_COLOR[row.feasibility]}30` }}>
                    {row.feasibility}
                  </span>
                </td>
                <td className="py-2.5 hidden sm:table-cell">
                  <div className="flex items-center gap-2">
                    <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                      <div className="h-full rounded-full" style={{ width: `${row.confidence}%`, background: 'linear-gradient(90deg,#00ff88,#00e5ff)' }} />
                    </div>
                    <span className="text-slate-500">{row.confidence}%</span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

const WASTE_TYPES = [
  'coconut shell','rice husk','banana peel','food waste','textile waste',
  'plastic bottles','glass bottles','cardboard','paper waste','e-waste',
  'aluminium cans','steel scrap','wood waste','sawdust','construction debris',
  'used cooking oil','rubber tyres','coffee grounds','sugarcane bagasse',
  'corn husk','eggshells','fish waste','leather scraps','cotton waste',
  'coconut coir','wet waste','dry leaves','garden waste','battery waste','medical waste',
]

function ScoreBar({ score, label }) {
  const color = score >= 70 ? '#00ff88' : score >= 50 ? '#eab308' : '#ef4444'
  return (
    <div>
      <div className="flex justify-between items-center mb-1">
        <span className="text-xs text-slate-400">{label}</span>
        <span className="text-sm font-bold" style={{ color }}>{score}/100</span>
      </div>
      <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all duration-1000" style={{ width: `${score}%`, background: color }} />
      </div>
    </div>
  )
}

function PathwayCard({ title, emoji, description, pros, cons, valueMultiplier, feasibility, envScore, isBest, result }) {
  const minVal = result?.estimated_recovery?.min_inr || 0
  const maxVal = result?.estimated_recovery?.max_inr || 0
  const adjMin = Math.round(minVal * valueMultiplier)
  const adjMax = Math.round(maxVal * valueMultiplier)
  const isHazard = result?.hazard_warning
  const score = result?.hidden_value_score || 0

  return (
    <div className={`p-4 rounded-xl relative transition-all duration-300 ${isBest ? 'glow-green' : ''}`}
      style={{
        background: isBest ? 'rgba(0,255,136,0.06)' : 'rgba(15,23,42,0.5)',
        border: isBest ? '1px solid rgba(0,255,136,0.35)' : '1px solid rgba(255,255,255,0.06)',
      }}>
      {isBest && (
        <div className="absolute -top-2.5 left-4 flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold"
          style={{ background: 'rgba(0,255,136,0.9)', color: '#030712' }}>
          <Star className="w-3 h-3" /> Best Pathway
        </div>
      )}
      <div className="flex items-center gap-2 mb-3 mt-1">
        <span className="text-xl">{emoji}</span>
        <h4 className="text-sm font-bold text-white">{title}</h4>
      </div>
      <p className="text-xs text-slate-400 leading-relaxed mb-3">{description}</p>

      {!isHazard && (adjMin > 0 || adjMax > 0) ? (
        <div className="mb-3 p-2 rounded-lg" style={{ background: 'rgba(0,255,136,0.06)', border: '1px solid rgba(0,255,136,0.12)' }}>
          <p className="text-xs text-slate-500 mb-0.5">Estimated value range</p>
          <p className="text-sm font-black text-green-400">
            ₹{adjMin.toLocaleString()} – ₹{adjMax.toLocaleString()}
          </p>
          <p className="text-xs text-slate-600">est. only · simulated data</p>
        </div>
      ) : isHazard ? (
        <div className="mb-3 p-2 rounded-lg" style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)' }}>
          <p className="text-xs text-red-400">Financial value suppressed — hazardous material</p>
        </div>
      ) : null}

      <div className="grid grid-cols-3 gap-2 text-center mt-2">
        <div>
          <p className="text-xs text-slate-600">Feasibility</p>
          <p className="text-xs font-bold" style={{ color: feasibility === 'High' ? '#00ff88' : feasibility === 'Medium' ? '#eab308' : '#ef4444' }}>
            {feasibility}
          </p>
        </div>
        <div>
          <p className="text-xs text-slate-600">Env. Impact</p>
          <div className="flex justify-center mt-0.5">
            {Array.from({ length: 5 }).map((_, i) => (
              <span key={i} style={{ color: i < envScore ? '#00ff88' : '#1e293b', fontSize: 10 }}>★</span>
            ))}
          </div>
        </div>
        <div>
          <p className="text-xs text-slate-600">Risk</p>
          <p className="text-xs font-bold text-slate-300">{pros}</p>
        </div>
      </div>
    </div>
  )
}

export default function WasteAnalyzer({ onResult }) {
  const [wasteType, setWasteType] = useState('coconut shell')
  const [quantity, setQuantity] = useState(50)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleAnalyze = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await analyzeWaste(wasteType, parseFloat(quantity))
      setResult(res.data)
      if (onResult) onResult(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const isHazard = result?.hazard_warning
  const isMedical = wasteType === 'medical waste'
  const score = result?.hidden_value_score || 0
  const pathway = result?.recommended_pathway || ''

  /* Determine best pathway index based on recommended_pathway */
  const bestIdx = pathway.includes('sell') ? 0 : pathway.includes('process') ? 1 : 2

  return (
    <section className="px-6 py-16 max-w-7xl mx-auto" id="waste">
      <div className="mb-8">
        <h2 className="text-3xl font-black text-white mb-2">
          Waste <span className="text-gradient-green">Intelligence</span>
        </h2>
        <p className="text-slate-400 text-sm max-w-2xl">
          Market intelligence for 30 campus waste streams — recovery pathways, estimated value ranges,
          and feasibility scoring. Select a material below to run agent-based analysis.
        </p>
      </div>

      <MarketIntelPanel />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Input Panel */}
        <div className="glass-card p-6">
          <h3 className="text-sm font-semibold text-cyan-400 uppercase tracking-wider mb-6 flex items-center gap-2">
            <Package className="w-4 h-4" /> Waste Stream Input
          </h3>

          <div className="mb-5">
            <label className="block text-slate-300 text-sm font-medium mb-2">Waste Category</label>
            <select
              value={wasteType}
              onChange={(e) => { setWasteType(e.target.value); setResult(null) }}
              className="w-full px-4 py-3 rounded-lg text-white text-sm outline-none"
              style={{ background: 'rgba(15,23,42,0.8)', border: '1px solid rgba(0,229,255,0.2)', color: '#e2e8f0' }}>
              {WASTE_TYPES.map((w) => (
                <option key={w} value={w} style={{ background: '#0f172a' }}>{w}</option>
              ))}
            </select>
          </div>

          <div className="mb-6">
            <label className="block text-slate-300 text-sm font-medium mb-2">
              Quantity: <span className="text-cyan-400 font-bold">{quantity} kg</span>
            </label>
            <input type="range" min="1" max="1000" value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              className="w-full accent-green-400" />
            <div className="flex justify-between text-xs text-slate-600 mt-1">
              <span>1 kg</span><span>500 kg</span><span>1000 kg</span>
            </div>
          </div>

          <button className="btn-primary w-full justify-center" onClick={handleAnalyze} disabled={loading}>
            {loading ? (
              <><div className="w-4 h-4 border-2 border-black/30 border-t-black rounded-full animate-spin" /> Analyzing pathway...</>
            ) : (
              <><Search className="w-4 h-4" /> Analyze Waste Stream</>
            )}
          </button>

          {error && (
            <div className="mt-4 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">{error}</div>
          )}

          {!result && (
            <div className="mt-6 p-4 rounded-lg" style={{ background: 'rgba(0,229,255,0.04)', border: '1px solid rgba(0,229,255,0.1)' }}>
              <p className="text-xs text-slate-500 leading-relaxed">
                The agent looks up the waste type in a 30-material knowledge base,
                applies hazard guardrails, and maps it to one of three recovery pathways.
                Try <span className="text-cyan-400">coconut shell</span> for a clean pathway,
                or <span className="text-red-400">e-waste</span> to see mandatory hazard warnings.
              </p>
            </div>
          )}
        </div>

        {/* Result Panel */}
        {result ? (
          <div className="fade-in space-y-4">
            {/* Hazard Warning */}
            {result.hazard_warning && (
              <div className="glass-card-red p-4 flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-red-400 font-bold text-sm mb-1">Hazardous Material — CPCB Safety Notice</p>
                  <p className="text-red-300/80 text-xs leading-relaxed">{result.hazard_message}</p>
                </div>
              </div>
            )}

            {/* Overview */}
            <div className="glass-card p-5">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="font-bold text-white capitalize">{result.waste_type}</h3>
                  <p className="text-xs text-slate-400 mt-0.5">{result.category}</p>
                </div>
                <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                  result.hazard_level === 'none' ? 'badge-low' :
                  result.hazard_level === 'low' ? 'badge-medium' :
                  result.hazard_level === 'medium' ? 'badge-high' : 'badge-critical'
                }`}>{result.hazard_level.toUpperCase()} RISK</span>
              </div>

              <ScoreBar score={score} label="Hidden Value Score (agent-assessed)" />

              <div className="mt-4 grid grid-cols-2 gap-3">
                <div>
                  <p className="text-xs text-slate-500 mb-1">Possible Products</p>
                  <div className="flex flex-wrap gap-1">
                    {result.possible_products?.slice(0, 3).map((p) => (
                      <span key={p} className="text-xs px-2 py-0.5 rounded-full badge-low">{p}</span>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-xs text-slate-500 mb-1">Buyer Types</p>
                  <div className="flex flex-wrap gap-1">
                    {result.buyer_types?.slice(0, 2).map((b) => (
                      <span key={b} className="text-xs px-2 py-0.5 rounded-full badge-info">{b}</span>
                    ))}
                  </div>
                </div>
              </div>

              <div className="mt-4">
                <p className="text-xs text-slate-500 mb-1">Sustainability Note</p>
                <p className="text-xs text-slate-300 leading-relaxed">{result.sustainability_notes}</p>
              </div>
            </div>

            {/* 3-Pathway Comparison */}
            {!isMedical && (
              <div className="glass-card p-5">
                <div className="flex items-center gap-2 mb-4">
                  <TrendingUp className="w-4 h-4 text-cyan-400" />
                  <h4 className="text-sm font-bold text-cyan-400 uppercase tracking-wider">Recovery Pathway Comparison</h4>
                </div>
                <div className="grid grid-cols-1 gap-3">
                  <PathwayCard
                    title="Sell as Raw Material"
                    emoji="🏷️"
                    description="Direct sale to scrap dealers or bulk buyers. Fastest turnaround, lowest processing effort."
                    pros="Low"
                    feasibility={score > 40 ? 'High' : 'Medium'}
                    envScore={3}
                    valueMultiplier={1.0}
                    isBest={bestIdx === 0}
                    result={result}
                  />
                  <PathwayCard
                    title="Process into Product"
                    emoji="⚙️"
                    description="Convert into a refined product (e.g., briquettes, compost, pellets). Higher value, requires processing setup."
                    pros="Medium"
                    feasibility={score > 60 ? 'Medium' : 'Low'}
                    envScore={4}
                    valueMultiplier={1.8}
                    isBest={bestIdx === 1}
                    result={result}
                  />
                  <PathwayCard
                    title="Partner with Certified Recycler"
                    emoji="🤝"
                    description="Route to a certified waste partner. Preferred for regulatory compliance; value is moderate but risk is lowest."
                    pros="Minimal"
                    feasibility="Medium"
                    envScore={5}
                    valueMultiplier={1.3}
                    isBest={bestIdx === 2}
                    result={result}
                  />
                </div>
                <p className="text-xs text-slate-600 mt-3">
                  Value estimates are calculated from simulated knowledge base ranges. Actual recovery depends on local market conditions.
                </p>
              </div>
            )}

            {/* Reasoning Trace */}
            <div className="glass-card p-4">
              <p className="text-xs font-semibold text-purple-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                <CheckCircle className="w-3 h-3" /> Agent Reasoning Trace
              </p>
              <div className="space-y-1">
                {result.reasoning_trace?.map((step, i) => (
                  <p key={i} className="text-xs text-slate-400 leading-relaxed">
                    <span className="text-purple-400 mr-1">›</span>{step}
                  </p>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="glass-card p-10 flex flex-col items-center justify-center text-center">
            <div className="text-5xl mb-4">♻️</div>
            <p className="text-slate-300 text-sm font-medium mb-2">30 waste materials in the knowledge base</p>
            <p className="text-slate-500 text-xs leading-relaxed">
              Select a waste type, set quantity, then run the agent to identify recovery pathways,
              estimated value, and compliance requirements.
            </p>
          </div>
        )}
      </div>
    </section>
  )
}
