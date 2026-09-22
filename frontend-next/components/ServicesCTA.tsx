'use client';

import React, { useEffect } from 'react';
import Link from 'next/link';
import { ArrowRight } from 'lucide-react';
import { trackEvent, type KavachEventName } from '../lib/analytics';

interface ServicesCTAProps {
  heading?: string;
  body?: string;
  label?: string;
  className?: string;
  /** Override for a placement-specific click event; defaults to services_cta_click. */
  clickEvent?: KavachEventName;
}

/**
 * Reusable "Explore services" CTA.
 *
 * Designed to sit calmly after any KAVACH result (Kundli, KAVACH Reading, Life
 * Summary, Daily Prediction, Yes/No). It is intentionally neutral: it never
 * reacts to, restates or dramatises the result it follows, so a difficult
 * reading can never be turned into commercial pressure. Placement on those
 * existing pages requires owner approval.
 */
export function ServicesCTA({
  heading = 'Want deeper guidance?',
  body = 'Explore private consultations and personalized spiritual services.',
  label = 'EXPLORE SERVICES',
  className = '',
  clickEvent = 'services_cta_click',
}: ServicesCTAProps) {
  useEffect(() => {
    trackEvent('services_cta_view');
  }, []);

  return (
    <section
      className={`w-full rounded-lg border border-[#A62A34]/25 bg-[#160A0C]/60 px-6 py-7 sm:px-8 sm:py-8 ${className}`}
    >
      <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
        <div className="space-y-1.5">
          <h2 className="text-lg font-semibold tracking-tight text-[#F7F5F0] sm:text-xl">
            {heading}
          </h2>
          <p className="text-sm leading-relaxed text-[#EEE9DF]/70">{body}</p>
        </div>

        <Link
          href="/services"
          onClick={() => trackEvent(clickEvent)}
          className="group inline-flex min-h-[48px] shrink-0 items-center justify-center gap-2.5 rounded border border-[#B39250]/40 bg-[#B39250]/15 px-6 py-3.5 text-xs font-medium uppercase tracking-[0.18em] text-[#D6BE85] transition-all duration-200 hover:bg-[#B39250]/25"
        >
          <span>{label}</span>
          <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-1" />
        </Link>
      </div>
    </section>
  );
}
