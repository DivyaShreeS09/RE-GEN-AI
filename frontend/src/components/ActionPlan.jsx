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
  infrastructure:{ owner: 'Facilities Management',     icon: '🏗️' },
  compliance:    { owner: 'Legal & Compliance',        icon: '📋' },
  sustainability:{ owner: 'Sustainability Office',     icon: '🌿' },
  general:       { owner: 'Operations',                icon: '🏗️' },
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

function PlanSection({ sectionKey, icon, title, color, items, timeline, highlightDomains }) {
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

          const isHighlighted = highlightDomains?.length && highlightDomains.includes(domainKey)
          return (
            <div key={i} className="flex items-start gap-3 p-3 rounded-lg"
              style={{
                background: isHighlighted ? 'rgba(0,229,255,0.07)' : 'rgba(15,23,42,0.5)',
                border: isHighlighted ? '1px solid rgba(0,229,255,0.32)' : '1px solid rgba(255,255,255,0.04)',
                transition: 'background 0.3s, border-color 0.3s',
              }}>
              <CheckCircle className="w-4 h-4 flex-shrink-0 mt-0.5" style={{ color: isHighlighted ? '#00e5ff' : color }} />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-slate-200 leading-relaxed">{item.action}</p>
                <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-2">
                  <span className="text-xs text-slate-500 uppercase tracking-wide">
                    {item.domain || 'General'}
                  </span>
                  {isHighlighted && (
                    <span className="text-xs px-1.5 py-0.5 rounded font-medium"
                      style={{ background: 'rgba(0,229,255,0.12)', color: '#00e5ff', border: '1px solid rgba(0,229,255,0.25)' }}>
                      ↑ Digital Twin
                    </span>
                  )}
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
          Sustainability Health Index
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
              <p className="text-xs text-slate-500">Current sustainability grade</p>
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
                  <p className="text-xs text-slate-500">SDG {sdg.goal.replace(/^SDG\s*/i, '')}</p>
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

export default function ActionPlan({ data, selectedBuilding }) {
  if (!data) return null

  const plan           = data?.report?.action_plan       || data?.action_plan
  const summary        = data?.report?.executive_summary || data?.executive_summary
  const campusHealth   = data?.report?.campus_health_index   || data?.campus_health_index
  const sdgAlignment   = data?.report?.sdg_alignment         || data?.sdg_alignment
  const buildingRanking = data?.report?.building_risk_ranking || data?.building_risk_ranking
  const aiUsed         = data?.report?.ai_enhanced ?? data?.ai_enhanced
  const dataSource     = data?.report?.data_source || data?.data_source || 'Simulated sensor data'
  const orgName        = data?.report?.org_name || data?.org_name || null

  if (!plan) return null

  const handleExportJSON = () => {
    const exportData = {
      generated:  new Date().toISOString(),
      system:     'RE:GEN AI — Sustainability Intelligence OS',
      disclaimer: orgName
        ? `Prototype decision-support system. Analysis derived from uploaded ${orgName} data. Not professional advice.`
        : 'Prototype decision-support system. All data simulated. Not professional advice.',
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
    a.download = `regen-ai-report-${Date.now()}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleExportPDF = () => {
    const now = new Date().toLocaleDateString('en-IN', { year: 'numeric', month: 'long', day: 'numeric' })
    const reportMeta     = data?.report?.analysis_metadata || data?.analysis_metadata || null
    const anomalyOk      = reportMeta ? reportMeta.anomaly_detection_available !== false : true
    const isUpload       = !!orgName
    const allActions = [
      ...(plan.immediate    || []).map(a => ({ ...a, _priority: 'CRITICAL',  _color: '#b91c1c', _timeline: 'Within 24 hours'  })),
      ...(plan.next_7_days  || []).map(a => ({ ...a, _priority: 'HIGH',      _color: '#c2410c', _timeline: 'Within 7 days'    })),
      ...(plan.next_30_days || []).map(a => ({ ...a, _priority: 'MEDIUM',    _color: '#92400e', _timeline: 'Within 30 days'   })),
      ...(plan.long_term    || []).map(a => ({ ...a, _priority: 'STRATEGIC', _color: '#15803d', _timeline: '12+ months'       })),
    ]

    const actionRows = allActions.map(a => `
      <tr>
        <td><span style="color:${a._color};font-weight:700;">${a._priority}</span></td>
        <td>${a.action || '—'}</td>
        <td>${a.domain || 'General'}</td>
        <td>${a._timeline}</td>
        <td>${a.estimated_saving_inr > 0 ? '≈ ₹' + Number(a.estimated_saving_inr).toFixed(0) : '—'}</td>
      </tr>`).join('')

    const buildingRows = (buildingRanking || []).map((b, i) => {
      const rc = i === 0 ? '#b91c1c' : i === 1 ? '#c2410c' : i === 2 ? '#92400e' : '#374151'
      return `<tr>
        <td style="color:${rc};font-weight:700;">#${b.rank || i+1}</td>
        <td style="font-weight:600;">${b.building || '—'}</td>
        <td>${(b.water_loss_liters || 0).toLocaleString()} L</td>
        <td>${(b.energy_loss_kwh || 0).toFixed(1)} kWh</td>
        <td>${b.risk_score?.toFixed(0) ?? '—'}</td>
        <td>${(b.water_severity || 'none').toUpperCase()}</td>
        <td>${(b.energy_severity || 'none').toUpperCase()}</td>
      </tr>`}).join('')

    const sdgCards = (sdgAlignment || []).map(sdg => {
      const color = { 6:'#26bde2',7:'#fcc30b',9:'#fd6925',11:'#fd9d24',12:'#bf8b2e',13:'#3f7e44' }[sdg.goal] || '#3b82f6'
      return `<div class="sdg-item">
        <div class="sdg-badge" style="background:${color};">SDG ${sdg.goal.replace(/^SDG\s*/i, '')}</div>
        <div class="sdg-title">${sdg.title || ''}</div>
        <div class="sdg-text">${sdg.relevance || ''}</div>
      </div>`}).join('')

    const curGrade = campusHealth?.current?.grade || '—'
    const curScore = campusHealth?.current?.score || '—'
    const curLabel = campusHealth?.current?.label || '—'
    const tgtGrade = campusHealth?.target?.grade  || '—'

    const html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>RE:GEN AI — Sustainability Report</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0;}
  @page{size:A4;margin:18mm 16mm 14mm 16mm;}
  @page:first{margin-top:0;}
  body{font-family:'Segoe UI',Arial,sans-serif;color:#111827;background:#fff;font-size:9.5pt;line-height:1.6;}

  /* ── Cover ── */
  .cover{
    background:linear-gradient(135deg,#0a1f0d 0%,#0d2240 55%,#030912 100%);
    color:#fff;min-height:26cm;display:flex;flex-direction:column;
    justify-content:flex-end;padding:2.5cm 2cm 2cm;
    page-break-after:always;
  }
  .cover-tag{font-size:8pt;color:rgba(0,255,136,0.8);letter-spacing:0.22em;text-transform:uppercase;margin-bottom:14pt;
    border:1px solid rgba(0,255,136,0.25);display:inline-block;padding:4pt 12pt;border-radius:99pt;}
  .cover-title{font-size:36pt;font-weight:900;line-height:1.05;letter-spacing:-0.02em;margin-bottom:10pt;}
  .cover-sub{font-size:12pt;color:rgba(255,255,255,0.55);margin-bottom:36pt;line-height:1.5;}
  .cover-chips{display:flex;gap:8pt;flex-wrap:wrap;margin-bottom:32pt;}
  .cover-chip{font-size:8pt;padding:4pt 10pt;border-radius:99pt;background:rgba(255,255,255,0.07);
    border:1px solid rgba(255,255,255,0.12);color:rgba(255,255,255,0.65);}
  .cover-meta{font-size:8pt;color:rgba(255,255,255,0.28);padding-top:14pt;
    border-top:1px solid rgba(255,255,255,0.08);line-height:1.8;}

  /* ── Header (non-cover pages) ── */
  .page-header{display:flex;align-items:center;justify-content:space-between;
    padding-bottom:8pt;border-bottom:1.5pt solid #15803d;margin-bottom:20pt;}
  .page-header-logo{font-size:11pt;font-weight:900;color:#15803d;letter-spacing:0.04em;}
  .page-header-meta{font-size:7.5pt;color:#9ca3af;}

  /* ── Section heads ── */
  .section{margin-bottom:22pt;}
  .section-title{font-size:13pt;font-weight:800;color:#111827;margin-bottom:4pt;}
  .section-rule{height:2pt;background:linear-gradient(90deg,#15803d,#047a8a);border-radius:1pt;margin-bottom:12pt;}
  .section-sub{font-size:8.5pt;color:#6b7280;margin-bottom:10pt;}

  /* ── Score block ── */
  .score-row{display:flex;align-items:center;gap:20pt;padding:14pt;
    background:#f0fdf4;border:1pt solid #bbf7d0;border-radius:8pt;margin-bottom:14pt;}
  .score-num{font-size:52pt;font-weight:900;color:#15803d;line-height:1;letter-spacing:-0.02em;}
  .score-info{flex:1;}
  .score-grade{font-size:20pt;font-weight:800;color:#15803d;}
  .score-label{font-size:9pt;color:#374151;}
  .score-target{font-size:8.5pt;color:#6b7280;margin-top:4pt;}

  /* ── Tables ── */
  table{width:100%;border-collapse:collapse;font-size:8.5pt;margin-bottom:14pt;}
  th{background:#f3f4f6;color:#374151;font-weight:700;text-align:left;
    padding:5pt 7pt;border:1pt solid #e5e7eb;font-size:7.5pt;text-transform:uppercase;letter-spacing:0.05em;}
  td{padding:4.5pt 7pt;border:1pt solid #e5e7eb;color:#374151;vertical-align:top;}
  tr:nth-child(even) td{background:#f9fafb;}

  /* ── SDG cards ── */
  .sdg-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:7pt;}
  .sdg-item{padding:8pt;border-radius:6pt;background:#f9fafb;border:1pt solid #e5e7eb;}
  .sdg-badge{display:inline-block;font-size:7.5pt;font-weight:800;color:#fff;
    padding:2pt 7pt;border-radius:4pt;margin-bottom:4pt;}
  .sdg-title{font-size:8.5pt;font-weight:700;color:#111827;margin-bottom:2pt;}
  .sdg-text{font-size:7.5pt;color:#6b7280;line-height:1.4;}

  /* ── Summary pre ── */
  .summary-box{background:#f9fafb;border-left:2.5pt solid #15803d;padding:12pt 14pt;
    border-radius:0 6pt 6pt 0;font-size:9pt;color:#374151;line-height:1.8;
    white-space:pre-wrap;font-family:inherit;}

  /* ── Disclaimer ── */
  .disclaimer{background:#fffbeb;border:1pt solid #fde68a;border-radius:6pt;
    padding:10pt 12pt;font-size:8pt;color:#92400e;line-height:1.6;margin-top:20pt;}

  /* ── Footer ── */
  .page-footer{font-size:7pt;color:#9ca3af;text-align:center;margin-top:18pt;
    border-top:1pt solid #e5e7eb;padding-top:6pt;}

  .page-break{page-break-before:always;padding-top:16pt;}
</style>
</head>
<body>

<!-- ─── Cover ─── -->
<div class="cover">
  <div class="cover-tag">Enterprise Release 2026</div>
  <div class="cover-title">RE:GEN AI<br>Sustainability<br>Intelligence Report</div>
  <div class="cover-sub">${orgName ? orgName + ' — Sustainability Analysis' : 'Agent-Prioritized Resource Analysis'}<br>Multi-Domain Decision Support · 7 AI Agents</div>
  <div class="cover-chips">
    ${anomalyOk ? '<span class="cover-chip">💧 Water Leakage Detection</span>' : '<span class="cover-chip">💧 Water Consumption Analysis</span>'}
    ${anomalyOk ? '<span class="cover-chip">⚡ Energy Anomaly Audit</span>' : '<span class="cover-chip">⚡ Energy Consumption Analysis</span>'}
    <span class="cover-chip">♻ Waste-to-Wealth Pathways</span>
    <span class="cover-chip">📊 Impact Analysis</span>
    <span class="cover-chip">🤖 AI Reasoning</span>
    ${reportMeta ? `<span class="cover-chip">📈 ${reportMeta.overall_label || 'Analysis'} · ${reportMeta.confidence_pct || '—'}% confidence</span>` : ''}
  </div>
  <div class="cover-meta">
    Report generated: ${now}<br>
    Multi-Agent Sustainability Intelligence Platform<br>
    Data source: ${dataSource}.<br>
    ${reportMeta ? `Analysis level: ${reportMeta.overall_label || 'N/A'} · Confidence: ${reportMeta.confidence_pct ?? '—'}%${reportMeta.anomaly_detection_available === false ? ' · Anomaly detection: unavailable at this data resolution' : ''}<br>` : ''}
    RE:GEN AI is a decision-support prototype — not professional regulatory, financial, or engineering advice.
  </div>
</div>

<!-- ─── Page 2: Score + Executive Summary ─── -->
<div class="page-header">
  <span class="page-header-logo">RE:GEN AI</span>
  <span class="page-header-meta">Sustainability Intelligence Report · ${now}</span>
</div>

${campusHealth?.current ? `
<div class="section">
  <div class="section-title">Sustainability Health Index</div>
  <div class="section-rule"></div>
  <div class="score-row">
    <div class="score-num">${curScore}</div>
    <div class="score-info">
      <div class="score-grade">${curGrade}</div>
      <div class="score-label">${curLabel}</div>
      <div class="score-target">Target: ${tgtGrade} &nbsp;·&nbsp; Composite of 6 sustainability dimensions</div>
    </div>
  </div>
  ${campusHealth.interpretation ? `<div class="summary-box">${campusHealth.interpretation}</div>` : ''}
</div>` : ''}

${reportMeta && (reportMeta.skipped_modules?.length > 0 || reportMeta.anomaly_detection_available === false) ? `
<div class="section">
  <div class="section-title">Analysis Limitations</div>
  <div class="section-rule"></div>
  <div style="background:#fffbeb;border:1pt solid #fde68a;border-radius:6pt;padding:10pt 12pt;font-size:8.5pt;color:#92400e;line-height:1.7;">
    ${reportMeta.anomaly_detection_available === false ? `<strong>Anomaly detection unavailable</strong> — ${reportMeta.overall_label || 'Current'} data does not include hourly time-series. Leak detection, after-hours energy waste, and zone-level risk mapping require Level 3 (hourly) data.<br>` : ''}
    ${reportMeta.skipped_modules?.length > 0 ? `<strong>Skipped modules:</strong> ${reportMeta.skipped_modules.map(m => m.module).join(', ')}.<br>` : ''}
    <strong>Confidence:</strong> ${reportMeta.confidence_pct ?? '—'}% · <strong>Analysis level:</strong> ${reportMeta.overall_label || 'N/A'}
  </div>
</div>` : ''}

${summary ? `
<div class="section">
  <div class="section-title">Executive Summary</div>
  <div class="section-rule"></div>
  <div class="section-sub">${aiUsed ? 'Generated by AI Core · Multi-agent synthesis' : 'Rule-based analysis summary'}</div>
  <div class="summary-box">${summary}</div>
</div>` : ''}

<!-- ─── Page 3: Action Plan ─── -->
<div class="page-break">
<div class="page-header">
  <span class="page-header-logo">RE:GEN AI · Action Plan</span>
  <span class="page-header-meta">${now}</span>
</div>

<div class="section">
  <div class="section-title">Agent-Prioritized Action Plan</div>
  <div class="section-rule"></div>
  <div class="section-sub">Ranked by urgency × cost-saving × environmental impact × feasibility. All savings are estimates only.</div>
  <table>
    <thead><tr><th>Priority</th><th>Action</th><th>Domain</th><th>Timeline</th><th>Est. Saving</th></tr></thead>
    <tbody>${actionRows || '<tr><td colspan="5" style="color:#9ca3af;font-style:italic;">No actions generated.</td></tr>'}</tbody>
  </table>
</div>
</div>

${buildingRanking?.length ? `
<!-- ─── Page 4: Building Risk ─── -->
<div class="page-break">
<div class="page-header">
  <span class="page-header-logo">RE:GEN AI · Building Risk Ranking</span>
  <span class="page-header-meta">${now}</span>
</div>
<div class="section">
  <div class="section-title">Building Risk Ranking</div>
  <div class="section-rule"></div>
  <div class="section-sub">Merged water + energy anomaly data across all monitored resource zones.</div>
  <table>
    <thead><tr><th>Rank</th><th>Building</th><th>Water Loss</th><th>Energy Loss</th><th>Risk Score</th><th>Water</th><th>Energy</th></tr></thead>
    <tbody>${buildingRows}</tbody>
  </table>
</div>
</div>` : ''}

${sdgAlignment?.length ? `
<!-- ─── Page 5: SDG Alignment ─── -->
<div class="page-break">
<div class="page-header">
  <span class="page-header-logo">RE:GEN AI · SDG Alignment</span>
  <span class="page-header-meta">${now}</span>
</div>
<div class="section">
  <div class="section-title">UN Sustainable Development Goal Alignment</div>
  <div class="section-rule"></div>
  <div class="section-sub">Mapped by the Impact Analyzer Agent across all interventions.</div>
  <div class="sdg-grid">${sdgCards}</div>
</div>
</div>` : ''}

<!-- ─── Final page: Disclaimer ─── -->
<div class="page-break">
<div class="page-header">
  <span class="page-header-logo">RE:GEN AI</span>
  <span class="page-header-meta">${now}</span>
</div>
<div class="section">
  <div class="section-title">System Information</div>
  <div class="section-rule"></div>
  <table>
    <tbody>
      <tr><td style="font-weight:700;width:160pt;">System</td><td>RE:GEN AI — Sustainability Intelligence OS</td></tr>
      <tr><td style="font-weight:700;">Version</td><td>Enterprise Release 2026 · Multi-Agent Sustainability Intelligence Platform</td></tr>
      <tr><td style="font-weight:700;">Agents</td><td>Water Leakage · Energy Optimizer · Waste-to-Wealth · Impact Analyzer · Sustainability Score · Decision Priority · Report Narrative</td></tr>
      <tr><td style="font-weight:700;">AI Layer</td><td>OpenAI gpt-4o-mini · Multi-agent coordination (graceful fallback to rule-based engine)</td></tr>
      <tr><td style="font-weight:700;">Data Source</td><td>${dataSource}</td></tr>
      <tr><td style="font-weight:700;">Generated</td><td>${new Date().toISOString()}</td></tr>
    </tbody>
  </table>
</div>
<div class="disclaimer">
  ⚠ Important Disclaimer: ${isUpload
    ? `Analysis is derived from uploaded data for ${orgName}. Results are estimates based on rule-based agent analysis.`
    : 'All data presented in this report is simulated for demonstration purposes.'
  }
  RE:GEN AI is a prototype decision-support system and not professional regulatory, financial, or engineering advice.
  Financial saving estimates are illustrative only — actual results will vary based on real infrastructure conditions,
  usage patterns, and local regulations. Consult certified engineering, waste management, and environmental
  professionals before implementing any intervention. Hazardous waste determinations require licensed waste auditors.
</div>
<div class="page-footer">
  RE:GEN AI · Sustainability Intelligence OS · Multi-Agent Resource Intelligence Platform<br>
  Decision-support prototype · ${isUpload ? 'Uploaded data analysis' : 'Data simulated'} · Not professional advice
</div>
</div>

</body></html>`

    const win = window.open('', '_blank', 'width=900,height=700')
    if (!win) { alert('Please allow pop-ups to export the PDF.'); return }
    win.document.write(html)
    win.document.close()
    win.addEventListener('load', () => {
      setTimeout(() => {
        win.focus()
        win.print()
      }, 400)
    })
  }

  return (
    <section className="px-6 py-16 max-w-7xl mx-auto" id="action-plan">
      <div className="flex items-start justify-between mb-8">
        <div>
          <h2 className="text-3xl font-black text-white mb-2">
            Sustainability <span className="text-gradient-green">Action Plan</span>
          </h2>
          <p className="text-slate-400 text-sm">
            Agent-prioritised interventions ranked by urgency, cost savings, environmental impact, and feasibility.
          </p>
          {aiUsed != null && (
            <div className="flex items-center gap-2 mt-2">
              <div className={`w-2 h-2 rounded-full ${aiUsed ? 'bg-purple-400' : 'bg-slate-500'}`} />
              <span className="text-xs text-slate-500">
                {aiUsed ? 'AI-enhanced executive summary' : 'Rule-based analysis (AI unavailable)'}
              </span>
            </div>
          )}
        </div>
        <div className="flex items-center gap-2 no-print flex-shrink-0">
          <button onClick={handleExportPDF} className="btn-secondary">
            <Printer className="w-4 h-4" />
            Export PDF
          </button>
          <button onClick={handleExportJSON} className="btn-secondary">
            <Download className="w-4 h-4" />
            Export JSON
          </button>
        </div>
      </div>

      {/* Building context banner — shown when a Digital Twin building is selected */}
      {selectedBuilding && (() => {
        const b = selectedBuilding
        const riskColors = { high: '#ef4444', critical: '#ef4444', medium: '#f97316', low: '#22c55e', none: '#475569' }
        const riskLabels = { high: 'HIGH RISK', critical: 'CRITICAL', medium: 'MEDIUM RISK', low: 'LOW RISK', none: 'NORMAL' }
        const domainRisks = ['water','energy','waste'].filter(d => b[d]?.level && b[d].level !== 'none' && b[d].level !== 'low')
        const domainColors = { water: '#00b4ff', energy: '#fbbf24', waste: '#a78bfa' }
        const domainIcons  = { water: '💧', energy: '⚡', waste: '♻️' }
        const rc = riskColors[b.risk] || '#475569'
        return (
          <div className="mb-6 rounded-xl overflow-hidden no-print" style={{
            border: '1px solid rgba(0,229,255,0.25)',
            background: 'linear-gradient(135deg, rgba(0,229,255,0.06) 0%, rgba(15,23,42,0.85) 100%)',
          }}>
            <div className="flex items-center justify-between px-5 py-3" style={{
              borderBottom: '1px solid rgba(0,229,255,0.12)',
              background: 'rgba(0,229,255,0.05)',
            }}>
              <div className="flex items-center gap-3">
                <span className="text-xl">{b.icon}</span>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-white">{b.name}</span>
                    <span className="text-xs px-2 py-0.5 rounded-full font-bold"
                      style={{ background: `${rc}18`, border: `1px solid ${rc}55`, color: rc }}>
                      {riskLabels[b.risk] || b.risk?.toUpperCase()}
                    </span>
                  </div>
                  <span className="text-xs text-slate-400">{b.type} · {b.buildingId} · {b.occupancy}</span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-cyan-400 font-medium">Filtered from Digital Twin</span>
                <span className="w-2 h-2 rounded-full bg-cyan-400" style={{ animation: 'pulse 2s infinite' }} />
              </div>
            </div>
            <div className="px-5 py-4 flex flex-wrap gap-6">
              {/* Risk domains */}
              <div className="flex-1 min-w-48">
                <p className="text-xs text-slate-500 mb-2 uppercase tracking-wider font-semibold">Risk Domains</p>
                <div className="flex flex-wrap gap-2">
                  {domainRisks.length ? domainRisks.map(d => (
                    <span key={d} className="flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full font-medium"
                      style={{ background: `${domainColors[d]}18`, border: `1px solid ${domainColors[d]}44`, color: domainColors[d] }}>
                      {domainIcons[d]} {d.charAt(0).toUpperCase()+d.slice(1)} — {b[d]?.value}
                    </span>
                  )) : (
                    <span className="text-xs text-slate-500 italic">No critical domains flagged</span>
                  )}
                </div>
              </div>
              {/* Building-specific recommendations */}
              {b.recommendations?.length > 0 && (
                <div className="flex-1 min-w-56">
                  <p className="text-xs text-slate-500 mb-2 uppercase tracking-wider font-semibold">Building Insights</p>
                  <ul className="space-y-1">
                    {b.recommendations.slice(0, 3).map((r, i) => (
                      <li key={i} className="text-xs text-slate-300 flex items-start gap-1.5">
                        <span className="text-cyan-500 mt-0.5">›</span>
                        {r}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
            {domainRisks.length > 0 && (
              <div className="px-5 pb-3">
                <p className="text-xs text-cyan-500/70 italic">
                  Action items matching risk domains ({domainRisks.join(', ')}) are highlighted below.
                </p>
              </div>
            )}
          </div>
        )
      })()}

      {/* Action plan grid */}
      {(() => {
        const highlightDomains = selectedBuilding
          ? ['water','energy','waste'].filter(d => selectedBuilding[d]?.level && selectedBuilding[d].level !== 'none' && selectedBuilding[d].level !== 'low')
          : []
        return (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <PlanSection sectionKey="immediate"    icon={<Clock        className="w-5 h-5" />}
              title="Immediate Actions"  color="#ef4444" timeline="Within 24 hours"
              items={plan.immediate}    highlightDomains={highlightDomains} />
            <PlanSection sectionKey="next_7_days"  icon={<Calendar     className="w-5 h-5" />}
              title="Next 7 Days"        color="#f97316" timeline="This week — schedule now"
              items={plan.next_7_days}  highlightDomains={highlightDomains} />
            <PlanSection sectionKey="next_30_days" icon={<CalendarDays className="w-5 h-5" />}
              title="Next 30 Days"       color="#eab308" timeline="This month — assign and track"
              items={plan.next_30_days} highlightDomains={highlightDomains} />
            <PlanSection sectionKey="long_term"    icon={<TrendingUp   className="w-5 h-5" />}
              title="Long-Term Strategy" color="#00ff88" timeline="12+ months — sustainability transformation"
              items={plan.long_term}    highlightDomains={highlightDomains} />
          </div>
        )
      })()}

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
              {aiUsed ? 'Generated by AI Core' : 'Rule-based template'}
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
          {orgName
            ? `All recommendations are derived from uploaded ${orgName} data and rule-based agent analysis.`
            : 'All recommendations are generated from simulated sensor data and rule-based agent analysis.'}
          {' '}Consult certified engineering, waste management, and environmental professionals before
          implementing any intervention. RE:GEN AI is a prototype decision-support system and not
          professional regulatory, financial, or engineering advice.
        </p>
      </div>
    </section>
  )
}
