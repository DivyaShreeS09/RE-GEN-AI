import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const healthCheck = () => api.get('/health')
export const analyzeWaste = (waste_type, quantity_kg) =>
  api.post('/analyze/waste', { waste_type, quantity_kg })
export const analyzeWater = () => api.get('/analyze/water')
export const analyzeEnergy = () => api.get('/analyze/energy')
export const getDashboardSummary = () => api.get('/dashboard/summary')
export const getWarRoom = () => api.get('/agent-war-room')
export const generateActionPlan = (payload) =>
  api.post('/generate/action-plan', payload)
