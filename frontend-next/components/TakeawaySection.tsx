import React from 'react';
import { Container } from './Container';
import { SectionLabel } from './SectionLabel';

interface TakeawayProps {
  takeaway: {
    title: string;
    thesis: string;
    guidance: string;
    anchorWords: string[];
  };
}

export function TakeawaySection({ takeaway }: TakeawayProps) {
  return (
    <section className="relative w-full bg-[#F6F5F1] text-[#171717] py-24 sm:py-32 border-t border-[#171717]/10 architectural-grid-light">
      <Container size="md" className="space-y-12">
        <div className="space-y-4">
          <SectionLabel label="SYNTHESIS" number="SEC.06" tone="dark" />
          <h3 className="text-xs uppercase font-mono tracking-[0.25em] text-[#7B1D26] font-semibold">
            {takeaway.title}
          </h3>
        </div>

        {/* Large memorable thesis statement */}
        <div className="space-y-6">
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold tracking-tight text-[#171717] leading-[1.15]">
            &ldquo;{takeaway.thesis}&rdquo;
          </h2>

          <p className="text-base sm:text-lg text-[#171717]/80 leading-relaxed font-normal max-w-2xl">
            {takeaway.guidance}
          </p>
        </div>

        {/* Anchor Words (Quiet editorial tags) */}
        <div className="pt-8 border-t border-[#171717]/15">
          <span className="block text-[10px] font-mono uppercase tracking-widest text-[#171717]/50 mb-3">
            STRATEGIC ANCHORS FOR THE CURRENT CYCLE
          </span>
          <div className="flex flex-wrap gap-2.5">
            {takeaway.anchorWords.map((word, i) => (
              <span
                key={i}
                className="px-3.5 py-1.5 rounded-sm bg-[#FFFFFF] border border-[#171717]/15 text-xs font-mono text-[#171717] font-medium shadow-sm"
              >
                {word}
              </span>
            ))}
          </div>
        </div>
      </Container>
    </section>
  );
}
