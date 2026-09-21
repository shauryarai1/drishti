import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Panchang | KAVACH',
  description: 'The Vedic map of the day: Tithi, Nakshatra, Yoga, Karana, planetary timing and Muhurta.',
  openGraph: {
    title: 'Panchang | KAVACH',
    description: 'The Vedic map of the day: Tithi, Nakshatra, Yoga, Karana, planetary timing and Muhurta.',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Panchang | KAVACH',
    description: 'The Vedic map of the day: Tithi, Nakshatra, Yoga, Karana, planetary timing and Muhurta.',
  },
};

export default function Layout({ children }: { children: React.ReactNode }) {
  return children;
}
