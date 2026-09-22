import React from 'react';
import { Container } from './Container';
import { SectionLabel } from './SectionLabel';
import { MaskedReveal } from './motion/MaskedReveal';

const STEPS = [
  {
    number: '01',
    title: 'Tell us about yourself.',
    body: 'Enter your birth date, birth time and birth place.',
  },
  {
    number: '02',
    title: 'KAVACH studies your chart.',
    body: 'Your astrological information is analyzed using the KAVACH system.',
  },
  {
    number: '03',
    title: 'Get clear guidance.',
    body: 'Instead of dozens of technical terms, you get simple insights you can actually understand.',
  },
];

export function HomeHowItWorks() {
  return (
    <section
      id="how-it-works"
      className="relative w-full border-t border-[#A62A34]/20 bg-[#160A0C] py-20 sm:py-28"
    >
      <Container size="lg">
        <div className="max-w-2xl space-y-4">
          <MaskedReveal>
            <SectionLabel label="HOW IT WORKS" tone="brass" />
          </MaskedReveal>
          <MaskedReveal delay={0.08}>
            <h2 className="text-3xl font-bold tracking-tight text-[#F7F5F0] sm:text-4xl">
              Astrology without the complicated language.
            </h2>
          </MaskedReveal>
        </div>

        <div className="mt-12 grid grid-cols-1 gap-6 sm:grid-cols-3 sm:gap-8">
          {STEPS.map((step, index) => (
            <MaskedReveal key={step.number} delay={index * 0.08}>
              <div className="h-full rounded-xl border border-[#A62A34]/20 bg-[#090909]/60 p-6">
                <span className="font-mono text-[11px] tracking-wider text-[#B39250]">
                  {step.number}
                </span>
                <h3 className="mt-4 text-lg font-semibold text-[#F7F5F0]">{step.title}</h3>
                <p className="mt-3 text-sm leading-relaxed text-[#EEE9DF]/75">{step.body}</p>
              </div>
            </MaskedReveal>
          ))}
        </div>
      </Container>
    </section>
  );
}
