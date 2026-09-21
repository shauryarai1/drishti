import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Kundli Generator | KAVACH',
  description: 'Generate your sidereal birth chart and explore planetary positions, Nakshatras, birth Panchang, Dashas and current transits.',
  openGraph: {
    title: 'Kundli Generator | KAVACH',
    description: 'Generate your sidereal birth chart and explore planetary positions, Nakshatras, birth Panchang, Dashas and current transits.',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Kundli Generator | KAVACH',
    description: 'Generate your sidereal birth chart and explore planetary positions, Nakshatras, birth Panchang, Dashas and current transits.',
  },
};

export default function Layout({ children }: { children: React.ReactNode }) {
  return children;
}
