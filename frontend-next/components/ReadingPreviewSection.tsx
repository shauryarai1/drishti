import React from 'react';
import { Container } from './Container';
import { SectionLabel } from './SectionLabel';
import { MaskedReveal } from './motion/MaskedReveal';

const AREAS = [
  {
    title: 'ATTENTION',
    question: 'Where should you slow down and think carefully?',
    description: 'Areas where acting too quickly may create unnecessary friction.',
  },
  {
    title: 'PROTECT',
    question: 'Where should you protect your time, energy or boundaries?',
    description: 'Areas where stronger boundaries and greater awareness may help.',
  },
  {
    title: 'DANGER',
    question: 'Where should you avoid unnecessary risks?',
    description: 'Areas where impulsive decisions or poor timing may deserve extra caution.',
  },
];

export function ReadingPreviewSection() {
  return (
    <section
      id="preview"
      className="relative w-full overflow-hidden border-t border-[#A62A34]/20 bg-[#090909] py-20 sm:py-28"
    >
      <Container size="lg">
        <div className="max-w-3xl space-y-4">
          <MaskedReveal>
            <SectionLabel label="THREE FOCUS AREAS" tone="crimson" />
          </MaskedReveal>
          <MaskedReveal delay={0.08}>
            <h2 className="text-3xl font-bold tracking-tight text-[#F7F5F0] sm:text-4xl">
              Three things worth knowing.
            </h2>
          </MaskedReveal>
          <MaskedReveal delay={0.16}>
            <p className="text-base leading-relaxed text-[#EEE9DF]/75 sm:text-lg">
              Your KAVACH Reading helps you understand where greater awareness may be useful.
            </p>
          </MaskedReveal>
        </div>

        <div className="mt-12 grid grid-cols-1 gap-6 md:grid-cols-3">
          {AREAS.map((area, index) => (
            <MaskedReveal key={area.title} delay={index * 0.08}>
              <div className="flex h-full flex-col rounded-xl border border-[#A62A34]/25 bg-[#160A0C]/60 p-6 transition-colors hover:border-[#A62A34]/45 sm:p-7">
                <span className="font-mono text-[11px] uppercase tracking-[0.24em] text-[#B39250]">
                  {area.title}
                </span>
                <h3 className="mt-4 text-lg font-semibold leading-snug text-[#F7F5F0] sm:text-xl">
                  {area.question}
                </h3>
                <p className="mt-3 text-sm leading-relaxed text-[#EEE9DF]/75">{area.description}</p>
              </div>
            </MaskedReveal>
          ))}
        </div>

        <div className="mt-12">
          <a
            href="/reading"
            className="group inline-flex items-center gap-2 rounded bg-[#7B1D26] px-8 py-4 text-base font-medium tracking-wide text-[#F7F5F0] border border-[#A62A34]/40 shadow-[0_4px_24px_rgba(123,29,38,0.35)] transition-colors hover:bg-[#A62A34]"
          >
            BEGIN YOUR KAVACH READING
            <span className="transition-transform group-hover:translate-x-1">&rarr;</span>
          </a>
        </div>
      </Container>
    </section>
  );
}
