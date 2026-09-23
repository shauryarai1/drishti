import React from 'react';
import { GuardedLayout } from '../../components/GuardedLayout';

/** Login only: Ask KAVACH does not use a birth profile. */
export default function AskLayout({ children }: { children: React.ReactNode }) {
  return <GuardedLayout requireProfile={false}>{children}</GuardedLayout>;
}
