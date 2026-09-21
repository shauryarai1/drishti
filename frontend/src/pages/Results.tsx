import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import Navbar from '../components/Navbar'
import KundliRenderer from '../components/KundliRenderer'
import type { InterpretationResponse, InterpretationArea, ChartData } from '../types/interpretation'

const PLANET_LEGEND = [
  { abbr: 'Su', name: 'Sun' },
  { abbr: 'Mo', name: 'Moon' },
  { abbr: 'Ma', name: 'Mars' },
  { abbr: 'Me', name: 'Mercury' },
  { abbr: 'Ju', name: 'Jupiter' },
  { abbr: 'Ve', name: 'Venus' },
  { abbr: 'Sa', name: 'Saturn' },
  { abbr: 'Ra', name: 'Rahu' },
  { abbr: 'Ke', name: 'Ketu' },
  { abbr: 'Ur', name: 'Uranus' },
  { abbr: 'Ne', name: 'Neptune' },
  { abbr: 'Pl', name: 'Pluto' },
]

interface BirthDetails {
  date: string
  time: string
  place: string
}

// ── Shared motion variants ──
const EASE: [number, number, number, number] = [0.23, 1, 0.32, 1]

const fadeUp = (delay: number) => ({
  initial: { opacity: 0, y: 30 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.6, delay, ease: EASE },
})

const dividerAnim = (delay: number) => ({
  initial: { scaleX: 0 },
  animate: { scaleX: 1 },
  transition: { duration: 0.8, delay },
})

// ── Danger Area Section ──
function DangerSection({ area, delay }: { area: InterpretationArea; delay: number }) {
  return (
    <motion.article className="reading-section danger-section" {...fadeUp(delay)}>
      <div className="section-number" aria-hidden="true">03</div>
      <div className="reading-section__content">
        <div className="section-badge section-badge--danger">
          <span className="section-badge__text">DANGER AREA · HIGH PRIORITY</span>
        </div>

        <h2 className="reading-section__area">{area.area}</h2>

        <p className="reading-section__lead">This is the part of your reading to take most seriously.</p>

      {area.hook && (
        <p className="reading-section__hook">{area.hook}</p>
      )}

        <div className="reading-section__body">
          <p className="reading-section__desc">{area.description}</p>
          {area.potential_impact && (
            <p className="reading-section__impact">{area.potential_impact}</p>
          )}
        </div>

        {area.mindful_of.length > 0 && (
          <div className="reading-section__careful">
            <div className="reading-section__careful-label">Be careful with:</div>
            <ul className="reading-section__list">
              {area.mindful_of.map((item, i) => (
                <li key={i} className="reading-section__list-item">{item}</li>
              ))}
            </ul>
          </div>
        )}

        {area.takeaway && (
          <div className="reading-section__takeaway">
            <p className="reading-section__takeaway-text">{area.takeaway}</p>
          </div>
        )}
      </div>
    </motion.article>
  )
}

function AttentionSection({ area, delay }: { area: InterpretationArea; delay: number }) {
  return (
    <motion.article className="reading-section attention-section" {...fadeUp(delay)}>
      <div className="section-number" aria-hidden="true">01</div>
      <div className="reading-section__content">
        <div className="section-badge section-badge--attention">
          <span className="section-badge__text">ATTENTION AREA</span>
        </div>
        <h2 className="reading-section__area">{area.area}</h2>
        <div className="reading-section__micro-label">WHY THIS MATTERS</div>
        <div className="reading-section__body">
          <p className="reading-section__desc">{area.description}</p>
        </div>
      </div>
    </motion.article>
  )
}

// ── Protect Area Section ──
function ProtectSection({ area, delay }: { area: InterpretationArea; delay: number }) {
  return (
    <motion.article className="reading-section protect-section" {...fadeUp(delay)}>
      <div className="section-number" aria-hidden="true">02</div>
      <div className="reading-section__content">
        <div className="section-badge section-badge--protect">
          <span className="section-badge__text">PROTECT THIS AREA</span>
        </div>

        <h2 className="reading-section__area">{area.area}</h2>

        <div className="reading-section__micro-label">KNOW WHERE TO STOP</div>

      {area.hook && (
        <p className="reading-section__hook">{area.hook}</p>
      )}

      <div className="reading-section__body">
        <p className="reading-section__desc">{area.description}</p>
        {area.potential_impact && (
          <p className="reading-section__impact">{area.potential_impact}</p>
        )}
      </div>

      {area.mindful_of.length > 0 && (
        <div className="reading-section__careful">
          <div className="reading-section__careful-label">Pay attention to:</div>
          <ul className="reading-section__list">
            {area.mindful_of.map((item, i) => (
              <li key={i} className="reading-section__list-item">{item}</li>
            ))}
          </ul>
        </div>
      )}

        {area.takeaway && (
          <div className="reading-section__takeaway">
            <p className="reading-section__takeaway-text">{area.takeaway}</p>
          </div>
        )}
      </div>
    </motion.article>
  )
}

function KundliFrame({ chart, birthDetails }: { chart: ChartData; birthDetails?: BirthDetails }) {
  const [tilt, setTilt] = useState({ x: 0, y: 0 })

  const handlePointerMove = (event: React.PointerEvent<HTMLDivElement>) => {
    if (
      event.pointerType !== 'mouse' ||
      window.matchMedia('(prefers-reduced-motion: reduce)').matches
    ) return
    const bounds = event.currentTarget.getBoundingClientRect()
    const x = ((event.clientX - bounds.left) / bounds.width - 0.5) * 2
    const y = ((event.clientY - bounds.top) / bounds.height - 0.5) * 2
    setTilt({ x: y * -1.4, y: x * 1.4 })
  }

  const formatDate = (value: string) => {
    if (!value) return 'Not provided'
    const parsed = new Date(`${value}T12:00:00`)
    return Number.isNaN(parsed.getTime())
      ? value
      : parsed.toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })
  }

  return (
    <div className="kundli-layout">
      <div
        className="kundli-frame"
        onPointerMove={handlePointerMove}
        onPointerLeave={() => setTilt({ x: 0, y: 0 })}
        style={{ transform: `perspective(1400px) rotateX(${tilt.x}deg) rotateY(${tilt.y}deg)` }}
      >
        <div className="kundli-frame__halo" aria-hidden="true" />
        <div className="kundli-frame__inner">
          <KundliRenderer chart={chart} />
        </div>
      </div>

      <div className="kundli-info" aria-label="Birth details">
        <div className="kundli-info__intro">
          <span className="kundli-info__label">THE FOUNDATION</span>
          <p>This is the birth chart behind your personal reading — a visual map of the patterns highlighted below.</p>
        </div>
        <dl className="kundli-info__details">
          <div><dt>Date</dt><dd>{formatDate(birthDetails?.date || '')}</dd></div>
          <div><dt>Time</dt><dd>{birthDetails?.time || 'Not provided'}</dd></div>
          <div><dt>Place</dt><dd>{birthDetails?.place || 'Not provided'}</dd></div>
          <div><dt>Ascendant</dt><dd>{chart.ascendant_sign || 'Not available'}</dd></div>
        </dl>
      </div>
    </div>
  )
}

// ── Consultation CTA ──
function ConsultationCTA({ delay }: { delay: number }) {
  return (
    <motion.div className="consultation-cta" {...fadeUp(delay)}>
      <div className="consultation-cta__card">
        <div className="consultation-cta__eyebrow">Want to go deeper?</div>
        <h2 className="consultation-cta__headline">
          Your Kundli shows the pattern.<br />
          A personal reading explains the story behind it.
        </h2>
        <p className="consultation-cta__text">
          If you want to understand the rest of your chart — including the areas
          that weren't covered in this quick reading — reach out for a detailed
          consultation.
        </p>
        <a href="mailto:hello@drishti.app" className="btn btn--primary btn--lg consultation-cta__btn">
          Contact for a Personal Reading
          <span className="btn__arrow">→</span>
        </a>
      </div>
    </motion.div>
  )
}

// ══════════════════════════════════════════════════════════════════════════
// Main Results Page
// ══════════════════════════════════════════════════════════════════════════

export default function Results() {
  const navigate = useNavigate()
  const [result, setResult] = useState<InterpretationResponse | null>(null)
  const [name, setName] = useState('')
  const [birthDetails, setBirthDetails] = useState<BirthDetails>()

  useEffect(() => {
    const stored = sessionStorage.getItem('drishti_result')
    if (!stored) {
      navigate('/tool')
      return
    }
    try {
      setResult(JSON.parse(stored))
      setName(sessionStorage.getItem('drishti_name') || '')
      const storedDetails = sessionStorage.getItem('drishti_birth_details')
      if (storedDetails) setBirthDetails(JSON.parse(storedDetails))
    } catch {
      navigate('/tool')
    }
  }, [navigate])

  if (!result) return null

  const chart: ChartData | undefined = result.chart
  return (
    <div className="results-page">
      <Navbar />

      <main className="results-main">
        <div className="results-container">

          {/* ════════════════════════════════════════════
              1. YOUR DRISHTI — Header
              ════════════════════════════════════════════ */}
          <motion.div className="results-header" {...fadeUp(0)}>
            <div className="results-header__eyebrow">Your Drishti</div>
            <h1 className="results-header__title">
              {name ? `${name}'s Reading` : 'What deserves your attention'}
            </h1>
            <p className="results-header__sub">
              A personalized view of the areas of life that may require greater care.
            </p>
          </motion.div>

          <motion.div className="results-divider" {...dividerAnim(0.3)} />

          {/* ════════════════════════════════════════════
              2. YOUR KUNDLI — Chart near the top
              ════════════════════════════════════════════ */}
          {chart && (
            <motion.div className="kundli-section" {...fadeUp(0.4)}>
              <div className="kundli-section__header">
                <div className="kundli-section__eyebrow">Your Kundli</div>
                <h2 className="kundli-section__title">The Map Behind Your Reading</h2>
                <p className="kundli-section__sub">
                  A visual foundation for the patterns highlighted in your reading.
                </p>
              </div>

              <KundliFrame chart={chart} birthDetails={birthDetails} />

              <div className="kundli-legend">
                {PLANET_LEGEND.map(({ abbr, name }) => (
                  <div key={abbr} className="kundli-legend__item">
                    <span className="kundli-legend__abbr">{abbr}</span>
                    <span className="kundli-legend__name">{name}</span>
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          <motion.div className="results-divider" {...dividerAnim(0.7)} />

          {/* ════════════════════════════════════════════
              3. ATTENTION, PROTECT, AND DANGER
              ════════════════════════════════════════════ */}
          <AttentionSection area={result.attention} delay={0.8} />

          <motion.div className="results-divider" {...dividerAnim(1.1)} />

          <ProtectSection area={result.protect} delay={1.2} />

          <motion.div className="results-divider" {...dividerAnim(1.5)} />

          <DangerSection area={result.danger} delay={1.6} />

          <motion.div className="results-divider" {...dividerAnim(1.9)} />

          {/* ════════════════════════════════════════════
              6. YOUR TAKEAWAY
              ════════════════════════════════════════════ */}
          <motion.div className="results-takeaway-section" {...fadeUp(2.0)}>
            <div className="results-takeaway-card">
              <div className="results-takeaway-card__label">Your Takeaway</div>
              <p className="results-takeaway-card__text">
                This reading is not asking you to fear these areas. It is showing you where awareness matters most: stay alert around {result.attention.area.toLowerCase()}, create a clear boundary around {result.protect.area.toLowerCase()}, and take the greatest care with {result.danger.area.toLowerCase()}.
              </p>
            </div>
          </motion.div>

          <motion.div className="results-divider" {...dividerAnim(2.1)} />

          {/* ════════════════════════════════════════════
              7. CONSULTATION CTA
              ════════════════════════════════════════════ */}
          <ConsultationCTA delay={2.2} />

          {/* ════════════════════════════════════════════
              FOOTER ACTIONS
              ════════════════════════════════════════════ */}
          <motion.div className="results-footer" {...fadeUp(2.4)}>
            <div className="results-footer__actions">
              <Link to="/tool" className="btn btn--secondary">
                New Reading
              </Link>
              <Link to="/" className="btn btn--ghost">
                Back to Home
              </Link>
            </div>
          </motion.div>
        </div>
      </main>

      <footer className="footer">
        <div className="footer__inner">
          <span className="footer__brand">DRISHTI</span>
          <span className="footer__tagline">दृष्टि — vision, perspective, insight</span>
        </div>
      </footer>
    </div>
  )
}
