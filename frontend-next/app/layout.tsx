import React from 'react';
import type { Metadata } from 'next';
import './globals.css';
import { Providers } from './providers';

export const metadata: Metadata = {
  title: 'KAVACH – Astrological Guidance',
  description:
    'Personalized astrological guidance designed to help you understand what may deserve your attention.',
  openGraph: {
    title: 'KAVACH – Astrological Guidance',
    description:
      'Personalized astrological guidance designed to help you understand what may deserve your attention.',
    type: 'website',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark bg-[#090909]">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600&family=Manrope:wght@300;400;500;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="bg-[#090909] text-[#EEE9DF] antialiased selection:bg-[#7B1D26] selection:text-[#F7F5F0]">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
