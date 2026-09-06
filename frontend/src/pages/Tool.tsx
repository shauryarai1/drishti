import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import Navbar from '../components/Navbar'
import LocationInput from '../components/LocationInput'
import { fetchInterpretation } from '../services/api'

interface FormData {
  name: string
  date: string
  time: string
  place: string
}

const steps = [
  {
    key: 'date',
    number: '01',
    label: 'Date of Birth',
    question: 'When did your journey begin?',
    hint: 'Enter your date of birth in DD/MM/YYYY format.',
  },
  {
    key: 'time',
    number: '02',
    label: 'Time of Birth',
    question: 'What time were you born?',
    hint: 'If you\'re unsure, an approximate time works too.',
  },
  {
    key: 'place',
    number: '03',
    label: 'Place of Birth',
    question: 'Where were you born?',
    hint: 'Enter the city and country, for example: Delhi, India.',
  },
]

export default function Tool() {
  const navigate = useNavigate()
  const [step, setStep] = useState(0)
  const [form, setForm] = useState<FormData>({ name: '', date: '', time: '', place: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [direction, setDirection] = useState(1)

  const current = steps[step]
  const isLast = step === steps.length - 1

  const updateField = (value: string) => {
    setForm((prev) => ({ ...prev, [current.key]: value }))
  }

  const canContinue = () => {
    const val = (form as any)[current.key]
    return val && val.trim().length > 0
  }

  const handleNext = () => {
    if (!canContinue()) return
    setError(null)
    if (isLast) {
      handleSubmit()
    } else {
      setDirection(1)
      setStep((s) => s + 1)
    }
  }

  const handleBack = () => {
    if (step > 0) {
      setDirection(-1)
      setStep((s) => s - 1)
    }
  }

  const handleSubmit = async () => {
    if (!form.date || !form.time || !form.place) return
    setLoading(true)
    setError(null)
    try {
      const result = await fetchInterpretation({
        date: form.date,
        time: form.time,
        place: form.place,
      })
      sessionStorage.setItem('drishti_result', JSON.stringify(result))
      sessionStorage.setItem('drishti_name', form.name || '')
      navigate('/results')
    } catch (err: any) {
      setError(err.message || 'Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && canContinue() && !loading) {
      e.preventDefault()
      handleNext()
    }
  }

  return (
    <div className="tool-page">
      <Navbar />

      <main className="tool-main">
        <div className="tool-container">
          <div className="tool-header">
            <h1 className="tool-title">Your Reading</h1>
            <p className="tool-subtitle">Tell us a little about yourself.</p>
          </div>

          {/* Progress */}
          <div className="progress-bar">
            {steps.map((s, i) => (
              <div
                key={s.key}
                className={`progress-bar__step ${
                  i < step ? 'progress-bar__step--done' : ''
                } ${i === step ? 'progress-bar__step--active' : ''}`}
              >
                <div className="progress-bar__dot" />
                {i < steps.length - 1 && <div className="progress-bar__line" />}
              </div>
            ))}
          </div>

          {/* Form Step */}
          <AnimatePresence mode="wait" custom={direction}>
            <motion.div
              key={step}
              custom={direction}
              variants={{
                enter: (dir: number) => ({
                  x: dir > 0 ? 80 : -80,
                  opacity: 0,
                }),
                center: { x: 0, opacity: 1 },
                exit: (dir: number) => ({
                  x: dir > 0 ? -80 : 80,
                  opacity: 0,
                }),
              }}
              initial="enter"
              animate="center"
              exit="exit"
              transition={{ duration: 0.35, ease: [0.25, 0.1, 0.25, 1] }}
              className="form-step"
              onKeyDown={handleKeyDown}
            >
              <div className="form-step__number">{current.number}</div>
              <div className="form-step__label">{current.label}</div>
              <h2 className="form-step__question">{current.question}</h2>
              <p className="form-step__hint">{current.hint}</p>

              <div className="form-step__input-wrap">
                {current.key === 'date' ? (
                  <input
                    type="date"
                    className="form-input form-input--date"
                    value={form.date}
                    onChange={(e) => updateField(e.target.value)}
                    max={new Date().toISOString().split('T')[0]}
                    autoFocus
                    aria-label="Date of birth"
                  />
                ) : current.key === 'time' ? (
                  <input
                    type="time"
                    className="form-input form-input--time"
                    value={form.time}
                    onChange={(e) => updateField(e.target.value)}
                    autoFocus
                    aria-label="Time of birth"
                  />
                ) : (
                  <LocationInput
                    value={form.place}
                    onChange={(val) => setForm((prev) => ({ ...prev, place: val }))}
                    placeholder="Start typing a city…"
                    autoFocus
                  />
                )}
              </div>
            </motion.div>
          </AnimatePresence>

          {/* Navigation */}
          <div className="form-nav">
            {step > 0 && (
              <button
                className="btn btn--ghost"
                onClick={handleBack}
                type="button"
              >
                ← Back
              </button>
            )}
            <div className="form-nav__spacer" />
            <button
              className="btn btn--primary"
              onClick={handleNext}
              disabled={!canContinue() || loading}
              type="button"
            >
              {loading ? (
                <span className="btn__loading">
                  <span className="spinner" />
                  Reading your profile…
                </span>
              ) : isLast ? (
                <>
                  Begin Reading
                  <span className="btn__arrow">→</span>
                </>
              ) : (
                <>
                  Continue
                  <span className="btn__arrow">→</span>
                </>
              )}
            </button>
          </div>

          {error && (
            <div className="error-banner" role="alert">
              <p className="error-banner__title">We couldn't complete your reading.</p>
              <p className="error-banner__text">{error}</p>
              <button className="btn btn--ghost btn--sm" onClick={() => setError(null)}>
                Try Again
              </button>
            </div>
          )}

          <div className="privacy-note">
            <div className="privacy-note__icon" aria-hidden="true">🔒</div>
            <div>
              <p className="privacy-note__title">Your details remain private.</p>
              <p className="privacy-note__text">
                Your information is used only to generate your personalized reading.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
