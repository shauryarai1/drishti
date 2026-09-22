import React from 'react';
import { Container } from './Container';
import { SectionLabel } from './SectionLabel';
import { MaskedReveal } from './motion/MaskedReveal';

export function HomePhilosophy() {
  return (
    <section
      id="philosophy"
      className="relative w-full border-t border-[#A62A34]/20 bg-[#160A0C] py-20 sm:py-24"
    >
      <Container size="lg">
        <div className="max-w-2xl space-y-4">
          <MaskedReveal>
            <SectionLabel label="OUR APPROACH" tone="crimson" />
          </MaskedReveal>
          <MaskedReveal delay={0.08}>
            <h2 className="text-3xl font-bold tracking-tight text-[#F7F5F0] sm:text-4xl">
              Guidance, not fixed destiny.
            </h2>
          </MaskedReveal>
          <MaskedReveal delay={0.16}>
            <p className="text-base leading-relaxed text-[#EEE9DF]/75 sm:text-lg">
              KAVACH doesn&rsquo;t tell you that your future is already decided. It helps you notice
              patterns, timing and areas that may deserve more care &mdash; so you can make your own
              decisions with greater awareness.
            </p>
          </MaskedReveal>
          <MaskedReveal delay={0.24}>
            <p className="text-[12.5px] leading-relaxed text-[#EEE9DF]/50">
              Your birth details are used to prepare your astrological calculations and personalized
              guidance.
            </p>
          </MaskedReveal>
        </div>
      </Container>
    </section>
  );
}
