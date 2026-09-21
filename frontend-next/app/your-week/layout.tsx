import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Your Week | KAVACH',
  description: 'Your personal seven-day outlook, showing where the period may support you and where patience helps.',
  openGraph: {
    title: 'Your Week | KAVACH',
    description: 'Your personal seven-day outlook, showing where the period may support you and where patience helps.',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Your Week | KAVACH',
    description: 'Your personal seven-day outlook, showing where the period may support you and where patience helps.',
  },
};

export default function Layout({ children }: { children: React.ReactNode }) {
  return children;
}
