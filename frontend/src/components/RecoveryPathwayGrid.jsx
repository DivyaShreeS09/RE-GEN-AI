import {
  Gem, Recycle, HeartHandshake, Wrench,
  Scissors, Leaf, Network, ShieldCheck,
  MapPin, ChevronDown, ExternalLink,
  Info, Sparkles, IndianRupee
} from 'lucide-react'

const styles = {
  sell: [Gem, '#34d399', 'Financial recovery'],
  reuse: [Leaf, '#2dd4bf', 'Resource preservation'],
  repair: [Wrench, '#38bdf8', 'Value restoration'],
  upcycle: [Scissors, '#c084fc', 'Creative recovery'],
  donate: [HeartHandshake, '#f472b6', 'Social contribution'],
  recycle: [Recycle, '#38bdf8', 'Material recovery'],
  compost: [Leaf, '#84cc16', 'Organic recovery'],
  collective: [Network, '#a78bfa', 'Collective recovery'],
  professional: [ShieldCheck, '#fbbf24', 'Professional recovery'],
}

const currency = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 2,
})

function money(value) {
  return currency.format(value)
}

function validAmount(value) {
  return typeof value === 'number' && Number.isFinite(value)
}

function range(low, high) {
  if (!validAmount(low) || !validAmount(high)) return null
  return low === high
    ? money(low)
    : `${money(low)} - ${money(high)}`
}

function safeUrl(value) {
  try {
    const url = new URL(value)
    return url.protocol === 'https:' && !url.username && !url.password ? url.href : null
  } catch {
    return null
  }
}

function Rating({ label, value, risk = false }) {
  const normalized = String(value || '').toLowerCase()

  const level = {
    low: 1,
    medium: 2,
    high: 3,
  }[normalized] || 0

  const color = level === 0
    ? '#64748b'
    : level === 2
      ? '#fbbf24'
      : (risk ? level === 1 : level === 3)
        ? '#34d399'
        : '#fb7185'

  return (
    <div className="min-w-0">
      <div className="text-[11px] text-slate-400">
        {label}
      </div>
      <div
        className="mt-1 text-xs font-semibold capitalize"
        style={{ color }}
      >
        {level ? normalized : 'Unassessed'}
      </div>
      <div className="mt-2 flex gap-1">
        {[1, 2, 3].map(segment => (
          <span
            key={segment}
            className="h-1 flex-1 rounded-full"
            style={{
              backgroundColor:
                segment <= level ? color : '#253447'
            }}
          />
        ))}
      </div>
    </div>
  )
}

const researchLabels = {
  reviewed_reference: 'Reviewed reference',
  live_research: 'Public research - acceptance unconfirmed',
  cached_research: 'Cached research - acceptance unconfirmed',
  verified_quotation: 'Verified directory quotation',
}

function Valuation({ route }) {
  const value = route.valuation || {}
  const rate = range(value.rate_min_inr, value.rate_max_inr)
  const rateOnly = value.status === 'rate_only' && Boolean(rate)

  const estimate = range(
    value.minimum_inr,
    value.maximum_inr
  )

  const net = range(
    value.net_minimum_inr,
    value.net_maximum_inr
  )

  const label = {
    avoided_purchase: 'Potential avoided expenditure',
    gross_service_quote: 'Projected gross quotation',
    net_service_quote: 'Projected net quotation',
    direct_cash_return: 'Direct cash return',
    gross_reference: 'Indicative gross market value',
    treatment_cost: 'Estimated treatment cost',
    refurbishment_cost: 'Estimated refurbishment cost',
    output_revenue: 'Estimated gross output revenue',
  }[value.value_type] || 'Estimated financial potential'

  return (
    <div className="rounded-xl border border-white/5 bg-black/20 p-4">
      <div className="flex items-center gap-1.5 text-xs text-slate-400">
        <IndianRupee size={13} />
        {label}
      </div>

      <div className="mt-1 text-2xl font-bold tracking-tight text-emerald-400">
        {estimate || (rateOnly
          ? `${rate} / ${value.unit}`
          : 'Quote required')}
      </div>

      {rateOnly && (
        <p className="mt-2 text-xs text-slate-400">
          Published indicative buying rate.
          Multiply by eligible measured {value.unit === 'kg' ? 'weight' : 'quantity'} to estimate total recovery.
        </p>
      )}

      {net && (
        <div className="mt-1 text-xs text-emerald-300">
          Estimated net: {net}
        </div>
      )}

      <p className="mt-2 text-xs leading-relaxed text-slate-400">
        {value.clarification || value.reason || 'Compatible market evidence is unavailable.'}
      </p>

      {route.category === 'donate' && (
        <p className="mt-1 text-xs text-pink-300">
          Social contribution rather than sale income.
        </p>
      )}

      {(estimate || rateOnly) && (
        <details className="mt-2 text-xs">
          <summary className="cursor-pointer text-cyan-400">
            Valuation basis
          </summary>
          <div className="mt-2 space-y-1 text-slate-400">
            {rate && !rateOnly && (
              <p>
                Rate: {range(
                  value.rate_min_inr,
                  value.rate_max_inr
                )} / {value.output_unit || value.unit}
              </p>
            )}
            {researchLabels[value.provenance] && <p>{researchLabels[value.provenance]}</p>}
            {value.saleable_output_per_input_unit != null && <p>Saleable yield: {value.saleable_output_per_input_unit} {value.output_unit} per {value.unit}</p>}
            {value.quantity_estimated &&
              validAmount(value.quantity_min) &&
              validAmount(value.quantity_max) && (
                <p>
                  Estimated weight: {value.quantity_min.toFixed(2)}
                  {' - '}
                  {value.quantity_max.toFixed(2)} {value.unit}
                </p>
            )}
            {value.quantity != null && (
              <p>Quantity: {value.quantity} {value.unit}</p>
            )}
            {value.costs_inr != null && <p>Documented estimated costs: {money(value.costs_inr)}</p>}
            {value.evidence_type && <p>Evidence: {value.evidence_type.replaceAll("_", " ")}</p>}
            {value.geographic_basis && <p>Coverage: {value.geographic_basis.replaceAll("_", " ")}</p>}
            {value.applicability && <p>{value.applicability}</p>}
            {value.locality && <p>Area: {value.locality}</p>}
            {value.observed_on && (
              <p>Evidence date: {value.observed_on}</p>
            )}
            {value.freshness && (
              <p>{value.freshness.replaceAll('_', ' ')}</p>
            )}
            {safeUrl(value.source_url) && (
              <a
                href={safeUrl(value.source_url)}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 text-cyan-400"
              >
                Market reference <ExternalLink size={11} />
              </a>
            )}
          </div>
        </details>
      )}
    </div>
  )
}

function Services({ route, researching }) {
  const verified = route.verified_services || []
  const publicLeads = route.public_services || []
  const mapLinks = route.maps_search_links || []

  const messages = {
    pending: 'Service research is still in progress.',
    pin_not_provided: 'Enter a PIN code to discover local services.',
    no_compatible_evidence: 'No compatible documented service was found for this pathway.',
    provider_unavailable: 'Optional research is unavailable. You can still check services using the Maps searches below.',
    deadline_reached: 'Optional research reached its time limit. Use the Maps searches below to check services.',
    authorized_service_required: 'An appropriately authorized service is required.',
  }

  return (
    <details className="group mt-auto border-t border-white/10 pt-3">
      <summary className="flex cursor-pointer list-none items-center gap-2 text-sm font-medium text-cyan-400">
        <MapPin size={15} />
        <span className="flex-1">Recommended local and remote services</span>
        <span className="text-xs text-slate-400">
          {verified.length + publicLeads.length || ''}
        </span>
        <ChevronDown
          size={15}
          className="transition-transform group-open:rotate-180"
        />
      </summary>

      <div className="mt-3 space-y-3">
        {verified.map((service, index) => (
          <div
            key={`verified-${service.service_id || index}`}
            className="rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-3"
          >
            <div className="flex items-start gap-2">
              <ShieldCheck
                size={15}
                className="mt-0.5 shrink-0 text-emerald-400"
              />
              <div>
                <p className="text-sm font-medium text-slate-100">
                  {service.organization}
                </p>
                <p className="mt-1 text-xs text-emerald-400">
                  Eligible directory service
                </p>
              </div>
            </div>

            {validAmount(service.net_paise) && (
              <p className="mt-2 text-xs text-emerald-300">
                Projected net: {money(service.net_paise / 100)}
              </p>
            )}

            {service.next_action && (
              <p className="mt-2 text-xs text-slate-400">
                {service.next_action}
              </p>
            )}

            {service.quote_expires && (
              <p className="mt-1 text-xs text-slate-500">
                Quote expires: {service.quote_expires}
              </p>
            )}
          </div>
        ))}

        {publicLeads.map((service, index) => (
          <div
            key={`public-${service.source_url || index}`}
            className="rounded-lg border border-white/10 bg-white/[0.025] p-3"
          >
            <p className="text-sm font-medium text-slate-100">
              {service.organization}
            </p>
            <p className="mt-1 text-xs text-amber-400">
              Public lead · acceptance unconfirmed{service.evidence_type !== 'google_places' && researchLabels[service.provenance] ? " · " + researchLabels[service.provenance] : ""}
            </p>
            {service.evidence_type === 'google_places' && <p translate="no" className="whitespace-nowrap text-xs">Google Maps</p>}
            {service.coverage === 'remote_coverage' &&
              <p className="text-xs text-slate-400">Remote service · transfer terms require confirmation</p>}
            {service.coverage === 'documented_region' &&
              <p className="mt-1 text-xs text-slate-400">Documented regional service · exact PIN and pickup unconfirmed</p>}
            {validAmount(service.distance_km) && (
              <p className="mt-1 text-xs text-slate-400">
                Approx. {service.distance_km} km straight-line from postal centroid
              </p>
            )}
            <p className="mt-2 text-xs text-slate-400">
              {service.locality && <>{service.locality}. </>}{service.description || "Material acceptance, pricing and pickup are unconfirmed."}
            </p>
            {safeUrl(service.source_url) && (
              <a
                href={safeUrl(service.source_url)}
                target="_blank"
                rel="noreferrer"
                className="mt-2 inline-flex items-center gap-1 text-xs text-cyan-400"
              >
                View public listing <ExternalLink size={12} />
              </a>
            )}
          </div>
        ))}

        {!verified.length && !publicLeads.length && (
          <p className="text-xs leading-relaxed text-slate-400">
            {messages[route.discovery_status] || (researching && "Researching service evidence…")
              || 'No compatible service has been established.'}
          </p>
        )}

        {publicLeads.some(lead => lead.source === "OpenStreetMap contributors") && (
          <a
            href="https://www.openstreetmap.org/copyright"
            target="_blank"
            rel="noreferrer"
            className="text-[10px] text-slate-500"
          >
            OpenStreetMap contributors, ODbL
          </a>
        )}

        {mapLinks.length > 0 && <div className="flex flex-wrap gap-3">
          {mapLinks.map(link => <a key={link.url} href={safeUrl(link.url)} target="_blank" rel="noreferrer"
            className="inline-flex items-center gap-1 text-xs text-cyan-400">
            Search Google Maps · {link.label} <ExternalLink size={12} />
          </a>)}
        </div>}
        <p className="text-[11px] text-slate-500">
          Confirm acceptance through responsible adults or authorized facility staff before arranging a handover.
        </p>
      </div>
    </details>
  )
}

function PathwayCard({ route, index, researching }) {
  const [Icon, color, label] =
    styles[route.category] || styles[route.service_pathway] || styles.professional

  return (
    <article
      className={`flex min-w-0 flex-col gap-4 rounded-2xl border p-5
        transition-colors
        ${index === 0
          ? 'border-emerald-500/40'
          : 'border-slate-700/70 hover:border-slate-600'
        }`}
      style={{
        background: 'linear-gradient(145deg, #101c29, #0b1320)'
      }}
    >
      <header className="flex items-center gap-3">
        <div
          className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl"
          style={{ backgroundColor: `${color}18`, color }}
        >
          <Icon size={22} />
        </div>

        <div className="min-w-0">
          <p
            className="text-[10px] font-semibold uppercase tracking-widest"
            style={{ color }}
          >
            {String(index + 1).padStart(2, '0')} / {label}
          </p>
          <h3 className="mt-1 text-base font-semibold leading-snug text-slate-100">
            {route.title}
          </h3>
        </div>
      </header>

      {(route.conditional_completion || route.prerequisite) && <p className="text-xs text-amber-300">
        Conditional · {route.prerequisite}
      </p>}
      <Valuation route={route} />
      {route.ranking_reason && <p className="text-xs text-slate-400">{route.ranking_reason}</p>}

      <p className="text-sm leading-relaxed text-slate-300">
        {route.action}
      </p>

      {route.benefit && (
        <p className="text-xs leading-relaxed text-emerald-300/90">
          {route.benefit}
        </p>
      )}

      <div className="grid grid-cols-3 gap-3 rounded-lg bg-black/15 p-3">
        <Rating label="Feasibility" value={route.feasibility} />
        <Rating label="Env. Impact" value={route.environmental_impact} />
        <Rating label="Risk" value={route.risk} risk />
      </div>

      <details className="text-xs">
        <summary className="cursor-pointer text-slate-400">
          Preparation and limitations
        </summary>
        <div className="mt-3 space-y-3 leading-relaxed text-slate-300">
          {route.preparation && (
            <p>
              <strong className="text-slate-200">Preparation: </strong>
              {route.preparation}
            </p>
          )}
          {route.recipient_type && (
            <p>
              <strong className="text-slate-200">Suitable recipient: </strong>
              {route.recipient_type}
            </p>
          )}
          {route.limitation && (
            <p>
              <strong className="text-amber-400">Limitation: </strong>
              {route.limitation}
            </p>
          )}
        </div>
      </details>

      <Services route={route} researching={researching} />
    </article>
  )
}

export default function RecoveryPathwayGrid({ item }) {
  if (!item) return null

  const intelligence = item.intelligence || {}
  const investigation = intelligence.investigation || {}
  const pathways = intelligence.pathways || []

  return (
    <section className="mt-6 space-y-5">
      <div className="rounded-2xl border border-cyan-500/15 bg-cyan-500/[0.035] p-5">
        <div className="flex items-center gap-2 text-sm font-semibold text-cyan-400">
          <Sparkles size={17} />
          Material intelligence
        </div>

        <h3 className="mt-2 text-lg font-semibold text-slate-100">
          {item.material}
        </h3>

        <p className="mt-1 text-xs text-slate-400">
          {item.quantity} {item.unit} / {item.condition}
        </p>

        {item.postal_locality?.name && <p className="text-sm text-slate-400">
          Reviewed postal locality: {item.postal_locality.name}
        </p>}
        {intelligence.research_status === 'deadline_reached' &&
          <p className="text-sm text-slate-400">Optional research reached its time limit. Available evidence is shown below.</p>}
        {intelligence.research_status === 'provider_unavailable' &&
          <p className="text-sm text-slate-400">Optional research is temporarily unavailable.</p>}
        {intelligence.material_identity?.analysis?.state === 'offline_or_budget_exhausted' &&
          <p className="text-sm text-slate-400">This material uses validated fallback guidance.</p>}
        {intelligence.material_identity?.analysis?.state === 'inference_unavailable' &&
          <p className="text-sm text-slate-400">Model interpretation was unavailable. This material uses validated fallback guidance.</p>}
        {investigation.condition_assessment && (
          <p className="mt-3 text-sm leading-relaxed text-slate-300">
            {investigation.condition_assessment}
          </p>
        )}

        {investigation.hidden_opportunity && (
          <p className="mt-2 text-sm leading-relaxed text-emerald-300">
            {investigation.hidden_opportunity}
          </p>
        )}
      </div>

      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-lg font-semibold text-slate-100">
          Recovery Pathway Comparison
        </h3>
        <span className="text-xs text-slate-400">
          {pathways.length} alternatives
        </span>
      </div>

      {pathways.length < 4 && intelligence.exclusion_reason && (
        <p className="text-sm text-slate-400">{intelligence.exclusion_reason}</p>
      )}

      {pathways.length ? (
        <div className="grid grid-cols-1 items-stretch gap-4 md:grid-cols-2">
          {pathways.slice(0, 4).map((route, index) => (
            <PathwayCard
              key={`${route.category}-${index}`}
              route={route}
              index={index}
              researching={intelligence.research_status === "pending"}
            />
          ))}
        </div>
      ) : (
        <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-5 text-sm text-amber-300">
          No validated recovery pathways are available.
          Additional material information or another analysis may be required.
        </div>
      )}

      <div className="flex items-start gap-2 text-xs leading-relaxed text-slate-500">
        <Info size={15} className="shrink-0" />
        <p>
          Financial estimates are not guaranteed earnings.
          Pathways are alternatives, not cumulative revenue.
          Ratings are qualitative. A responsible adult or authorized facility staff should arrange any handover.
        </p>
      </div>
    </section>
  )
}
