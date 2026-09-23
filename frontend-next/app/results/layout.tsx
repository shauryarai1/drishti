import React from 'react';
import { GuardedLayout } from '../../components/GuardedLayout';

export default function ResultsLayout({ children }: { children: React.ReactNode }) {
  return <GuardedLayout>{children}</GuardedLayout>;
}
