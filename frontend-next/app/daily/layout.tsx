import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Daily Prediction | KAVACH',
  description: 'See how the day shapes mood, relationships, health and work for every Moon sign.',
  openGraph: {
    title: 'Daily Prediction | KAVACH',
    description: 'See how the day shapes mood, relationships, health and work for every Moon sign.',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Daily Prediction | KAVACH',
    description: 'See how the day shapes mood, relationships, health and work for every Moon sign.',
  },
};

export default function Layout({ children }: { children: React.ReactNode }) {
  return children;
}
