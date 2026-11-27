import {
  BrainCircuit,
  History,
  ShieldCheck,
  AlertTriangle,
  GitBranch,
  IndianRupee,
} from 'lucide-react'

const humanize = value =>
  String(value ?? 'Unknown').replaceAll('_', ' ')

const money = value =>
  typeof value === 'number' && Number.isFinite(value)
    ? new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
      }).format(value / 100)
    : 'Not established'

const formatTime = value => {
  const date = new Date(value)
  return Number.isNaN(date.getTime())
    ? 'Time unavailable'
    : date.toLocaleString()
}

function Metric({ label, value }) {
  return (
    <div className="rounded-xl border border-slate-700/60 bg-slate-950/50 p-4">
      <p className="text-xs text-slate-400 uppercase tracking-wide">
        {label}
      </p>
      <p className="mt-2 text-lg font-semibold text-slate-100 capitalize">
        {value}
      </p>
    </div>
  )
}

export default function RecoveryIntelligence({ mission }) {
  if (!mission) return null

  const events = mission.events ?? []
  const result = mission.result ?? {}
  const options = result.options ?? []

  const decisions = events.filter(
    entry => entry.intelligence
  )

  const decision = decisions.at(-1)?.intelligence

  const selected = options.find(
    option => option.service_id === decision?.selected_service_id
  )

  const isAnalysis = mission.inputs?.kind === 'analysis'

  const activeProposal =
    mission.state === 'awaiting_approval' && Boolean(selected)

  const alternatives = decision?.alternatives ?? []

  const currentIds = new Set(
    options.map(option => option.service_id)
  )

  const provider = decision?.source === 'ai'
    ? [decision.provider, decision.model]
        .filter(Boolean).join(' / ') || 'AI provider'
    : decision
      ? 'Deterministic'
      : 'Not recorded'

  return (
    <section className="glass-card p-5 md:p-7 my-6 space-y-6">
      <header className="flex items-start gap-3">
        <BrainCircuit className="w-7 h-7 text-emerald-400 shrink-0" />
        <div>
          <h3 className="text-xl font-bold">
            {isAnalysis
              ? 'Resource Investigation Intelligence'
              : 'Waste-to-Wealth Intelligence'}
          </h3>
          <p className="text-sm text-slate-400 mt-1">
            Recorded decisions, evidence and mission history.
          </p>
        </div>
      </header>

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">
        <Metric label="Mission state" value={humanize(mission.state)} />
        <Metric label="Recorded events" value={events.length} />
        <Metric
          label={isAnalysis ? 'Pending investigations' : 'Current options'}
          value={isAnalysis ? (result.pending ?? []).length : options.length}
        />
        <Metric
          label={isAnalysis ? 'Recorded findings' : 'Decision engine'}
          value={isAnalysis ? (result.findings ?? []).length : provider}
        />
      </div>

      {!isAnalysis && (
        <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-5">
          <div className="flex items-center gap-2 mb-3">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            <h4 className="font-semibold">
              {activeProposal
                ? 'Current recovery recommendation'
                : 'Recovery decision record'}
            </h4>
          </div>

          {activeProposal ? (
            <>
              <p className="text-xl font-semibold capitalize">
                {humanize(selected.pathway)}
              </p>
              <p className="text-sm text-slate-300 mt-1">
                {selected.organization}
              </p>
              <div className="flex items-center gap-2 mt-4">
                <IndianRupee className="w-5 h-5 text-emerald-400" />
                <span className="text-xl font-semibold">
                  {money(selected.net_paise)}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Current quoted net value. Not realized revenue.
              </p>
              <p className="text-sm text-slate-300 mt-3">
                {selected.rationale}
              </p>
              <p className="text-sm text-amber-300 mt-3">
                Authorized facility approval is required.
              </p>
            </>
          ) : (
            <p className="text-sm text-slate-400">
              {decision
                ? 'A previous decision is recorded below. It is not an active approval recommendation.'
                : 'No intelligence recommendation has been recorded for this mission.'}
            </p>
          )}

          {decision && (
            <div className="mt-4 pt-4 border-t border-slate-700/60">
              <p className="text-xs text-slate-400">
                Recorded decision engine: {provider}
              </p>
              <p className="text-xs text-slate-400 mt-1">
                Inference attempts: {decision.inference_attempts ?? 'Not recorded'}
              </p>

              {(decision.evidence_gaps ?? []).length > 0 && (
                <div className="mt-4">
                  <h4 className="flex items-center gap-2 text-amber-300 text-sm">
                    <AlertTriangle className="w-4 h-4" />
                    Evidence gaps at decision time
                  </h4>
                  <ul className="mt-2 space-y-1 text-sm text-slate-300">
                    {decision.evidence_gaps.map((gap, index) => (
                      <li key={index}>- {gap}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {!isAnalysis && alternatives.length > 0 && (
        <div>
          <h4 className="flex items-center gap-2 font-semibold mb-3">
            <GitBranch className="w-5 h-5 text-cyan-400" />
            Recovery alternative comparison
          </h4>
          <p className="text-xs text-slate-400 mb-3">
            Historical planning comparison. Current eligibility is checked separately.
          </p>
          <div className="overflow-x-auto rounded-xl border border-slate-700/60">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-900">
                <tr>
                  {['Pathway', 'Net benefit', 'Trade-off', 'Evidence gaps', 'Availability'].map(label => (
                    <th key={label} className="p-3 font-medium text-slate-400">
                      {label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {alternatives.map(item => (
                  <tr key={item.service_id} className="border-t border-slate-800">
                    <td className="p-3 capitalize">
                      {humanize(item.pathway)}
                      {item.service_id === decision.selected_service_id && (
                        <span className="block text-xs text-emerald-400">
                          Selected at planning
                        </span>
                      )}
                    </td>
                    <td className="p-3 whitespace-nowrap">
                      {money(item.net_benefit_paise)}
                    </td>
                    <td className="p-3">
                      {item.pareto_efficient
                        ? 'Non-dominated'
                        : 'Other alternative'}
                    </td>
                    <td className="p-3 text-slate-400">
                      {(item.evidence_gaps ?? []).join('; ') || 'None flagged'}
                    </td>
                    <td className="p-3">
                      {mission.state === 'awaiting_approval'
                        ? currentIds.has(item.service_id)
                          ? 'Currently listed'
                          : 'Not currently listed'
                        : 'Historical'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {isAnalysis && (
        <div className="space-y-3">
          <h4 className="font-semibold">Investigation findings</h4>
          {(result.findings ?? []).map((finding, index) => (
            <div key={index} className="rounded-lg border border-slate-700 p-3">
              <p className="capitalize">
                {humanize(finding.metric ?? finding.action)}
              </p>
              {finding.value != null && (
                <p className="text-lg font-semibold">
                  {finding.value} {finding.unit}
                </p>
              )}
              <p className="text-xs text-slate-400">
                Evidence: {humanize(finding.evidence_type)}
              </p>
            </div>
          ))}
          {!(result.findings ?? []).length && (
            <p className="text-sm text-slate-400">
              No findings recorded.
            </p>
          )}
        </div>
      )}

      <div>
        <h4 className="flex items-center gap-2 font-semibold mb-4">
          <History className="w-5 h-5 text-cyan-400" />
          Agent execution history
        </h4>

        <ol className="border-l border-slate-700 ml-2 pl-5 space-y-5">
          {events.map((entry, index) => {
            const planner = entry.evidence?.planner
            const intelligence = entry.intelligence

            return (
              <li key={index} className="relative">
                <span className="absolute -left-[25px] top-1.5 w-2 h-2 rounded-full bg-cyan-400" />
                <time className="text-xs text-slate-500">
                  {formatTime(entry.at)}
                </time>
                <p className="text-sm font-semibold text-slate-200 mt-1">
                  {entry.agent}
                </p>
                <p className="text-xs text-cyan-300 capitalize">
                  {humanize(entry.action)}
                </p>
                {entry.reason && (
                  <p className="text-sm text-slate-400 mt-1">
                    {entry.reason}
                  </p>
                )}
                {planner && (
                  <p className="text-xs text-slate-400 mt-2">
                    Selected tool: {humanize(planner.tool)} |
                    Source: {planner.source}
                    {planner.provider ? ` | ${planner.provider}` : ''}
                  </p>
                )}
                {intelligence && (
                  <p className="text-xs text-emerald-400 mt-2">
                    Compared {intelligence.alternatives?.length ?? 0} alternatives |
                    Source: {intelligence.source}
                  </p>
                )}
              </li>
            )
          })}
        </ol>

        {!events.length && (
          <p className="text-sm text-slate-400">
            No execution events recorded.
          </p>
        )}
      </div>

      <p className="text-xs text-slate-500">
        Mission {mission.id} | Checkpoint {mission.version}.
        Recommendations are not proof of completed recovery.
      </p>
    </section>
  )
}

function MissionBudget({ mission }) {
  const decisions = (mission.events || [])
    .filter(entry => entry.intelligence?.mission_budget)

  const latest = decisions.at(-1)?.intelligence?.mission_budget

  const used = mission.recorded_inference_attempts ?? (mission.inputs?.kind === 'analysis'
    ? mission.result?.inference_attempts || 0
    : latest?.recorded_attempts || 0)

  const limit = 3

  return (
    <div className="rounded-xl border border-slate-700 p-4 my-4">
      <div className="flex justify-between items-center">
        <span className="font-semibold">Recorded AI inference budget</span>
        <span className="text-sm">{used} / {limit}</span>
      </div>

      <progress
        value={Math.min(used, limit)}
        max={limit}
        className="w-full h-2 my-3 accent-emerald-500"
      />

      <p className="text-xs text-slate-400">
        {used >= limit
          ? 'Budget exhausted. Deterministic planning remains available.'
          : 'Provider attempts are bounded to conserve inference resources.'}
      </p>
    </div>
  )
}

export { MissionBudget }
