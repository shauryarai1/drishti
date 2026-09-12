import React from 'react';
import { Container } from './Container';
import { SectionLabel } from './SectionLabel';
import { Button } from './Button';
import { Sparkles, Compass, UserCheck, ShieldCheck } from 'lucide-react';
import { DrishtiReading } from '../lib/types';

interface PersonalReadingCTAProps {
  onExplorePersonalReading?: () => void;
  reading: DrishtiReading;
}

export function PersonalReadingCTA({
  onExplorePersonalReading,
  reading,
}: PersonalReadingCTAProps) {
  const buildWhatsAppMessage = () => {
    const current = reading.cautionPeriods.find((period) => period.isCurrent);
    const next = reading.cautionPeriods.find((period) => !period.isCurrent);
    const shortSummary = (area: DrishtiReading['attentionArea']) =>
      `${area.title}. ${area.watchFor.primary}`;
    const timing = current
      ? `A caution period is currently active until ${current.period.split(' — ')[1] || current.period}.\n\nNext sensitive period:\n${next ? `${next.period}\n${next.focus}` : 'No further period is currently listed.'}`
      : `No major caution period is active right now.\n\nNext sensitive period:\n${next ? `${next.period}\n${next.focus}` : 'No upcoming period is currently listed.'}`;
    const message = [
      'Hello,',
      '',
      'I came from DRISHTI and would like to book a personal reading.',
      '',
      'My birth details are:',
      '',
      `Date of Birth: ${reading.birthDetails.date}`,
      `Time of Birth: ${reading.birthDetails.time}`,
      `Place of Birth: ${reading.birthDetails.place}`,
      '',
      'DRISHTI Summary:',
      '',
      `🔴 Attention: ${shortSummary(reading.attentionArea)}`,
      '',
      `🔵 Protect: ${shortSummary(reading.protectArea)}`,
      '',
      `⚠️ Danger: ${shortSummary(reading.dangerArea)}`,
      '',
      `⏳ Timing:\n${timing}`,
      '',
      'I would like to understand this reading in more detail through a personal consultation.',
      '',
      'Thank you.',
    ].join('\n');
    return `https://wa.me/919911233375?text=${encodeURIComponent(message)}`;
  };

  return (
    <section className="relative w-full bg-[#160A0C] text-[#EEE9DF] py-28 sm:py-36 border-t border-[#A62A34]/30 overflow-hidden architectural-grid">
      {/* Dynamic ambient backlight */}
      <div className="absolute top-1/2 right-1/4 w-[600px] h-[500px] rounded-full bg-gradient-to-br from-[#7B1D26]/30 via-[#541219]/20 to-transparent blur-[140px] pointer-events-none" />

      <Container size="lg" className="relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-center">

          {/* Left Column: Provocative Editorial Discourse */}
          <div className="lg:col-span-7 space-y-6">
            <SectionLabel label="THE PRIVATE DISCOURSE" number="FINAL" tone="crimson" />

            <div className="space-y-4">
              <span className="text-xs uppercase font-mono tracking-widest text-[#A62A34] font-semibold">
                WANT TO GO DEEPER?
              </span>

              <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold tracking-tight text-[#F7F5F0] leading-[1.14]">
                Your Kundli shows the pattern.{' '}
                <span className="text-[#EEE9DF]/70 font-light block sm:inline">
                  A personal reading explains the story behind it.
                </span>
              </h2>
            </div>

            <p className="text-base sm:text-lg text-[#EEE9DF]/80 leading-relaxed font-normal">
              Digital synthesis provides essential orientation. In an intimate 1-on-1 dialogue with a master Vedic scholar, we unpack the precise karmic debts, dasha transitions, and generational cycles governing your specific questions.
            </p>

            {/* Structured Deliverables (Not generic cards) */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
              <div className="flex items-start gap-3 p-3.5 rounded bg-[#090909]/60 border border-[#A62A34]/20">
                <Compass className="w-4 h-4 text-[#B39250] shrink-0 mt-0.5" />
                <div className="space-y-0.5">
                  <h4 className="text-xs font-mono text-[#F7F5F0] font-semibold">
                    10-YEAR DASHA TRAJECTORY
                  </h4>
                  <p className="text-xs text-[#EEE9DF]/65">
                    Exact timing of major career & relationship chapters.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3 p-3.5 rounded bg-[#090909]/60 border border-[#A62A34]/20">
                <ShieldCheck className="w-4 h-4 text-[#A62A34] shrink-0 mt-0.5" />
                <div className="space-y-0.5">
                  <h4 className="text-xs font-mono text-[#F7F5F0] font-semibold">
                    CONFIDENTIAL DISCOURSE
                  </h4>
                  <p className="text-xs text-[#EEE9DF]/65">
                    Unfiltered, private analysis of sensitive decisions.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Dimensional Invitation Artifact (NOT an empty background or plain gold button) */}
          <div className="lg:col-span-5 relative p-8 sm:p-10 rounded-xl bg-gradient-to-b from-[#2B0C11]/90 via-[#160A0C] to-[#090909] border border-[#A62A34]/40 shadow-[0_24px_80px_rgba(0,0,0,0.9)] space-y-6">

            <div className="flex items-center justify-between border-b border-[#A62A34]/20 pb-4">
              <div className="space-y-1">
                <span className="text-[10px] font-mono uppercase tracking-widest text-[#B39250]">
                  SESSION FORMAT
                </span>
                <div className="text-sm font-mono text-[#F7F5F0] font-semibold">
                  60-MINUTE PRIVATE CONSULTATION
                </div>
              </div>
              <span className="w-2.5 h-2.5 rotate-45 border border-[#B39250] bg-[#7B1D26]" />
            </div>

            <div className="space-y-3 text-xs sm:text-sm text-[#EEE9DF]/75">
              <div className="flex justify-between py-1.5 border-b border-[#A62A34]/15">
                <span>Direct Astrologer Dialogue</span>
                <span className="text-[#F7F5F0] font-mono">1-on-1 Zoom</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-[#A62A34]/15">
                <span>Comprehensive Audio Recording</span>
                <span className="text-[#F7F5F0] font-mono">Included</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-[#A62A34]/15">
                <span>Remedial & Gemological Audit</span>
                <span className="text-[#F7F5F0] font-mono">Tailored</span>
              </div>
            </div>

            <div className="pt-2">
              <Button
                variant="primary"
                size="lg"
                showArrow
                className="w-full"
                onClick={() => {
                  window.open(buildWhatsAppMessage(), '_blank', 'noopener,noreferrer');
                }}
              >
                Explore a Personal Reading
              </Button>
            </div>

            <div className="text-center">
              <span className="text-[10px] font-mono text-[#EEE9DF]/40 uppercase tracking-wider">
                STRICTLY LIMITED CAPACITY &bull; SENIOR VEDIC ADVISORS ONLY
              </span>
            </div>

          </div>

        </div>
      </Container>
    </section>
  );
}
