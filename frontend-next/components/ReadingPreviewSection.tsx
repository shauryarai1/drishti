import React, { useState } from 'react';
import { Container } from './Container';
import { SectionLabel } from './SectionLabel';
import { Button } from './Button';
import { Eye, Shield, AlertTriangle, ArrowRight } from 'lucide-react';

interface ReadingPreviewSectionProps {
  onStartReading: () => void;
}

export function ReadingPreviewSection({ onStartReading }: ReadingPreviewSectionProps) {
  const [activeArea, setActiveArea] = useState<'attention' | 'protect' | 'danger'>('attention');

  const areas = [
    {
      id: 'attention' as const,
      number: '01',
      title: 'ATTENTION',
      subtitle: 'What deserves awareness',
      badge: 'AWARENESS',
      accentColor: '#A62A34',
      bgGlow: 'from-[#7B1D26]/20',
      description:
        'Areas of life where your natural instinct accelerates beyond what the situation requires. Here, heightened awareness prevents self-inflicted interpersonal or tactical friction.',
      exampleQuote: 'Intensity can make you move faster than the situation requires.',
      takeaway: 'Identify where slowing down generates disproportionate leverage.',
      icon: Eye,
    },
    {
      id: 'protect' as const,
      number: '02',
      title: 'PROTECT',
      subtitle: 'Where boundaries matter',
      badge: 'CONTAINMENT',
      accentColor: '#B39250',
      bgGlow: 'from-[#B39250]/15',
      description:
        'Where energy and creative capital subtly leak. When your competence is high, others instinctively transfer their operational weight onto your shoulders.',
      exampleQuote: 'Generosity without containment becomes silent resentment.',
      takeaway: 'Erect structural gates before exhaustion forces an involuntary halt.',
      icon: Shield,
    },
    {
      id: 'danger' as const,
      number: '03',
      title: 'DANGER',
      subtitle: 'What should not be ignored',
      badge: 'CRITICAL BUFFER',
      accentColor: '#E53E3E',
      bgGlow: 'from-[#541219]/40',
      description:
        'Specific windows where rash commitments, speculative investments, or irrevocable life pivots carry high downside. This is not fatalism; it is operational caution.',
      exampleQuote: 'Velocity is fatal when applied to incomplete contractual ground.',
      takeaway: 'Establish mandatory cooling-off buffers before irreversible commitments.',
      icon: AlertTriangle,
    },
  ];

  const current = areas.find((a) => a.id === activeArea) || areas[0];

  return (
    <section
      id="preview"
      className="relative w-full bg-[#090909] text-[#EEE9DF] py-28 sm:py-36 border-t border-[#A62A34]/20 overflow-hidden"
    >
      <Container size="lg">
        {/* Section Header */}
        <div className="max-w-3xl mb-16 space-y-4">
          <SectionLabel label="THE TRIAD OF GUIDANCE" number="SEC.04" tone="crimson" />
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-[#F7F5F0] tracking-tight leading-[1.15]">
            The Three Focus Dimensions
          </h2>
          <p className="text-base sm:text-lg text-[#EEE9DF]/75 leading-relaxed">
            Every DRISHTI reading structures your chart’s astrological tensions into three actionable categories.
          </p>
        </div>

        {/* Editorial Narrative Grid (Asymmetric visual narrative, not 3 side-by-side cards) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-16 items-center">
          {/* Left Column: Interactive Navigational Spine */}
          <div className="lg:col-span-5 space-y-3">
            {areas.map((area) => {
              const isSelected = area.id === activeArea;
              const Icon = area.icon;
              return (
                <div
                  key={area.id}
                  onClick={() => setActiveArea(area.id)}
                  className={`group relative p-6 rounded-lg transition-all duration-300 cursor-pointer border select-none ${
                    isSelected
                      ? 'bg-[#160A0C] border-[#A62A34]/50 shadow-[0_12px_40px_rgba(0,0,0,0.8)]'
                      : 'bg-[#160A0C]/30 border-[#A62A34]/15 hover:bg-[#160A0C]/60 hover:border-[#A62A34]/30'
                  }`}
                >
                  {/* Left accent bar on active */}
                  {isSelected && (
                    <div
                      className="absolute left-0 top-3 bottom-3 w-1 rounded-r"
                      style={{ backgroundColor: area.accentColor }}
                    />
                  )}

                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2.5">
                      <span className="font-mono text-xs text-[#EEE9DF]/50">{area.number}</span>
                      <h3
                        className={`text-xl font-bold tracking-wide transition-colors ${
                          isSelected ? 'text-[#F7F5F0]' : 'text-[#EEE9DF]/70'
                        }`}
                      >
                        {area.title}
                      </h3>
                    </div>
                    <span
                      className="text-[10px] font-mono px-2 py-0.5 rounded uppercase tracking-wider"
                      style={{
                        backgroundColor: `${area.accentColor}18`,
                        color: area.accentColor,
                        border: `1px solid ${area.accentColor}40`,
                      }}
                    >
                      {area.badge}
                    </span>
                  </div>

                  <p className="text-xs sm:text-sm text-[#EEE9DF]/70 pl-6">{area.subtitle}</p>
                </div>
              );
            })}

            <div className="pt-4 pl-2">
              <Button size="md" variant="primary" showArrow onClick={onStartReading}>
                Unlock your three areas
              </Button>
            </div>
          </div>

          {/* Right Column: Deep Architectural Focus Stage */}
          <div className="lg:col-span-7 relative p-8 sm:p-12 rounded-xl bg-gradient-to-br from-[#160A0C] via-[#2B0C11]/50 to-[#090909] border border-[#A62A34]/40 shadow-[0_24px_80px_rgba(0,0,0,0.9)] overflow-hidden">
            {/* Dynamic ambient color glow */}
            <div
              className={`absolute -top-12 -right-12 w-80 h-80 rounded-full bg-gradient-to-br ${current.bgGlow} to-transparent blur-[80px] pointer-events-none`}
            />

            {/* Architectural corner registration */}
            <div className="absolute top-4 left-4 font-mono text-[9px] text-[#A62A34]/50 tracking-widest">
              DIMENSION.{current.number} // ACTIVE REFLECTION
            </div>

            <div className="relative z-10 space-y-6 pt-4">
              <div className="flex items-center gap-3">
                <span className="p-2.5 rounded bg-[#090909] border border-[#A62A34]/30 text-[#F7F5F0]">
                  <current.icon className="w-5 h-5" style={{ color: current.accentColor }} />
                </span>
                <div>
                  <span className="text-[11px] font-mono uppercase tracking-widest text-[#EEE9DF]/60">
                    FOCUS SECTOR
                  </span>
                  <h4 className="text-2xl font-bold text-[#F7F5F0] tracking-tight">
                    {current.title} AREA
                  </h4>
                </div>
              </div>

              {/* Large quote treatment */}
              <div className="p-5 rounded-sm bg-[#090909]/80 border-l-2 border-[#A62A34] text-[#F7F5F0] font-serif italic text-base sm:text-lg leading-relaxed">
                &ldquo;{current.exampleQuote}&rdquo;
              </div>

              <p className="text-sm sm:text-base text-[#EEE9DF]/80 leading-relaxed">
                {current.description}
              </p>

              <div className="pt-4 border-t border-[#A62A34]/20 space-y-2">
                <span className="text-[10px] font-mono uppercase tracking-widest text-[#B39250]">
                  CORE TAKEAWAY
                </span>
                <p className="text-sm font-medium text-[#F7F5F0]">{current.takeaway}</p>
              </div>
            </div>
          </div>
        </div>
      </Container>
    </section>
  );
}
