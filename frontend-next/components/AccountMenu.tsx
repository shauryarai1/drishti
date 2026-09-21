'use client';

import React, { useEffect, useRef, useState } from 'react';
import { usePathname } from 'next/navigation';
import { ChevronDown, History, LogOut, User as UserIcon } from 'lucide-react';
import { useAuth } from '../lib/auth';
import { loginHref } from '../lib/authPaths';

/** Compact navbar account control. The full email is never shown in the navbar. */
export function AccountMenu() {
  const { status, user, signOut } = useAuth();
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!open) return;
    const onPointerDown = (event: MouseEvent | TouchEvent) => {
      if (!containerRef.current?.contains(event.target as Node)) setOpen(false);
    };
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false);
    };
    document.addEventListener('mousedown', onPointerDown);
    document.addEventListener('touchstart', onPointerDown);
    document.addEventListener('keydown', onKeyDown);
    return () => {
      document.removeEventListener('mousedown', onPointerDown);
      document.removeEventListener('touchstart', onPointerDown);
      document.removeEventListener('keydown', onKeyDown);
    };
  }, [open]);

  useEffect(() => setOpen(false), [pathname]);

  if (status === 'loading') {
    return <span aria-hidden className="block h-8 w-[86px] rounded border border-[#A62A34]/15 bg-[#160A0C]/40" />;
  }

  if (status === 'signedOut' || !user) {
    return (
      <a
        href={loginHref(pathname)}
        aria-label="Sign in"
        className="inline-flex h-8 shrink-0 items-center gap-1.5 rounded border border-[#A62A34]/30 px-2 font-mono text-[10px] uppercase tracking-[0.16em] text-[#EEE9DF]/75 transition-colors duration-200 hover:border-[#A62A34]/60 hover:text-[#F7F5F0] sm:px-2.5"
      >
        <UserIcon className="h-3.5 w-3.5" aria-hidden />
        <span className="hidden sm:inline">Sign in</span>
      </a>
    );
  }

  const initial = (user.email ?? '?').trim().charAt(0).toUpperCase();

  const handleSignOut = async () => {
    setOpen(false);
    await signOut();
    window.location.href = '/';
  };

  return (
    <div ref={containerRef} className="relative shrink-0">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label="Account menu"
        className="inline-flex h-8 items-center gap-1.5 rounded border border-[#A62A34]/30 pl-1 pr-1.5 transition-colors duration-200 hover:border-[#A62A34]/60 cursor-pointer"
      >
        <span
          aria-hidden
          className="flex h-6 w-6 items-center justify-center rounded-[3px] border border-[#B39250]/40 bg-[#2B0C11] font-mono text-[10px] text-[#D6BE85]"
        >
          {initial}
        </span>
        <ChevronDown
          aria-hidden
          className={`h-3 w-3 text-[#EEE9DF]/50 transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
        />
      </button>

      {open && (
        <div
          role="menu"
          className="absolute right-0 top-full z-50 mt-2 w-48 overflow-hidden rounded-md border border-[#A62A34]/30 bg-[#160A0C]/97 shadow-[0_18px_48px_rgba(0,0,0,0.75)] backdrop-blur-md"
        >
          <div className="truncate border-b border-[#A62A34]/20 px-3 py-2 font-mono text-[9.5px] uppercase tracking-[0.14em] text-[#B39250]">
            {user.email}
          </div>
          <a
            role="menuitem"
            href="/account"
            className="flex items-center gap-2 px-3 py-2.5 text-[12px] text-[#EEE9DF]/80 transition-colors hover:bg-[#2B0C11]/70 hover:text-[#F7F5F0]"
          >
            <UserIcon className="h-3.5 w-3.5" aria-hidden /> Account
          </a>
          <a
            role="menuitem"
            href="/history"
            className="flex items-center gap-2 px-3 py-2.5 text-[12px] text-[#EEE9DF]/80 transition-colors hover:bg-[#2B0C11]/70 hover:text-[#F7F5F0]"
          >
            <History className="h-3.5 w-3.5" aria-hidden /> History
          </a>
          <button
            role="menuitem"
            type="button"
            onClick={handleSignOut}
            className="flex w-full items-center gap-2 border-t border-[#A62A34]/20 px-3 py-2.5 text-left text-[12px] text-[#EEE9DF]/80 transition-colors hover:bg-[#2B0C11]/70 hover:text-[#F7F5F0] cursor-pointer"
          >
            <LogOut className="h-3.5 w-3.5" aria-hidden /> Log out
          </button>
        </div>
      )}
    </div>
  );
}
