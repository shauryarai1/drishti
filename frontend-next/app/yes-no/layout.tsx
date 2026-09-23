import React from 'react';
import { GuardedLayout } from '../../components/GuardedLayout';

/** Login only: YES / NO does not use a birth profile. */
export default function YesNoLayout({ children }: { children: React.ReactNode }) {
  return <GuardedLayout requireProfile={false}>{children}</GuardedLayout>;
}
