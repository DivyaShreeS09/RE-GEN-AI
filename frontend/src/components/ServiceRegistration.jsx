import { useState } from 'react'
import { submitRecoveryService } from '../api'

const pathways = [
  'sell',
  'donate',
  'reuse',
  'repair',
  'internal_redistribution',
  'upcycling',
  'composting',
  'industrial_symbiosis',
  'collective_recovery',
  'recycling',
  'authorized_disposal',
]

const inputClass =
  'w-full rounded-lg bg-slate-950 border border-slate-700 p-2.5 mt-1 text-sm'

function Field({ label, children }) {
  return (
    <label className="block text-sm text-slate-300">
      {label}
      {children}
    </label>
  )
}

export default function ServiceRegistration({ onRegistered }) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [pathway, setPathway] = useState('recycling')

  async function submit(event) {
    event.preventDefault()

    const element = event.currentTarget
    const form = new FormData(element)

    const value = name =>
      String(form.get(name) ?? '').trim()

    const optional = name =>
      value(name) || null

    const date = name =>
      value(name) ? new Date(value(name)).toISOString() : null

    const money = name =>
      value(name) === ''
        ? null
        : Math.round(Number(value(name)) * 100)

    setBusy(true)
    setError('')
    setNotice('')

    try {
      const pins = [...new Set(
        value('pins').split(/[\s,]+/).filter(Boolean)
      )]

      if (!pins.length || pins.length > 100 ||
          pins.some(pin => !/^[1-9][0-9]{5}$/.test(pin))) {
        throw new Error('Enter valid six-digit service PIN codes.')
      }

      const minimum = Math.round(Number(value('minimum')) * 1000)
      const capacity = Math.round(Number(value('capacity')) * 1000)

      if (minimum <= 0 || capacity < minimum) {
        throw new Error('Capacity must cover the minimum accepted quantity.')
      }

      if (new Date(value('expires')).getTime() <= Date.now()) {
        throw new Error('Service expiry must be in the future.')
      }

      const body = {
        organization: value('organization'),
        registration: value('registration'),
        pathway,
        transfer: value('transfer'),
        material: value('material'),
        condition: value('condition'),
        service_pins: pins,
        minimum_g: minimum,
        capacity_g: capacity,
        expires: date('expires'),
        identity_evidence: value('identity'),
        acceptance_evidence: value('acceptance'),
        consent_evidence: value('consent'),
        regulatory_evidence: optional('regulatory'),
        publication_consent: form.has('publish'),
        business_email: form.has('publish') ? optional('business_email') : null,
        quote_paise_per_kg: money('quote'),
        quote_expires: date('quote_expiry'),
        avoided_purchase_paise: money('avoided_purchase'),
        collection_start: optional('window_start'),
        collection_end: optional('window_end'),
        collection_paise: money('collection'),
        fees_paise: money('fees'),
        transport_paise: money('transport'),
        preparation_paise: money('preparation_cost'),
        preparation: optional('preparation'),
        effort: value('effort'),
        avoided_co2e_g_per_kg: value('carbon') === ''
          ? null
          : Math.round(Number(value('carbon')) * 1000),
        environmental_evidence: optional('environmental_evidence'),
      }

      if (body.publication_consent && !body.business_email) throw new Error('Enter the authorized business mailbox.')
      if ((body.quote_paise_per_kg === null) !==
          (body.quote_expires === null)) {
        throw new Error('Provide both the quote and its expiry.')
      }

      if (body.quote_expires &&
          new Date(body.quote_expires).getTime() <= Date.now()) {
        throw new Error('Quote expiry must be in the future.')
      }

      if (pathway === 'sell' && body.quote_paise_per_kg === null) {
        throw new Error('Sale registration requires a current documented quote.')
      }

      if ((body.avoided_co2e_g_per_kg === null) !==
          (body.environmental_evidence === null)) {
        throw new Error(
          'Environmental estimates require documented comparison evidence.'
        )
      }

      const { data } = await submitRecoveryService(body)

      setNotice(
        `Registration ${data.id} submitted with status ${data.status}. ` +
        'Independent verification is required.'
      )

      element.reset()
      setPathway('recycling')

      if (onRegistered) await onRegistered()

    } catch (err) {
      setError(
        err.response
          ? 'Registration rejected. Check your facility permissions and evidence fields.'
          : err.message || 'Registration could not be completed.'
      )
    } finally {
      setBusy(false)
    }
  }

  return (
    <details className="rounded-xl border border-slate-700 p-5">
      <summary className="cursor-pointer font-semibold text-emerald-300">
        Register a recovery service
      </summary>

      <p className="text-sm text-slate-400 mt-3">
        For authorized facility personnel. Submit only genuine,
        consented service information. Registration does not establish
        verified status or initiate external communication.
      </p>

      <form onSubmit={submit} className="space-y-5 mt-5">
        <fieldset className="grid md:grid-cols-2 gap-4">
          <legend className="font-semibold mb-3">
            Organization and material demand
          </legend>

          <Field label="Organization name">
            <input name="organization" required maxLength={160}
              className={inputClass} />
          </Field>

          <Field label="Registration type">
            <select name="registration" className={inputClass}>
              <option value="organization">Organization</option>
              <option value="assisted_collector">Assisted collector</option>
            </select>
          </Field>

          <Field label="Recovery pathway">
            <select value={pathway}
              onChange={e => setPathway(e.target.value)}
              className={inputClass}>
              {pathways.map(item => (
                <option key={item} value={item}>
                  {item.replaceAll('_', ' ')}
                </option>
              ))}
            </select>
          </Field>

          <Field label="Transfer arrangement">
            <select name="transfer" required className={inputClass}
              defaultValue="">
              <option value="" disabled>Select arrangement</option>
              <option value="pickup">Facility-coordinated pickup</option>
              <option value="dropoff">Facility-coordinated drop-off</option>
              <option value="internal">Internal recovery</option>
            </select>
          </Field>

          <Field label="Accepted material">
            <input name="material" required maxLength={160}
              className={inputClass} />
          </Field>

          <Field label="Accepted material condition">
            <input name="condition" required maxLength={160}
              className={inputClass} />
          </Field>

          <Field label="Service PIN codes (comma separated)">
            <input name="pins" required className={inputClass} />
          </Field>
        </fieldset>

        <fieldset className="grid md:grid-cols-3 gap-4">
          <legend className="font-semibold mb-3">
            Capacity and validity
          </legend>

          <Field label="Minimum accepted mass (kg)">
            <input name="minimum" type="number" min="0.001"
              max="100000" step="0.001" required className={inputClass} />
          </Field>

          <Field label="Available capacity (kg)">
            <input name="capacity" type="number" min="0.001"
              max="100000" step="0.001" required className={inputClass} />
          </Field>

          <Field label="Service expiry">
            <input name="expires" type="datetime-local"
              required className={inputClass} />
          </Field>
        </fieldset>

        <fieldset className="grid md:grid-cols-2 gap-4">
          <legend className="font-semibold mb-3">
            Verification evidence
          </legend>

          <Field label="Organization identity reference">
            <input name="identity" required maxLength={160}
              className={inputClass} />
          </Field>

          <Field label="Material acceptance reference">
            <input name="acceptance" required maxLength={160}
              className={inputClass} />
          </Field>

          <label><input type="checkbox" name="publish" /> Organization authorizes publication of its business mailbox</label>
          <Field label="Authorized role mailbox (optional)">
            <input name="business_email" type="email" maxLength={160} placeholder="operations@example.org" />
          </Field>
          <Field label="Documented consent reference">
            <input name="consent" required maxLength={160}
              className={inputClass} />
          </Field>

          <Field label="Regulatory authorization reference">
            <input name="regulatory" maxLength={160}
              required={pathway === 'authorized_disposal'}
              className={inputClass} />
          </Field>
        </fieldset>

        <fieldset className="grid md:grid-cols-3 gap-4">
          <legend className="font-semibold mb-3">
            Documented economics
          </legend>

          <Field label="Quoted INR per kg">
            <input name="quote" type="number" min="0"
              max="10000000" step="0.01" className={inputClass} />
          </Field>

          <Field label="Quote expiry">
            <input name="quote_expiry" type="datetime-local"
              className={inputClass} />
          </Field>

          <Field label="Avoided purchase value (INR)">
            <input name="avoided_purchase" type="number"
              min="0" max="10000000" step="0.01"
              className={inputClass} />
          </Field>
        </fieldset>

        <fieldset className="grid md:grid-cols-3 gap-4">
          <legend className="font-semibold mb-3">
            Recovery transaction costs
          </legend>

          <Field label="Earliest collection date (optional)"><input type="date" name="window_start" /></Field>
          <Field label="Latest collection date (optional)"><input type="date" name="window_end" /></Field>
          <Field label="Collection charge per transaction (INR)">
            <input name="collection" type="number" min="0" max="10000000" step="0.01" required className={inputClass} />
          </Field>
          <Field label="Service fees excluding collection (INR)">
            <input name="fees" type="number" min="0"
              max="10000000" step="0.01" required
              className={inputClass} />
          </Field>

          <Field label="Transport cost per transaction (INR)">
            <input name="transport" type="number" min="0"
              max="10000000" step="0.01" required
              className={inputClass} />
          </Field>

          <Field label="Preparation cost per transaction (INR)">
            <input name="preparation_cost" type="number"
              min="0" max="10000000" step="0.01" required
              className={inputClass} />
          </Field>

          <Field label="Facility effort">
            <select name="effort" className={inputClass}>
              <option value="low">Low</option>
              <option value="moderate">Moderate</option>
              <option value="high">High</option>
            </select>
          </Field>

          <Field label="Documented preparation requirements">
            <input name="preparation" maxLength={160}
              className={inputClass} />
          </Field>

          <p className="text-xs text-amber-300">
            Enter zero only when the documented cost is zero.
            Unknown transaction costs require further facility review.
          </p>
        </fieldset>

        <fieldset className="grid md:grid-cols-2 gap-4">
          <legend className="font-semibold mb-3">
            Environmental comparison evidence
          </legend>

          <Field label="Avoided kg CO2e per kg of material">
            <input name="carbon" type="number"
              min="0" max="1000" step="0.001"
              className={inputClass} />
          </Field>

          <Field label="Reviewed environmental source reference">
            <input name="environmental_evidence"
              maxLength={160} className={inputClass} />
          </Field>

          <p className="text-xs text-slate-400 md:col-span-2">
            Optional. Supply a reviewed comparison against an
            identified baseline. Projected avoided emissions
            are not verified realized reductions.
          </p>
        </fieldset>

        <p className="text-xs text-slate-400">
          Leave unknown financial values blank. Do not substitute
          zero for missing evidence. Publication requires independent confirmation.
        </p>

        <label className="flex items-start gap-2 text-sm">
          <input type="checkbox" required className="mt-1" />
          <span>
            I confirm that I am authorized to submit these records
            and that the evidence references are genuine.
          </span>
        </label>

        <button className="btn-primary" disabled={busy}>
          {busy ? 'Submitting...' : 'Submit for independent review'}
        </button>

        {error && <p role="alert" className="text-red-400">{error}</p>}
        {notice && <p role="status" className="text-emerald-400">{notice}</p>}
      </form>
    </details>
  )
}
