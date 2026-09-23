'use client';

import React from 'react';
import { RequireProfile } from './RequireProfile';

/**
 * Route-level wrapper so a whole route can be gated with a layout file, without
 * touching the page itself. Two modes:
 *   requireProfile (default) - login + Primary Profile
 *   requireProfile={false}   - login only (the feature does not use a profile)
 */
export function GuardedLayout({
  children,
  requireProfile = true,
}: {
  children: React.ReactNode;
  requireProfile?: boolean;
}) {
  return <RequireProfile requireProfile={requireProfile}>{children}</RequireProfile>;
}
