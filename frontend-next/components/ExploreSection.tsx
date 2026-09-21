'use client';

import React from 'react';
import { Container } from './Container';
import { SectionLabel } from './SectionLabel';
import { MaskedReveal } from './motion/MaskedReveal';

const FEATURES = [
  {
    href: '/life-summary',
    title: 'Life Summary',
    description: 'Understand the major themes of your life through your birth details.',
    requires: 'Needs your birth date, time and place',
    cta: 'Explore My Life',
    primary: true,
  },
  {
    href: '/ask',
    title: 'Ask Kavach',
    description: "Ask what's on your mind and receive guidance for the moment.",
    requires: 'No birth details needed',
    cta: 'Ask Kavach',
    primary: true,
  },
  {
    href: '/panchang',
    title: 'Panchang',
    description: "Explore today's Panchang, planetary positions and timings.",
    requires: 'Date and location',
    cta: 'View Panchang',
    primary: false,
  },
];

export function ExploreSection() {
  return (
    <section id="explore" className="relative w-full overflow-hidden bg-[#090909] py-20 sm:py-28 border-t border-[#A62A34]/20 architectural-grid">
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/3 left-[10%] h-[380px] w-[380px] rounded-full bg-[#541219]/15 blur-[120px]" />
      </div>

      <Container size="lg" className="relative z-10">
        <div className="mb-12 max-w-2xl space-y-4">
          <MaskedReveal>
            <SectionLabel label="CHOOSE A TOOL" number="EXPLORE" tone="crimson" />
          </MaskedReveal>
          <MaskedReveal delay={0.08}>
            <h2 className="text-3xl font-bold tracking-tight text-[#F7F5F0] sm:text-4xl">
              What would you like to explore?
            </h2>
          </MaskedReveal>
        </div>

        <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
          {FEATURES.map((feature, index) => (
            <MaskedReveal key={feature.href} delay={index * 0.08}>
              <a
                href={feature.href}
                className={`group flex h-full flex-col justify-between rounded-xl border p-6 transition-colors ${
                  feature.primary
                    ? 'border-[#A62A34]/35 bg-gradient-to-b from-[#2B0C11]/60 to-[#160A0C]/80 hover:border-[#A62A34]/70'
                    : 'border-[#A62A34]/20 bg-[#160A0C]/60 hover:border-[#A62A34]/45'
                }`}
              >
                <div>
                  <h3 className="text-xl font-bold text-[#F7F5F0]">{feature.title}</h3>
                  <p className="mt-3 text-sm leading-relaxed text-[#EEE9DF]/75">{feature.description}</p>
                  <p className="mt-3 font-mono text-[10px] uppercase tracking-[0.14em] text-[#D6BE85]">{feature.requires}</p>
                </div>
                <span className={`mt-6 inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-wider ${
                  feature.primary ? 'text-[#E53E3E]' : 'text-[#D6BE85]'
                }`}>
                  {feature.cta}
                  <span className="transition-transform group-hover:translate-x-1">→</span>
                </span>
              </a>
            </MaskedReveal>
          ))}
        </div>
      </Container>
    </section>
  );
}
