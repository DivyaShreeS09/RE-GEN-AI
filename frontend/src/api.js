import axios from 'axios'

// In local dev, Vite proxies /api -> http://localhost:8000
// In production (Vercel/Netlify), set VITE_API_URL to your backend URL
const BASE = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/^﻿/, '').trim()

const api = axios.create({ baseURL: BASE, timeout: 90000 })

export const healthCheck = () => api.get('/health')
export const analyzeWaste = (waste_type, quantity_kg) =>
  api.post('/analyze/waste', { waste_type, quantity_kg })

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

export const BASE_URL = BASE
