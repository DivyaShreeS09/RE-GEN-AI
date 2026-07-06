import axios from 'axios'

// In local dev, Vite proxies /api -> http://localhost:8000
// In production (Vercel/Netlify), set VITE_API_URL to your backend URL
const BASE = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/^﻿/, '').trim()

const api = axios.create({ baseURL: BASE })

export const healthCheck = () => api.get('/health')
export const analyzeWaste = (waste_type, quantity_kg) =>
  api.post('/analyze/waste', { waste_type, quantity_kg })
export const analyzeWater = () => api.get('/analyze/water')
export const analyzeEnergy = () => api.get('/analyze/energy')
export const getDashboardSummary = () => api.get('/dashboard/summary')
export const getWarRoom = () => api.get('/agent-war-room')
export const generateActionPlan = (payload) =>
  api.post('/generate/action-plan', payload)
