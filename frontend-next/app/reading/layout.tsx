import React from 'react';
import { GuardedLayout } from '../../components/GuardedLayout';

export default function ReadingLayout({ children }: { children: React.ReactNode }) {
  return <GuardedLayout>{children}</GuardedLayout>;
}
