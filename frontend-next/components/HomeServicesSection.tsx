import React from 'react';
import { Container } from './Container';
import { SectionLabel } from './SectionLabel';
import { MaskedReveal } from './motion/MaskedReveal';

const SERVICES = [
  { name: 'Private Consultation', price: '\u20b91,100' },
  { name: 'Pooja & Mantra Jaap', price: 'From \u20b92,100' },
];

export function HomeServicesSection() {
  return (
    <section
      id="services"
      className="relative w-full border-t border-[#A62A34]/20 bg-[#090909] py-20 sm:py-28"
    >
      <Container size="lg">
        <div className="max-w-2xl space-y-4">
          <MaskedReveal>
            <SectionLabel label="HUMAN SERVICES" tone="brass" />
          </MaskedReveal>
          <MaskedReveal delay={0.08}>
            <h2 className="text-3xl font-bold tracking-tight text-[#F7F5F0] sm:text-4xl">
              Want deeper guidance?
            </h2>
          </MaskedReveal>
          <MaskedReveal delay={0.16}>
            <p className="text-base leading-relaxed text-[#EEE9DF]/75 sm:text-lg">
              Speak directly with an astrologer or explore personalized spiritual services based on
              your Kundli.
            </p>
          </MaskedReveal>
        </div>

        <div className="mt-12 grid grid-cols-1 gap-5 sm:grid-cols-2">
          {SERVICES.map((service) => (
            <div
              key={service.name}
              className="flex items-baseline justify-between rounded-xl border border-[#A62A34]/25 bg-[#160A0C]/60 p-6"
            >
              <span className="text-lg font-semibold text-[#F7F5F0]">{service.name}</span>
              <span className="font-mono text-lg text-[#D6BE85]">{service.price}</span>
            </div>
          ))}
        </div>

        <div className="mt-10">
          <a
            href="/services"
            className="group inline-flex items-center gap-2 rounded border border-[#B39250]/40 bg-[#B39250]/15 px-6 py-3.5 text-xs font-medium uppercase tracking-[0.18em] text-[#D6BE85] transition-colors hover:bg-[#B39250]/25"
          >
            EXPLORE SERVICES
            <span className="transition-transform group-hover:translate-x-1">&rarr;</span>
          </a>
        </div>
      </Container>
    </section>
  );
}
