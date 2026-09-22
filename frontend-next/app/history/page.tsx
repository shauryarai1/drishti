'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { Container } from '../../components/Container';
import { Header } from '../../components/Header';
import { MaskedReveal } from '../../components/motion/MaskedReveal';
import { useAuth } from '../../lib/auth';
import { displayPersonName } from '../../lib/personName';
import {
  READING_TYPE_LABELS,
  deleteReading,
  listReadings,
  renameReading,
  type SavedReadingSummary,
} from '../../lib/history';

function createdDate(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return '';
  return date.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
}

function nativeName(item: SavedReadingSummary): string {
  const name = item.input_data?.name;
  return typeof name === 'string' && name.trim() ? name.trim() : '';
}

/** Kundli cards are identified by the person whose chart they are. */
function personLabel(item: SavedReadingSummary): string {
  return displayPersonName(item.input_data?.name);
}

export default function HistoryPage() {
  const { status, user, configured } = useAuth();
  const [items, setItems] = useState<SavedReadingSummary[] | null>(null);
  const [error, setError] = useState('');
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState('');
  const [confirmId, setConfirmId] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!user) return;
    setError('');
    setItems(null);
    try {
      setItems(await listReadings(user.id));
    } catch (exc) {
      setItems([]);
      setError(exc instanceof Error ? exc.message : 'We could not load your history. Please try again.');
    }
  }, [user]);

  useEffect(() => {
    if (status === 'signedIn' && user) void load();
    if (status === 'signedOut') setItems(null);
  }, [status, user, load]);

  const commitRename = async (item: SavedReadingSummary) => {
    if (!user) return;
    setBusyId(item.id);
    try {
      await renameReading(user.id, item.id, renameValue);
      setItems((current) =>
        (current ?? []).map((row) => (row.id === item.id ? { ...row, title: renameValue.trim() } : row)),
      );
      setRenamingId(null);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : 'We could not update that reading. Please try again.');
    } finally {
      setBusyId(null);
    }
  };

  const remove = async (item: SavedReadingSummary) => {
    if (!user) return;
    setBusyId(item.id);
    try {
      await deleteReading(user.id, item.id);
      setItems((current) => (current ?? []).filter((row) => row.id !== item.id));
      setConfirmId(null);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : 'We could not delete that reading. Please try again.');
    } finally {
      setBusyId(null);
    }
  };

  const actionClass =
    'font-mono text-[10px] uppercase tracking-[0.14em] text-[#EEE9DF]/50 transition-colors hover:text-[#D6BE85] cursor-pointer';

  return (
    <main className="min-h-screen bg-[#090909] text-[#EEE9DF] architectural-grid">
      <Header onStartReading={() => { window.location.href = '/'; }} />
      <Container size="xl" className="py-10 sm:py-16">
        <MaskedReveal>
          <div className="font-mono text-[9.5px] uppercase tracking-[0.24em] text-[#B39250]">KAVACH · Archive</div>
          <h1 className="mt-2 text-2xl font-semibold tracking-[0.06em] text-[#F7F5F0] sm:text-3xl">YOUR HISTORY</h1>
          <p className="mt-1.5 text-[13px] leading-relaxed text-[#EEE9DF]/50">
            Your saved charts and readings, kept in one place.
          </p>
        </MaskedReveal>

        {error && (
          <div role="alert" className="mt-6 rounded border border-[#A62A34]/40 bg-[#2B0C11]/60 p-3 text-[12.5px] text-[#EEE9DF]/80">
            {error}
          </div>
        )}

        {!configured && (
          <div className="mt-6 rounded-lg border border-[#A62A34]/25 bg-[#160A0C]/70 p-5 text-[13px] text-[#EEE9DF]/60">
            Accounts are not enabled on this deployment yet.
          </div>
        )}

        {configured && status === 'loading' && (
          <div className="mt-8 space-y-2" aria-hidden>
            <div className="h-16 animate-pulse rounded-lg border border-[#A62A34]/15 bg-[#160A0C]/50" />
            <div className="h-16 animate-pulse rounded-lg border border-[#A62A34]/15 bg-[#160A0C]/50" />
          </div>
        )}

        {configured && status === 'signedOut' && (
          <div className="mt-6 rounded-lg border border-[#A62A34]/25 bg-[#160A0C]/70 p-5 sm:p-6">
            <p className="text-[13px] leading-relaxed text-[#EEE9DF]/70">
              Sign in to view your saved charts and readings. Your history is private to your account.
            </p>
            <div className="mt-4 flex flex-wrap gap-2.5">
              <a
                href="/login"
                className="inline-flex h-9 items-center rounded bg-[#7B1D26] px-4 font-mono text-[10px] uppercase tracking-[0.16em] text-[#F7F5F0] transition-colors hover:bg-[#A62A34]"
              >
                Sign in
              </a>
              <a
                href="/signup"
                className="inline-flex h-9 items-center rounded border border-[#A62A34]/40 px-4 font-mono text-[10px] uppercase tracking-[0.16em] text-[#EEE9DF]/85 transition-colors hover:border-[#A62A34]/70 hover:text-[#F7F5F0]"
              >
                Create account
              </a>
            </div>
          </div>
        )}

        {configured && status === 'signedIn' && items === null && !error && (
          <div className="mt-8 space-y-2" aria-hidden>
            <div className="h-16 animate-pulse rounded-lg border border-[#A62A34]/15 bg-[#160A0C]/50" />
            <div className="h-16 animate-pulse rounded-lg border border-[#A62A34]/15 bg-[#160A0C]/50" />
          </div>
        )}

        {configured && status === 'signedIn' && items !== null && items.length === 0 && !error && (
          <div className="mt-6 rounded-lg border border-[#A62A34]/25 bg-[#160A0C]/70 p-6 text-center">
            <p className="text-[13px] text-[#EEE9DF]/60">No saved readings yet.</p>
            <p className="mt-1 text-[13px] text-[#EEE9DF]/45">
              Generate a Kundli and save it here when you want to return to it.
            </p>
            <a
              href="/kundli"
              className="mt-5 inline-flex h-9 items-center rounded bg-[#7B1D26] px-4 font-mono text-[10px] uppercase tracking-[0.16em] text-[#F7F5F0] transition-colors hover:bg-[#A62A34]"
            >
              Generate Kundli
            </a>
          </div>
        )}

        {configured && status === 'signedIn' && items !== null && items.length > 0 && (
          <div className="mt-6 space-y-2.5">
            {items.map((item) => (
              <div key={item.id} className="rounded-lg border border-[#A62A34]/25 bg-[#160A0C]/70 p-4 sm:p-5">
                {renamingId === item.id ? (
                  <div className="flex flex-wrap items-center gap-2.5">
                    <input
                      value={renameValue}
                      onChange={(event) => setRenameValue(event.target.value)}
                      aria-label="New title"
                      className="min-w-[200px] flex-1 rounded border border-[#A62A34]/25 bg-[#0E0708]/70 px-3 py-2 text-[13px] text-[#F7F5F0] outline-none focus:border-[#A62A34]/60"
                    />
                    <button
                      type="button"
                      onClick={() => void commitRename(item)}
                      disabled={busyId === item.id}
                      className={`${actionClass} text-[#D6BE85]`}
                    >
                      {busyId === item.id ? 'Saving…' : 'Save'}
                    </button>
                    <button type="button" onClick={() => setRenamingId(null)} className={actionClass}>
                      Cancel
                    </button>
                  </div>
                ) : (
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="min-w-0">
                      {item.type === 'kundli' && (
                        <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-[#D6BE85]">
                          {personLabel(item)}
                        </div>
                      )}
                      <h2 className="truncate text-[15px] font-medium text-[#F7F5F0]">{item.title}</h2>
                      <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 font-mono text-[9.5px] uppercase tracking-[0.16em] text-[#B39250]">
                        <span>{READING_TYPE_LABELS[item.type] ?? item.type}</span>
                        <span className="text-[#EEE9DF]/35">{createdDate(item.created_at)}</span>
                        {item.type !== 'kundli' && nativeName(item) && (
                          <span className="text-[#EEE9DF]/35">{nativeName(item)}</span>
                        )}
                      </div>
                    </div>

                    <div className="flex shrink-0 items-center gap-3">
                      {(item.type === 'kundli' || item.type === 'compatibility') && (
                        <a
                          href={
                            item.type === 'kundli'
                              ? `/kundli?saved=${encodeURIComponent(item.id)}`
                              : `/compatibility?saved=${encodeURIComponent(item.id)}`
                          }
                          className={`${actionClass} text-[#D6BE85]`}
                        >
                          Open
                        </a>
                      )}
                      <button
                        type="button"
                        onClick={() => {
                          setRenamingId(item.id);
                          setRenameValue(item.title);
                          setConfirmId(null);
                        }}
                        className={actionClass}
                      >
                        Rename
                      </button>
                      {confirmId === item.id ? (
                        <>
                          <button
                            type="button"
                            onClick={() => void remove(item)}
                            disabled={busyId === item.id}
                            className={`${actionClass} text-[#D6BE85]`}
                          >
                            {busyId === item.id ? 'Deleting…' : 'Confirm delete'}
                          </button>
                          <button type="button" onClick={() => setConfirmId(null)} className={actionClass}>
                            Cancel
                          </button>
                        </>
                      ) : (
                        <button type="button" onClick={() => setConfirmId(item.id)} className={actionClass}>
                          Delete
                        </button>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </Container>
    </main>
  );
}
