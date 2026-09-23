import React from 'react';
import { GuardedLayout } from '../../components/GuardedLayout';

export default function CompatibilityLayout({ children }: { children: React.ReactNode }) {
  return <GuardedLayout>{children}</GuardedLayout>;
}
