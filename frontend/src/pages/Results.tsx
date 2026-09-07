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

// ── Shared motion variants ──
const EASE: [number, number, number, number] = [0.25, 0.1, 0.25, 1]

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
    <motion.div className="reading-section danger-section" {...fadeUp(delay)}>
      <div className="section-badge section-badge--danger">
        <span className="section-badge__icon">⚠️</span>
        <span className="section-badge__text">DANGER AREA</span>
      </div>

      <h2 className="reading-section__area">{area.area}</h2>

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
    </motion.div>
  )
}

function AttentionSection({ area, delay }: { area: InterpretationArea; delay: number }) {
  return (
    <motion.div className="reading-section protect-section" {...fadeUp(delay)}>
      <div className="section-badge section-badge--protect">
        <span className="section-badge__text">ATTENTION AREA</span>
      </div>
      <h2 className="reading-section__area">{area.area}</h2>
      <div className="reading-section__body">
        <p className="reading-section__desc">{area.description}</p>
      </div>
    </motion.div>
  )
}

// ── Protect Area Section ──
function ProtectSection({ area, delay }: { area: InterpretationArea; delay: number }) {
  return (
    <motion.div className="reading-section protect-section" {...fadeUp(delay)}>
      <div className="section-badge section-badge--protect">
        <span className="section-badge__icon">🛡️</span>
        <span className="section-badge__text">PROTECT THIS AREA</span>
      </div>

      <h2 className="reading-section__area">{area.area}</h2>

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
    </motion.div>
  )
}

// ── Transit Caution Section ──
function TransitSection({ heading, description, delay }: { heading: string; description: string; delay: number }) {
  return (
    <motion.div className="reading-section sudden-section" {...fadeUp(delay)}>
      <div className="section-badge section-badge--sudden">
        <span className="section-badge__icon">⚡</span>
        <span className="section-badge__text">{heading}</span>
      </div>

      <div className="reading-section__body">
        <p className="reading-section__desc">{description}</p>
      </div>
    </motion.div>
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

  useEffect(() => {
    const stored = sessionStorage.getItem('drishti_result')
    if (!stored) {
      navigate('/tool')
      return
    }
    try {
      setResult(JSON.parse(stored))
      setName(sessionStorage.getItem('drishti_name') || '')
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
                <h2 className="kundli-section__title">Birth Chart</h2>
                <p className="kundli-section__sub">
                  Your Vedic birth chart, calculated from your exact birth details.
                </p>
              </div>

              <KundliRenderer chart={chart} />

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

          <TransitSection
            heading={result.transit.heading}
            description={result.transit.description}
            delay={2.0}
          />

          <motion.div className="results-divider" {...dividerAnim(2.3)} />

          {/* ════════════════════════════════════════════
              6. YOUR TAKEAWAY
              ════════════════════════════════════════════ */}
          <motion.div className="results-takeaway-section" {...fadeUp(1.9)}>
            <div className="results-takeaway-card">
              <div className="results-takeaway-card__label">Your Takeaway</div>
              <p className="results-takeaway-card__text">
                These are the areas where you should pay extra attention.
                Stay aware. Don't ignore warning signs. Small mindful choices today
                can prevent bigger problems tomorrow.
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
