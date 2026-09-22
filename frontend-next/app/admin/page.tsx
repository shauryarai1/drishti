'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { Container } from '../../components/Container';
import { Header } from '../../components/Header';
import { MaskedReveal } from '../../components/motion/MaskedReveal';
import { useAuth } from '../../lib/auth';
import {
  PRODUCT_FILTERS,
  PRODUCT_LABELS,
  RANGE_FILTERS,
  VISITOR_FILTERS,
  deleteAdminSubmission,
  fetchAdminStats,
  fetchAdminSubmission,
  fetchAdminSubmissions,
  type AdminStats,
  type AdminSubmissionDetail,
  type AdminSubmissionRow,
} from '../../lib/admin';

const PANEL = 'rounded-lg border border-[#A62A34]/25 bg-[#160A0C]/70';
const LABEL = 'font-mono text-[9.5px] uppercase tracking-[0.18em] text-[#B39250]';
const SELECT =
  'rounded border border-[#A62A34]/25 bg-[#0E0708]/80 px-2.5 py-1.5 font-mono text-[10px] uppercase tracking-[0.12em] text-[#EEE9DF]/80 outline-none focus:border-[#A62A34]/60';

const STAT_TILES: Array<{ key: keyof AdminStats; label: string }> = [
  { key: 'total', label: 'Total submissions' },
  // Server-side boundary is the UTC calendar day (see archive.STATS_TIMEZONE).
  { key: 'today', label: 'Today (UTC)' },
  { key: 'guests', label: 'Guests' },
  { key: 'accounts', label: 'Accounts' },
  { key: 'reading', label: 'KAVACH readings' },
  { key: 'kundli', label: 'Kundlis' },
  { key: 'ask', label: 'Ask KAVACH' },
  { key: 'daily', label: 'Daily' },
  { key: 'weekly', label: 'Weekly' },
  { key: 'life_summary', label: 'Life summary' },
  { key: 'dasha', label: 'Dasha reading' },
  { key: 'panchang', label: 'Panchang' },
];

function formatWhen(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return `${date.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })} · ${date.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}`;
}

function shortTime(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
}

function visitorLabel(row: AdminSubmissionRow): string {
  if (!row.user_id) return 'Guest';
  return row.account_email ? `Account · ${row.account_email}` : 'Account';
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <div className={LABEL}>{label}</div>
      <div className="mt-1 whitespace-pre-wrap break-words text-[13px] text-[#EEE9DF]/85">{children}</div>
    </div>
  );
}

function Json({ value }: { value: unknown }) {
  return (
    <pre className="mt-2 max-h-[360px] overflow-auto rounded border border-[#A62A34]/20 bg-[#0E0708]/70 p-3 text-[11px] leading-relaxed text-[#EEE9DF]/70">
      {JSON.stringify(value ?? null, null, 2)}
    </pre>
  );
}

function KundliResult({ result }: { result: any }) {
  const ascendant = result?.chart?.ascendant;
  const planets: any[] = Array.isArray(result?.planets) ? result.planets : [];
  return (
    <div className="space-y-4">
      {ascendant && (
        <Field label="Ascendant">
          {ascendant.rashi ?? ascendant.sign}
          {typeof ascendant.degree === 'number' ? ` · ${ascendant.degree.toFixed(2)}°` : ''}
        </Field>
      )}
      {planets.length > 0 && (
        <div className="-mx-1 overflow-x-auto px-1">
          <table className="w-full min-w-[420px] border-collapse">
            <thead>
              <tr>
                {['Planet', 'Rashi', 'House', 'Motion'].map((head) => (
                  <th key={head} className={`${LABEL} border-b border-[#A62A34]/25 pb-2 text-left`}>
                    {head}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {planets.map((planet, index) => (
                <tr key={planet.planet ?? index} className={index % 2 ? 'bg-[#0E0708]/40' : ''}>
                  <td className="border-b border-[#A62A34]/10 px-2 py-1.5 text-[12.5px] text-[#F7F5F0]">{planet.planet}</td>
                  <td className="border-b border-[#A62A34]/10 px-2 py-1.5 text-[12.5px] text-[#EEE9DF]/80">{planet.rashi}</td>
                  <td className="border-b border-[#A62A34]/10 px-2 py-1.5 text-[12.5px] text-[#EEE9DF]/80">{planet.house}</td>
                  <td className="border-b border-[#A62A34]/10 px-2 py-1.5 text-[12.5px] text-[#EEE9DF]/80">{planet.motion ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <div className={LABEL}>Full stored snapshot</div>
      <Json value={result} />
    </div>
  );
}

function AskResult({ result }: { result: any }) {
  return (
    <div className="space-y-4">
      <Field label="KAVACH response">{String(result?.answer ?? '—')}</Field>
      <Field label="Answered">{result?.answered ? 'Yes' : 'No'}</Field>
      <div className={LABEL}>Full stored snapshot</div>
      <Json value={result} />
    </div>
  );
}

function GenericResult({ result }: { result: unknown }) {
  return (
    <div>
      <div className={LABEL}>Stored result snapshot</div>
      <Json value={result} />
    </div>
  );
}

export default function AdminPage() {
  const { status, user } = useAuth();
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [rows, setRows] = useState<AdminSubmissionRow[] | null>(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [product, setProduct] = useState('all');
  const [visitor, setVisitor] = useState('all');
  const [range, setRange] = useState('all');
  const [query, setQuery] = useState('');
  const [search, setSearch] = useState('');
  const [error, setError] = useState('');
  const [detail, setDetail] = useState<AdminSubmissionDetail | null>(null);
  const [detailError, setDetailError] = useState('');
  // In-flight marker: prevents repeated VIEW clicks from firing many requests.
  const [detailLoadingId, setDetailLoadingId] = useState<string | null>(null);
  const [rawOpen, setRawOpen] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [confirmId, setConfirmId] = useState<string | null>(null);

  const pageSize = 50;

  const load = useCallback(async () => {
    if (status !== 'signedIn' || !user) return;
    setError('');
    setRows(null);
    try {
      const [nextStats, list] = await Promise.all([
        fetchAdminStats(),
        fetchAdminSubmissions({ product, visitor, range, q: search, page, pageSize }),
      ]);
      setStats(nextStats);
      setRows(list.submissions);
      setTotal(list.total);
    } catch (exc) {
      setRows([]);
      setError(exc instanceof Error ? exc.message : 'We could not load the archive. Please try again.');
    }
  }, [status, user, product, visitor, range, search, page]);

  useEffect(() => {
    if (status === 'signedIn') void load();
    if (status === 'signedOut') {
      setRows(null);
      setStats(null);
    }
  }, [status, load]);

  useEffect(() => {
    setDetail(null);
    setDetailError('');
    setRawOpen(false);
    setConfirmId(null);
  }, [product, visitor, range, search, page]);

  const open = async (row: AdminSubmissionRow) => {
    if (detailLoadingId === row.id) return; // already loading this row
    setDetailError('');
    setRawOpen(false);
    setDetailLoadingId(row.id);
    try {
      const loaded = await fetchAdminSubmission(row.id);
      setDetail(loaded);
      // The panel is rendered above the list; bring it into view so the action is obvious.
      requestAnimationFrame(() => {
        document.getElementById('admin-detail-panel')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
    } catch (exc) {
      setDetail(null);
      setDetailError(exc instanceof Error ? exc.message : 'Could not load submission details.');
    } finally {
      setDetailLoadingId(null);
    }
  };

  const remove = async (id: string) => {
    setBusyId(id);
    try {
      await deleteAdminSubmission(id);
      setConfirmId(null);
      if (detail?.id === id) setDetail(null);
      await load();
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : 'We could not delete that submission.');
    } finally {
      setBusyId(null);
    }
  };

  const pages = Math.max(1, Math.ceil(total / pageSize));
  const inputData = (detail?.input_data ?? {}) as Record<string, unknown>;

  return (
    <main className="min-h-screen bg-[#090909] text-[#EEE9DF] architectural-grid">
      <Header onStartReading={() => { window.location.href = '/'; }} />
      <Container size="xl" className="py-10 sm:py-14">
        <MaskedReveal>
          <div className={LABEL}>KAVACH Admin</div>
          <h1 className="mt-2 text-2xl font-semibold tracking-[0.06em] text-[#F7F5F0] sm:text-3xl">SUBMISSIONS</h1>
          <p className="mt-1.5 text-[13px] leading-relaxed text-[#EEE9DF]/50">
            Retained product submissions and their generated results. Accessible to registered administrators only.
          </p>
        </MaskedReveal>

        {status === 'loading' && (
          <div className={`${PANEL} mt-6 p-5`}>
            <div className={LABEL}>Checking your session</div>
            <p className="mt-1 text-[13px] text-[#EEE9DF]/55">Verifying administration access&hellip;</p>
          </div>
        )}

        {status === 'signedOut' && (
          <div className={`${PANEL} mt-6 p-5`}>
            <p className="text-[13px] text-[#EEE9DF]/70">Sign in with an administrator account to view submissions.</p>
            <a
              href="/login?next=%2Fadmin"
              className="mt-4 inline-flex h-9 items-center rounded bg-[#7B1D26] px-4 font-mono text-[10px] uppercase tracking-[0.16em] text-[#F7F5F0] transition-colors hover:bg-[#A62A34]"
            >
              Sign in
            </a>
          </div>
        )}

        {status === 'signedIn' && (
          <>
            {error && (
              <div role="alert" className="mt-6 rounded border border-[#A62A34]/40 bg-[#2B0C11]/60 p-3 text-[12.5px] text-[#EEE9DF]/80">
                {error}
              </div>
            )}

            <div className="mt-6 grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-6">
              {STAT_TILES.map((tile) => (
                <div key={String(tile.key)} className={`${PANEL} p-3`}>
                  <div className={LABEL}>{tile.label}</div>
                  <div className="mt-1 text-xl font-semibold text-[#F7F5F0]">
                    {stats ? (stats[tile.key] ?? 0) : '—'}
                  </div>
                </div>
              ))}
            </div>

            <div className={`${PANEL} mt-6 flex flex-wrap items-center gap-2.5 p-3`}>
              <select className={SELECT} value={product} onChange={(event) => { setProduct(event.target.value); setPage(1); }} aria-label="Filter by product">
                {PRODUCT_FILTERS.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
              <select className={SELECT} value={visitor} onChange={(event) => { setVisitor(event.target.value); setPage(1); }} aria-label="Filter by visitor">
                {VISITOR_FILTERS.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
              <select className={SELECT} value={range} onChange={(event) => { setRange(event.target.value); setPage(1); }} aria-label="Filter by period">
                {RANGE_FILTERS.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
              <form
                className="flex flex-1 items-center gap-2"
                onSubmit={(event) => { event.preventDefault(); setSearch(query); setPage(1); }}
              >
                <input
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Search name, question, place or id"
                  aria-label="Search submissions"
                  className="min-w-[180px] flex-1 rounded border border-[#A62A34]/25 bg-[#0E0708]/80 px-2.5 py-1.5 text-[12.5px] text-[#F7F5F0] outline-none placeholder:text-[#EEE9DF]/30 focus:border-[#A62A34]/60"
                />
                <button type="submit" className="font-mono text-[10px] uppercase tracking-[0.14em] text-[#D6BE85] hover:text-[#F7F5F0] cursor-pointer">
                  Search
                </button>
              </form>
            </div>

            <div className="mt-6">
              {/* Detail panel is rendered ABOVE the list so VIEW is immediately visible. */}
              {(detail || detailError || detailLoadingId) && (
                <div id="admin-detail-panel" className={`${PANEL} mb-4 p-5`}>
                  {detailError && (
                    <div role="alert" className="text-[13px] text-[#EEE9DF]/80">{detailError}</div>
                  )}
                  {!detail && !detailError && detailLoadingId && (
                    <div className="flex items-center justify-between gap-3">
                      <div className="text-[13px] text-[#EEE9DF]/70">Loading submission&hellip;</div>
                      <button
                        type="button"
                        onClick={() => setDetailLoadingId(null)}
                        className="font-mono text-[10px] uppercase tracking-[0.14em] text-[#EEE9DF]/50 hover:text-[#D6BE85] cursor-pointer"
                      >
                        Cancel
                      </button>
                    </div>
                  )}
                  {detail && (
                    <>
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div>
                          <div className={LABEL}>{PRODUCT_LABELS[detail.product] ?? detail.product} submission</div>
                          <h2 className="mt-1 text-lg font-semibold tracking-[0.04em] text-[#F7F5F0]">
                            {formatWhen(detail.created_at)}
                          </h2>
                        </div>
                        <button
                          type="button"
                          onClick={() => { setDetail(null); setDetailError(''); }}
                          className="font-mono text-[10px] uppercase tracking-[0.14em] text-[#EEE9DF]/50 hover:text-[#D6BE85] cursor-pointer"
                        >
                          Close
                        </button>
                      </div>

                      <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
                        <Field label="User">{detail.user_id ? 'Account' : 'Guest'}</Field>
                        <Field label="Account email">{detail.account_email ?? '—'}</Field>
                        <Field label="Status">{detail.status}</Field>
                        <Field label="Error category">{detail.error_category ?? '—'}</Field>
                      </div>

                      <div className="mt-6 border-t border-[#A62A34]/20 pt-5">
                        <div className={LABEL}>Submitted information</div>
                        {detail.product === 'ask' ? (
                          <div className="mt-3">
                            <Field label="User question">{String(inputData.question ?? '—')}</Field>
                          </div>
                        ) : (
                          <div className="mt-3 grid gap-4 sm:grid-cols-2">
                            {Object.entries(inputData).map(([key, value]) => (
                              <Field key={key} label={key}>
                                {typeof value === 'object' && value !== null ? JSON.stringify(value) : String(value ?? '—')}
                              </Field>
                            ))}
                          </div>
                        )}
                      </div>

                      <div className="mt-6 border-t border-[#A62A34]/20 pt-5">
                        <div className={LABEL}>Generated result</div>
                        <div className="mt-3">
                          {detail.product === 'kundli' && <KundliResult result={detail.result_data} />}
                          {detail.product === 'ask' && <AskResult result={detail.result_data} />}
                          {detail.product !== 'kundli' && detail.product !== 'ask' && (
                            <GenericResult result={detail.result_data} />
                          )}
                        </div>
                      </div>

                      <div className="mt-6 border-t border-[#A62A34]/20 pt-4">
                        <button
                          type="button"
                          onClick={() => setRawOpen((value) => !value)}
                          aria-expanded={rawOpen}
                          className="font-mono text-[10px] uppercase tracking-[0.14em] text-[#EEE9DF]/50 hover:text-[#D6BE85] cursor-pointer"
                        >
                          {rawOpen ? 'Hide raw stored data' : 'Raw stored data'}
                        </button>
                        {rawOpen && (
                          <div className="mt-3 space-y-3">
                            <div>
                              <div className={LABEL}>input_data</div>
                              <Json value={detail.input_data} />
                            </div>
                            <div>
                              <div className={LABEL}>result_data</div>
                              <Json value={detail.result_data} />
                            </div>
                          </div>
                        )}
                      </div>
                    </>
                  )}
                </div>
              )}

              <div className="flex items-center justify-between">
                <div className={LABEL}>Recent submissions</div>
                <div className="font-mono text-[9.5px] uppercase tracking-[0.14em] text-[#EEE9DF]/40">
                  {total} total · page {page} of {pages}
                </div>
              </div>

              {rows === null && (
                <div className="mt-3 space-y-2" aria-hidden>
                  <div className="h-12 animate-pulse rounded border border-[#A62A34]/15 bg-[#160A0C]/50" />
                  <div className="h-12 animate-pulse rounded border border-[#A62A34]/15 bg-[#160A0C]/50" />
                </div>
              )}

              {rows !== null && rows.length === 0 && !error && (
                <div className={`${PANEL} mt-3 p-5 text-[13px] text-[#EEE9DF]/60`}>
                  No submissions match these filters yet.
                </div>
              )}

              {rows !== null && rows.length > 0 && (
                <div className="mt-3 divide-y divide-[#A62A34]/15 overflow-hidden rounded-lg border border-[#A62A34]/25">
                  {rows.map((row) => (
                    <div key={row.id} className="bg-[#160A0C]/60">
                      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3">
                        <div className="flex min-w-0 flex-wrap items-center gap-x-4 gap-y-1">
                          <span className="font-mono text-[10px] tracking-[0.1em] text-[#EEE9DF]/45">{shortTime(row.created_at)}</span>
                          <span className="font-mono text-[10px] uppercase tracking-[0.16em] text-[#D6BE85]">
                            {PRODUCT_LABELS[row.product] ?? row.product}
                          </span>
                          <span className="truncate text-[12.5px] text-[#EEE9DF]/70">{visitorLabel(row)}</span>
                          {row.status !== 'SUCCEEDED' && (
                            <span className="font-mono text-[9px] uppercase tracking-[0.14em] text-[#A62A34]">{row.status}</span>
                          )}
                        </div>
                        <div className="flex shrink-0 items-center gap-3">
                          <button
                            type="button"
                            onClick={() => void open(row)}
                            disabled={detailLoadingId === row.id}
                            aria-busy={detailLoadingId === row.id}
                            className="font-mono text-[10px] uppercase tracking-[0.14em] text-[#D6BE85] hover:text-[#F7F5F0] disabled:opacity-40 cursor-pointer"
                          >
                            {detailLoadingId === row.id ? 'Loading…' : detail?.id === row.id ? 'Viewing' : 'View'}
                          </button>
                          {confirmId === row.id ? (
                            <>
                              <button type="button" onClick={() => void remove(row.id)} disabled={busyId === row.id} className="font-mono text-[10px] uppercase tracking-[0.14em] text-[#D6BE85] cursor-pointer">
                                {busyId === row.id ? 'Deleting…' : 'Confirm delete'}
                              </button>
                              <button type="button" onClick={() => setConfirmId(null)} className="font-mono text-[10px] uppercase tracking-[0.14em] text-[#EEE9DF]/50 cursor-pointer">
                                Cancel
                              </button>
                            </>
                          ) : (
                            <button type="button" onClick={() => setConfirmId(row.id)} className="font-mono text-[10px] uppercase tracking-[0.14em] text-[#EEE9DF]/50 hover:text-[#D6BE85] cursor-pointer">
                              Delete
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {pages > 1 && (
                <div className="mt-3 flex items-center gap-3">
                  <button
                    type="button"
                    disabled={page <= 1}
                    onClick={() => setPage((value) => Math.max(1, value - 1))}
                    className="font-mono text-[10px] uppercase tracking-[0.14em] text-[#EEE9DF]/60 hover:text-[#F7F5F0] disabled:opacity-30 cursor-pointer"
                  >
                    Previous
                  </button>
                  <button
                    type="button"
                    disabled={page >= pages}
                    onClick={() => setPage((value) => Math.min(pages, value + 1))}
                    className="font-mono text-[10px] uppercase tracking-[0.14em] text-[#EEE9DF]/60 hover:text-[#F7F5F0] disabled:opacity-30 cursor-pointer"
                  >
                    Next
                  </button>
                </div>
              )}
            </div>
          </>
        )}
      </Container>
    </main>
  );
}
