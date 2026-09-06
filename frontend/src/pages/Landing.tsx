import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import Navbar from '../components/Navbar'

const steps = [
  {
    number: '01',
    title: 'Enter',
    text: 'Share a few details to begin.',
  },
  {
    number: '02',
    title: 'Understand',
    text: 'DRISHTI analyzes your profile to identify areas that may deserve greater attention.',
  },
  {
    number: '03',
    title: 'Act',
    text: 'Receive clear guidance on what to watch and what may be affected if it is neglected.',
  },
]

export default function Landing() {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    requestAnimationFrame(() => setVisible(true))
  }, [])

  return (
    <div className="landing">
      <Navbar />

      {/* Hero */}
      <section className={`hero ${visible ? 'hero--visible' : ''}`}>
        <div className="hero__container">
          <div className="hero__badge">दृष्टि</div>
          <h1 className="hero__title">DRISHTI</h1>
          <p className="hero__headline">Know what deserves your attention.</p>
          <p className="hero__sub">
            Enter a few details and receive a personalized view of the areas of
            life that may require greater care.
          </p>
          <div className="hero__actions">
            <Link to="/tool" className="btn btn--primary btn--lg">
              Begin Your Reading
              <span className="btn__arrow">→</span>
            </Link>
            <a href="#how-it-works" className="btn btn--ghost btn--lg">
              How it works
            </a>
          </div>
        </div>
        <div className="hero__ornament" aria-hidden="true">
          <svg viewBox="0 0 200 200" className="hero__mandala">
            <circle cx="100" cy="100" r="90" fill="none" stroke="currentColor" strokeWidth="0.5" opacity="0.15" />
            <circle cx="100" cy="100" r="70" fill="none" stroke="currentColor" strokeWidth="0.5" opacity="0.12" />
            <circle cx="100" cy="100" r="50" fill="none" stroke="currentColor" strokeWidth="0.5" opacity="0.1" />
            <circle cx="100" cy="100" r="30" fill="none" stroke="currentColor" strokeWidth="0.5" opacity="0.08" />
            {[...Array(12)].map((_, i) => {
              const angle = (i * 30 * Math.PI) / 180
              return (
                <line
                  key={i}
                  x1={100 + 30 * Math.cos(angle)}
                  y1={100 + 30 * Math.sin(angle)}
                  x2={100 + 90 * Math.cos(angle)}
                  y2={100 + 90 * Math.sin(angle)}
                  stroke="currentColor"
                  strokeWidth="0.5"
                  opacity="0.08"
                />
              )
            })}
          </svg>
        </div>
      </section>

      {/* How It Works */}
      <section className="how-it-works" id="how-it-works">
        <div className="section-container">
          <div className="section-label">How It Works</div>
          <div className="steps">
            {steps.map((step, i) => (
              <div key={step.number} className="step" style={{ animationDelay: `${i * 0.15}s` }}>
                <div className="step__number">{step.number}</div>
                <h3 className="step__title">{step.title}</h3>
                <p className="step__text">{step.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Philosophy */}
      <section className="philosophy" id="philosophy">
        <div className="section-container">
          <div className="section-label">Philosophy</div>
          <h2 className="philosophy__headline">
            Not everything needs your attention.
            <br />
            Some things need it more.
          </h2>
          <p className="philosophy__text">
            DRISHTI helps you identify the specific areas of your life that may
            benefit from greater awareness and care. Rather than overwhelming you
            with information, it focuses on what matters most — providing clear,
            practical guidance on where your attention can make the greatest
            difference.
          </p>
        </div>
      </section>

      {/* Privacy */}
      <section className="privacy-section" id="privacy">
        <div className="section-container">
          <div className="section-label">Privacy</div>
          <div className="privacy-card">
            <h3 className="privacy-card__title">Your details remain private.</h3>
            <p className="privacy-card__text">
              Your information is used only to generate your personalized
              reading. We do not store, share, or sell your data. Everything is
              processed securely and discarded after your reading is delivered.
            </p>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="final-cta">
        <div className="section-container">
          <h2 className="final-cta__headline">
            Some things are worth noticing early.
          </h2>
          <p className="final-cta__sub">
            Discover what deserves your attention.
          </p>
          <Link to="/tool" className="btn btn--primary btn--lg">
            Begin Your Reading
            <span className="btn__arrow">→</span>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <div className="footer__inner">
          <span className="footer__brand">DRISHTI</span>
          <span className="footer__tagline">दृष्टि — vision, perspective, insight</span>
        </div>
      </footer>
    </div>
  )
}
