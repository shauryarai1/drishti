import React from 'react';
import Link from 'next/link';
import { Container } from '../../components/Container';
import { SectionLabel } from '../../components/SectionLabel';
import { AnalyticsPageView } from '../../components/AnalyticsPageView';
import { ServiceBookingButton } from '../../components/ServiceBookingButton';
import { PoojaPackageCard } from '../../components/PoojaPackageCard';
import {
  CONSULTATION,
  PLANETARY_FOCUS,
  POOJA_PACKAGES,
  bookingUrl,
} from '../../lib/services';

export const metadata = {
  title: 'KAVACH Services | Private Consultation, Pooja & Mantra Jaap',
  description:
    'Personal consultations, mantra jaap and planetary pooja based on your individual astrological requirements.',
};

const HOW_IT_WORKS = [
  'Choose a service',
  'Contact KAVACH through WhatsApp',
  'Kundli and details are reviewed',
  'The appropriate consultation or pooja is discussed',
  'Booking is confirmed manually',
];

export default function ServicesPage() {
  return (
    <main className="min-h-screen bg-[#090909] text-[#EEE9DF]">
      <AnalyticsPageView event="services_page_view" />

      {/* Minimal brand bar: the global navigation is left untouched for now. */}
      <div className="border-b border-[#A62A34]/20">
        <Container size="lg">
          <div className="flex items-center justify-between py-5">
            <Link href="/" className="flex items-center gap-3">
              <span className="h-2.5 w-2.5 rotate-45 border border-[#B39250] bg-[#7B1D26]" />
              <span className="text-lg font-bold tracking-[0.25em] text-[#F7F5F0]">KAVACH</span>
            </Link>
            <Link
              href="/"
              className="font-mono text-[11px] uppercase tracking-[0.18em] text-[#EEE9DF]/60 transition-colors duration-200 hover:text-[#D6BE85]"
            >
              Back to KAVACH
            </Link>
          </div>
        </Container>
      </div>

      {/* Hero */}
      <section className="architectural-grid relative overflow-hidden border-b border-[#A62A34]/20 bg-[#160A0C]">
        <div className="pointer-events-none absolute right-1/4 top-1/2 h-[420px] w-[520px] rounded-full bg-gradient-to-br from-[#7B1D26]/25 via-[#541219]/15 to-transparent blur-[130px]" />
        <Container size="lg" className="relative z-10">
          <div className="py-20 sm:py-28">
            <SectionLabel label="HUMAN SERVICES" tone="brass" />
            <h1 className="mt-6 text-3xl font-semibold tracking-[0.06em] text-[#F7F5F0] sm:text-4xl md:text-5xl">
              KAVACH SERVICES
            </h1>
            <p className="mt-5 max-w-2xl text-base leading-relaxed text-[#EEE9DF]/80 sm:text-lg">
              Guidance beyond the digital reading.
            </p>
            <p className="mt-4 max-w-2xl text-sm leading-relaxed text-[#EEE9DF]/65 sm:text-base">
              Personal consultations, mantra jaap and planetary pooja based on your individual
              astrological requirements.
            </p>
          </div>
        </Container>
      </section>

      {/* Service 1: Private Consultation */}
      <section id="consultation" className="scroll-mt-20 border-b border-[#A62A34]/20 bg-[#090909]">
        <Container size="lg">
          <div className="grid grid-cols-1 gap-10 py-20 sm:py-24 lg:grid-cols-12 lg:gap-16">
            <div className="lg:col-span-7">
              <SectionLabel label="SERVICE 01" number="01" tone="crimson" />
              <h2 className="mt-6 text-2xl font-semibold tracking-tight text-[#F7F5F0] sm:text-3xl md:text-4xl">
                {CONSULTATION.name}
              </h2>
              <p className="mt-5 max-w-xl text-sm leading-relaxed text-[#EEE9DF]/75 sm:text-base">
                {CONSULTATION.summary}
              </p>

              <p className="mt-8 font-mono text-[10px] uppercase tracking-[0.24em] text-[#B39250]">
                Can include discussion around
              </p>
              <ul className="mt-4 grid grid-cols-1 gap-2.5 sm:grid-cols-2">
                {[
                  'Kundli',
                  'Career',
                  'Relationships',
                  'Finances',
                  'Important decisions',
                  'Current planetary periods',
                  'Timing',
                  'Personal concerns',
                ].map((item) => (
                  <li key={item} className="flex items-start gap-2.5 text-sm text-[#EEE9DF]/80">
                    <span className="mt-[7px] h-1.5 w-1.5 shrink-0 rotate-45 border border-[#B39250]/70 bg-[#7B1D26]/60" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="lg:col-span-5">
              <div className="rounded-xl border border-[#A62A34]/40 bg-gradient-to-b from-[#2B0C11]/90 via-[#160A0C] to-[#090909] p-7 shadow-[0_24px_80px_rgba(0,0,0,0.85)] sm:p-9">
                <span className="font-mono text-[10px] uppercase tracking-[0.24em] text-[#B39250]">
                  One-to-one session
                </span>
                <div className="mt-5 font-mono text-3xl tracking-tight text-[#D6BE85] sm:text-4xl">
                  {CONSULTATION.priceLabel}
                </div>

                <ul className="mt-7 space-y-3">
                  {CONSULTATION.includes.map((item) => (
                    <li key={item} className="flex items-start gap-2.5 text-sm text-[#EEE9DF]/80">
                      <span className="mt-[7px] h-1.5 w-1.5 shrink-0 rotate-45 border border-[#B39250]/70 bg-[#7B1D26]/60" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>

                <div className="mt-8">
                  <ServiceBookingButton
                    href={bookingUrl(CONSULTATION)}
                    event={CONSULTATION.clickEvent}
                    service={CONSULTATION.id}
                    className="w-full"
                  >
                    {CONSULTATION.ctaLabel}
                  </ServiceBookingButton>
                </div>

                <p className="mt-5 text-center text-[11px] leading-relaxed text-[#EEE9DF]/45">
                  Booking and payment are coordinated with the astrologer after the conversation
                  begins.
                </p>
              </div>
            </div>
          </div>
        </Container>
      </section>

      {/* Service 2: Pooja & Mantra Jaap */}
      <section className="border-b border-[#A62A34]/20 bg-[#160A0C]">
        <Container size="lg">
          <div className="py-20 sm:py-24">
            <SectionLabel label="SERVICE 02" number="02" tone="crimson" />
            <h2 className="mt-6 text-2xl font-semibold tracking-tight text-[#F7F5F0] sm:text-3xl md:text-4xl">
              POOJA &amp; MANTRA JAAP
            </h2>
            <p className="mt-5 max-w-2xl text-sm leading-relaxed text-[#EEE9DF]/75 sm:text-base">
              Personalized planetary pooja and mantra jaap selected according to your Kundli and the
              areas that may benefit from spiritual support.
            </p>
            <p className="mt-4 max-w-2xl text-sm leading-relaxed text-[#EEE9DF]/60">
              Based on the Kundli and astrological assessment, an appropriate planetary pooja and
              mantra jaap may be suggested. The specific planetary focus is suggested after the
              assessment — never automatically from a single placement — and you choose voluntarily
              whether to enquire further.
            </p>

            <div className="mt-12 grid grid-cols-1 gap-6 lg:grid-cols-3">
              {POOJA_PACKAGES.map((service) => (
                <PoojaPackageCard key={service.id} service={service} />
              ))}
            </div>

            <div className="mt-12 rounded-lg border border-[#A62A34]/20 bg-[#090909]/60 p-6 sm:p-7">
              <p className="font-mono text-[10px] uppercase tracking-[0.24em] text-[#B39250]">
                Planetary poojas that may be suggested
              </p>
              <p className="mt-4 text-sm leading-relaxed text-[#EEE9DF]/75">
                {PLANETARY_FOCUS.join(' \u00b7 ')}
              </p>
              <p className="mt-4 text-[12px] leading-relaxed text-[#EEE9DF]/50">
                The exact procedure is confirmed by the astrologer according to your Kundli. Further
                package details are shared during the conversation.
              </p>
            </div>
          </div>
        </Container>
      </section>

      {/* How it works */}
      <section className="border-b border-[#A62A34]/20 bg-[#090909]">
        <Container size="lg">
          <div className="py-20 sm:py-24">
            <SectionLabel label="HOW IT WORKS" tone="brass" />
            <ol className="mt-8 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-5">
              {HOW_IT_WORKS.map((step, index) => (
                <li
                  key={step}
                  className="rounded-lg border border-[#A62A34]/20 bg-[#160A0C]/60 p-5"
                >
                  <span className="font-mono text-[11px] tracking-wider text-[#B39250]">
                    {String(index + 1).padStart(2, '0')}
                  </span>
                  <p className="mt-3 text-sm leading-relaxed text-[#EEE9DF]/80">{step}</p>
                </li>
              ))}
            </ol>
          </div>
        </Container>
      </section>

      {/* Responsible note */}
      <section className="bg-[#090909]">
        <Container size="lg">
          <div className="py-14">
            <p className="max-w-3xl text-[12.5px] leading-relaxed text-[#EEE9DF]/45">
              Astrological guidance and spiritual practices are matters of personal belief and should
              not be treated as guaranteed outcomes or substitutes for professional medical, legal or
              financial advice.
            </p>
          </div>
        </Container>
      </section>
    </main>
  );
}
