import React from 'react';
import { InsightArea } from '../lib/types';
import { Container } from './Container';
import { SectionLabel } from './SectionLabel';
import { Eye, Shield, AlertOctagon, Check, ArrowRight } from 'lucide-react';

interface ResultChapterProps {
  area: InsightArea;
}

export function ResultChapter({ area }: ResultChapterProps) {
  const isAttention = area.id === 'attention';
  const isProtect = area.id === 'protect';
  const isDanger = area.id === 'danger';

  // =========================================================================
  // CHAPTER 01: ATTENTION AREA (Warm Light Editorial Canvas #F7F5F0)
  // =========================================================================
  if (isAttention) {
    return (
      <section className="relative w-full bg-[#F7F5F0] text-[#171717] py-24 sm:py-32 border-t border-[#171717]/10 architectural-grid-light">
        <Container size="lg">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-start">

            {/* Left Column: Number, Category Label, Anchor Title */}
            <div className="lg:col-span-4 space-y-6">
              <SectionLabel label={area.label} number={area.stepNumber} tone="dark" />

              <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-[#171717] leading-tight">
                {area.title}
              </h2>

              <p className="text-sm uppercase font-mono tracking-widest text-[#7B1D26]">
                {area.subtitle}
              </p>

              {/* Editorial thematic coordinate stamp */}
              <div className="pt-6 border-t border-[#171717]/10 font-mono text-xs text-[#171717]/60 space-y-1">
                <div>DIMENSION // RELATIONSHIP & PACING</div>
                <div>STATE: ACTIVE CALIBRATION</div>
              </div>
            </div>

            {/* Right Column: Detailed Narrative + WATCH FOR takeaway */}
            <div className="lg:col-span-8 space-y-8">

              {/* Standout Quote (Not inside a card) */}
              <blockquote className="border-l-2 border-[#7B1D26] pl-6 py-2 text-xl sm:text-2xl font-serif italic text-[#171717] leading-relaxed">
                &ldquo;{area.quote}&rdquo;
              </blockquote>

              {/* Explanatory Body */}
              <div className="space-y-4 text-base sm:text-lg text-[#171717]/85 leading-relaxed font-normal">
                <p className="font-medium text-[#171717]">{area.summary}</p>
                {area.body.map((paragraph, idx) => (
                  <p key={idx}>{paragraph}</p>
                ))}
              </div>

              {/* WATCH FOR: Practical Takeaway (Minimalist editorial list) */}
              <div className="pt-8 border-t border-[#171717]/15 space-y-4">
                <div className="flex items-center gap-3">
                  <span className="w-2 h-2 rounded-full bg-[#7B1D26]" />
                  <h4 className="text-xs uppercase font-mono tracking-[0.2em] font-semibold text-[#171717]">
                    WATCH FOR
                  </h4>
                </div>

                <div className="p-5 bg-[#FFFFFF] border border-[#171717]/10 rounded-sm space-y-3">
                  <p className="text-sm font-semibold text-[#7B1D26]">
                    {area.watchFor.primary}
                  </p>
                  <ul className="space-y-2 text-sm text-[#171717]/80">
                    {area.watchFor.points.map((pt, i) => (
                      <li key={i} className="flex items-start gap-2.5">
                        <span className="font-mono text-[#7B1D26] text-xs mt-0.5">&bull;</span>
                        <span>{pt}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

            </div>
          </div>
        </Container>
      </section>
    );
  }

  // =========================================================================
  // CHAPTER 02: PROTECT THIS AREA (Mixed Environment: Boundaries & Containment)
  // =========================================================================
  if (isProtect) {
    return (
      <section className="relative w-full bg-[#160A0C] text-[#EEE9DF] py-24 sm:py-32 border-t border-[#A62A34]/20 architectural-grid">
        {/* Subtle radial glow */}
        <div className="absolute top-1/2 left-10 w-[500px] h-[500px] rounded-full bg-[#B39250]/10 blur-[120px] pointer-events-none" />

        <Container size="lg">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-start">

            {/* Left Column: Bold Boundary Title & Prominent Supporting Phrase */}
            <div className="lg:col-span-5 space-y-6">
              <SectionLabel label={area.label} number={area.stepNumber} tone="brass" />

              <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-[#F7F5F0] leading-tight">
                {area.title}
              </h2>

              {/* Supporting phrase in prominent typography */}
              <div className="inline-block p-3 rounded bg-[#B39250]/10 border border-[#B39250]/30 text-[#D6BE85] font-mono text-xs uppercase tracking-[0.25em]">
                {area.subtitle}
              </div>

              {/* Boundary layers visualization motif */}
              <div className="p-6 rounded-lg bg-[#090909]/70 border border-[#A62A34]/30 space-y-3 font-mono text-xs">
                <div className="text-[10px] text-[#B39250] uppercase tracking-widest">
                  CONTAINMENT RATIO // 72% LEAKAGE RISK
                </div>
                <div className="space-y-1.5 pt-1">
                  <div className="flex justify-between text-[#EEE9DF]/70 text-[11px]">
                    <span>Sovereign Morning Hours</span>
                    <span className="text-[#D6BE85]">Protected</span>
                  </div>
                  <div className="h-1 w-full bg-[#2B0C11] rounded">
                    <div className="h-full w-3/4 bg-[#B39250]" />
                  </div>
                </div>
                <div className="space-y-1.5 pt-2">
                  <div className="flex justify-between text-[#EEE9DF]/70 text-[11px]">
                    <span>Peripheral Delegations</span>
                    <span className="text-[#A62A34]">Uncontained</span>
                  </div>
                  <div className="h-1 w-full bg-[#2B0C11] rounded">
                    <div className="h-full w-2/5 bg-[#A62A34]" />
                  </div>
                </div>
              </div>
            </div>

            {/* Right Column: Narrative & Boundary Takeaway */}
            <div className="lg:col-span-7 space-y-8">
              <blockquote className="border-l-2 border-[#B39250] pl-6 py-2 text-xl sm:text-2xl font-serif italic text-[#F7F5F0] leading-relaxed">
                &ldquo;{area.quote}&rdquo;
              </blockquote>

              <div className="space-y-4 text-base sm:text-lg text-[#EEE9DF]/80 leading-relaxed">
                <p className="text-[#F7F5F0] font-medium">{area.summary}</p>
                {area.body.map((p, i) => (
                  <p key={i}>{p}</p>
                ))}
              </div>

              {/* WATCH FOR: Practical Takeaway */}
              <div className="pt-8 border-t border-[#A62A34]/25 space-y-4">
                <div className="flex items-center gap-3">
                  <span className="w-2 h-2 rounded-full bg-[#B39250]" />
                  <h4 className="text-xs uppercase font-mono tracking-[0.2em] font-semibold text-[#D6BE85]">
                    WATCH FOR
                  </h4>
                </div>

                <div className="p-5 bg-[#090909]/90 border border-[#B39250]/30 rounded-sm space-y-3">
                  <p className="text-sm font-semibold text-[#D6BE85]">
                    {area.watchFor.primary}
                  </p>
                  <ul className="space-y-2 text-sm text-[#EEE9DF]/75">
                    {area.watchFor.points.map((pt, i) => (
                      <li key={i} className="flex items-start gap-2.5">
                        <span className="font-mono text-[#B39250] text-xs mt-0.5">&bull;</span>
                        <span>{pt}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

            </div>
          </div>
        </Container>
      </section>
    );
  }

  // =========================================================================
  // CHAPTER 03: DANGER AREA (Deep Crimson & Highest Contrast)
  // =========================================================================
  return (
    <section className="relative w-full bg-gradient-to-b from-[#2B0C11] via-[#541219]/90 to-[#160A0C] text-[#EEE9DF] py-24 sm:py-32 border-t border-[#A62A34]/30 architectural-grid">
      {/* Deep environmental light */}
      <div className="absolute top-1/3 right-10 w-[550px] h-[550px] rounded-full bg-[#7B1D26]/30 blur-[140px] pointer-events-none" />

      <Container size="lg">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-start">

          {/* Left Column: High Serious Hierarchy (No warning emojis or horror aesthetic) */}
          <div className="lg:col-span-5 space-y-6">
            <SectionLabel label={area.label} number={area.stepNumber} tone="crimson" />

            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-[#F7F5F0] leading-tight">
              {area.title}
            </h2>

            <p className="text-sm uppercase font-mono tracking-widest text-[#E53E3E]">
              {area.subtitle}
            </p>

            <div className="p-5 rounded-lg bg-[#090909]/80 border border-[#E53E3E]/40 space-y-3">
              <span className="font-mono text-[10px] uppercase tracking-widest text-[#E53E3E] font-semibold">
                IRREVERSIBILITY PROTOCOL
              </span>
              <p className="text-xs text-[#EEE9DF]/80 leading-relaxed">
                Actions taken in this domain carry compounding structural consequences over the next 14 months. Require unanimous third-party verification before execution.
              </p>
            </div>
          </div>

          {/* Right Column: Serious Editorial Analysis */}
          <div className="lg:col-span-7 space-y-8">
            <blockquote className="border-l-2 border-[#E53E3E] pl-6 py-2 text-xl sm:text-2xl font-serif italic text-[#F7F5F0] leading-relaxed">
              &ldquo;{area.quote}&rdquo;
            </blockquote>

            <div className="space-y-4 text-base sm:text-lg text-[#EEE9DF]/85 leading-relaxed">
              <p className="text-[#F7F5F0] font-medium">{area.summary}</p>
              {area.body.map((p, i) => (
                <p key={i}>{p}</p>
              ))}
            </div>

            {/* WATCH FOR: Practical Takeaway */}
            <div className="pt-8 border-t border-[#A62A34]/30 space-y-4">
              <div className="flex items-center gap-3">
                <span className="w-2 h-2 rounded-full bg-[#E53E3E]" />
                <h4 className="text-xs uppercase font-mono tracking-[0.2em] font-semibold text-[#E53E3E]">
                  WATCH FOR
                </h4>
              </div>

              <div className="p-5 bg-[#090909]/90 border border-[#E53E3E]/30 rounded-sm space-y-3">
                <p className="text-sm font-semibold text-[#E53E3E]">
                  {area.watchFor.primary}
                </p>
                <ul className="space-y-2 text-sm text-[#EEE9DF]/80">
                  {area.watchFor.points.map((pt, i) => (
                    <li key={i} className="flex items-start gap-2.5">
                      <span className="font-mono text-[#E53E3E] text-xs mt-0.5">&bull;</span>
                      <span>{pt}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

          </div>
        </div>
      </Container>
    </section>
  );
}
