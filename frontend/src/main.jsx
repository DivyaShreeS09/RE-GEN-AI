import { StrictMode, Suspense } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import AnalysisErrorBoundary from './components/AnalysisErrorBoundary'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <AnalysisErrorBoundary><Suspense fallback={<p role="status">Loading RE:GEN AI…</p>}><App /></Suspense></AnalysisErrorBoundary>
  </StrictMode>,
)
