import { useEffect, useState } from 'react'
import { listDevices, meterReadings } from '../api'

export default function MeterZones() {
  const [devices, setDevices] = useState([])
  const [selected, select] = useState('')
  const [series, setSeries] = useState(null)
  const [error, setError] = useState('')
  useEffect(() => {
    let active = true
    listDevices().then(({data}) => { if (active) setDevices(data) }).catch(() => { if (active) setError('Meter inventory unavailable.') })
    return () => { active = false }
  }, [])
  useEffect(() => {
    setSeries(null)
    if (!selected) return
    let active = true
    const refresh = () => meterReadings(selected).then(({data}) => {
      if (active) { setSeries(data); setError('') }
    }).catch(() => { if (active) setError('Meter readings unavailable.') })
    refresh()
    const timer = setInterval(refresh, 30000)
    return () => { active = false; clearInterval(timer) }
  }, [selected])
  return <section id="meter-zones" className="glass p-5"><h2>Instrumented zones</h2>
    {error && <p role="alert">{error}</p>}
    {devices.length ? <label>Meter <select value={selected} onChange={e => select(e.target.value)}>
      <option value="">Select a zone and meter</option>{devices.map(d => <option key={d.id} value={d.id}>{d.zone_id} · {d.metric} · {d.id.slice(-6)}</option>)}</select></label>
      : !error && <p>No registered meters returned.</p>}
    {series && <div><p>{{
      device_http: 'Authenticated gateway observations', staff_import: 'Uploaded historical observations',
      manual_meter_reading: 'Staff-entered meter observations',
    }[series.source] || 'No recorded source'}</p><p>{series.zone_id} · {series.readings.length === 0 ? 'No available readings' : series.stale ? 'Stale readings' : 'Current readings'} · {series.calibrated ? 'Within calibration period' : 'Calibration expired'}</p>
      {series.findings.map(f => <p key={f.label}>{f.label} · {f.next_step}</p>)}
      <table><caption>Latest meter observations</caption><thead><tr><th>Time</th><th>Raw reading</th><th>Interval total</th><th>Quality</th></tr></thead>
        <tbody>{series.readings.slice(-10).reverse().map(r => <tr key={r.timestamp}><td>{new Date(r.timestamp).toLocaleString()}</td><td>{r.value} {r.unit}</td>
          <td>{r.interval_total == null ? 'Unavailable' : r.interval_total.toFixed(3) + ' ' + series.interval_unit}</td><td>{r.quality}</td></tr>)}</tbody></table></div>}
  </section>
}
