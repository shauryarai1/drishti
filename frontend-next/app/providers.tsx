'use client';

import React from 'react';
import { AuthProvider } from '../lib/auth';

/** Client-side application providers. Kept tiny so layout stays a server component. */
export function Providers({ children }: { children: React.ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>;
}
