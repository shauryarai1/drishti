import React from 'react';
import { Container } from './Container';
import { SectionLabel } from './SectionLabel';
import { MaskedReveal } from './motion/MaskedReveal';
import { ArrowUpRight, Compass, Shield, Target } from 'lucide-react';

interface LightEditorialSectionProps {
  onStartReading: () => void;
}

export function LightEditorialSection({ onStartReading }: LightEditorialSectionProps) {
  return (
    <section
      id="how-it-works"
      className="relative w-full overflow-hidden bg-[#090909] text-[#EEE9DF] py-24 sm:py-32 lg:py-36 architectural-grid border-t border-[#A62A34]/20 transition-colors duration-500"
    >
      {/* Ambient burgundy environment — continuous with the hero above */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/4 right-[8%] w-[620px] h-[460px] rounded-full bg-gradient-to-br from-[#7B1D26]/15 via-[#2B0C11]/20 to-transparent blur-[130px]" />
        <div className="absolute bottom-[8%] left-[6%] w-[520px] h-[400px] rounded-full bg-gradient-to-tr from-[#541219]/15 via-[#160A0C]/25 to-transparent blur-[120px]" />
      </div>

      <Container size="lg" className="relative z-10">
        {/* Editorial Eyebrow and Section Header */}
        <div className="max-w-3xl mb-16 sm:mb-24 space-y-6">
          <MaskedReveal>
            <SectionLabel label="PHILOSOPHY & PROCESS" number="SEC.02" tone="crimson" />
          </MaskedReveal>

          <MaskedReveal delay={0.08}>
            <h2 className="text-3xl sm:text-4xl md:text-5xl lg:text-[46px] font-bold text-[#F7F5F0] tracking-tight leading-[1.18]">
              Your birth chart contains thousands of details.{' '}
              <span className="text-[#A62A34] font-normal block sm:inline">
                KAVACH helps you focus on what deserves attention.
              </span>
            </h2>
          </MaskedReveal>

          <MaskedReveal delay={0.16}>
            <p className="text-base sm:text-lg text-[#EEE9DF]/75 font-normal leading-relaxed max-w-2xl">
              Astrological charts are dense coordinate networks. Without synthesis, they produce noise.
              We parse the geometry to surface three distinct dimensions of practical awareness.
            </p>
          </MaskedReveal>
        </div>

        {/* Asymmetric Editorial Grid (NOT three equal cards) */}
        <div className="border-t border-[#A62A34]/25 pt-12 lg:pt-16">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-start">

            {/* Step 01: Asymmetric Left Column */}
            <div className="lg:col-span-4 space-y-6">
              <div className="flex items-center justify-between border-b border-[#A62A34]/20 pb-4">
                <span className="font-mono text-xs text-[#E53E3E] tracking-widest uppercase font-semibold">
                  01 // INPUT
                </span>
                <span className="text-[11px] font-mono text-[#EEE9DF]/50">MOMENT OF ARRIVAL</span>
              </div>

              <div className="space-y-3">
                <h3 className="text-2xl font-bold text-[#F7F5F0] tracking-tight">
                  Share your birth details.
                </h3>
                <p className="text-sm text-[#EEE9DF]/75 leading-relaxed">
                  Date, precise time, and geographical coordinates. These anchor your ascendant and establish the exact astronomical horizon at your birth.
                </p>
              </div>

              {/* Visual Micro-Demonstration for Step 01: Coordinate Stamp */}
              <div className="p-4 bg-[#160A0C]/70 border border-[#A62A34]/30 rounded-sm space-y-2 font-mono text-xs">
                <div className="flex items-center justify-between text-[#E53E3E]">
                  <span className="flex items-center gap-1.5 font-semibold">
                    <Compass className="w-3.5 h-3.5" />
                    COORDINATE FIX
                  </span>
                  <span className="text-[10px] text-[#EEE9DF]/50">CALIBRATED</span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-[11px] text-[#EEE9DF]/70 pt-1">
                  <div>LAT: 28.6139° N</div>
                  <div>LNG: 77.2090° E</div>
                  <div>LAGNA: SIMHA</div>
                  <div>HOUSE COUNT: 12</div>
                </div>
              </div>
            </div>

            {/* Step 02: Center Wider Column */}
            <div className="lg:col-span-4 space-y-6 lg:border-l lg:border-[#A62A34]/20 lg:pl-12">
              <div className="flex items-center justify-between border-b border-[#A62A34]/20 pb-4">
                <span className="font-mono text-xs text-[#E53E3E] tracking-widest uppercase font-semibold">
                  02 // SYNTHESIS
                </span>
                <span className="text-[11px] font-mono text-[#EEE9DF]/50">NOISE REDUCTION</span>
              </div>

              <div className="space-y-3">
                <h3 className="text-2xl font-bold text-[#F7F5F0] tracking-tight">
                  Your personalized reading is prepared.
                </h3>
                <p className="text-sm text-[#EEE9DF]/75 leading-relaxed">
                  Instead of generic horoscopes or endless lists of general predictions, our engine isolates the specific pressure points influencing your current trajectory.
                </p>
              </div>

              {/* Visual Micro-Demonstration for Step 02: Synthesis Matrix */}
              <div className="p-4 bg-[#160A0C]/70 border border-[#A62A34]/30 rounded-sm space-y-2">
                <div className="flex items-center justify-between text-xs font-mono text-[#EEE9DF]/60">
                  <span>RAW DATA (1,400+ VECTORS)</span>
                  <span className="text-[#E53E3E] font-semibold">→ 3 PILLARS</span>
                </div>
                <div className="space-y-1.5 pt-1">
                  <div className="h-1.5 w-full bg-[#090909] rounded-full overflow-hidden">
                    <div className="h-full w-4/5 bg-[#A62A34]" />
                  </div>
                  <div className="flex justify-between text-[10px] font-mono text-[#EEE9DF]/50">
                    <span>PATTERN DISTILLATION</span>
                    <span>100% COMPLETE</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Step 03: Right Editorial Focus Column */}
            <div className="lg:col-span-4 space-y-6 lg:border-l lg:border-[#A62A34]/20 lg:pl-12">
              <div className="flex items-center justify-between border-b border-[#A62A34]/20 pb-4">
                <span className="font-mono text-xs text-[#E53E3E] tracking-widest uppercase font-semibold">
                  03 // DISCERNMENT
                </span>
                <span className="text-[11px] font-mono text-[#EEE9DF]/50">ACTIONABLE RESTRAINT</span>
              </div>

              <div className="space-y-3">
                <h3 className="text-2xl font-bold text-[#F7F5F0] tracking-tight">
                  See where greater awareness may be useful.
                </h3>
                <p className="text-sm text-[#EEE9DF]/75 leading-relaxed">
                  Understand your Attention Area (what needs conscious pacing), Protect Area (where boundaries leak), and Danger Area (uncalculated risks to avoid).
                </p>
              </div>

              {/* Visual Micro-Demonstration for Step 03 */}
              <div className="p-4 bg-[#160A0C]/80 border border-[#B39250]/25 text-[#F7F5F0] rounded-sm space-y-2">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="text-[#B39250]">DELIVERABLE</span>
                  <span className="text-[10px] text-[#EEE9DF]/50">DIRECT GUIDANCE</span>
                </div>
                <p className="text-xs text-[#EEE9DF]/90 font-serif italic pt-0.5">
                  &ldquo;Intensity can make you move faster than the situation requires.&rdquo;
                </p>
                <div className="pt-2 border-t border-[#EEE9DF]/10 flex items-center justify-between text-[11px]">
                  <span className="text-[#EEE9DF]/60">CONCRETE TAKEAWAY</span>
                  <button
                    onClick={onStartReading}
                    className="text-[#B39250] hover:text-[#F7F5F0] flex items-center gap-1 font-mono cursor-pointer transition-colors"
                  >
                    <span>START NOW</span>
                    <ArrowUpRight className="w-3 h-3" />
                  </button>
                </div>
              </div>
            </div>

          </div>
        </div>

        {/* Large Statement Divider */}
        <div className="mt-20 pt-12 border-t border-[#A62A34]/25 flex flex-col md:flex-row items-baseline justify-between gap-6">
          <div className="max-w-xl">
            <span className="font-mono text-xs uppercase tracking-widest text-[#E53E3E]">
              Vedic Architecture // Classical Jyotish Re-imagined
            </span>
            <p className="text-base text-[#EEE9DF]/70 mt-1">
              Astrology is not about predicting a fixed destiny. It is about understanding the climate of your life so you make wiser choices.
            </p>
          </div>
          <button
            onClick={onStartReading}
            className="group inline-flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-[#E53E3E] hover:text-[#F7F5F0] cursor-pointer transition-colors"
          >
            <span>Begin your journey</span>
            <span className="transition-transform group-hover:translate-x-1">→</span>
          </button>
        </div>
      </Container>
    </section>
  );
}
