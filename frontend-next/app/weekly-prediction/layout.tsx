import type { Metadata } from 'next';
import React from 'react';

export const metadata: Metadata = {
  title: 'Weekly Prediction | KAVACH',
  description: 'See the rhythm of your next seven days and when support may be easier to find.',
};

/**
 * Public route. KAVACH astrology tools are usable without an account; signing
 * in is an optional convenience for saving readings and profiles. No login or
 * Primary Profile gate is applied here.
 */
export default function WeeklyPredictionLayout({ children }: { children: React.ReactNode }) {
  return children;
}
