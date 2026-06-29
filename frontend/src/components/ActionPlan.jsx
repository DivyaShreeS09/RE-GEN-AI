import { Clock, Calendar, CalendarDays, TrendingUp, CheckCircle, Download, User, Wrench } from 'lucide-react'

const PRIORITY_CONFIG = {
  immediate:   { label: 'CRITICAL',  color: '#ef4444', bg: 'rgba(239,68,68,0.12)',   border: 'rgba(239,68,68,0.3)' },
  next_7_days: { label: 'HIGH',      color: '#f97316', bg: 'rgba(249,115,22,0.1)',   border: 'rgba(249,115,22,0.3)' },
  next_30_days:{ label: 'MEDIUM',    color: '#eab308', bg: 'rgba(234,179,8,0.1)',    border: 'rgba(234,179,8,0.25)' },
  long_term:   { label: 'STRATEGIC', color: '#00ff88', bg: 'rgba(0,255,136,0.06)',   border: 'rgba(0,255,136,0.25)' },
}

const DOMAIN_OWNERS = {
  water:    { owner: 'Facilities & Maintenance',  icon: '🔧' },
  energy:   { owner: 'Electrical Maintenance',    icon: '⚡' },
  waste:    { owner: 'Sustainability Cell',        icon: '♻️' },
  impact:   { owner: 'Administration Office',     icon: '🏛️' },
  general:  { owner: 'Campus Operations',         icon: '🏗️' },
}

const EFFORT_CONFIG = {
  immediate:    { effort: 'Low',    color: '#22c55e' },
  next_7_days:  { effort: 'Medium', color: '#eab308' },
  next_30_days: { effort: 'Medium', color: '#eab308' },
  long_term:    { effort: 'High',   color: '#f97316' },
}

function PlanSection({ sectionKey, icon, title, color, items, timeline }) {
  const pc = PRIORITY_CONFIG[sectionKey] || PRIORITY_CONFIG.long_term
  const ec = EFFORT_CONFIG[sectionKey] || EFFORT_CONFIG.long_term

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
          <span className="text-xs font-bold px-2 py-0.5 rounded-full" style={{
            background: pc.bg, border: `1px solid ${pc.border}`, color: pc.color
          }}>{pc.label}</span>
          <span className="text-xs px-2 py-0.5 rounded-full" style={{
            background: 'rgba(15,23,42,0.6)', border: '1px solid rgba(255,255,255,0.06)', color: ec.color
          }}>{ec.effort} effort</span>
        </div>
      </div>

      <div className="space-y-3">
        {!items?.length ? (
          <p className="text-xs text-slate-600 italic py-2">No actions in this category</p>
        ) : items.map((item, i) => {
          const domainKey = (item.domain || 'general').toLowerCase()
          const ownerInfo = DOMAIN_OWNERS[domainKey] || DOMAIN_OWNERS.general

          return (
            <div key={i} className="flex items-start gap-3 p-3 rounded-lg" style={{
              background: 'rgba(15,23,42,0.5)', border: '1px solid rgba(255,255,255,0.04)'
            }}>
              <CheckCircle className="w-4 h-4 flex-shrink-0 mt-0.5" style={{ color }} />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-slate-200 leading-relaxed">{item.action}</p>
                <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-2">
                  <span className="text-xs text-slate-500 uppercase tracking-wide">{item.domain || 'General'}</span>
                  {item.estimated_saving_inr > 0 && (
                    <span className="text-xs text-green-400">≈ ₹{item.estimated_saving_inr?.toFixed(0)} est. saving</span>
                  )}
                  {item.priority_score != null && (
                    <span className="text-xs text-cyan-400">Score: {item.priority_score?.toFixed(1)}</span>
                  )}
                </div>
                <div className="flex items-center gap-3 mt-2">
                  <div className="flex items-center gap-1.5">
                    <User className="w-3 h-3 text-slate-500" />
                    <span className="text-xs text-slate-500">{ownerInfo.icon} {ownerInfo.owner}</span>
                  </div>
                  {item.timeline && (
                    <span className="text-xs px-2 py-0.5 rounded" style={{
                      background: 'rgba(0,229,255,0.06)', border: '1px solid rgba(0,229,255,0.12)', color: '#7dd3fc'
                    }}>{item.timeline}</span>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default function ActionPlan({ data }) {
  if (!data) return null

  const plan = data?.report?.action_plan || data?.action_plan
  const summary = data?.report?.executive_summary || data?.executive_summary
  if (!plan) return null

  const handleExport = () => {
    const exportData = {
      generated: new Date().toISOString(),
      system: 'RE:GEN AI — Sustainability Command Center',
      disclaimer: 'Prototype decision-support system. All data simulated. Not professional advice.',
      action_plan: plan,
      executive_summary: summary || '',
    }
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `regen-ai-action-plan-${Date.now()}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <section className="px-6 py-16 max-w-7xl mx-auto" id="action-plan">
      <div className="flex items-start justify-between mb-8">
        <div>
          <h2 className="text-3xl font-black text-white mb-2">
            Sustainability <span className="text-gradient-green">Action Plan</span>
          </h2>
          <p className="text-slate-400 text-sm">
            Agent-prioritized interventions ranked by urgency × cost-saving × environmental impact × feasibility.
          </p>
        </div>
        <button onClick={handleExport} className="btn-secondary flex-shrink-0">
          <Download className="w-4 h-4" />
          Export Plan
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <PlanSection sectionKey="immediate" icon={<Clock className="w-5 h-5" />}
          title="Immediate Actions" color="#ef4444" timeline="Within 24 hours" items={plan.immediate} />
        <PlanSection sectionKey="next_7_days" icon={<Calendar className="w-5 h-5" />}
          title="Next 7 Days" color="#f97316" timeline="This week — schedule now" items={plan.next_7_days} />
        <PlanSection sectionKey="next_30_days" icon={<CalendarDays className="w-5 h-5" />}
          title="Next 30 Days" color="#eab308" timeline="This month — assign and track" items={plan.next_30_days} />
        <PlanSection sectionKey="long_term" icon={<TrendingUp className="w-5 h-5" />}
          title="Long-Term Strategy" color="#00ff88" timeline="12+ months — campus transformation" items={plan.long_term} />
      </div>

      {/* Effort legend */}
      <div className="flex flex-wrap gap-4 mb-8 text-xs text-slate-500">
        <span className="font-semibold text-slate-400">Priority labels:</span>
        {[
          { label: 'CRITICAL', color: '#ef4444' }, { label: 'HIGH', color: '#f97316' },
          { label: 'MEDIUM', color: '#eab308' },   { label: 'STRATEGIC', color: '#00ff88' },
        ].map(p => (
          <span key={p.label} className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full inline-block" style={{ background: p.color }} />
            <span style={{ color: p.color }}>{p.label}</span>
          </span>
        ))}
        <span className="ml-4 font-semibold text-slate-400">Effort:</span>
        {['Low', 'Medium', 'High'].map(e => (
          <span key={e} className="text-slate-500">{e}</span>
        ))}
      </div>

      {/* Executive Summary */}
      {summary && (
        <div className="glass-card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-purple-400 uppercase tracking-wider flex items-center gap-2">
              <Wrench className="w-4 h-4" /> Executive Summary
            </h3>
            <span className="text-xs text-slate-600">Generated by Report Agent · confidence 0.95</span>
          </div>
          <pre className="text-xs text-slate-300 whitespace-pre-wrap leading-relaxed font-mono">{summary}</pre>
        </div>
      )}

      <div className="mt-6 p-4 rounded-lg text-center" style={{
        background: 'rgba(234,179,8,0.04)', border: '1px solid rgba(234,179,8,0.12)'
      }}>
        <p className="text-xs text-yellow-700 leading-relaxed">
          All recommendations are generated from simulated sensor data and rule-based agent analysis.
          Consult certified engineering, waste management, and environmental professionals before implementing any intervention.
        </p>
      </div>
    </section>
  )
}
