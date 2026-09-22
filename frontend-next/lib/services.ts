/**
 * KAVACH human services catalogue - the single source of truth for the
 * consultation and Pooja & Mantra Jaap offerings.
 *
 * Prices, names, included items and WhatsApp messages live here only, so the
 * page, the booking buttons and the reusable CTA can never drift apart.
 *
 * V1 booking is a WhatsApp handoff: no third-party payment processing, no card
 * collection and no automatic payment verification. Birth details are never
 * placed in the URL. Payment infrastructure is a separate future task.
 */

import type { KavachEventName } from './analytics';

/** The approved KAVACH WhatsApp business contact. */
export const WHATSAPP_NUMBER = '919911233375';
export const WHATSAPP_BASE_URL = `https://wa.me/${WHATSAPP_NUMBER}`;

export type ServiceId = 'consultation' | 'pooja_2100' | 'pooja_5100' | 'pooja_11000';

export interface ServiceDefinition {
  id: ServiceId;
  /** Public name. */
  name: string;
  priceInr: number;
  /** Pre-formatted so the display string never varies by locale. */
  priceLabel: string;
  summary: string;
  /** What the user receives. Deliberately limited to owner-approved wording. */
  includes: string[];
  ctaLabel: string;
  /** Exact WhatsApp message for this service (URL-encoded when used). */
  whatsappMessage: string;
  clickEvent: KavachEventName;
}

export const CONSULTATION: ServiceDefinition = {
  id: 'consultation',
  name: 'Private Consultation',
  priceInr: 1100,
  priceLabel: '\u20b91,100',
  summary:
    'A one-to-one astrology consultation for deeper understanding of your chart, current circumstances, important decisions and timing.',
  includes: [
    'One-to-one consultation',
    'Personalized chart-based guidance',
    'Questions about career, relationships, money, timing or current concerns',
    'Opportunity to discuss the situation in greater depth',
  ],
  ctaLabel: 'BOOK CONSULTATION',
  whatsappMessage: "Hi, I'd like to book a KAVACH Private Consultation for \u20b91,100.",
  clickEvent: 'consultation_booking_click',
};

export const POOJA_PACKAGES: ServiceDefinition[] = [
  {
    id: 'pooja_2100',
    name: 'Essential Pooja',
    priceInr: 2100,
    priceLabel: '\u20b92,100',
    summary:
      'A focused planetary pooja intended for a specific astrological concern or planetary influence identified through the Kundli.',
    includes: [
      'Kundli-based selection',
      'Appropriate planetary pooja',
      'Mantra jaap',
      'Basic guidance',
    ],
    ctaLabel: 'BOOK POOJA \u2014 \u20b92,100',
    whatsappMessage:
      "Hi, I'd like to enquire about the KAVACH \u20b92,100 Pooja & Mantra Jaap service.",
    clickEvent: 'pooja_2100_booking_click',
  },
  {
    id: 'pooja_5100',
    name: 'Special Pooja',
    priceInr: 5100,
    priceLabel: '\u20b95,100',
    summary:
      'A more comprehensive personalized pooja for significant planetary themes identified through the Kundli.',
    includes: [
      'Kundli-based assessment',
      'Personalized planetary pooja',
      'Mantra jaap',
      'Expanded spiritual procedure',
      'Guidance related to the selected planetary influence',
    ],
    ctaLabel: 'BOOK POOJA \u2014 \u20b95,100',
    whatsappMessage:
      "Hi, I'd like to enquire about the KAVACH \u20b95,100 Pooja & Mantra Jaap service.",
    clickEvent: 'pooja_5100_booking_click',
  },
  {
    id: 'pooja_11000',
    name: 'Premium Pooja',
    priceInr: 11000,
    priceLabel: '\u20b911,000',
    summary:
      "A comprehensive personalized spiritual service based on the individual's Kundli and relevant planetary influences.",
    includes: [
      'Detailed Kundli-based assessment',
      'Specialized planetary pooja',
      'Mantra jaap',
      'More comprehensive spiritual procedure',
      'Personalized guidance',
    ],
    ctaLabel: 'BOOK POOJA \u2014 \u20b911,000',
    whatsappMessage:
      "Hi, I'd like to enquire about the KAVACH \u20b911,000 Pooja & Mantra Jaap service.",
    clickEvent: 'pooja_11000_booking_click',
  },
];

export const SERVICES: ServiceDefinition[] = [CONSULTATION, ...POOJA_PACKAGES];

/**
 * Planetary poojas the service architecture supports.
 *
 * The planetary focus is suggested only after a Kundli assessment. Nothing here
 * decides that a user "needs" a paid service: the wording is always
 * "recommended", "suggested" or "may be suitable", and the user chooses
 * voluntarily whether to enquire.
 */
export const PLANETARY_FOCUS = [
  'Sun / Surya',
  'Moon / Chandra',
  'Mars / Mangal',
  'Mercury / Budh',
  'Jupiter / Guru',
  'Venus / Shukra',
  'Saturn / Shani',
  'Rahu',
  'Ketu',
] as const;

/** Build the approved WhatsApp deep link for an arbitrary message. */
export function whatsappUrl(message: string): string {
  return `${WHATSAPP_BASE_URL}?text=${encodeURIComponent(message)}`;
}

/** Build the booking deep link for a service. */
export function bookingUrl(service: ServiceDefinition): string {
  return whatsappUrl(service.whatsappMessage);
}

export function serviceById(id: ServiceId): ServiceDefinition {
  const found = SERVICES.find((service) => service.id === id);
  if (!found) throw new Error(`Unknown KAVACH service: ${id}`);
  return found;
}
