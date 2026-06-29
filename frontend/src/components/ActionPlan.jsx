import { Clock, Calendar, CalendarDays, TrendingUp, CheckCircle, Download, User, Printer, Award, Building2, Globe } from 'lucide-react'

const PRIORITY_CONFIG = {
  immediate:    { label: 'CRITICAL',  color: '#ef4444', bg: 'rgba(239,68,68,0.12)',   border: 'rgba(239,68,68,0.3)' },
  next_7_days:  { label: 'HIGH',      color: '#f97316', bg: 'rgba(249,115,22,0.1)',   border: 'rgba(249,115,22,0.3)' },
  next_30_days: { label: 'MEDIUM',    color: '#eab308', bg: 'rgba(234,179,8,0.1)',    border: 'rgba(234,179,8,0.25)' },
  long_term:    { label: 'STRATEGIC', color: '#00ff88', bg: 'rgba(0,255,136,0.06)',   border: 'rgba(0,255,136,0.25)' },
}

const DOMAIN_OWNERS = {
  water:         { owner: 'Facilities & Maintenance',  icon: '🔧' },
  energy:        { owner: 'Electrical Maintenance',    icon: '⚡' },
  waste:         { owner: 'Sustainability Cell',        icon: '♻️' },
  impact:        { owner: 'Administration Office',     icon: '🏛️' },
  infrastructure:{ owner: 'Campus Infrastructure',     icon: '🏗️' },
  compliance:    { owner: 'Legal & Compliance',        icon: '📋' },
  sustainability:{ owner: 'Sustainability Office',     icon: '🌿' },
  general:       { owner: 'Campus Operations',         icon: '🏗️' },
}

const EFFORT_CONFIG = {
  immediate:    { effort: 'Low',    color: '#22c55e' },
  next_7_days:  { effort: 'Medium', color: '#eab308' },
  next_30_days: { effort: 'Medium', color: '#eab308' },
  long_term:    { effort: 'High',   color: '#f97316' },
}

const SDG_COLORS = {
  6:  '#26bde2', 7: '#fcc30b', 9: '#fd6925',
  11: '#fd9d24', 12: '#bf8b2e', 13: '#3f7e44',
}

const GRADE_CONFIG = {
  'A+': { color: '#00ff88', bg: 'rgba(0,255,136,0.12)',  border: 'rgba(0,255,136,0.3)' },
  'A':  { color: '#22c55e', bg: 'rgba(34,197,94,0.10)',  border: 'rgba(34,197,94,0.25)' },
  'B':  { color: '#00e5ff', bg: 'rgba(0,229,255,0.08)',  border: 'rgba(0,229,255,0.2)'  },
  'C':  { color: '#eab308', bg: 'rgba(234,179,8,0.08)',  border: 'rgba(234,179,8,0.22)' },
  'D':  { color: '#f97316', bg: 'rgba(249,115,22,0.08)', border: 'rgba(249,115,22,0.22)'},
  'F':  { color: '#ef4444', bg: 'rgba(239,68,68,0.08)',  border: 'rgba(239,68,68,0.22)' },
}

function gradeStyle(grade) {
  const key = grade?.replace('+', '+') || 'C'
  return GRADE_CONFIG[key] || GRADE_CONFIG['C']
}

function PlanSection({ sectionKey, icon, title, color, items, timeline }) {
  const pc = PRIORITY_CONFIG[sectionKey] || PRIORITY_CONFIG.long_term
  const ec = EFFORT_CONFIG[sectionKey]   || EFFORT_CONFIG.long_term

  return (
    <div className="glass-card p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div style={{ color }}>{icon}</div>
          <div>
            <h3 className="font-bold text-sm" style={{ color }}>{title}</h3>
            <p className="text-xs text-slate-500">{timeline}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold px-2 py-0.5 rounded-full"
            style={{ background: pc.bg, border: `1px solid ${pc.border}`, color: pc.color }}>
            {pc.label}
          </span>
          <span className="text-xs px-2 py-0.5 rounded-full"
            style={{ background: 'rgba(15,23,42,0.6)', border: '1px solid rgba(255,255,255,0.06)', color: ec.color }}>
            {ec.effort} effort
          </span>
        </div>
      </div>

      <div className="space-y-3">
        {!items?.length ? (
          <p className="text-xs text-slate-600 italic py-2">No actions in this category</p>
        ) : items.map((item, i) => {
          const domainKey = (item.domain || 'general').toLowerCase()
          const ownerInfo = DOMAIN_OWNERS[domainKey] || DOMAIN_OWNERS.general

          return (
            <div key={i} className="flex items-start gap-3 p-3 rounded-lg"
              style={{ background: 'rgba(15,23,42,0.5)', border: '1px solid rgba(255,255,255,0.04)' }}>
              <CheckCircle className="w-4 h-4 flex-shrink-0 mt-0.5" style={{ color }} />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-slate-200 leading-relaxed">{item.action}</p>
                <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-2">
                  <span className="text-xs text-slate-500 uppercase tracking-wide">
                    {item.domain || 'General'}
                  </span>
                  {item.estimated_saving_inr > 0 && (
                    <span className="text-xs text-green-400">
                      ≈ ₹{item.estimated_saving_inr?.toFixed(0)} est. saving
                    </span>
                  )}
                  {item.priority_score != null && (
                    <span className="text-xs text-cyan-400">Score: {item.priority_score?.toFixed(1)}</span>
                  )}
                  {item.roi?.payback_months != null && (
                    <span className="text-xs text-purple-400">
                      ~{item.roi.payback_months}mo payback (est.)
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-3 mt-2">
                  <div className="flex items-center gap-1.5">
                    <User className="w-3 h-3 text-slate-500" />
                    <span className="text-xs text-slate-500">{ownerInfo.icon} {ownerInfo.owner}</span>
                  </div>
                  {item.timeline && (
                    <span className="text-xs px-2 py-0.5 rounded" style={{
                      background: 'rgba(0,229,255,0.06)', border: '1px solid rgba(0,229,255,0.12)', color: '#7dd3fc',
                    }}>{item.timeline}</span>
                  )}
                </div>
                {item.ai_priority_explanation && (
                  <div className="mt-2 px-3 py-2 rounded-lg text-xs text-slate-300 leading-relaxed italic"
                    style={{ background: 'rgba(167,139,250,0.06)', border: '1px solid rgba(167,139,250,0.15)' }}>
                    <span className="text-purple-400 font-bold not-italic">AI:</span>{' '}
                    {item.ai_priority_explanation}
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function CampusHealthSection({ healthIndex }) {
  if (!healthIndex?.current) return null
  const cur = healthIndex.current
  const tgt = healthIndex.target
  const cs  = gradeStyle(cur.grade)
  const ts  = gradeStyle(tgt?.grade)

  return (
    <div className="glass-card p-6 mb-6">
      <div className="flex items-center gap-2 mb-5">
        <Award className="w-5 h-5 text-yellow-400" />
        <h3 className="text-sm font-bold text-yellow-400 uppercase tracking-wider">
          Campus Health Index
        </h3>
        <span className="ml-auto text-xs text-slate-600">Composite of 6 sustainability dimensions</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <div className="flex items-center gap-4 mb-4">
            <div className="w-20 h-20 rounded-2xl flex items-center justify-center"
              style={{ background: cs.bg, border: `2px solid ${cs.border}` }}>
              <span className="text-4xl font-black" style={{ color: cs.color }}>{cur.grade}</span>
            </div>
            <div>
              <p className="font-bold text-white text-lg">{cur.label}</p>
              <p className="text-xs text-slate-500">Current campus grade</p>
              {tgt && (
                <div className="flex items-center gap-2 mt-2">
                  <span className="text-xs text-slate-500">Target:</span>
                  <span className="text-sm font-bold" style={{ color: ts.color }}>{tgt.grade}</span>
                  <span className="text-xs" style={{ color: ts.color }}>{tgt.label}</span>
                </div>
              )}
            </div>
          </div>

          {healthIndex.interpretation && (
            <p className="text-xs text-slate-400 leading-relaxed p-3 rounded-lg"
              style={{ background: 'rgba(15,23,42,0.5)', border: '1px solid rgba(255,255,255,0.04)' }}>
              {healthIndex.interpretation}
            </p>
          )}
        </div>

        <div>
          <p className="text-xs text-slate-500 mb-3 uppercase tracking-wider">Grade Scale</p>
          <div className="space-y-2">
            {[
              { g: 'A+', l: 'Carbon-Neutral Ready',    c: '#00ff88' },
              { g: 'A',  l: 'High-Performing',         c: '#22c55e' },
              { g: 'B',  l: 'On Track',                c: '#00e5ff' },
              { g: 'C',  l: 'Moderate Risk',           c: '#eab308' },
              { g: 'D',  l: 'High Risk — Act Now',     c: '#f97316' },
              { g: 'F',  l: 'Critical — Immediate',    c: '#ef4444' },
            ].map(row => (
              <div key={row.g} className="flex items-center gap-3">
                <span className="w-7 text-xs font-black" style={{ color: row.c }}>{row.g}</span>
                <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                  <div className="h-full rounded-full" style={{
                    width: row.g === cur.grade ? '100%' : row.g === tgt?.grade ? '60%' : '20%',
                    background: row.c,
                    opacity: row.g === cur.grade ? 1 : row.g === tgt?.grade ? 0.5 : 0.15,
                  }} />
                </div>
                <span className="text-xs text-slate-500 w-36">{row.l}</span>
                {row.g === cur.grade && (
                  <span className="text-xs font-bold" style={{ color: row.c }}>← now</span>
                )}
                {row.g === tgt?.grade && row.g !== cur.grade && (
                  <span className="text-xs text-slate-500">← target</span>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function SDGSection({ sdgItems }) {
  if (!sdgItems?.length) return null
  return (
    <div className="glass-card p-6 mb-6">
      <div className="flex items-center gap-2 mb-5">
        <Globe className="w-5 h-5 text-blue-400" />
        <h3 className="text-sm font-bold text-blue-400 uppercase tracking-wider">
          UN SDG Alignment
        </h3>
        <span className="ml-auto text-xs text-slate-600">Mapped by Impact Analyzer agent</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {sdgItems.map((sdg, i) => {
          const color = SDG_COLORS[sdg.goal] || '#3b82f6'
          return (
            <div key={i} className="p-4 rounded-xl"
              style={{ background: `${color}09`, border: `1px solid ${color}25` }}>
              <div className="flex items-center gap-2 mb-2">
                <div className="w-8 h-8 rounded-lg flex items-center justify-center text-sm font-black text-white"
                  style={{ background: color }}>
                  {sdg.goal}
                </div>
                <div>
                  <p className="text-xs font-bold" style={{ color }}>{sdg.title}</p>
                  <p className="text-xs text-slate-500">SDG {sdg.goal}</p>
                </div>
              </div>
              <p className="text-xs text-slate-400 mb-2 leading-relaxed">{sdg.relevance}</p>
              {sdg.contribution && (
                <p className="text-xs text-slate-500 italic leading-relaxed">{sdg.contribution}</p>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

function BuildingRankingSection({ ranking }) {
  if (!ranking?.length) return null
  return (
    <div className="glass-card p-6 mb-6">
      <div className="flex items-center gap-2 mb-5">
        <Building2 className="w-5 h-5 text-cyan-400" />
        <h3 className="text-sm font-bold text-cyan-400 uppercase tracking-wider">
          Building Risk Ranking
        </h3>
        <span className="ml-auto text-xs text-slate-600">Merged water + energy anomaly data</span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr style={{ borderBottom: '1px solid rgba(0,229,255,0.1)' }}>
              {['Rank', 'Building', 'Water Loss (L)', 'Energy Loss (kWh)', 'Risk Score', 'Water', 'Energy'].map(h => (
                <th key={h} className="text-left pb-2 pr-4 text-slate-500 font-semibold uppercase tracking-wider">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {ranking.map((b, i) => {
              const rankColor = i === 0 ? '#ef4444' : i === 1 ? '#f97316' : i === 2 ? '#eab308' : '#6b7280'
              return (
                <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                  <td className="py-2 pr-4 font-black" style={{ color: rankColor }}>#{b.rank || i + 1}</td>
                  <td className="py-2 pr-4 text-white font-medium">{b.building}</td>
                  <td className="py-2 pr-4 text-red-400">{b.water_loss_liters?.toLocaleString() || 0}</td>
                  <td className="py-2 pr-4 text-orange-400">{b.energy_loss_kwh?.toFixed(1) || 0}</td>
                  <td className="py-2 pr-4">
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 w-16 bg-slate-800 rounded-full overflow-hidden">
                        <div className="h-full rounded-full"
                          style={{ width: `${Math.min(b.risk_score || 0, 100)}%`, background: rankColor }} />
                      </div>
                      <span className="font-bold" style={{ color: rankColor }}>{b.risk_score?.toFixed(0)}</span>
                    </div>
                  </td>
                  <td className="py-2 pr-4">
                    <span className={`badge-${b.water_severity || 'none'}`}>
                      {(b.water_severity || 'none').toUpperCase()}
                    </span>
                  </td>
                  <td className="py-2">
                    <span className={`badge-${b.energy_severity || 'none'}`}>
                      {(b.energy_severity || 'none').toUpperCase()}
                    </span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default function ActionPlan({ data }) {
  if (!data) return null

  const plan           = data?.report?.action_plan       || data?.action_plan
  const summary        = data?.report?.executive_summary || data?.executive_summary
  const campusHealth   = data?.report?.campus_health_index   || data?.campus_health_index
  const sdgAlignment   = data?.report?.sdg_alignment         || data?.sdg_alignment
  const buildingRanking = data?.report?.building_risk_ranking || data?.building_risk_ranking
  const geminiUsed     = data?.report?.gemini_enhanced       ?? data?.gemini_enhanced

  if (!plan) return null

  const handleExportJSON = () => {
    const exportData = {
      generated:  new Date().toISOString(),
      system:     'RE:GEN AI -- Sustainability Command Center',
      disclaimer: 'Prototype decision-support system. All data simulated. Not professional advice.',
      action_plan:       plan,
      executive_summary: summary || '',
      campus_health_index:   campusHealth || null,
      sdg_alignment:         sdgAlignment || [],
      building_risk_ranking: buildingRanking || [],
    }
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
    const url  = URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href     = url
    a.download = `regen-ai-sustainability-report-${Date.now()}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  const handlePrint = () => window.print()

  return (
    <section className="px-6 py-16 max-w-7xl mx-auto" id="action-plan">
      <div className="flex items-start justify-between mb-8">
        <div>
          <h2 className="text-3xl font-black text-white mb-2">
            Sustainability <span className="text-gradient-green">Action Plan</span>
          </h2>
          <p className="text-slate-400 text-sm">
            Agent-prioritized interventions ranked by urgency x cost-saving x environmental impact x feasibility.
          </p>
          {geminiUsed != null && (
            <div className="flex items-center gap-2 mt-2">
              <div className={`w-2 h-2 rounded-full ${geminiUsed ? 'bg-purple-400' : 'bg-slate-500'}`} />
              <span className="text-xs text-slate-500">
                {geminiUsed ? 'AI-enhanced executive summary (Gemini)' : 'Rule-based analysis (Gemini unavailable)'}
              </span>
            </div>
          )}
        </div>
        <div className="flex items-center gap-2 no-print flex-shrink-0">
          <button onClick={handlePrint} className="btn-secondary">
            <Printer className="w-4 h-4" />
            Print PDF
          </button>
          <button onClick={handleExportJSON} className="btn-secondary">
            <Download className="w-4 h-4" />
            Export JSON
          </button>
        </div>
      </div>

      {/* Action plan grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <PlanSection sectionKey="immediate"    icon={<Clock        className="w-5 h-5" />}
          title="Immediate Actions"  color="#ef4444" timeline="Within 24 hours"
          items={plan.immediate} />
        <PlanSection sectionKey="next_7_days"  icon={<Calendar     className="w-5 h-5" />}
          title="Next 7 Days"        color="#f97316" timeline="This week -- schedule now"
          items={plan.next_7_days} />
        <PlanSection sectionKey="next_30_days" icon={<CalendarDays className="w-5 h-5" />}
          title="Next 30 Days"       color="#eab308" timeline="This month -- assign and track"
          items={plan.next_30_days} />
        <PlanSection sectionKey="long_term"    icon={<TrendingUp   className="w-5 h-5" />}
          title="Long-Term Strategy" color="#00ff88" timeline="12+ months -- campus transformation"
          items={plan.long_term} />
      </div>

      {/* Campus Health Index */}
      <CampusHealthSection healthIndex={campusHealth} />

      {/* SDG Alignment */}
      <SDGSection sdgItems={sdgAlignment} />

      {/* Building Risk Ranking */}
      <BuildingRankingSection ranking={buildingRanking} />

      {/* Executive Summary */}
      {summary && (
        <div className="glass-card p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-purple-400 uppercase tracking-wider">
              Executive Summary
            </h3>
            <span className="text-xs text-slate-600">
              {geminiUsed ? 'Generated by Gemini 2.0 Flash' : 'Rule-based template'}
            </span>
          </div>
          <pre className="text-xs text-slate-300 whitespace-pre-wrap leading-relaxed font-mono">{summary}</pre>
        </div>
      )}

      {/* Priority legend */}
      <div className="flex flex-wrap gap-4 mb-6 text-xs text-slate-500 no-print">
        <span className="font-semibold text-slate-400">Priority:</span>
        {[{ label: 'CRITICAL', color: '#ef4444' }, { label: 'HIGH', color: '#f97316' },
          { label: 'MEDIUM', color: '#eab308' },   { label: 'STRATEGIC', color: '#00ff88' }].map(p => (
          <span key={p.label} className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full inline-block" style={{ background: p.color }} />
            <span style={{ color: p.color }}>{p.label}</span>
          </span>
        ))}
      </div>

      <div className="p-4 rounded-lg text-center" style={{
        background: 'rgba(234,179,8,0.04)', border: '1px solid rgba(234,179,8,0.12)',
      }}>
        <p className="text-xs text-yellow-700 leading-relaxed">
          All recommendations are generated from simulated sensor data and rule-based agent analysis.
          Consult certified engineering, waste management, and environmental professionals before
          implementing any intervention. RE:GEN AI is a prototype decision-support system and not
          professional regulatory, financial, or engineering advice.
        </p>
      </div>
    </section>
  )
}
