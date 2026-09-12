import React from 'react';
import { Container } from './Container';
import { SectionLabel } from './SectionLabel';
import { Button } from './Button';
import { ShieldCheck, Sparkles, Sliders } from 'lucide-react';

interface ImmersiveStorySectionProps {
  onStartReading: () => void;
}

export function ImmersiveStorySection({ onStartReading }: ImmersiveStorySectionProps) {
  return (
    <section className="relative w-full bg-[#160A0C] text-[#EEE9DF] py-28 sm:py-36 overflow-hidden architectural-grid">
      {/* Background ambient lighting */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/3 left-1/4 w-[600px] h-[500px] rounded-full bg-[#541219]/25 blur-[140px]" />
        <div className="absolute bottom-10 right-1/4 w-[500px] h-[400px] rounded-full bg-[#7B1D26]/20 blur-[120px]" />
      </div>

      <Container size="lg" className="relative z-10">
        {/* Section Heading */}
        <div className="max-w-2xl mb-14 space-y-4">
          <SectionLabel label="THE LANDSCAPE OF YOUR CHART" number="SEC.03" tone="crimson" />
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-[#F7F5F0] tracking-tight leading-[1.15]">
            From celestial complexity to{' '}
            <span className="text-[#A62A34]">disciplined direction.</span>
          </h2>
          <p className="text-base sm:text-lg text-[#EEE9DF]/75 leading-relaxed">
            The sky at your birth is an undulating terrain of planetary intersections. Rather than overwhelming you with endless astrological jargon, DRISHTI extracts the exact pressure points requiring conscious pacing.
          </p>
        </div>

        {/* Centerpiece Composition: Topographic Crimson Terrain + ONE Translucent Interface Module */}
        <div className="relative rounded-xl overflow-hidden border border-[#A62A34]/30 shadow-[0_32px_96px_rgba(0,0,0,0.9)] bg-[#090909]">

          {/* Organic Crimson Landscape Artwork */}
          <div className="relative w-full aspect-[16/9] md:aspect-[21/9] min-h-[420px] overflow-hidden">
            <img
              src="/assets/crimson_terrain.jpg"
              alt="Organic rolling topographic landscape of crimson archival paper and fine celestial trajectories"
              className="w-full h-full object-cover object-center transform scale-105 transition-transform duration-1000 hover:scale-100"
              referrerPolicy="no-referrer"
            />
            {/* Soft dark vignetting to blend with interface */}
            <div className="absolute inset-0 bg-gradient-to-r from-[#160A0C]/90 via-[#160A0C]/40 to-transparent" />
            <div className="absolute inset-0 bg-gradient-to-t from-[#160A0C] via-transparent to-[#090909]/40" />

            {/* Fine architectural coordinate line etched across landscape */}
            <div className="absolute top-[40%] left-0 right-0 h-[1px] bg-[#A62A34]/25" />
            <div className="absolute top-[40%] left-[30%] px-2 py-0.5 bg-[#160A0C]/80 font-mono text-[9px] text-[#B39250] -translate-y-1/2">
              EQUINOCTIAL HORIZON // 14°28&apos; SIMHA
            </div>
          </div>

          {/* ONE Sophisticated Translucent Interface Module */}
          <div className="absolute bottom-6 left-6 right-6 md:left-auto md:right-10 md:bottom-10 md:w-[480px] p-6 sm:p-8 rounded-lg bg-[#160A0C]/85 backdrop-blur-2xl border border-[#A62A34]/40 shadow-[0_16px_48px_rgba(0,0,0,0.85)] space-y-5">
            <div className="flex items-center justify-between border-b border-[#A62A34]/20 pb-3">
              <div className="flex items-center gap-2">
                <Sliders className="w-4 h-4 text-[#B39250]" />
                <span className="text-xs uppercase font-mono tracking-widest text-[#EEE9DF]">
                  SYNTHESIS MODULE
                </span>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#7B1D26]/40 text-[#EEE9DF] border border-[#A62A34]/30">
                ACTIVE FOCUS
              </span>
            </div>

            <div className="space-y-3">
              <h4 className="text-lg font-bold text-[#F7F5F0] tracking-tight">
                Filtered for Immediate Relevance
              </h4>
              <p className="text-xs sm:text-sm text-[#EEE9DF]/75 leading-relaxed">
                Traditional astrology gives you eighty pages of conflicting interpretations. We translate those planetary forces into three crisp questions:
              </p>
            </div>

            {/* 3 mini distilled rows */}
            <div className="space-y-2.5 pt-1 text-xs">
              <div className="flex items-center justify-between p-2.5 rounded bg-[#2B0C11]/50 border border-[#A62A34]/20">
                <span className="font-mono text-[#A62A34] font-semibold">ATTENTION</span>
                <span className="text-[#EEE9DF]/80">Where does urgency create friction?</span>
              </div>
              <div className="flex items-center justify-between p-2.5 rounded bg-[#2B0C11]/50 border border-[#A62A34]/20">
                <span className="font-mono text-[#B39250] font-semibold">PROTECT</span>
                <span className="text-[#EEE9DF]/80">Where are energy reserves bleeding?</span>
              </div>
              <div className="flex items-center justify-between p-2.5 rounded bg-[#541219]/50 border border-[#A62A34]/30">
                <span className="font-mono text-[#E53E3E] font-semibold">DANGER</span>
                <span className="text-[#EEE9DF]/80">What premature contracts to avoid?</span>
              </div>
            </div>

            <div className="pt-2 flex items-center justify-between">
              <span className="text-[11px] font-mono text-[#EEE9DF]/50">ZERO SUPERFICIAL FLUFF</span>
              <Button size="sm" variant="primary" showArrow onClick={onStartReading}>
                Get your synthesis
              </Button>
            </div>
          </div>

        </div>
      </Container>
    </section>
  );
}
