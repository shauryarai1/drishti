import React from 'react';
import { Container } from './Container';

interface FooterProps {
  onStartReading?: () => void;
  onNavigateSection?: (sectionId: string) => void;
}

export function Footer({ onStartReading, onNavigateSection }: FooterProps) {
  const handleNav = (id: string) => {
    if (onNavigateSection) {
      onNavigateSection(id);
    } else {
      const el = document.getElementById(id);
      if (el) el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <footer className="w-full bg-[#090909] border-t border-[#A62A34]/20 pt-16 pb-12 text-[#EEE9DF]">
      <Container size="lg">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-12 mb-16">
          {/* Brand column */}
          <div className="md:col-span-5 space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-2.5 h-2.5 rotate-45 border border-[#B39250] bg-[#7B1D26]" />
              <span className="text-xl font-bold tracking-[0.25em] text-[#F7F5F0]">
                DRISHTI
              </span>
            </div>
            <p className="text-sm text-[#EEE9DF]/70 max-w-sm leading-relaxed">
              Personalized Indian astrology guidance designed around clarity, boundary awareness,
              and timing. Built for modern discernment.
            </p>
            <div className="pt-2">
              <span className="inline-block text-[11px] font-mono tracking-wider text-[#B39250] border border-[#B39250]/30 px-2.5 py-1 rounded-[2px] bg-[#B39250]/5">
                Vedic Astrological Intelligence
              </span>
            </div>
          </div>

          {/* Navigation */}
          <div className="md:col-span-3 space-y-3">
            <h4 className="text-xs uppercase tracking-[0.2em] font-semibold text-[#A62A34]">
              Navigation
            </h4>
            <ul className="space-y-2 text-sm text-[#EEE9DF]/70">
              <li>
                <button
                  onClick={() => handleNav('hero')}
                  className="hover:text-[#F7F5F0] transition-colors cursor-pointer"
                >
                  Homepage
                </button>
              </li>
              <li>
                <button
                  onClick={() => handleNav('how-it-works')}
                  className="hover:text-[#F7F5F0] transition-colors cursor-pointer"
                >
                  How It Works
                </button>
              </li>
              <li>
                <button
                  onClick={() => handleNav('preview')}
                  className="hover:text-[#F7F5F0] transition-colors cursor-pointer"
                >
                  The Three Focus Areas
                </button>
              </li>
              <li>
                <button
                  onClick={onStartReading}
                  className="hover:text-[#A62A34] transition-colors font-medium cursor-pointer"
                >
                  Begin Your Reading →
                </button>
              </li>
            </ul>
          </div>

          {/* Ethical & Methodology note */}
          <div className="md:col-span-4 space-y-3">
            <h4 className="text-xs uppercase tracking-[0.2em] font-semibold text-[#A62A34]">
              Privacy & Dignity
            </h4>
            <p className="text-xs text-[#EEE9DF]/60 leading-relaxed">
              Birth details are processed strictly for calculating planetary coordinates and are never sold or shared. Readings focus on constructive personal awareness rather than fatalistic prediction.
            </p>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="pt-8 border-t border-[#A62A34]/15 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-mono text-[#EEE9DF]/40">
          <div>© {new Date().getFullYear()} DRISHTI. All rights reserved.</div>
          <div className="flex items-center gap-6">
            <span>Non-Fatalistic Guidance</span>
            <span>•</span>
            <span>Confidential Calculation</span>
          </div>
        </div>
      </Container>
    </footer>
  );
}
