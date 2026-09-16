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
    <section className="relative w-full bg-gradient-to-b from-[#2B0C11] via-[#541219]/90 to-[#160A0C] text-[#EEE9DF] py-24 sm:py-32 border-t border-[#A62A34]/30 architectural-grid">
      <Container size="md" className="space-y-12">
        <div className="space-y-4">
          <SectionLabel label="SYNTHESIS" number="SEC.06" tone="crimson" />
          <h3 className="text-xs uppercase font-mono tracking-[0.25em] text-[#E53E3E] font-semibold">
            {takeaway.title}
          </h3>
        </div>

        {/* Large memorable thesis statement */}
        <div className="space-y-6">
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold tracking-tight text-[#F7F5F0] leading-[1.15]">
            &ldquo;{takeaway.thesis}&rdquo;
          </h2>

          <p className="text-base sm:text-lg text-[#EEE9DF]/80 leading-relaxed font-normal max-w-2xl">
            {takeaway.guidance}
          </p>
        </div>

        {/* Anchor Words (Quiet editorial tags) */}
        <div className="pt-8 border-t border-[#A62A34]/25">
          <span className="block text-[10px] font-mono uppercase tracking-widest text-[#EEE9DF]/55 mb-3">
            STRATEGIC ANCHORS FOR THE CURRENT CYCLE
          </span>
          <div className="flex flex-wrap gap-2.5">
            {takeaway.anchorWords.map((word, i) => (
              <span
                key={i}
                className="px-3.5 py-1.5 rounded-sm bg-[#090909]/70 border border-[#A62A34]/30 text-xs font-mono text-[#F7F5F0] font-medium"
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
