import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Life Summary | KAVACH',
  description: 'A structured life summary covering personality, relationships, professional nature, inner patterns and how you handle difficulties.',
  openGraph: {
    title: 'Life Summary | KAVACH',
    description: 'A structured life summary covering personality, relationships, professional nature, inner patterns and how you handle difficulties.',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Life Summary | KAVACH',
    description: 'A structured life summary covering personality, relationships, professional nature, inner patterns and how you handle difficulties.',
  },
};

export default function Layout({ children }: { children: React.ReactNode }) {
  return children;
}
