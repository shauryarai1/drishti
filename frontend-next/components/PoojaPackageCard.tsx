import React from 'react';
import { ServiceBookingButton } from './ServiceBookingButton';
import { bookingUrl, type ServiceDefinition } from '../lib/services';

interface PoojaPackageCardProps {
  service: ServiceDefinition;
}

/**
 * One Pooja & Mantra Jaap option. All packages share the same restrained
 * styling: no ranking badges, no discounts, no scarcity and no visual pressure
 * toward the most expensive option.
 */
export function PoojaPackageCard({ service }: PoojaPackageCardProps) {
  return (
    <article className="flex h-full flex-col rounded-lg border border-[#A62A34]/25 bg-[#160A0C]/70 p-6 sm:p-7 transition-colors duration-200 hover:border-[#B39250]/35">
      <span className="font-mono text-[10px] uppercase tracking-[0.24em] text-[#B39250]">
        Pooja &amp; Mantra Jaap
      </span>

      <h3 className="mt-3 text-xl font-semibold tracking-tight text-[#F7F5F0] sm:text-2xl">
        {service.name}
      </h3>

      <div className="mt-4 text-2xl font-mono tracking-tight text-[#D6BE85] sm:text-3xl">
        {service.priceLabel}
      </div>

      <p className="mt-4 text-sm leading-relaxed text-[#EEE9DF]/75">{service.summary}</p>

      <ul className="mt-5 space-y-2.5">
        {service.includes.map((item) => (
          <li key={item} className="flex items-start gap-2.5 text-sm text-[#EEE9DF]/80">
            <span className="mt-[7px] h-1.5 w-1.5 shrink-0 rotate-45 border border-[#B39250]/70 bg-[#7B1D26]/60" />
            <span>{item}</span>
          </li>
        ))}
      </ul>

      <div className="mt-auto pt-7">
        <ServiceBookingButton
          href={bookingUrl(service)}
          event={service.clickEvent}
          service={service.id}
          variant="brass"
          className="w-full"
        >
          {service.ctaLabel}
        </ServiceBookingButton>
      </div>
    </article>
  );
}
