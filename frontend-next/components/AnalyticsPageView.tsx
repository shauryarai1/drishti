'use client';

import { useEffect } from 'react';
import { trackEvent, type KavachEventName } from '../lib/analytics';

interface AnalyticsPageViewProps {
  event: KavachEventName;
}

/**
 * Emits a page-view event once on mount. Provider-free: nothing is loaded and
 * the call is a safe no-op until analytics is wired up.
 */
export function AnalyticsPageView({ event }: AnalyticsPageViewProps) {
  useEffect(() => {
    trackEvent(event);
  }, [event]);

  return null;
}
