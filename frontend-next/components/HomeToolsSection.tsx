import React from 'react';
import { Container } from './Container';
import { SectionLabel } from './SectionLabel';
import { MaskedReveal } from './motion/MaskedReveal';

interface Tool {
  href: string;
  title: string;
  description: string;
  cta: string;
}

// Primary tools first: what most visitors will want.
const PRIMARY_TOOLS: Tool[] = [
  {
    href: '/life-summary',
    title: 'Life Summary',
    description: 'Understand the important themes, strengths and areas of attention in your life.',
    cta: 'EXPLORE MY LIFE',
  },
  {
    href: '/reading',
    title: 'KAVACH Reading',
    description: 'See where you may need to pay more attention, protect yourself, or move carefully.',
    cta: 'GET MY READING',
  },
  {
    href: '/ask',
    title: 'Ask KAVACH',
    description: 'Have something on your mind? Ask a personal question and receive guidance.',
    cta: 'ASK KAVACH',
  },
  {
    href: '/yes-no',
    title: 'YES / NO',
    description: 'Ask one clear question and get a simple indication.',
    cta: 'GET AN ANSWER',
  },
  {
    href: '/daily',
    title: 'Daily Prediction',
    description: 'See what may deserve your attention today.',
    cta: 'VIEW TODAY',
  },
];

// Secondary tools stay visually quiet.
const SECONDARY_TOOLS = [
  { href: '/kundli', label: 'Kundli Generator' },
  { href: '/panchang', label: 'Panchang' },
  { href: '/your-week', label: 'Your Week' },
];

export function HomeToolsSection() {
  return (
    <section
      id="tools"
      className="relative w-full overflow-hidden border-t border-[#A62A34]/20 bg-[#090909] py-20 sm:py-28"
    >
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-[10%] top-1/3 h-[360px] w-[360px] rounded-full bg-[#541219]/15 blur-[120px]" />
      </div>

      <Container size="lg" className="relative z-10">
        <div className="mb-12 max-w-2xl space-y-4">
          <MaskedReveal>
            <SectionLabel label="CHOOSE A TOOL" tone="crimson" />
          </MaskedReveal>
          <MaskedReveal delay={0.08}>
            <h2 className="text-3xl font-bold tracking-tight text-[#F7F5F0] sm:text-4xl">
              What can KAVACH help you with?
            </h2>
          </MaskedReveal>
        </div>

        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {PRIMARY_TOOLS.map((tool, index) => (
            <MaskedReveal key={tool.href} delay={index * 0.06}>
              <a
                href={tool.href}
                className="group flex h-full flex-col justify-between rounded-xl border border-[#A62A34]/25 bg-[#160A0C]/60 p-6 transition-colors hover:border-[#A62A34]/55 hover:bg-[#160A0C]"
              >
                <div>
                  <h3 className="text-xl font-bold text-[#F7F5F0]">{tool.title}</h3>
                  <p className="mt-3 text-sm leading-relaxed text-[#EEE9DF]/75">
                    {tool.description}
                  </p>
                </div>
                <span className="mt-6 inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[#D6BE85]">
                  {tool.cta}
                  <span className="transition-transform group-hover:translate-x-1">&rarr;</span>
                </span>
              </a>
            </MaskedReveal>
          ))}
        </div>

        {/* Secondary tools: smaller, quieter, still easy to find. */}
        <div className="mt-12 flex flex-col gap-4 border-t border-[#A62A34]/15 pt-8 sm:flex-row sm:items-center sm:gap-8">
          <span className="font-mono text-[10px] uppercase tracking-[0.24em] text-[#B39250]">
            More tools
          </span>
          <div className="flex flex-wrap items-center gap-x-8 gap-y-3">
            {SECONDARY_TOOLS.map((tool) => (
              <a
                key={tool.href}
                href={tool.href}
                className="text-sm text-[#EEE9DF]/70 transition-colors hover:text-[#F7F5F0]"
              >
                {tool.label}
              </a>
            ))}
          </div>
        </div>
      </Container>
    </section>
  );
}
