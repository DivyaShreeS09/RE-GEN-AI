import { useState } from 'react'
import { Layers, RefreshCw, PackageCheck } from 'lucide-react'
import { openMaterialMissions, groupMissions } from '../api'

export default function CollectiveRecoveryBoard({ onOpenMission }) {
  const [records, setRecords] = useState([])
  const [loaded, setLoaded] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function load() {
    setBusy(true)
    setError('')

    try {
      const { data } = await openMaterialMissions()

      const rows = Array.isArray(data)
        ? data
        : data.missions

      if (!Array.isArray(rows)) {
        throw new Error('Unexpected inventory response')
      }

      setRecords(rows)
      setLoaded(true)
    } catch {
      setRecords([])
      setLoaded(false)
      setError('Unable to load authorized facility inventory.')
    } finally {
      setBusy(false)
    }
  }

  const groups = new Map()

  for (const record of records) {
    const batch = record

    if (
      batch.kind === 'analysis' ||
      batch.contaminated !== false ||
      batch.collective_consent !== true ||
      !batch.material ||
      !batch.condition ||
      !batch.service_pin ||
      !batch.collection_date ||
      !Number.isSafeInteger(batch.quantity_g) ||
      batch.quantity_g <= 0 ||
      !['needs_evidence', 'awaiting_approval'].includes(record.state) ||
      record.result?.sources?.length
    ) continue

    const key = JSON.stringify([
      batch.canonical_material || batch.material,
      batch.condition.toLowerCase(),
      batch.service_pin,
      batch.collection_date,
    ])

    if (!groups.has(key)) {
      groups.set(key, {
        material: batch.material,
        condition: batch.condition,
        pin: batch.service_pin,
        date: batch.collection_date,
        quantity: 0,
        batches: [],
      })
    }

    const group = groups.get(key)

    group.quantity += batch.quantity_g
    group.batches.push({
      id: record.id,
      quantity: batch.quantity_g,
      state: record.state,
    })
  }

  const candidates = [...groups.values()]
    .filter(group => group.batches.length >= 2)
    .sort((a, b) => b.quantity - a.quantity)

  const total = candidates.reduce(
    (sum, group) => sum + group.quantity, 0
  )

  return (
    <section className="glass-card p-6 my-6">
      <div className="flex flex-wrap justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold flex gap-2 items-center">
            <Layers className="text-emerald-400" />
            Collective Recovery Network
          </h2>

          <p className="text-sm text-slate-400 mt-2">
            Identify compatible, consented material inventories
            within the authorized facility.
          </p>
        </div>

        <button
          type="button"
          disabled={busy}
          onClick={load}
          className="flex gap-2 items-center rounded-lg
            bg-emerald-600 px-4 py-2 text-white"
        >
          <RefreshCw size={16} />
          {busy ? 'Loading...' : 'Discover compatible batches'}
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
            {[
              ['Open inventory records', records.length],
              ['Potential groups', candidates.length],
              ['Candidate material mass', `${total / 1000} kg`],
            ].map(([label, value]) => (
              <div
                key={label}
                className="rounded-xl bg-slate-900 p-4"
              >
                <p className="text-sm text-slate-400">
                  {label}
                </p>
                <p className="text-2xl font-bold">{value}</p>
              </div>
            ))}
          </div>

          {!candidates.length && (
            <p className="rounded-xl border border-slate-700 p-5">
              No compatible consented batches currently found.
            </p>
          )}

          <div className="grid lg:grid-cols-2 gap-4">
            {candidates.map(group => (
              <article
                key={JSON.stringify([
                  group.material,
                  group.condition,
                  group.pin,
                  group.date,
                ])}
                className="rounded-xl border border-slate-700
                  bg-slate-900/60 p-5"
              >
                <div className="flex gap-2 items-center
                  text-emerald-400 text-sm">
                  <PackageCheck size={17} />
                  Potential aggregation opportunity
                </div>

                <h3 className="font-bold text-xl mt-3">
                  {group.material}
                </h3>

                <p className="text-3xl font-bold my-3">
                  {group.quantity / 1000} kg
                </p>

                <dl className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <dt className="text-slate-400">Condition</dt>
                    <dd>{group.condition}</dd>
                  </div>

                  <div>
                    <dt className="text-slate-400">Service PIN</dt>
                    <dd>{group.pin}</dd>
                  </div>

                  <div>
                    <dt className="text-slate-400">Collection date</dt>
                    <dd>{group.date}</dd>
                  </div>

                  <div>
                    <dt className="text-slate-400">Source batches</dt>
                    <dd>{group.batches.length}</dd>
                  </div>
                </dl>

                <div className="border-t border-slate-700 mt-4 pt-3">
                  {group.batches.map(batch => (
                    <div
                      key={batch.id}
                      className="flex justify-between gap-3
                        text-sm py-2"
                    >
                      <span title={batch.id}>
                        Batch {String(batch.id).slice(0, 8)}
                      </span>
                      <span>{batch.quantity / 1000} kg</span>
                    </div>
                  ))}
                </div>

                <button disabled={busy} onClick={async () => {
                  setBusy(true)
                  setError('')
                  try {
                    const { data } = await groupMissions(group.batches.map(batch => batch.id))
                    onOpenMission(data)
                    await load()
                  } catch {
                    setError('Grouping requires administrator approval and current compatible capacity.')
                  } finally { setBusy(false) }
                }}>Group batches for review</button>

                <p className="text-xs text-amber-300 mt-4">
                  Candidate only. Partner acceptance, minimum
                  quantity, available capacity and staff approval
                  must be confirmed by the recovery engine.
                </p>
              </article>
            ))}
          </div>
        </>
      )}
    </section>
  )
}
