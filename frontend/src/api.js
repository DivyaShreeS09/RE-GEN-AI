import axios from 'axios'

// In local dev, Vite proxies /api -> http://localhost:8000
// In production (Vercel/Netlify), set VITE_API_URL to your backend URL
const BASE = (import.meta.env.VITE_API_URL || '/api').replace(/^﻿/, '').trim()

const api = axios.create({ baseURL: BASE, timeout: 90000 })

export const healthCheck = () => api.get('/health')
export const analyzeWaste = (waste_type, quantity_kg, details = {}) =>
  api.post('/analyze/waste', { waste_type, quantity_kg, ...details })

export const getWasteMaterials = () => api.get('/analyze/waste/materials')
export const analyzeWater = () => api.get('/analyze/water')
export const analyzeEnergy = () => api.get('/analyze/energy')
export const getDashboardSummary = () => api.get('/dashboard/summary')
export const getWarRoom = () => api.get('/agent-war-room')
export const generateActionPlan = (payload) =>
  api.post('/generate/action-plan', payload)

export const validateUpload = (formData) =>
  api.post('/upload/validate', formData, { headers: { 'Content-Type': 'multipart/form-data' } })

export const analyzeUpload = (formData) =>
  api.post('/analyze/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 180000,
  })

export const interpretDatasets = (payload) =>
  api.post('/interpret/datasets', payload)

export const getHistory = (orgName, limit = 20) =>
  api.get(`/history/${encodeURIComponent(orgName)}`, { params: { limit } })

export const BASE_URL = BASE

// The OIDC client is public. Facility access tokens live only in memory.
let accessToken = null
let expiresAt = 0
api.interceptors.response.use(response => response, error => {
  if (error.response?.status === 401) {
    accessToken = null
    delete api.defaults.headers.common.Authorization
  }
  return Promise.reject(error)
})
const clientId = import.meta.env.VITE_OIDC_CLIENT_ID
const redirectUri = () => location.origin + location.pathname
const base64url = bytes => btoa(String.fromCharCode(...bytes)).replaceAll('+', '-').replaceAll('/', '_').replace(/=+$/, '')

function issuerEndpoint(value) {
  if (!value || new URL(value).protocol !== 'https:') throw new Error('Facility sign-in requires a configured HTTPS identity provider.')
  return value
}

export async function signIn() {
  if (accessToken && Date.now() < expiresAt) return true
  if (import.meta.env.DEV && import.meta.env.VITE_LOCAL_IDENTITY === '1' &&
      ['http://localhost:15173', 'http://127.0.0.1:15173'].includes(location.origin)) {
    const {data} = await axios.post('/api/dev/session', {}, {headers: {'X-Regen-Local': '1'}})
    accessToken = data.access_token
    expiresAt = Date.now() + (data.expires_in - 10) * 1000
    api.defaults.headers.common.Authorization = 'Bearer ' + accessToken
    return true
  }
  const endpoint = issuerEndpoint(import.meta.env.VITE_OIDC_AUTHORIZE_URL)
  if (!clientId) throw new Error('Facility sign-in has not been configured.')
  const verifier = base64url(crypto.getRandomValues(new Uint8Array(48)))
  const state = crypto.randomUUID()
  const challenge = base64url(new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(verifier))))
  sessionStorage.setItem('regen-pkce', JSON.stringify({ verifier, state, at: Date.now() }))
  const url = new URL(endpoint)
  url.search = new URLSearchParams({ client_id: clientId, redirect_uri: redirectUri(), response_type: 'code',
    scope: 'openid', state, code_challenge: challenge, code_challenge_method: 'S256' })
  location.assign(url)
  return false
}

let callback
export function finishSignIn() {
  const params = new URLSearchParams(location.search)
  if (!params.has('code') && !params.has('error')) return callback || Promise.resolve(false)
  const saved = sessionStorage.getItem('regen-pkce')
  sessionStorage.removeItem('regen-pkce')
  history.replaceState(null, '', location.pathname)
  callback = (async () => {
    const pending = saved && JSON.parse(saved)
    if (!params.has('code') || !pending || params.get('state') !== pending.state || Date.now() - pending.at > 600000)
      throw new Error('Facility sign-in expired or was declined.')
    const res = await fetch(issuerEndpoint(import.meta.env.VITE_OIDC_TOKEN_URL), {
      method: 'POST', credentials: 'omit', redirect: 'error', body: new URLSearchParams({ client_id: clientId,
        grant_type: 'authorization_code', code: params.get('code'), redirect_uri: redirectUri(), code_verifier: pending.verifier }),
    })
    if (!res.ok) throw new Error('Facility sign-in failed.')
    const session = await res.json()
    if (typeof session.access_token !== 'string' || session.token_type?.toLowerCase() !== 'bearer') throw new Error('Invalid facility session.')
    expiresAt = Date.now() + 1000 * Math.max(0, Number(session.expires_in ?? 300) - 10)
    accessToken = session.access_token
    api.defaults.headers.common.Authorization = 'Bearer ' + accessToken
    return true
  })()
  return callback
}

const consentHeaders = enabled => enabled ? {headers: {'X-AI-Consent': 'yes'}} : {}

export const createMission = (body, cloudConsent = false) => api.post('/missions', body,
  consentHeaders(cloudConsent))
export const readMission = id => api.get('/missions/' + encodeURIComponent(id))
export const updateMission = (id, body, consent = false) => api.post('/missions/' + encodeURIComponent(id) + '/transitions', body, consentHeaders(consent))
async function downloadPdf(path, filename) {
  const response = await api.get(path, { responseType: 'blob' })
  const url = URL.createObjectURL(response.data)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

export const listDevices = () => api.get('/devices')
export const meterReadings = id => api.get('/devices/' + encodeURIComponent(id) + '/observations')
export const demoWaste = (waste_type, quantity_kg) => api.post('/demo/waste', { waste_type, quantity_kg })
export const startAnalysisMission = body => api.post('/analysis-missions', body)
export const advanceAnalysisMission = (id, body, consent = false) => api.post('/analysis-missions/' + encodeURIComponent(id) + '/steps', body, consentHeaders(consent))
export const saveMaterialPhoto = file => {
  const form = new FormData()
  form.append('file', file)
  return api.post('/recovery/photos', form)
}

export const downloadAudit = id => downloadPdf('/report/' + id + '/audit-record.pdf', 'regen-audit-' + id + '.pdf')
export const downloadPassport = id => downloadPdf('/missions/' + id + '/passport.pdf', 'regen-material-passport.pdf')
export const openMaterialMissions = () => api.get('/missions')
export const groupMissions = ids => api.post('/recovery/collectives', { mission_ids: ids })
export const requestFacilityReview = mission_id => api.post('/recovery/relay', { mission_id, purpose: 'request_onboarding' })

export const clarifyMaterial = (id, body, consent = false) => api.post('/missions/' + encodeURIComponent(id) + '/clarifications', body, consentHeaders(consent))

export const readBusinessChannels = pin => api.get('/recovery/directory/' + encodeURIComponent(pin))

export const listRecoveryServices = () =>
  api.get('/recovery/services')

export const submitRecoveryService = body =>
  api.post('/recovery/services', body)

export const reviewRecoveryService = (id, body) =>
  api.post(
    '/recovery/services/' + encodeURIComponent(id) + '/review',
    body
  )

export const listRecoveryOpportunities = () => api.get('/recovery/opportunities')
export const executeAnalysisMission = id => api.post('/analysis-missions/' + encodeURIComponent(id) + '/queue')
export const readExecutionJob = id => api.get('/execution-jobs/' + encodeURIComponent(id))

export const refreshRecoveryMission = (id, version) =>
  api.post('/missions/' + encodeURIComponent(id) + '/refresh', {
    version,
  })


export const analyzeInventory = (body, consent = false) =>
  api.post('/analyze/waste/inventory', body, {
    ...consentHeaders(consent),
    timeout: 300000
  })

export async function streamInventory(body, onSnapshot, signal) {
  let offset = 0
  let pending = ''
  function consume(text) {
    if (typeof text !== 'string') return
    pending += text.slice(offset)
    offset = text.length
    const lines = pending.split('\n')
    pending = lines.pop()
    for (const line of lines) if (line.trim()) onSnapshot(JSON.parse(line))
  }

  const response = await api.post('/analyze/waste/inventory', body, {
    headers: {Accept: 'application/x-ndjson'},
    responseType: 'text',
    timeout: 300000,
    signal,
    onDownloadProgress: progress => {
      const xhr = progress.event?.target
      if (xhr?.status === 200) consume(xhr.responseText)
    },
  })
  consume(response.data)
}
