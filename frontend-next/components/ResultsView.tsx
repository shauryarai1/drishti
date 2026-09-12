import React, { useState } from 'react';
import { DrishtiReading } from '../lib/types';
import { Container } from './Container';
import { SectionLabel } from './SectionLabel';
import { Button } from './Button';
import { Kundli } from './Kundli';
import { ResultChapter } from './ResultChapter';
import { CautionTimeline } from './CautionTimeline';
import { TakeawaySection } from './TakeawaySection';
import { PersonalReadingCTA } from './PersonalReadingCTA';
import { Footer } from './Footer';
import { ArrowLeft, Share2, Sparkles, Printer } from 'lucide-react';

interface ResultsViewProps {
  reading: DrishtiReading;
  onReset: () => void;
  onExplorePersonalReading?: () => void;
}

export function ResultsView({
  reading,
  onReset,
  onExplorePersonalReading,
}: ResultsViewProps) {
  const [copiedNotification, setCopiedNotification] = useState(false);

  const handleShare = () => {
    navigator.clipboard?.writeText(window.location.href);
    setCopiedNotification(true);
    setTimeout(() => setCopiedNotification(false), 2000);
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="relative min-h-screen w-full bg-[#090909] text-[#EEE9DF]">

      {/* ========================================================================= */}
      {/* STICKY RESULTS TOP BAR                                                    */}
      {/* ========================================================================= */}
      <div className="sticky top-0 z-50 w-full bg-[#160A0C]/90 backdrop-blur-xl border-b border-[#A62A34]/25 py-3.5 px-5 sm:px-10 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={onReset}
            className="flex items-center gap-2 text-xs uppercase font-mono tracking-wider text-[#EEE9DF]/70 hover:text-[#F7F5F0] transition-colors cursor-pointer"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>New Reading</span>
          </button>
          <span className="hidden sm:inline-block w-[1px] h-4 bg-[#A62A34]/30" />
          <span className="hidden sm:inline-block font-mono text-xs text-[#F7F5F0] font-semibold tracking-wide">
            DRISHTI // {reading.birthDetails.place.split(',')[0]}
          </span>
        </div>

        <div className="flex items-center gap-3">
          <Button
            size="sm"
            variant="ghost"
            icon={Printer}
            onClick={handlePrint}
            className="hidden sm:inline-flex"
          >
            Print
          </Button>

          <Button
            size="sm"
            variant="secondary"
            icon={Share2}
            onClick={handleShare}
          >
            {copiedNotification ? 'Link Copied' : 'Share'}
          </Button>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 19. RESULTS INTRODUCTION & 20. KUNDLI ARTIFACT PRESENTATION                */}
      {/* ========================================================================= */}
      <section className="relative w-full py-20 sm:py-28 overflow-hidden architectural-grid">
        {/* Ambient atmospheric red lighting */}
        <div className="absolute top-1/4 right-1/3 w-[700px] h-[550px] rounded-full bg-gradient-to-br from-[#7B1D26]/20 via-[#541219]/25 to-transparent blur-[140px] pointer-events-none" />

        <Container size="lg" className="relative z-10 space-y-16">

          {/* Results Intro Header */}
          <div className="max-w-3xl space-y-6">
            <SectionLabel label="YOUR DRISHTI" number="CHART.SYNTHESIS" tone="crimson" />

            <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold text-[#F7F5F0] tracking-tight leading-[1.12]">
              {reading.headline}
            </h1>

            <p className="text-base sm:text-lg text-[#EEE9DF]/80 leading-relaxed font-normal">
              {reading.overview}
            </p>

            <div className="pt-2 flex flex-wrap items-center gap-3 font-mono text-xs">
              <span className="px-3 py-1 rounded bg-[#160A0C] border border-[#A62A34]/30 text-[#A62A34]">
                {reading.ascendant}
              </span>
              <span className="px-3 py-1 rounded bg-[#160A0C] border border-[#B39250]/30 text-[#B39250]">
                NATAL HORIZON FIX
              </span>
            </div>
          </div>

          {/* 20. THE KUNDLI AS THE STAR ARTIFACT */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="font-mono text-xs uppercase tracking-widest text-[#B39250]">
                ARTIFACT // TRADITIONAL NORTH INDIAN KUNDLI
              </span>
              <span className="text-[11px] font-mono text-[#EEE9DF]/50 hidden sm:inline">
                INTERACTIVE INSPECTION ACTIVE
              </span>
            </div>

            <Kundli
              kundli={reading.kundli}
              birthDetails={reading.birthDetails}
              ascendant={reading.ascendant}
            />
          </div>

        </Container>
      </section>

      {/* ========================================================================= */}
      {/* 21. ATTENTION AREA (Light Editorial Canvas)                                */}
      {/* ========================================================================= */}
      <ResultChapter area={reading.attentionArea} />

      {/* ========================================================================= */}
      {/* 22. PROTECT THIS AREA (Mixed Boundary Environment)                         */}
      {/* ========================================================================= */}
      <ResultChapter area={reading.protectArea} />

      {/* ========================================================================= */}
      {/* 23. DANGER AREA (Deep Crimson High Contrast)                              */}
      {/* ========================================================================= */}
      <ResultChapter area={reading.dangerArea} />

      {/* ========================================================================= */}
      {/* 24. TIMING / CAUTION PERIOD                                               */}
      {/* ========================================================================= */}
      {reading.cautionPeriods.length > 0 && <CautionTimeline periods={reading.cautionPeriods} />}

      {/* ========================================================================= */}
      {/* 25. OVERALL TAKEAWAY (Quiet Light Editorial Canvas)                       */}
      {/* ========================================================================= */}
      <TakeawaySection takeaway={reading.takeaway} />

      {/* ========================================================================= */}
      {/* 26. PERSONAL READING CTA                                                  */}
      {/* ========================================================================= */}
      <PersonalReadingCTA reading={reading} onExplorePersonalReading={onExplorePersonalReading} />

      {/* FOOTER */}
      <Footer onStartReading={onReset} />

    </div>
  );
}
