/**
 * HeroSection — Premium image-driven hero.
 * Apple / Vercel / Nothing aesthetic: one image, one headline, one panel.
 * No Three.js. No procedural geometry. No clutter.
 */

import { useEffect, useRef, useState } from 'react'

/* ─── Timing constants ───────────────────────────────── */
const EASE = 'cubic-bezier(0.16, 1, 0.3, 1)'

/* ─── Animated counter ───────────────────────────────── */
function useCountUp(target, delayMs = 0, duration = 1600) {
  const [v, setV] = useState(0)
  useEffect(() => {
    const id = setTimeout(() => {
      const t0 = performance.now()
      const run = (now) => {
        const p = Math.min((now - t0) / duration, 1)
        const e = 1 - Math.pow(1 - p, 3)
        setV(Math.round(e * target))
        if (p < 1) requestAnimationFrame(run)
      }
      requestAnimationFrame(run)
    }, delayMs)
    return () => clearTimeout(id)
  }, [target, delayMs, duration])
  return v
}

/* ─── Floating dust particles (CSS-only, no canvas) ───── */
const DUST = Array.from({ length: 28 }, (_, i) => {
  const r = ((i * 7919 + 3571) % 1000) / 1000
  const r2 = ((i * 4999 + 1237) % 1000) / 1000
  const r3 = ((i * 6271 + 9871) % 1000) / 1000
  return {
    left: `${r * 100}%`,
    top:  `${r2 * 100}%`,
    size: 1.5 + r3 * 2.5,
    dur:  12 + r * 18,
    del:  r2 * 10,
    dx:   (r3 - 0.5) * 60,
    dy:   -(30 + r * 60),
  }
})

function DustParticles() {
  return (
    <div style={{ position: 'absolute', inset: 0, overflow: 'hidden', pointerEvents: 'none', zIndex: 2 }}>
      {DUST.map((p, i) => (
        <div
          key={i}
          style={{
            position: 'absolute',
            left: p.left,
            top: p.top,
            width: p.size,
            height: p.size,
            borderRadius: '50%',
            background: 'rgba(255,255,255,0.55)',
            animation: `dust-float-${i % 4} ${p.dur}s ${p.del}s ease-in-out infinite`,
            opacity: 0,
          }}
        />
      ))}
      <style>{`
        @keyframes dust-float-0 {
          0%   { opacity: 0; transform: translate(0px, 0px); }
          15%  { opacity: 0.6; }
          85%  { opacity: 0.4; }
          100% { opacity: 0; transform: translate(40px, -50px); }
        }
        @keyframes dust-float-1 {
          0%   { opacity: 0; transform: translate(0px, 0px); }
          20%  { opacity: 0.5; }
          80%  { opacity: 0.3; }
          100% { opacity: 0; transform: translate(-30px, -65px); }
        }
        @keyframes dust-float-2 {
          0%   { opacity: 0; transform: translate(0px, 0px); }
          25%  { opacity: 0.45; }
          75%  { opacity: 0.25; }
          100% { opacity: 0; transform: translate(20px, -45px); }
        }
        @keyframes dust-float-3 {
          0%   { opacity: 0; transform: translate(0px, 0px); }
          18%  { opacity: 0.55; }
          82%  { opacity: 0.35; }
          100% { opacity: 0; transform: translate(-45px, -55px); }
        }
      `}</style>
    </div>
  )
}

/* ─── Light ray effect ───────────────────────────────── */
function LightRays() {
  return (
    <div style={{
      position: 'absolute', inset: 0, pointerEvents: 'none', zIndex: 2,
      background: `
        radial-gradient(ellipse 40% 60% at 78% 20%,
          rgba(255,180,60,0.10) 0%,
          transparent 65%
        )
      `,
      animation: 'ray-breathe 8s ease-in-out infinite',
    }}>
      <style>{`
        @keyframes ray-breathe {
          0%, 100% { opacity: 0.7; }
          50%       { opacity: 1; }
        }
      `}</style>
    </div>
  )
}

/* ─── Metric bar ─────────────────────────────────────── */
const METRICS = [
  { label: 'Water',  value: 92, color: '#5bc8f0', icon: '💧' },
  { label: 'Energy', value: 78, color: '#f0c84a', icon: '⚡' },
  { label: 'Waste',  value: 85, color: '#6dcf6d', icon: '♻'  },
  { label: 'Carbon', value: 76, color: '#9ab4cc', icon: '🌿' },
]

function MetricRow({ label, value, color, icon, delay }) {
  const v = useCountUp(value, delay)
  const [barW, setBarW] = useState(0)
  useEffect(() => {
    const id = setTimeout(() => setBarW(value), delay + 200)
    return () => clearTimeout(id)
  }, [value, delay])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
          <span style={{ fontSize: 12 }}>{icon}</span>
          <span style={{ fontSize: 12, color: 'rgba(255,255,255,0.55)', fontWeight: 500, letterSpacing: '0.02em' }}>
            {label}
          </span>
        </div>
        <span style={{ fontSize: 13, color, fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>
          {v}%
        </span>
      </div>
      <div style={{ height: 2, background: 'rgba(255,255,255,0.08)', borderRadius: 2, overflow: 'hidden' }}>
        <div style={{
          height: '100%', background: color, borderRadius: 2,
          width: `${barW}%`,
          transition: `width 1.4s ${EASE}`,
        }} />
      </div>
    </div>
  )
}

/* ─── Glass metrics panel ────────────────────────────── */
function SustainabilityPanel({ onExplore }) {
  const [mounted, setMounted] = useState(false)
  const score = useCountUp(82, 900)

  useEffect(() => {
    const id = setTimeout(() => setMounted(true), 600)
    return () => clearTimeout(id)
  }, [])

  return (
    <div style={{
      width: 340,
      opacity: mounted ? 1 : 0,
      transform: mounted ? 'translateY(0) translateX(0)' : 'translateY(20px) translateX(8px)',
      transition: `opacity 1s ${EASE} 0.6s, transform 1s ${EASE} 0.6s`,
      animation: mounted ? 'panel-float 6s ease-in-out 1.8s infinite' : 'none',
    }}>
      <div style={{
        background: 'rgba(4, 14, 8, 0.62)',
        backdropFilter: 'blur(28px)',
        WebkitBackdropFilter: 'blur(28px)',
        border: '1px solid rgba(255,255,255,0.09)',
        borderTop: '1px solid rgba(90,200,120,0.20)',
        borderRadius: 22,
        padding: '28px 26px 24px',
        boxShadow: '0 24px 80px rgba(0,0,0,0.50), 0 0 0 0.5px rgba(255,255,255,0.04) inset',
      }}>
        {/* Label */}
        <div style={{
          fontSize: 9.5, color: 'rgba(255,255,255,0.30)',
          letterSpacing: '0.20em', textTransform: 'uppercase',
          marginBottom: 10,
        }}>
          Campus Sustainability Score
        </div>

        {/* Big number */}
        <div style={{ display: 'flex', alignItems: 'flex-end', gap: 3, marginBottom: 4 }}>
          <span style={{
            fontSize: 56, fontWeight: 800, lineHeight: 1, color: '#6fd46f',
            fontVariantNumeric: 'tabular-nums',
            textShadow: '0 0 40px rgba(111,212,111,0.25)',
          }}>
            {score}
          </span>
          <span style={{ fontSize: 26, fontWeight: 700, color: '#6fd46f', marginBottom: 4 }}>%</span>
        </div>
        <div style={{ fontSize: 11, color: '#6fd46f', marginBottom: 22, letterSpacing: '0.04em' }}>
          ● Excellent
        </div>

        <div style={{ height: 1, background: 'rgba(255,255,255,0.06)', marginBottom: 20 }} />

        {/* Metrics */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {METRICS.map((m, i) => (
            <MetricRow key={m.label} {...m} delay={900 + i * 200} />
          ))}
        </div>

        <div style={{ height: 1, background: 'rgba(255,255,255,0.05)', marginTop: 22, marginBottom: 16 }} />

        {/* Explore button */}
        <button
          onClick={onExplore}
          style={{
            width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: '11px 14px',
            background: 'rgba(111,212,111,0.08)',
            border: '1px solid rgba(111,212,111,0.18)',
            borderRadius: 12,
            color: 'rgba(255,255,255,0.65)', fontSize: 12, fontWeight: 500,
            cursor: 'pointer', fontFamily: 'inherit',
            transition: 'background 0.2s, color 0.2s, border-color 0.2s',
          }}
          onMouseEnter={e => {
            e.currentTarget.style.background = 'rgba(111,212,111,0.14)'
            e.currentTarget.style.color = 'rgba(255,255,255,0.9)'
            e.currentTarget.style.borderColor = 'rgba(111,212,111,0.30)'
          }}
          onMouseLeave={e => {
            e.currentTarget.style.background = 'rgba(111,212,111,0.08)'
            e.currentTarget.style.color = 'rgba(255,255,255,0.65)'
            e.currentTarget.style.borderColor = 'rgba(111,212,111,0.18)'
          }}
        >
          <span>Explore Full Story</span>
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M2 7h10M8 4l3 3-3 3" stroke="currentColor" strokeWidth="1.5"
              strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
      </div>

      <style>{`
        @keyframes panel-float {
          0%, 100% { transform: translateY(0px); }
          50%       { transform: translateY(-6px); }
        }
      `}</style>
    </div>
  )
}

/* ─── Main hero ──────────────────────────────────────── */
export default function HeroSection({ onScan, loading }) {
  const [vis, setVis] = useState(false)
  const bgRef = useRef(null)
  const mouse = useRef({ x: 0, y: 0 })
  const frame = useRef(null)
  const curr  = useRef({ x: 0, y: 0 })

  /* Fade-in on mount */
  useEffect(() => {
    const id = setTimeout(() => setVis(true), 100)
    return () => clearTimeout(id)
  }, [])

  /* Subtle mouse parallax — max 8px */
  useEffect(() => {
    const onMove = (e) => {
      mouse.current.x = ((e.clientX / window.innerWidth)  - 0.5) * 2
      mouse.current.y = ((e.clientY / window.innerHeight) - 0.5) * 2
    }
    window.addEventListener('mousemove', onMove)

    const animate = () => {
      curr.current.x += (mouse.current.x - curr.current.x) * 0.04
      curr.current.y += (mouse.current.y - curr.current.y) * 0.04
      if (bgRef.current) {
        const px = curr.current.x * 8
        const py = curr.current.y * 8
        bgRef.current.style.transform = `scale(1.06) translate(${px}px, ${py}px)`
      }
      frame.current = requestAnimationFrame(animate)
    }
    frame.current = requestAnimationFrame(animate)

    return () => {
      window.removeEventListener('mousemove', onMove)
      cancelAnimationFrame(frame.current)
    }
  }, [])

  const rise = (delay) => ({
    opacity:    vis ? 1 : 0,
    transform:  vis ? 'translateY(0)' : 'translateY(24px)',
    transition: `opacity 0.95s ${EASE} ${delay}ms, transform 0.95s ${EASE} ${delay}ms`,
  })

  const scrollTo = (id) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <section style={{
      position: 'relative',
      width: '100%',
      height: '100vh',
      overflow: 'hidden',
      background: '#060e08',
      display: 'flex',
      alignItems: 'center',
    }}>

      {/* ── Background image with slow zoom ── */}
      <div style={{ position: 'absolute', inset: 0, overflow: 'hidden', zIndex: 0 }}>
        <img
          ref={bgRef}
          src="/hero-campus.jpg"
          alt=""
          aria-hidden
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            objectPosition: 'center 30%',
            transform: 'scale(1.06)',
            transformOrigin: 'center center',
            animation: 'hero-zoom 28s ease-in-out infinite alternate',
            willChange: 'transform',
            display: 'block',
          }}
        />
      </div>

      {/* ── Left gradient — text legibility ── */}
      <div style={{
        position: 'absolute', inset: 0, zIndex: 1, pointerEvents: 'none',
        background: `
          linear-gradient(
            105deg,
            rgba(4,12,6,0.88) 0%,
            rgba(4,12,6,0.65) 32%,
            rgba(4,12,6,0.22) 55%,
            transparent 72%
          )
        `,
      }} />

      {/* ── Right dim veil — behind panel ── */}
      <div style={{
        position: 'absolute', inset: 0, zIndex: 1, pointerEvents: 'none',
        background: `
          linear-gradient(
            to left,
            rgba(4,12,6,0.55) 0%,
            rgba(4,12,6,0.20) 38%,
            transparent 55%
          )
        `,
      }} />

      {/* ── Vignette — edges ── */}
      <div style={{
        position: 'absolute', inset: 0, zIndex: 1, pointerEvents: 'none',
        background: `
          radial-gradient(
            ellipse 90% 85% at 50% 50%,
            transparent 55%,
            rgba(2,8,4,0.55) 100%
          )
        `,
      }} />

      {/* ── Bottom shadow ── */}
      <div style={{
        position: 'absolute', bottom: 0, left: 0, right: 0, height: '25%',
        zIndex: 1, pointerEvents: 'none',
        background: 'linear-gradient(to top, rgba(2,8,4,0.60) 0%, transparent 100%)',
      }} />

      {/* ── Light rays + dust particles ── */}
      <LightRays />
      <DustParticles />

      {/* ── Hero content grid ── */}
      <div style={{
        position: 'relative', zIndex: 10,
        width: '100%', maxWidth: 1440,
        margin: '0 auto',
        padding: '0 100px',
        display: 'grid',
        gridTemplateColumns: 'repeat(12, 1fr)',
        gap: 24,
        alignItems: 'center',
        paddingTop: 64, /* clear fixed nav */
      }}>

        {/* ── Left: headline + CTAs (cols 1–6) ── */}
        <div style={{ gridColumn: '1 / 7' }}>

          {/* Eyebrow */}
          <div style={{ ...rise(180), display: 'flex', alignItems: 'center', gap: 10, marginBottom: 24 }}>
            <span style={{ fontSize: 10.5, color: 'rgba(255,255,255,0.32)', letterSpacing: '0.26em' }}>01</span>
            <div style={{ width: 28, height: 1, background: 'rgba(255,255,255,0.18)' }} />
            <span style={{
              fontSize: 10.5, color: 'rgba(111,212,111,0.75)',
              letterSpacing: '0.20em', textTransform: 'uppercase', fontWeight: 600,
            }}>
              The Awakening
            </span>
          </div>

          {/* Headline */}
          <h1 style={{
            ...rise(360),
            margin: '0 0 20px',
            fontSize: 'clamp(38px, 4.6vw, 66px)',
            fontWeight: 800,
            lineHeight: 1.04,
            letterSpacing: '-0.028em',
            color: '#ffffff',
            textShadow: '0 2px 60px rgba(0,0,0,0.55)',
            textWrap: 'balance',
          }}>
            Every Campus<br />
            Tells a{' '}
            <span style={{
              color: '#6fd46f',
              textShadow: '0 0 60px rgba(111,212,111,0.30)',
            }}>
              Story.
            </span>
          </h1>

          {/* Subtitle */}
          <p style={{
            ...rise(520),
            margin: '0 0 40px',
            fontSize: 16.5, lineHeight: 1.65, fontWeight: 400,
            color: 'rgba(255,255,255,0.52)',
            textShadow: '0 1px 20px rgba(0,0,0,0.55)',
            maxWidth: 400,
          }}>
            RE:GEN AI listens, understands,<br />and helps it heal.
          </p>

          {/* CTAs */}
          <div style={{ ...rise(680), display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>

            {/* Primary — Begin Mission */}
            <button
              onClick={onScan}
              disabled={loading}
              style={{
                display: 'inline-flex', alignItems: 'center', gap: 10,
                padding: '14px 30px',
                background: loading ? 'rgba(255,255,255,0.75)' : 'rgba(255,255,255,0.96)',
                color: '#0d1f12',
                border: 'none', borderRadius: 50,
                fontSize: 14, fontWeight: 700, letterSpacing: '0.01em',
                cursor: loading ? 'not-allowed' : 'pointer',
                boxShadow: '0 4px 28px rgba(0,0,0,0.30), 0 1px 0 rgba(255,255,255,0.8) inset',
                fontFamily: 'inherit',
                transition: 'transform 0.18s ease, box-shadow 0.25s ease, background 0.2s',
              }}
              onMouseEnter={e => {
                if (!loading) {
                  e.currentTarget.style.transform = 'translateY(-2px) scale(1.02)'
                  e.currentTarget.style.boxShadow = '0 10px 42px rgba(0,0,0,0.38), 0 1px 0 rgba(255,255,255,0.8) inset'
                }
              }}
              onMouseLeave={e => {
                e.currentTarget.style.transform = ''
                e.currentTarget.style.boxShadow = '0 4px 28px rgba(0,0,0,0.30), 0 1px 0 rgba(255,255,255,0.8) inset'
              }}
            >
              {loading ? (
                <>
                  <span style={{
                    width: 15, height: 15,
                    border: '2.5px solid #0d1f12', borderTopColor: 'transparent',
                    borderRadius: '50%', display: 'inline-block',
                    animation: 'hero-spin 0.7s linear infinite',
                    flexShrink: 0,
                  }} />
                  Initializing…
                </>
              ) : (
                <>
                  <span style={{
                    width: 28, height: 28, background: '#0d1f12', borderRadius: '50%',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    marginLeft: -6, flexShrink: 0,
                  }}>
                    <svg width="11" height="11" viewBox="0 0 11 11" fill="none">
                      <path d="M2 5.5h7M6 3l2.5 2.5L6 8" stroke="white" strokeWidth="1.6"
                        strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  </span>
                  Begin Mission
                </>
              )}
            </button>

            {/* Secondary — Explore the Vision */}
            <button
              onClick={() => scrollTo('twin')}
              style={{
                display: 'inline-flex', alignItems: 'center', gap: 8,
                padding: '13px 24px',
                background: 'transparent',
                color: 'rgba(255,255,255,0.72)',
                border: '1px solid rgba(255,255,255,0.22)',
                borderRadius: 50,
                fontSize: 14, fontWeight: 500,
                cursor: 'pointer', fontFamily: 'inherit',
                transition: 'border-color 0.2s, color 0.2s, transform 0.18s ease, background 0.2s',
                letterSpacing: '0.01em',
              }}
              onMouseEnter={e => {
                e.currentTarget.style.borderColor = 'rgba(255,255,255,0.44)'
                e.currentTarget.style.color = 'rgba(255,255,255,0.95)'
                e.currentTarget.style.background = 'rgba(255,255,255,0.06)'
                e.currentTarget.style.transform = 'translateY(-2px)'
              }}
              onMouseLeave={e => {
                e.currentTarget.style.borderColor = 'rgba(255,255,255,0.22)'
                e.currentTarget.style.color = 'rgba(255,255,255,0.72)'
                e.currentTarget.style.background = 'transparent'
                e.currentTarget.style.transform = ''
              }}
            >
              Explore the Vision
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M2 7h10M8 4l3 3-3 3" stroke="currentColor" strokeWidth="1.5"
                  strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
          </div>

          {/* System status */}
          <div style={{ ...rise(860), display: 'flex', alignItems: 'center', gap: 8, marginTop: 32 }}>
            <div style={{
              width: 7, height: 7, borderRadius: '50%', background: '#4ade80',
              boxShadow: '0 0 8px rgba(74,222,128,0.7)',
              animation: 'hero-pulse 2.4s ease-in-out infinite',
            }} />
            <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.30)', letterSpacing: '0.06em' }}>
              System Online · All systems operational
            </span>
          </div>
        </div>

        {/* ── Right: glass panel (cols 8–12) ── */}
        <div style={{
          gridColumn: '8 / 13',
          display: 'flex',
          justifyContent: 'flex-end',
          alignItems: 'center',
        }}>
          <SustainabilityPanel onExplore={() => scrollTo('action-plan')} />
        </div>
      </div>

      {/* ── Scroll cue ── */}
      <div style={{
        position: 'absolute', bottom: 28, left: '50%',
        transform: 'translateX(-50%)',
        display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 7,
        zIndex: 10, pointerEvents: 'none',
        opacity: vis ? 0.38 : 0,
        transition: `opacity 1s ${EASE} 1.6s`,
      }}>
        <span style={{
          fontSize: 9.5, color: 'rgba(255,255,255,0.6)',
          letterSpacing: '0.26em', textTransform: 'uppercase', fontWeight: 500,
        }}>
          Scroll to explore
        </span>
        <div style={{
          width: 1, height: 24,
          background: 'linear-gradient(to bottom, rgba(255,255,255,0.5), transparent)',
          animation: 'hero-scroll-bob 2.2s ease-in-out infinite',
        }} />
      </div>

      {/* ── Global keyframes ── */}
      <style>{`
        @keyframes hero-zoom {
          0%   { transform: scale(1.06); }
          100% { transform: scale(1.09); }
        }
        @keyframes hero-spin  { to { transform: rotate(360deg); } }
        @keyframes hero-pulse {
          0%, 100% { box-shadow: 0 0 4px rgba(74,222,128,0.45); }
          50%       { box-shadow: 0 0 12px rgba(74,222,128,0.90); }
        }
        @keyframes hero-scroll-bob {
          0%, 100% { opacity: 0.5; transform: scaleY(1); }
          50%       { opacity: 1;   transform: scaleY(1.12); }
        }
      `}</style>
    </section>
  )
}
