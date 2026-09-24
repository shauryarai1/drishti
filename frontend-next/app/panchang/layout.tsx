import React from 'react';

/**
 * Public route. Panchang does not use a birth profile and is usable without an
 * account; signing in is an optional convenience for saving history.
 */
export default function PanchangLayout({ children }: { children: React.ReactNode }) {
  return children;
}
