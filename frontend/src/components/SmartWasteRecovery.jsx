import { useState } from 'react'
import { Recycle, Sparkles, MapPin, Package, Loader2, ArrowRight } from 'lucide-react'
import { createMission, signIn } from '../api'

const field = 'w-full rounded-xl border border-white/10 bg-slate-950 px-4 py-3 text-white outline-none focus:border-emerald-400'
const money = value => value == null ? 'Not yet quoted' :
  new Intl.NumberFormat('en-IN', {
    style: 'currency', currency: 'INR'
  }).format(value / 100)

export default function SmartWasteRecovery() {
  const [material, setMaterial] = useState('')
  const [quantity, setQuantity] = useState('')
  const [condition, setCondition] = useState('good')
  const [pin, setPin] = useState('')
  const [busy, setBusy] = useState(false)
  const [mission, setMission] = useState(null)
  const [error, setError] = useState('')

  async function search(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    setMission(null)

    try {
      if (import.meta.env.DEV &&
          import.meta.env.VITE_LOCAL_IDENTITY === '1') {
        await signIn()
      }

      const { data } = await createMission({
        request_id: crypto.randomUUID(),
        material: material.trim(),
        quantity_g: Math.round(Number(quantity) * 1000),
        condition,
        service_pin: pin,
        contaminated: condition === 'uncertain',
        mixed_inventory: condition === 'mixed',
        goal: 'sell',
        preferred_effort: 'any',
        collective_consent: false,
        collection_date: null,
        use_context: null
      }, false)

      setMission(data)
    } catch {
      setError('Unable to complete the search. Please check your facility session and try again.')
    } finally {
      setBusy(false)
    }
  }

  const options = mission?.result?.options || []

  return (
    <section className="max-w-7xl mx-auto px-6 py-12" id="smart-recovery">
      <div className="glass-card p-6 md:p-8">
        <div className="flex items-center gap-4 mb-6">
          <div className="rounded-2xl bg-emerald-500/10 p-4">
            <Recycle className="w-8 h-8 text-emerald-400" />
          </div>
          <div>
            <p className="text-xs tracking-widest text-emerald-400 uppercase">
              Intelligent material recovery
            </p>
            <h2 className="text-2xl font-bold text-white">
              Turn your waste into value
            </h2>
            <p className="text-sm text-slate-400 mt-1">
              Tell us what you have. RE:GEN AI will explore recovery opportunities.
            </p>
          </div>
        </div>

        <form onSubmit={search} className="grid md:grid-cols-2 gap-5">
          <label className="text-sm text-slate-300">
            What waste do you have?
            <input className={field + ' mt-2'}
              value={material}
              onChange={e => setMaterial(e.target.value)}
              placeholder="e.g. Cardboard boxes"
              maxLength={160} required />
          </label>

          <label className="text-sm text-slate-300">
            Quantity (kg)
            <input className={field + ' mt-2'}
              type="number" min="0.001" max="100000"
              step="0.001" value={quantity}
              onChange={e => setQuantity(e.target.value)}
              placeholder="e.g. 25" required />
          </label>

          <label className="text-sm text-slate-300">
            Condition
            <select className={field + ' mt-2'}
              value={condition}
              onChange={e => setCondition(e.target.value)}>
              <option value="good">Clean and usable</option>
              <option value="damaged">Used or damaged</option>
              <option value="mixed">Mixed materials</option>
              <option value="uncertain">Contaminated or unsure</option>
            </select>
          </label>

          <label className="text-sm text-slate-300">
            PIN code
            <input className={field + ' mt-2'}
              inputMode="numeric" pattern="[1-9][0-9]{5}"
              maxLength={6} value={pin}
              onChange={e => setPin(e.target.value)}
              placeholder="6-digit PIN code" required />
          </label>

          <button disabled={busy}
            className="md:col-span-2 rounded-xl bg-gradient-to-r from-emerald-400 to-cyan-400 text-slate-950 font-bold py-4 flex items-center justify-center gap-2 disabled:opacity-50">
            {busy ? <Loader2 className="w-5 h-5 animate-spin" /> :
              <Sparkles className="w-5 h-5" />}
            {busy ? 'Exploring recovery opportunities...' : 'Find the best value'}
          </button>
        </form>

        {error && <p role="alert" className="mt-5 text-red-400">{error}</p>}

        {mission && (
          <div className="mt-8 border-t border-white/10 pt-6">
            <h3 className="text-xl font-bold text-white mb-4">
              Your recovery opportunities
            </h3>

            {mission.state === 'manual_review' && (
              <div className="rounded-xl bg-amber-500/10 border border-amber-500/20 p-5 text-amber-200">
                <p className="font-bold">Material identification needs confirmation</p>
                <p className="text-sm mt-2">
                  {mission.result?.clarification?.question ||
                    'The material needs to be identified before a suitable recovery option can be recommended.'}
                </p>
                <p className="text-sm mt-2">
                  Please consult authorized facility staff before proceeding.
                </p>
              </div>
            )}

            {options.map((option, index) => (
              <article key={option.service_id}
                className="rounded-2xl bg-slate-900 border border-white/10 p-5 mb-4">
                <div className="flex flex-wrap justify-between gap-3">
                  <div>
                    <p className="text-xs uppercase tracking-wider text-emerald-400">
                      {index === 0 ? 'Recommended option' : 'Alternative option'}
                    </p>
                    <h4 className="text-lg font-bold text-white capitalize">
                      {option.pathway?.replaceAll('_', ' ')}
                    </h4>
                    <p className="text-sm text-slate-400 flex items-center gap-2 mt-1">
                      <MapPin size={14} /> {option.organization}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-400">Quoted net revenue</p>
                    <p className="text-2xl font-bold text-emerald-400">
                      {money(option.net_paise)}
                    </p>
                  </div>
                </div>

                {option.avoided_purchase_paise != null &&
                  <p className="mt-3 text-sm text-emerald-300">
                    Potential avoided purchases: {money(option.avoided_purchase_paise)}
                  </p>}

                <p className="text-sm text-slate-300 mt-4">{option.rationale}</p>

                {option.preparation &&
                  <p className="text-sm text-slate-400 mt-2">
                    Preparation: {option.preparation}
                  </p>}

                <p className="flex items-center gap-2 text-sm text-cyan-300 mt-4">
                  <ArrowRight size={15} />
                  {option.next_action || 'Request authorized facility review.'}
                </p>
              </article>
            ))}

            {!options.length && mission.state !== 'manual_review' && (
              <div className="rounded-xl border border-white/10 p-5">
                <Package className="text-cyan-400 mb-3" />
                <p className="font-bold text-white">No verified local match yet</p>
                <p className="text-sm text-slate-400 mt-2">
                  No currently eligible partner was found for this material,
                  quantity and PIN code. A recovery value cannot yet be confirmed.
                </p>
              </div>
            )}

            <p className="text-xs text-slate-500 mt-4">
              Recommendations are subject to material acceptance and current
              verified quotes. No transaction is initiated automatically.
            </p>
          </div>
        )}
      </div>
    </section>
  )
}
