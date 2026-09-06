import { Link, useLocation } from 'react-router-dom'
import { useState, useEffect } from 'react'

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false)
  const location = useLocation()

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  const isLanding = location.pathname === '/'

  return (
    <nav className={`navbar ${scrolled ? 'navbar--scrolled' : ''}`}>
      <div className="navbar__inner">
        <Link to="/" className="navbar__brand">
          <span className="navbar__logo">DRISHTI</span>
        </Link>

        {isLanding && (
          <div className="navbar__links">
            <a href="#how-it-works" className="navbar__link">How It Works</a>
            <a href="#philosophy" className="navbar__link">About</a>
            <a href="#privacy" className="navbar__link">Privacy</a>
          </div>
        )}

        <div className="navbar__right">
          <Link to="/tool" className="btn btn--primary btn--sm">
            Begin Reading
            <span className="btn__arrow">→</span>
          </Link>
        </div>
      </div>
    </nav>
  )
}
