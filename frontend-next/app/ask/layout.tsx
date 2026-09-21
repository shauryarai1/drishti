import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Ask KAVACH | KAVACH',
  description: 'Ask KAVACH a question and receive a natural, conversational response.',
  openGraph: {
    title: 'Ask KAVACH | KAVACH',
    description: 'Ask KAVACH a question and receive a natural, conversational response.',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Ask KAVACH | KAVACH',
    description: 'Ask KAVACH a question and receive a natural, conversational response.',
  },
};

export default function Layout({ children }: { children: React.ReactNode }) {
  return children;
}
