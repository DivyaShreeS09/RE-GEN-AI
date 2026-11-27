import { useState } from 'react'
import { Factory, Search, RefreshCw, ShieldCheck } from 'lucide-react'
import { listRecoveryOpportunities } from '../api'

const pathways = [
  'All pathways',
  'sell',
  'reuse',
  'recycling',
  'industrial_symbiosis',
  'collective_recovery',
  'donate',
  'composting',
]

const humanize = value =>
  String(value || '').replaceAll('_', ' ')

export default function SymbiosisBoard({ onSelectOpportunity }) {
  const [records, setRecords] = useState([])
  const [query, setQuery] = useState('')
  const [pathway, setPathway] = useState('All pathways')
  const [pin, setPin] = useState('')
  const [loaded, setLoaded] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function load() {
    setBusy(true)
    setError('')

    try {
      const { data } = await listRecoveryOpportunities()

      const rows = Array.isArray(data)
        ? data
        : data.services

      if (!Array.isArray(rows)) {
        throw new Error('Invalid directory response')
      }

      setRecords(rows)
      setLoaded(true)
    } catch {
      setRecords([])
      setLoaded(false)
      setError(
        'Directory unavailable. Authorized facility access is required.'
      )
    } finally {
      setBusy(false)
    }
  }

  const now = Date.now()

  const verified = records.filter(record =>
    record.status === 'verified' &&
    Date.parse(record.expires) > now &&
    Date.parse(record.verification_expires) > now &&
    record.remaining_g > 0
  )

  const visible = verified.filter(record => {
    const text = [
      record.material,
      record.organization,
      record.condition,
      record.pathway,
    ].join(' ').toLowerCase()

    return (
      text.includes(query.toLowerCase().trim()) &&
      (pathway === 'All pathways' ||
        record.pathway === pathway) &&
      (!pin || record.service_pins?.includes(pin))
    )
  })

  return (
    <section className="glass-card p-6 my-6">
      <div className="flex flex-wrap justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold flex items-center gap-2">
            <Factory className="text-emerald-400" />
            Industrial Symbiosis Exchange
          </h2>

          <p className="text-sm text-slate-400 mt-2">
            Discover documented demand for recoverable materials
            within the facility's reviewed partner network.
          </p>
        </div>

        <button
          type="button"
          disabled={busy}
          onClick={load}
          className="flex items-center gap-2 rounded-lg
            bg-emerald-600 px-4 py-2 text-white"
        >
          <RefreshCw size={16} />
          {busy ? 'Loading...' : 'Refresh opportunities'}
        </button>
      </div>

      {error && (
        <p role="alert" className="text-red-400 mt-4">
          {error}
        </p>
      )}

      {loaded && (
        <>
          <div className="grid sm:grid-cols-3 gap-3 my-5">
            <div className="rounded-xl bg-slate-900 p-4">
              <p className="text-sm text-slate-400">
                Current verified services
              </p>
              <p className="text-2xl font-bold">
                {verified.length}
              </p>
            </div>

            <div className="rounded-xl bg-slate-900 p-4">
              <p className="text-sm text-slate-400">
                Material categories
              </p>
              <p className="text-2xl font-bold">
                {new Set(verified.map(r => r.material)).size}
              </p>
            </div>

            <div className="rounded-xl bg-slate-900 p-4">
              <p className="text-sm text-slate-400">
                Matching listings
              </p>
              <p className="text-2xl font-bold">
                {visible.length}
              </p>
            </div>
          </div>

          <div className="grid md:grid-cols-3 gap-3 mb-5">
            <label className="text-sm">
              <span className="flex gap-2 items-center mb-2">
                <Search size={15} />
                Search material or organization
              </span>
              <input
                value={query}
                onChange={e => setQuery(e.target.value)}
                placeholder="Material or organization"
                className="w-full bg-slate-900 border
                  border-slate-700 rounded-lg p-3"
              />
            </label>

            <label className="text-sm">
              <span className="block mb-2">Recovery pathway</span>
              <select
                value={pathway}
                onChange={e => setPathway(e.target.value)}
                className="w-full bg-slate-900 border
                  border-slate-700 rounded-lg p-3"
              >
                {[...new Set([
                  ...pathways,
                  ...verified.map(r => r.pathway),
                ])].map(item => (
                  <option key={item} value={item}>
                    {humanize(item)}
                  </option>
                ))}
              </select>
            </label>

            <label className="text-sm">
              <span className="block mb-2">Service PIN code</span>
              <input
                value={pin}
                inputMode="numeric"
                maxLength={6}
                onChange={e =>
                  setPin(e.target.value.replace(/\D/g, ''))
                }
                placeholder="Six-digit PIN"
                className="w-full bg-slate-900 border
                  border-slate-700 rounded-lg p-3"
              />
            </label>
          </div>

          {!visible.length && (
            <div className="rounded-xl border border-slate-700 p-6">
              No current verified opportunities match these filters.
              Register documented demand through the partner directory.
            </div>
          )}

          <div className="grid lg:grid-cols-2 gap-4">
            {visible.map(record => (
              <article
                key={record.id}
                className="rounded-xl border border-slate-700
                  bg-slate-900/60 p-5"
              >
                <div className="flex items-center gap-2
                  text-sm text-emerald-400">
                  <ShieldCheck size={16} />
                  Reviewed directory listing
                </div>

                <h3 className="font-bold text-lg mt-2">
                  {record.organization}
                </h3>

                <p className="text-emerald-300 mt-1">
                  {humanize(record.pathway)}
                </p>

                <dl className="grid grid-cols-2 gap-3 text-sm mt-4">
                  {[
                    ['Material demand', record.material],
                    ['Accepted condition', record.condition],
                    ['Minimum accepted mass', `${record.minimum_g / 1000} kg`],
                    ['Collection window', [record.collection_start || 'Open start', record.collection_end || 'Until expiry'].join(' to ')],
                    ['Available capacity',
                      `${record.remaining_g / 1000} kg`],
                    ['Transfer', record.transfer || 'Not recorded'],
                    ['Service PINs',
                      record.service_pins?.join(', ')],
                    ['Verification expiry',
                      new Date(record.verification_expires)
                        .toLocaleDateString('en-IN')],
                  ].map(([label, value]) => (
                    <div key={label}>
                      <dt className="text-slate-400">{label}</dt>
                      <dd className="font-medium">{value}</dd>
                    </div>
                  ))}
                </dl>

                <div className="mt-4 border-t border-slate-700 pt-3">
                  <p className="text-sm">
                    {record.quote_paise_per_kg != null &&
                    Date.parse(record.quote_expires) > now
                      ? `Current documented quote: INR ${
                          record.quote_paise_per_kg / 100
                        }/kg`
                      : 'No current documented selling quote'}
                  </p>

                  <button onClick={() => onSelectOpportunity(record)}>Assess my inventory</button>
                  <p className="text-xs text-slate-400 mt-2">
                    Availability must be rechecked against the actual
                    inventory before authorized staff approve recovery.
                  </p>
                </div>
              </article>
            ))}
          </div>
        </>
      )}
    </section>
  )
}
