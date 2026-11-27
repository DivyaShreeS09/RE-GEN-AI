import { useState } from 'react'
import ServiceRegistration from './ServiceRegistration'
import {
  listRecoveryServices,
  reviewRecoveryService,
} from '../api'

export default function PartnerDirectory() {
  const [records, setRecords] = useState([])
  const [loaded, setLoaded] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [filter, setFilter] = useState('all')

  async function refresh() {
    setBusy(true)
    setError('')

    try {
      const { data } = await listRecoveryServices()
      setRecords(data)
      setLoaded(true)
    } catch {
      setRecords([])
      setLoaded(false)
      setError('Directory unavailable. Administrator access is required.')
    } finally {
      setBusy(false)
    }
  }

  async function review(event, record) {
    event.preventDefault()

    const form = new FormData(event.currentTarget)
    const decision = form.get('decision')
    const expiry = form.get('expiry')

    setBusy(true)
    setError('')
    setNotice('')

    try {
      await reviewRecoveryService(record.id, {
        decision,
        confirmation_ref: form.get('confirmation'),
        verification_expires: expiry
          ? new Date(expiry).toISOString()
          : null,
        publication_ref: form.get('publication_ref') || null,
      })

      setNotice('Directory review recorded.')
      await refresh()
    } catch {
      setError(
        'Review rejected. Independent administrator review and current evidence are required.'
      )
    } finally {
      setBusy(false)
    }
  }

  const visible = records.filter(
    record => filter === 'all' || record.status === filter
  )

  return (
    <section className="glass-card p-5 md:p-7 my-6 space-y-5">
      <header>
        <h2 className="text-xl font-bold">
          Recovery Partner Directory
        </h2>
        <p className="text-sm text-slate-400 mt-2">
          Facility-managed service records and independent verification.
          No external contact is initiated.
        </p>
      </header>

      <button
        type="button"
        className="btn-primary"
        disabled={busy}
        onClick={refresh}
      >
        {busy ? 'Loading...' : 'Load facility directory'}
      </button>

      {error && <p role="alert" className="text-red-400">{error}</p>}
      {notice && <p role="status" className="text-emerald-400">{notice}</p>}

      {loaded && <ServiceRegistration onRegistered={refresh} />}

      {loaded && (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {[
              ['Loaded records', records.length],
              ['Verified status', records.filter(r => r.status === 'verified').length],
              ['Pending', records.filter(r => r.status === 'pending').length],
              ['Inactive', records.filter(r => ['suspended', 'revoked'].includes(r.status)).length],
            ].map(([label, value]) => (
              <div key={label} className="rounded-xl border border-slate-700 p-4">
                <p className="text-xs text-slate-400">{label}</p>
                <p className="text-2xl font-semibold mt-2">{value}</p>
              </div>
            ))}
          </div>

          <p className="text-xs text-slate-400">
            Recorded verification status is not a guarantee of current eligibility.
            Mission matching independently checks expiry and capacity.
          </p>

          <label className="block">
            Filter by status
            <select
              className="ml-3 bg-slate-900 border border-slate-700 rounded p-2"
              value={filter}
              onChange={e => setFilter(e.target.value)}
            >
              {['all', 'pending', 'verified', 'suspended', 'revoked'].map(status => (
                <option key={status} value={status}>{status}</option>
              ))}
            </select>
          </label>

          {visible.map(record => (
            <article
              key={record.id}
              className="rounded-xl border border-slate-700 p-5 space-y-3"
            >
              <h3 className="font-semibold text-lg">
                {record.organization}
              </h3>

              <p className="text-sm text-cyan-300 capitalize">
                {record.pathway} | {record.material} | {record.status}
              </p>

              <div className="grid sm:grid-cols-2 gap-3 text-sm">
                <p>Condition: {record.condition}</p>
                <p>Capacity remaining: {record.remaining_g / 1000} kg</p>
                <p>Registered capacity: {record.capacity_g / 1000} kg</p>
                <p>Service expiry: {new Date(record.expires).toLocaleString()}</p>
                <p>Verification expiry: {record.verification_expires
                  ? new Date(record.verification_expires).toLocaleString()
                  : 'Not recorded'}</p>
                <p>PIN coverage: {record.service_pins.join(', ')}</p>
                <p>Quoted INR/kg: {record.quote_paise_per_kg == null
                  ? 'Unavailable'
                  : (record.quote_paise_per_kg / 100).toFixed(2)}</p>
                <p>Quote expiry: {record.quote_expires
                  ? new Date(record.quote_expires).toLocaleString()
                  : 'Not recorded'}</p>
              </div>

              <div className="rounded-lg bg-slate-950/50 p-4">
                <h4 className="font-semibold mb-3">
                  Documented recovery economics
                </h4>

                <div className="grid sm:grid-cols-2 gap-3 text-sm">
                  {[
                    ['Service fees', record.fees_paise],
                    ['Transport', record.transport_paise],
                    ['Preparation', record.preparation_paise],
                    ['Avoided purchase', record.avoided_purchase_paise],
                  ].map(([label, amount]) => (
                    <p key={label}>
                      {label}: {amount == null
                        ? 'Unavailable'
                        : new Intl.NumberFormat('en-IN', {
                            style: 'currency',
                            currency: 'INR',
                          }).format(amount / 100)}
                    </p>
                  ))}

                  <p>Effort: {record.effort || 'Not recorded'}</p>
                  <p>Transfer: {record.transfer || 'Not recorded'}</p>

                  <p>
                    Avoided CO2e per kg: {
                      record.avoided_co2e_g_per_kg == null
                        ? 'Unavailable'
                        : `${record.avoided_co2e_g_per_kg / 1000} kg`
                    }
                  </p>

                  <p>
                    Environmental source:
                    {' '}{record.environmental_evidence || 'Not recorded'}
                  </p>
                </div>

                <p className="text-sm mt-3">
                  Preparation: {record.preparation || 'Not recorded'}
                </p>
              </div>

              <details>
                <summary className="cursor-pointer text-cyan-300">
                  Evidence and audit history
                </summary>
                <div className="text-sm space-y-2 mt-3">
                  <p>Identity: {record.identity_evidence}</p>
                  <p>Acceptance: {record.acceptance_evidence}</p>
                  <p>Consent: {record.consent_evidence}</p>
                  <p>Regulatory: {record.regulatory_evidence || 'Not recorded'}</p>

                  {(record.audit ?? []).map((entry, index) => (
                    <p key={index} className="text-xs text-slate-400">
                      {new Date(entry.at).toLocaleString()} |
                      {entry.action} | {entry.evidence || 'No reference'}
                    </p>
                  ))}
                </div>
              </details>

              <details>
                <summary className="cursor-pointer text-emerald-300">
                  Independent administrator review
                </summary>

                <form
                  className="grid gap-3 mt-4"
                  onSubmit={event => review(event, record)}
                >
                  <label>
                    Review decision
                    <select name="decision" required defaultValue="">
                      <option value="" disabled>Select decision</option>
                      <option value="verified">Verify</option>
                      <option value="suspended">Suspend</option>
                      <option value="revoked">Revoke</option>
                    </select>
                  </label>

                  <label>
                    Reviewed evidence reference
                    <input
                      name="confirmation"
                      required
                      maxLength={160}
                    />
                  </label>

                  <label>
                    Verification expiry
                    <input name="expiry" type="datetime-local" />
                  </label>

                  {record.publication_requested && <label>
                    Independent confirmation of business mailbox publication (optional)
                    <input name="publication_ref" maxLength={160} />
                  </label>}
                  <p className="text-xs text-amber-300">
                    Review requires genuine independently checked evidence.
                    Confirm publication only with separate organizational consent.
                  </p>

                  <button
                    className="btn-primary"
                    disabled={busy}
                  >
                    Record review
                  </button>
                </form>
              </details>
            </article>
          ))}

          {!visible.length && (
            <p className="text-sm text-slate-400">
              No directory records match this view.
            </p>
          )}
        </>
      )}
    </section>
  )
}
