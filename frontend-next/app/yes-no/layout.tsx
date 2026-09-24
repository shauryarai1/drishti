import React from 'react';

/**
 * Public route. YES / NO does not use a birth profile and is usable without an
 * account; signing in is an optional convenience for saving history.
 */
export default function YesNoLayout({ children }: { children: React.ReactNode }) {
  return children;
}
