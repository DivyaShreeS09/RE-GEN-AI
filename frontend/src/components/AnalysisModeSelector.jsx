import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

export default function AnalysisModeSelector({ open, onDemo, onUpload, onClose }) {
  const [hovered, setHovered] = useState(null)

  if (!open) return null

  const cardBase = {
    position: 'relative',
    flex: '1 1 0',
    minWidth: 0,
    borderRadius: 20,
    padding: '32px 28px 28px',
    cursor: 'pointer',
    transition: 'border-color 0.22s ease, box-shadow 0.22s ease, transform 0.18s ease',
    display: 'flex',
    flexDirection: 'column',
    gap: 14,
    backdropFilter: 'blur(28px)',
    WebkitBackdropFilter: 'blur(28px)',
  }

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          key="mode-overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.25 }}
          onClick={onClose}
          style={{
            position: 'fixed', inset: 0, zIndex: 200,
            background: 'rgba(0,0,0,0.72)',
            backdropFilter: 'blur(6px)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            padding: '24px 16px',
          }}
        >
          <motion.div
            initial={{ scale: 0.93, opacity: 0, y: 16 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.93, opacity: 0, y: 16 }}
            transition={{ duration: 0.32, ease: [0.16, 1, 0.3, 1] }}
            onClick={e => e.stopPropagation()}
            style={{
              width: '100%', maxWidth: 680,
              background: 'rgba(3, 9, 20, 0.96)',
              border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: 28,
              padding: '36px 32px 32px',
              boxShadow: '0 40px 120px rgba(0,0,0,0.7), 0 0 0 0.5px rgba(255,255,255,0.04) inset',
            }}
          >
            {/* Header */}
            <div style={{ textAlign: 'center', marginBottom: 32 }}>
              <div style={{
                display: 'inline-flex', alignItems: 'center', gap: 8,
                padding: '4px 14px', borderRadius: 50,
                background: 'rgba(0,255,136,0.07)',
                border: '1px solid rgba(0,255,136,0.16)',
                marginBottom: 16,
              }}>
                <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#00ff88', boxShadow: '0 0 8px #00ff88', animation: 'modePulse 2s ease-in-out infinite' }} />
                <span style={{ fontSize: 10.5, fontWeight: 700, letterSpacing: '0.18em', color: '#00cc77', textTransform: 'uppercase' }}>
                  Start Analysis
                </span>
              </div>
              <h2 style={{
                fontSize: 'clamp(20px, 3vw, 28px)',
                fontWeight: 800, color: '#ffffff',
                lineHeight: 1.15, margin: '0 0 10px',
              }}>
                Choose Analysis Mode
              </h2>
              <p style={{ fontSize: 13.5, color: 'rgba(203,213,225,0.55)', margin: 0 }}>
                Use bundled demo datasets or upload your organization's resource data.
              </p>
            </div>

            {/* Cards */}
            <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>

              {/* Demo card */}
              <div
                onClick={onDemo}
                onMouseEnter={() => setHovered('demo')}
                onMouseLeave={() => setHovered(null)}
                style={{
                  ...cardBase,
                  background: hovered === 'demo'
                    ? 'rgba(0,229,255,0.07)'
                    : 'rgba(255,255,255,0.03)',
                  border: hovered === 'demo'
                    ? '1.5px solid rgba(0,229,255,0.42)'
                    : '1.5px solid rgba(255,255,255,0.09)',
                  boxShadow: hovered === 'demo' ? '0 0 32px rgba(0,229,255,0.12)' : 'none',
                  transform: hovered === 'demo' ? 'translateY(-2px)' : 'none',
                }}
              >
                {/* Recommended badge */}
                <div style={{
                  position: 'absolute', top: 16, right: 16,
                  padding: '3px 10px', borderRadius: 50,
                  background: 'rgba(0,255,136,0.10)',
                  border: '1px solid rgba(0,255,136,0.28)',
                  fontSize: 9.5, fontWeight: 700,
                  color: '#00cc77', letterSpacing: '0.12em', textTransform: 'uppercase',
                }}>
                  Recommended
                </div>

                <div style={{ fontSize: 36, marginBottom: 4 }}>🏛️</div>
                <div style={{ fontWeight: 800, fontSize: 17, color: '#ffffff' }}>
                  Demo Analysis
                </div>
                <div style={{ fontSize: 12.5, color: 'rgba(148,163,184,0.80)', lineHeight: 1.65 }}>
                  Instant analysis using bundled smart-campus datasets.
                  No upload required — see the full 7-agent pipeline in action.
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 7, marginTop: 4 }}>
                  {[
                    '7-day hourly water usage data',
                    'Campus energy consumption logs',
                    '97-material Waste-to-Wealth knowledge base',
                    'Fuel & occupancy demo datasets',
                  ].map(item => (
                    <div key={item} style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                      <span style={{ color: '#00e5ff', fontSize: 11, marginTop: 1, flexShrink: 0 }}>✓</span>
                      <span style={{ fontSize: 11.5, color: 'rgba(203,213,225,0.65)' }}>{item}</span>
                    </div>
                  ))}
                </div>

                <div style={{
                  marginTop: 'auto', paddingTop: 16,
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                }}>
                  <span style={{ fontSize: 11.5, color: '#00e5ff', fontWeight: 600 }}>
                    Launch instantly →
                  </span>
                  <div style={{
                    width: 32, height: 32, borderRadius: '50%',
                    background: 'rgba(0,229,255,0.12)',
                    border: '1px solid rgba(0,229,255,0.28)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}>
                    <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
                      <path d="M2 6.5h9M8 3.5l3 3-3 3" stroke="#00e5ff" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </div>
                </div>
              </div>

              {/* Upload card */}
              <div
                onClick={onUpload}
                onMouseEnter={() => setHovered('upload')}
                onMouseLeave={() => setHovered(null)}
                style={{
                  ...cardBase,
                  background: hovered === 'upload'
                    ? 'rgba(0,255,136,0.06)'
                    : 'rgba(255,255,255,0.03)',
                  border: hovered === 'upload'
                    ? '1.5px solid rgba(0,255,136,0.38)'
                    : '1.5px solid rgba(255,255,255,0.09)',
                  boxShadow: hovered === 'upload' ? '0 0 32px rgba(0,255,136,0.10)' : 'none',
                  transform: hovered === 'upload' ? 'translateY(-2px)' : 'none',
                }}
              >
                <div style={{ fontSize: 36, marginBottom: 4 }}>📂</div>
                <div style={{ fontWeight: 800, fontSize: 17, color: '#ffffff' }}>
                  Upload Your Data
                </div>
                <div style={{ fontSize: 12.5, color: 'rgba(148,163,184,0.80)', lineHeight: 1.65 }}>
                  Analyse your organization's actual resource usage data.
                  Supports partial uploads — every dataset is optional.
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 7, marginTop: 4 }}>
                  {[
                    'Universities, hotels, hospitals, offices',
                    'Industries, government buildings',
                    'CSV and Excel (.xlsx) supported',
                    'Manual entry for organizations without files',
                  ].map(item => (
                    <div key={item} style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                      <span style={{ color: '#00ff88', fontSize: 11, marginTop: 1, flexShrink: 0 }}>✓</span>
                      <span style={{ fontSize: 11.5, color: 'rgba(203,213,225,0.65)' }}>{item}</span>
                    </div>
                  ))}
                </div>

                {/* Coming Soon formats */}
                <div style={{
                  marginTop: 10,
                  padding: '8px 12px', borderRadius: 8,
                  background: 'rgba(255,255,255,0.03)',
                  border: '1px solid rgba(255,255,255,0.07)',
                }}>
                  <span style={{ fontSize: 9.5, color: 'rgba(100,116,139,0.8)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.1em' }}>
                    Coming Soon:&nbsp;
                  </span>
                  <span style={{ fontSize: 10.5, color: 'rgba(100,116,139,0.7)' }}>PDF · Images · IoT API · ERP Integration</span>
                </div>

                <div style={{
                  marginTop: 'auto', paddingTop: 16,
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                }}>
                  <span style={{ fontSize: 11.5, color: '#00ff88', fontWeight: 600 }}>
                    Upload Data →
                  </span>
                  <div style={{
                    width: 32, height: 32, borderRadius: '50%',
                    background: 'rgba(0,255,136,0.10)',
                    border: '1px solid rgba(0,255,136,0.25)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}>
                    <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
                      <path d="M2 6.5h9M8 3.5l3 3-3 3" stroke="#00ff88" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </div>
                </div>
              </div>
            </div>

            {/* Close hint */}
            <p style={{ textAlign: 'center', marginTop: 22, fontSize: 11, color: 'rgba(100,116,139,0.55)' }}>
              Press Esc or click outside to dismiss
            </p>
          </motion.div>
        </motion.div>
      )}
      <style>{`
        @keyframes modePulse {
          0%, 100% { box-shadow: 0 0 4px #00ff88; }
          50% { box-shadow: 0 0 12px #00ff88; }
        }
      `}</style>
    </AnimatePresence>
  )
}
