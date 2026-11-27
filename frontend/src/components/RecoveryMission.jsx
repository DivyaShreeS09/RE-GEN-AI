import RecoveryIntelligence, { MissionBudget } from './RecoveryIntelligence'
import { refreshRecoveryMission, executeAnalysisMission, readExecutionJob } from '../api'
import { useEffect, useRef, useState } from 'react'
import { readBusinessChannels, clarifyMaterial, createMission, readMission, updateMission, downloadPassport, openMaterialMissions, groupMissions, requestFacilityReview, saveMaterialPhoto, startAnalysisMission, advanceAnalysisMission } from '../api'

export default function RecoveryMission({ analysisId, opportunity, openedMission }) {
  const [mission, setMission] = useState(openedMission || null)
  const [consentMission, setConsentMission] = useState(null)
  const [jobId, setJobId] = useState(null)
  const [openBatches, setOpenBatches] = useState([])
  const [unit, setUnit] = useState('g')
  const [lotCount, setLotCount] = useState(1)
  const [contact, setContact] = useState(null)
  const [notice, setNotice] = useState('')
  const [deviceId, setDeviceId] = useState('')
  const [goal, setGoal] = useState('resource_review')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const request = useRef(null)
  const id = mission?.id
  useEffect(() => {
    const saved = id || sessionStorage.getItem('regen-mission') || localStorage.getItem('regen-mission')
    if (!saved) return
    let active = true
    const refresh = async () => {
      try {
        const response = await readMission(saved)
        if (active) setContact(null)
        if (active) setMission(previous => !previous || (previous.id === saved && response.data.version >= previous.version) ? response.data : previous)
      } catch {
        if (active) setError('Mission unavailable. Check your facility session.')
      }
    }
    refresh()
    const timer = setInterval(refresh, 5000)
    return () => { active = false; clearInterval(timer) }
  }, [id])

  useEffect(() => {
    if (!id) return
    localStorage.setItem('regen-mission', id)
    sessionStorage.setItem('regen-mission', id)
    const job = jobId?.missionId === id ? jobId.id : localStorage.getItem('regen-job-' + id)
    if (!job || mission?.inputs?.kind !== 'analysis') return
    let active = true
    let timer
    async function poll() {
      try {
        const {data} = await readExecutionJob(job)
        if (!active || data.mission_id !== id) return
        setNotice('Investigation: ' + data.status + (data.error ? '. ' + data.error : ''))
        if (['completed', 'paused', 'cancelled', 'failed'].includes(data.status)) {
          localStorage.removeItem('regen-job-' + id)
          return
        }
      } catch { if (active) setNotice('Job status unavailable. Retrying.') }
      if (active) timer = setTimeout(poll, 3000)
    }
    poll()
    return () => { active = false; clearTimeout(timer) }
  }, [id, jobId, mission?.inputs?.kind])

  async function submit(event) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    const fields = { use_context: form.get('use_context') || null, preferred_effort: form.get('effort'), material: form.get('material'), condition: form.get('condition'), quantity_g: Math.round(Number(form.get('quantity_g')) * (unit === 'kg' ? 1000 : 1)),
      service_pin: form.get('pin'), contaminated: form.has('contaminated'), goal: form.get('goal'),
      mixed_inventory: form.has('mixed_inventory'), collective_consent: form.has('collective'), collection_date: form.get('collection_date') || null }
    const photo = form.get('photo')
    const fingerprint = JSON.stringify([fields, photo?.name, photo?.size, photo?.lastModified])
    if (request.current?.fingerprint !== fingerprint) request.current = { fingerprint, id: crypto.randomUUID() }
    setBusy(true)
    setError('')
    try {
      if (photo?.size && !request.current.photoId) request.current.photoId = (await saveMaterialPhoto(photo)).data.id
      const response = await createMission({ ...fields, request_id: request.current.id, photo_id: request.current.photoId }, form.has('cloud_consent'))
      sessionStorage.setItem('regen-mission', response.data.id)
      setMission(response.data)
    } catch { setError('Could not save the mission. Check your facility session and inputs.') }
    finally { setBusy(false) }
  }

  async function analyze() {
    setBusy(true)
    setError('')
    try {
      const response = await startAnalysisMission({ goal, device_id: deviceId || null, analysis_id: analysisId, request_id: crypto.randomUUID() })
      sessionStorage.setItem('regen-mission', response.data.id)
      setMission(response.data)
    } catch { setError('Analysis mission could not be started.') }
    finally { setBusy(false) }
  }

  async function refreshRecovery() {
    if (!mission || busy) return

    setBusy(true)
    setError('')
    setNotice('')

    try {
      const { data } = await refreshRecoveryMission(
        mission.id,
        mission.version
      )

      setMission(data)

      setNotice(
        data.result.options.length
          ? `${data.result.options.length} currently eligible recovery alternatives found.`
          : 'No current verified match. Facility evidence is still required.'
      )
    } catch {
      setError(
        'Unable to refresh recovery opportunities. Reopen the current mission.'
      )
    } finally {
      setBusy(false)
    }
  }

  async function runInvestigation() {
    if (busy || mission?.inputs?.kind !== 'analysis') return

    setBusy(true)
    setError('')
    setNotice('')

    try {
      const { data } = await executeAnalysisMission(mission.id)
      localStorage.setItem('regen-job-' + mission.id, data.id)
      setJobId({missionId: mission.id, id: data.id})
      setNotice('Investigation: ' + data.status)
    } catch {
      setError('Execution paused. Committed checkpoints remain saved.')

      try {
        const { data } = await readMission(mission.id)
        setMission(data)
      } catch {
        // Retain the last known checkpoint.
      }
    } finally {
      setBusy(false)
    }
  }

  async function transition(action, service_id, evidence = {}) {
    setBusy(true)
    setError('')
    const consent = consentMission === id
    setConsentMission(null)
    try {
      const response = mission.inputs?.kind === 'analysis'
        ? await advanceAnalysisMission(id, { version: mission.version, action, ...evidence }, consent)
        : await updateMission(id, { version: mission.version, action, service_id, ...evidence }, consent)
      setMission(response.data)
    } catch { setError('Transition unavailable. Check your role and current service capacity.') }
    finally { setBusy(false) }
  }

  async function clarify(event) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    const unresolved = form.get('unresolved') === 'on'
    const lots = unresolved ? [] : Array.from({length:lotCount}, (_, i) => ({
      material: form.get('lot-material-'+i), condition: form.get('lot-condition-'+i),
      quantity_g: Number(form.get('lot-mass-'+i)), contaminated: form.has('lot-unsafe-'+i)
    }))
    setBusy(true)
    setError('')
    const consent = consentMission === id
    setConsentMission(null)
    try {
      const {data} = await clarifyMaterial(id, {version:mission.version, evidence_ref:form.get('source'),
        answer:form.get('answer'), disposition:unresolved ? 'unresolved' : lots.length > 1 ? 'separate_lots' : 'identified', lots}, consent)
      setMission(data)
      setLotCount(1)
    } catch { setError('Facility review requires administrator access, a current mission and a complete mass balance.') }
    finally { setBusy(false) }
  }

  async function group(event) {
    event.preventDefault()
    const second = new FormData(event.currentTarget).get('second')
    setBusy(true)
    try {
      const {data} = await groupMissions([id, second])
      sessionStorage.setItem('regen-mission', data.id)
      setOpenBatches([])
      setMission(data)
    } catch { setError('Grouping requires compatible consent, date, PIN and current capacity.') }
    finally { setBusy(false) }
  }

  function confirm(event) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    if (mission.inputs.kind === 'analysis') return transition('verify', undefined, {evidence_ref: form.get('receipt'), work_order_id: form.get('work_order') || null})
    return transition('confirm_handover', undefined, {receipt_ref: form.get('receipt'), accepted_g: Number(form.get('accepted')),
      revenue_paise: form.get('revenue') === '' ? null : Number(form.get('revenue')),
      costs_paise: form.get('costs') === '' ? null : Number(form.get('costs'))})
  }

  return <section className="glass p-5 my-6" aria-label="Recovery mission">
    <h2 className="text-xl font-bold mb-4">Waste-to-Wealth recovery mission</h2>
    <form onSubmit={submit} className="grid gap-3 md:grid-cols-2">
      <label>Material <input defaultValue={opportunity?.material} name="material" maxLength={160} required /></label>
      <label>Condition <input defaultValue={opportunity?.condition} name="condition" maxLength={160} required /></label>
      <label>Quantity ({unit === 'kg' ? 'kilograms' : 'grams'}) <input type="number" name="quantity_g" min={unit === 'kg' ? 0.001 : 1} step={unit === 'kg' ? 0.001 : 1} max={unit === 'kg' ? 100000 : 100000000} required /></label>
      <label>Mass unit <select value={unit} onChange={e => setUnit(e.target.value)}><option value="g">Grams</option><option value="kg">Kilograms</option></select></label>
      <label><input type="checkbox" name="mixed_inventory" /> Multiple lots or composite inventory</label>
      <label>Material photo (optional, material only) <input type="file" name="photo" accept="image/png,image/jpeg" /></label>
      <label>Service PIN <input defaultValue={opportunity?.service_pins?.length === 1 ? opportunity.service_pins[0] : undefined} name="pin" inputMode="numeric" pattern="[1-9][0-9]{5}" maxLength={6} required /></label>
      <label><input name="cloud_consent" type="checkbox" /> Permit configured production AI providers to compare eligible options using summarized evidence for this request</label>
      <label>Prior use (optional) <input name="use_context" maxLength={160} /></label>
      <label>Preferred effort <select name="effort" defaultValue="any"><option value="any">Any</option><option value="low">Low</option><option value="moderate">Moderate</option></select></label>
      <label>Preferred pathway <select defaultValue={opportunity?.pathway} name="goal">{['recycling','sell','donate','reuse','repair','internal_redistribution','upcycling','composting','industrial_symbiosis','collective_recovery','authorized_disposal'].map(x =>
        <option key={x} value={x}>{x.replaceAll('_',' ')}</option>)}</select></label>
      <label><input type="checkbox" name="contaminated" /> Contaminated or uncertain</label>
      <label><input type="checkbox" name="collective" /> Facility consents to collective recovery</label>
      <label>Agreed collection date <input type="date" name="collection_date" /></label>
      <button className="btn-primary" disabled={busy}>Check reviewed services</button>
    </form>
    {analysisId && <div className="mt-4"><label>Inspection goal <select value={goal} onChange={e => setGoal(e.target.value)}>
      <option value="resource_review">Water and energy</option><option value="water">Water</option><option value="energy">Energy</option></select></label>
      <label>Registered meter ID (optional) <input value={deviceId} maxLength={32} onChange={e => setDeviceId(e.target.value)} /></label>
      <button disabled={busy} onClick={analyze}>Review analysis evidence</button></div>}
    {error && <p role="alert">{error}</p>}
    {mission && <div className="mt-4"><h3>Agent War Room · {mission.state.replaceAll('_', ' ')}</h3>
      <RecoveryIntelligence mission={mission} />
      <MissionBudget mission={mission} />
      {['planned','in_progress','manual_review','needs_evidence','awaiting_approval'].includes(mission.state) &&
        <label><input type="checkbox" checked={consentMission === id} onChange={e => setConsentMission(e.target.checked ? id : null)} />
          Allow configured cloud AI to compare summarized evidence for the next manual planning step</label>}

      {mission.inputs?.kind !== 'analysis' &&
        ['needs_evidence', 'awaiting_approval'].includes(mission.state) && (
          <div className="rounded-xl border border-emerald-500/30 p-4 my-4">
            <h3 className="font-semibold">
              Adaptive recovery planning
            </h3>

            <p className="text-sm text-slate-400 my-2">
              Recheck current verified partners, capacity,
              quotes and recovery alternatives without creating
              a duplicate material inventory.
            </p>

            <button
              type="button"
              disabled={busy}
              onClick={refreshRecovery}
              className="rounded-lg bg-emerald-600 px-4 py-2 text-white disabled:opacity-50"
            >
              {busy ? 'Processing...' : 'Re-evaluate recovery opportunities'}
            </button>
          </div>
        )}

      {mission.inputs?.kind === 'analysis' &&
        ['planned', 'in_progress'].includes(mission.state) && (
          <div className="glass-card p-4 my-4">
            <h4 className="font-semibold mb-2">
              Autonomous investigation
            </h4>
            <p className="text-sm text-slate-400 mb-3">
              Execute remaining eligible investigations automatically.
              Stops before approval or verification.
            </p>
            <button
              type="button"
              className="btn-primary"
              disabled={busy}
              onClick={runInvestigation}
            >
              {busy ? 'Investigating...' : 'Run investigation'}
            </button>
          </div>
        )}

      {mission.state === 'manual_review' && <form onSubmit={clarify} className="grid gap-2">
        <h4>Facility material review</h4>
        <p>{mission.result.clarification?.question || 'What identification evidence is available?'}</p>
        <label>Review response <input name="answer" required maxLength={160} /></label>
        <label>Evidence reference <input name="source" required maxLength={160} /></label>
        {Array.from({length:lotCount}, (_, i) => <fieldset key={i}><legend>Weighed lot {i+1}</legend>
          <label>Identified material <input name={'lot-material-'+i} maxLength={160} /></label>
          <label>Documented condition <input name={'lot-condition-'+i} defaultValue={mission.inputs.condition} /></label>
          <label>Mass in grams <input name={'lot-mass-'+i} type="number" min="1" defaultValue={i === 0 ? mission.inputs.quantity_g : ''} /></label>
          <label><input type="checkbox" name={'lot-unsafe-'+i} /> Requires professional handling</label>
        </fieldset>)}
        {mission.result.clarification?.proposed_material && <p>Unconfirmed candidate from supplied text: {mission.result.clarification.proposed_material}</p>}
        <button type="button" disabled={lotCount >= 30} onClick={() => setLotCount(n => n+1)}>Add separately weighed lot</button>
        <label><input name="unresolved" type="checkbox" /> Identity unresolved; refer for professional review</label>
        <button disabled={busy}>Record review and continue mission</button>
      </form>}
      {mission.result.lots?.map(lot => <button key={lot.id} onClick={async () => {
        try { const {data} = await readMission(lot.id); sessionStorage.setItem('regen-mission',data.id); setMission(data) }
        catch { setError('Lot unavailable.') }
      }}>Open {lot.material} ({lot.quantity_g} g)</button>)}
      {(mission.result.options || []).map(m => <div key={m.service_id}>{m.organization} · {m.pathway} · {m.net_paise == null ? 'Price unavailable' : 'Quoted net ₹' + (m.net_paise/100).toFixed(2)}
        {m.rationale && <p>{m.rationale} {m.next_action}</p>}
        {m.source && <p>Acceptance evidence: {m.source}. Eligible mass: {m.minimum_g}–{m.available_g} g. {m.assumption}</p>}
        {m.environmental_evidence && <p>Projected avoided emissions: {m.projected_co2e_g} g CO₂e. Basis: {m.environmental_evidence}</p>}
        {m.preparation && <p>Preparation: {m.preparation}</p>}
        {m.gross_paise != null && <p>Gross quoted revenue INR {(m.gross_paise / 100).toFixed(2)}</p>}
        {m.costs_paise?.collection_paise != null && <p>Collection charge INR {(m.costs_paise.collection_paise / 100).toFixed(2)}</p>}
        {m.costs_paise && <p>Fees ₹{m.costs_paise.fees_paise/100}, transport ₹{m.costs_paise.transport_paise/100}, preparation ₹{m.costs_paise.preparation_paise/100}.</p>}
        <p>{m.transfer} · {m.effort} effort · Reviewed {new Date(m.reviewed_at).toLocaleDateString()} · Service expires {new Date(m.expires).toLocaleDateString()}</p>
        {mission.state === 'awaiting_approval' && <button type="button" onClick={async () => {
          try {
            const {data} = await readBusinessChannels(mission.inputs.service_pin)
            const channel = data.find(entry => entry.id === m.service_id)
            setContact({mission:id,service:m.service_id,email:channel?.business_email})
          } catch { setContact(null); setError('Directory unavailable.') }
        }}>Check approved business contact</button>}
        {contact?.mission === id && contact.service === m.service_id && <p>{contact.email || 'No authorized business contact published.'}</p>}
        {m.quote_expires && <p>Quote valid until {new Date(m.quote_expires).toLocaleString()}</p>}
        {m.avoided_purchase_paise != null && <p>Estimated avoided purchase ₹{(m.avoided_purchase_paise / 100).toFixed(2)}</p>}
        {mission.state === 'awaiting_approval' && <><button className="btn-secondary" disabled={busy} onClick={() => transition('approve', m.service_id)}>Approve as administrator</button>
          <button disabled={busy} onClick={() => transition('reject', m.service_id)}>Decline option and replan</button></>}</div>)}
      {mission.inputs?.kind === 'analysis' && ['planned','in_progress','awaiting_approval'].includes(mission.state) &&
        <button disabled={busy} onClick={() => transition(mission.state === 'awaiting_approval' ? 'approve' : 'advance')}>
          {mission.state === 'awaiting_approval' ? 'Approve inspection' : 'Inspect next evidence'}</button>}
      {mission.inputs?.kind !== 'analysis' && ['needs_evidence','awaiting_approval','manual_review'].includes(mission.state) && <button disabled={busy} onClick={() => transition('replan')}>Recheck evidence</button>}
      {mission.state === 'needs_evidence' && <button disabled={busy} onClick={async () => {
        try { await requestFacilityReview(id); setNotice('Queued for facility review.') }
        catch { setError('An authorized facility administrator must request onboarding.') }
      }}>Request facility review</button>}
      {mission.inputs?.collective_consent && ['needs_evidence','awaiting_approval'].includes(mission.state) && <div>
        <button disabled={busy} onClick={async () => {
          try { const {data} = await openMaterialMissions(); const others = data.filter(m => m.id !== id && m.collective_consent)
            setOpenBatches(others); if (!others.length) setNotice('No other consenting batch available.') }
          catch { setError('Facility batch list unavailable.') }
        }}>Find collective batches</button>
        {openBatches.length > 0 && <form onSubmit={group}><label>Second batch <select name="second">
          {openBatches.map(b => <option key={b.id} value={b.id}>{b.material} · {b.quantity_g} g · {b.id.slice(0,8)}</option>)}</select></label>
          <button disabled={busy}>Group with administrator approval</button></form>}
      </div>}
      {['approved','awaiting_verification'].includes(mission.state) && <form onSubmit={confirm} className="grid gap-2">
        <label>Private evidence reference <input name="receipt" maxLength={160} required /></label>
        {mission.state === 'awaiting_verification' && mission.inputs.device_id && <label>Reviewed work order (optional) <input name="work_order" /></label>}
        {mission.state === 'approved' && <>
          <label>Accepted mass (g) <input name="accepted" type="number" min="1" max={mission.inputs.quantity_g} required /></label>
          <label>Confirmed revenue (paise, optional) <input name="revenue" type="number" min="0" /></label>
          <label>Confirmed costs (paise, optional) <input name="costs" type="number" min="0" /></label>
          <button type="button" disabled={busy} onClick={() => transition('reject')}>Record rejection and replan</button></>}
        <button disabled={busy}>Confirm with evidence</button></form>}
      {mission.result?.actual && <section aria-label="Recorded recovery receipt">
        <h4>Recorded recovery receipt</h4>
        <p>Accepted {mission.result.actual.accepted_g} g</p>
        {['revenue','costs','net'].map(field => <p key={field}>Recorded {field}: {
          mission.result.actual[field + '_paise'] == null ? 'Not established' :
          'INR ' + (mission.result.actual[field + '_paise'] / 100).toFixed(2)
        }</p>)}
      </section>}
      {mission.passport && <button onClick={() => downloadPassport(id).catch(() => setError('Passport unavailable.'))}>Download material passport</button>}
      {['planned','in_progress','needs_evidence','awaiting_approval','approved','manual_review'].includes(mission.state) &&
        <button disabled={busy} onClick={() => transition('cancel')}>Cancel mission</button>}
      {notice && <p role="status">{notice}</p>}
    </div>}
  </section>
}
