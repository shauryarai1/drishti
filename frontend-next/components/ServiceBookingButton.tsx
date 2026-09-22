'use client';

import React from 'react';
import { ArrowRight } from 'lucide-react';
import { trackEvent, type KavachEventName } from '../lib/analytics';

interface ServiceBookingButtonProps {
  href: string;
  event: KavachEventName;
  /** Optional descriptor sent with the event (never personal data). */
  service?: string;
  variant?: 'primary' | 'brass';
  className?: string;
  children: React.ReactNode;
}

/**
 * A real link to the approved WhatsApp booking destination, so booking works
 * even if JavaScript fails, plus a semantic analytics event on click.
 *
 * Touch target is comfortable on mobile and the label comes from the catalogue.
 */
export function ServiceBookingButton({
  href,
  event,
  service,
  variant = 'primary',
  className = '',
  children,
}: ServiceBookingButtonProps) {
  const styles =
    variant === 'brass'
      ? 'bg-[#B39250]/15 hover:bg-[#B39250]/25 text-[#D6BE85] border border-[#B39250]/40'
      : 'bg-[#7B1D26] hover:bg-[#A62A34] text-[#F7F5F0] border border-[#A62A34]/40 shadow-[0_4px_24px_rgba(123,29,38,0.35)]';

  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      onClick={() => trackEvent(event, service ? { service } : {})}
      className={`group inline-flex min-h-[48px] items-center justify-center gap-2.5 rounded px-6 py-3.5 text-sm font-medium tracking-wide transition-all duration-200 cursor-pointer ${styles} ${className}`}
    >
      <span>{children}</span>
      <ArrowRight className="h-4 w-4 text-current transition-transform duration-200 group-hover:translate-x-1" />
    </a>
  );
}
