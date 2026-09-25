'use client';

import React, { useEffect, useRef, useState } from 'react';
import { API_BASE } from '../../lib/api';
import { Header } from '../../components/Header';
import { RichAnswer } from '../../components/RichAnswer';

interface City { label: string; latitude: number; longitude: number; timezone: string }

const CITIES: City[] = [
  { label: 'New Delhi, India', latitude: 28.6139, longitude: 77.209, timezone: 'Asia/Kolkata' },
  { label: 'Mumbai, India', latitude: 19.076, longitude: 72.8777, timezone: 'Asia/Kolkata' },
  { label: 'Bengaluru, India', latitude: 12.9716, longitude: 77.5946, timezone: 'Asia/Kolkata' },
  { label: 'Chennai, India', latitude: 13.0827, longitude: 80.2707, timezone: 'Asia/Kolkata' },
  { label: 'Kolkata, India', latitude: 22.5726, longitude: 88.3639, timezone: 'Asia/Kolkata' },
  { label: 'Hyderabad, India', latitude: 17.385, longitude: 78.4867, timezone: 'Asia/Kolkata' },
  { label: 'London, United Kingdom', latitude: 51.5074, longitude: -0.1278, timezone: 'Europe/London' },
  { label: 'New York, United States', latitude: 40.7128, longitude: -74.006, timezone: 'America/New_York' },
  { label: 'Dubai, UAE', latitude: 25.2048, longitude: 55.2708, timezone: 'Asia/Dubai' },
  { label: 'Singapore', latitude: 1.3521, longitude: 103.8198, timezone: 'Asia/Singapore' },
  { label: 'Sydney, Australia', latitude: -33.8688, longitude: 151.2093, timezone: 'Australia/Sydney' },
];

const STARTERS = [
  'How will my interview go?',
  'Should I be careful about this situation?',
  'How is this relationship situation looking?',
];

const STORAGE_KEY = 'kavach_ask_location';

// Static first-run greeting. It is rendered without an Ask request and is never
// persisted as a conversation turn.
const WELCOME_MESSAGE = "Hi, I’m Ask KAVACH.\n\nAsk me what’s on your mind — a situation, decision, relationship,\nconcern, or simply something you want clarity on. I’ll help you explore\nit, and when one of KAVACH’s dedicated tools can give you a better\nanswer, I’ll take you there.";

// Development-only inspector tooling. In a production build Next.js inlines
// `process.env.NODE_ENV` as "production", so the control is never rendered.
// The backend independently refuses inspector/trace data to ordinary
// production requests.
const DEV_TOOLS_ENABLED = process.env.NODE_ENV !== 'production';

interface ToolAction { tool: string; label: string; href: string }
interface Turn { id: number; question: string; answer: string; answered: boolean; assistantIndex: number; toolAction?: ToolAction }
interface TraceCard {
  position_label: string; name: string; orientation: string; card_id: string; valence?: string | null;
  core_meaning?: string | null; contextual_meaning?: string | null; source?: string | null;
}
interface TraceEvent {
  event_id: string; question: string;
  request: { type: string; reason: string };
  draw: { before: string | null; after: string; reused: boolean };
  context: Record<string, string | null>;
  cards: TraceCard[];
  private_context: string | null;
  model: { called: boolean; status: string; preferred?: string | null; actual?: string | null;
    attempts: Array<{ model: string; reason: string }>; fallback?: boolean };
  response: { raw: string | null; public: string | null; sanitised: boolean };
}

const newConversationId = () =>
  typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;

const withOffset = (d: Date) => {
  const pad = (n: number) => String(n).padStart(2, '0');
  const off = -d.getTimezoneOffset();
  const sign = off >= 0 ? '+' : '-';
  const abs = Math.abs(off);
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}${sign}${pad(Math.floor(abs / 60))}:${pad(abs % 60)}`;
};

const label = (value: string) => value.replace(/_/g, ' ').replace(/\b\w/g, (m) => m.toUpperCase());

function DevInspector({ event, onClose }: { event: TraceEvent; onClose: () => void }) {
  const [copied, setCopied] = useState(false);
  const warnings: string[] = [];
  if (event.cards.some((card) => card.source === 'fallback')) warnings.push('Used fallback interpretation');
  if (event.cards.some((card) => card.orientation === 'reversed' && card.source === 'curated_context')) {
    warnings.push('Contextual entry is orientation-agnostic (reversed card uses an upright-flavoured entry)');
  }
  if ((event.context?.domain ?? 'general') === 'general') warnings.push('Context classified as general');
  if (event.response?.sanitised) warnings.push('Sanitiser modified the model response');
  if (event.model?.fallback === true) warnings.push('Model fallback occurred');

  return (
    <div className="mt-2 rounded-lg border border-[#B39250]/40 bg-[#120A0B] p-3 text-left">
      <div className="flex items-start justify-between gap-3">
        <div className="text-[10px] uppercase tracking-[0.22em] text-[#B39250]">Dev · Internal reading</div>
        <button onClick={onClose} className="text-[11px] text-[#EEE9DF]/50 hover:text-[#D6BE85]">close</button>
      </div>

      <div className="mt-2 text-[11px] text-[#EEE9DF]/80">
        <span className="rounded bg-[#2B0C11] px-2 py-0.5 text-[#D6BE85]">{event.request.type}</span>
        <span className="ml-2 font-mono text-[#EEE9DF]/60">{event.draw.after}</span>
        <span className="ml-2 text-[#EEE9DF]/50">· {event.draw.reused ? 'REUSED' : 'NEW'}</span>
      </div>
      <div className="mt-1 text-[11px] text-[#EEE9DF]/50">reason: {event.request.reason}</div>

      <div className="mt-2 text-[11px] text-[#EEE9DF]/70">
        <span className="text-[#B39250]">Context:</span>{' '}
        {label(String(event.context?.domain ?? '—'))} · {label(String(event.context?.subcontext ?? '—'))} ·{' '}
        {label(String(event.context?.intent ?? '—'))}
        {event.context?.timeframe ? ` · ${label(String(event.context.timeframe))}` : ''}
      </div>

      {warnings.length > 0 && (
        <ul className="mt-2 space-y-1 text-[11px] text-[#E5B567]">
          {warnings.map((warning) => <li key={warning}>⚠ {warning}</li>)}
        </ul>
      )}

      <div className="mt-3 space-y-2">
        {event.cards.map((card, index) => (
          <div key={`${card.card_id}-${index}`} className="rounded border border-[#A62A34]/30 bg-[#0B0B0B]/60 p-2.5">
            <div className="text-[10px] uppercase tracking-[0.18em] text-[#B39250]">{card.position_label}</div>
            <div className="mt-1 flex items-center gap-2">
              <span className="text-[13px] font-semibold text-[#F7F5F0]">{card.name}</span>
              <span className={`rounded px-1.5 py-0.5 text-[10px] tracking-[0.12em] ${
                card.orientation === 'upright' ? 'bg-[#7BD88F]/15 text-[#7BD88F]' : 'bg-[#E5B567]/15 text-[#E5B567]'}`}>
                {card.orientation.toUpperCase()}
              </span>
            </div>
            <div className="mt-2 text-[11px] text-[#EEE9DF]/60">
              <span className="text-[#B39250]">Core meaning:</span> {card.core_meaning ?? '—'}
            </div>
            <div className="mt-1.5 text-[11px] text-[#EEE9DF]/85">
              <span className="text-[#B39250]">Interpreted for this question:</span> {card.contextual_meaning ?? '—'}
            </div>
            <div className="mt-1 text-[10px] text-[#EEE9DF]/40">source: {card.source ?? '—'}</div>
          </div>
        ))}
      </div>

      <details className="mt-3">
        <summary className="cursor-pointer text-[10px] uppercase tracking-[0.18em] text-[#B39250]">Private context given to model</summary>
        <button
          onClick={() => { navigator.clipboard?.writeText(event.private_context ?? ''); setCopied(true); }}
          className="mt-2 rounded border border-[#A62A34]/40 px-2 py-1 text-[10px] text-[#EEE9DF]/70"
        >
          {copied ? 'copied' : 'copy'}
        </button>
        <pre className="mt-2 whitespace-pre-wrap font-mono text-[11px] text-[#EEE9DF]/80">{event.private_context ?? '—'}</pre>
      </details>

      <details className="mt-2">
        <summary className="cursor-pointer text-[10px] uppercase tracking-[0.18em] text-[#B39250]">Model details</summary>
        <div className="mt-2 text-[11px] text-[#EEE9DF]/75">
          <div>status: {event.model.status}{event.model.called ? '' : ' · model call: not made'}</div>
          <div>preferred: <span className="font-mono">{event.model.preferred ?? '—'}</span></div>
          <div>actual: <span className="font-mono">{event.model.actual ?? '—'}</span></div>
          {event.model.attempts.map((attempt, index) => (
            <div key={index} className="font-mono text-[10px] text-[#E5B567]">{attempt.model} → {attempt.reason}</div>
          ))}
        </div>
      </details>

      <details className="mt-2">
        <summary className="cursor-pointer text-[10px] uppercase tracking-[0.18em] text-[#B39250]">Raw vs public response</summary>
        <div className="mt-2 text-[11px] text-[#EEE9DF]/80">
          <div className="text-[#EEE9DF]/50">RAW MODEL RESPONSE</div>
          <div>{event.response.raw ?? '—'}</div>
          <div className="mt-2 text-[#EEE9DF]/50">PUBLIC RESPONSE</div>
          <div>{event.response.public ?? '—'}</div>
          <div className={`mt-2 ${event.response.sanitised ? 'text-[#E5B567]' : 'text-[#7BD88F]'}`}>
            SANITISER MODIFIED RESPONSE: {event.response.sanitised ? 'YES' : 'NO'}
          </div>
        </div>
      </details>
    </div>
  );
}

export default function AskPage() {
  const [city, setCity] = useState<City | null>(null);
  const [changingLocation, setChangingLocation] = useState(false);
  const [input, setInput] = useState('');
  const [turns, setTurns] = useState<Turn[]>([]);
  const [busy, setBusy] = useState(false);
  const [conversationId, setConversationId] = useState('');
  // Fail-closed by default: the inspector control stays hidden unless the
  // development probe below succeeds, and that probe never runs in production.
  const [devEnabled, setDevEnabled] = useState(DEV_TOOLS_ENABLED);
  const [inspecting, setInspecting] = useState<number | null>(null);
  const [trace, setTrace] = useState<TraceEvent | null>(null);
  const [traceError, setTraceError] = useState('');
  const nextId = useRef(1);
  const assistantCount = useRef(0);

  useEffect(() => {
    setConversationId((current) => current || newConversationId());
  }, []);

  useEffect(() => {
    if (!DEV_TOOLS_ENABLED) return;
    setDevEnabled(true);
  }, []);

  useEffect(() => {
    try {
      const stored = window.localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const found = CITIES.find((c) => c.label === stored);
        if (found) setCity(found);
      }
    } catch {
      /* storage unavailable */
    }
  }, []);

  const chooseCity = (value: string) => {
    const found = CITIES.find((c) => c.label === value) || CITIES[0];
    setCity(found);
    setChangingLocation(false);
    try {
      window.localStorage.setItem(STORAGE_KEY, found.label);
    } catch {
      /* ignore */
    }
  };

  const openInspector = async (turn: Turn) => {
    if (inspecting === turn.id) { setInspecting(null); return; }
    setInspecting(turn.id);
    setTrace(null);
    setTraceError('');
    try {
      const response = await fetch(`${API_BASE}/dev/kavach-trace`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ conversation_id: conversationId, index: turn.assistantIndex }),
      });
      if (!response.ok) throw new Error('No internal trace available for this answer.');
      setTrace(await response.json());
    } catch (exc) {
      setTraceError(exc instanceof Error ? exc.message : 'Trace unavailable');
    }
  };

  const send = async (text?: string) => {
    const question = (text ?? input).trim();
    if (!question || busy || !city) return;
    setBusy(true);
    setInput('');

    const previous = turns.length > 0;
    const timestamp = withOffset(new Date());
    const chatId = conversationId || newConversationId();
    if (!conversationId) setConversationId(chatId);

    try {
      const res = await fetch(`${API_BASE}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question,
          timestamp,
          latitude: city.latitude,
          longitude: city.longitude,
          timezone: city.timezone,
          location_label: city.label,
          is_follow_up: previous,
          original_timestamp: null,
          conversation_id: chatId,
        }),
      });
      const body = await res.json();
      const allowedTools: Record<string, string> = {
        kundli: '/kundli', dasha: '/kundli', navtara: '/kundli', daily: '/daily',
        matchmaking: '/compatibility', yes_no: '/yes-no', panchang: '/panchang',
        life_summary: '/life-summary',
      };
      const candidate = body.tool_action as ToolAction | undefined;
      const toolAction = candidate && allowedTools[candidate.tool]
        && candidate.href === allowedTools[candidate.tool] ? candidate : undefined;
      assistantCount.current += 1;
      setTurns((prev) => [
        ...prev,
        {
          id: nextId.current++,
          question,
          answer: body.answer ?? "We couldn't process that question right now.",
          answered: Boolean(body.answered),
          assistantIndex: assistantCount.current,
          toolAction,
        },
      ]);
    } catch {
      assistantCount.current += 1;
      setTurns((prev) => [
        ...prev,
        { id: nextId.current++, question, answer: "We couldn't process that question right now.", answered: false,
          assistantIndex: assistantCount.current },
      ]);
    } finally {
      setBusy(false);
    }
  };

  // Location gate — asked once, remembered locally.
  if (!city || changingLocation) {
    return (
      <main className="min-h-screen bg-[#090909] text-[#EEE9DF] architectural-grid">
        <Header onStartReading={() => { window.location.href = '/'; }} />
        <div className="mx-auto w-full max-w-lg px-5 pb-16">
          <div className="text-lg font-bold tracking-[0.28em] text-[#F7F5F0]">KAVACH</div>
          <div className="mt-1 text-xs uppercase tracking-[0.24em] text-[#B39250]">Ask KAVACH</div>
          <h1 className="mt-6 text-2xl font-semibold text-[#F7F5F0]">Your location</h1>
          <p className="mt-2 text-sm text-[#EEE9DF]/60">
            Used for the moment you ask a question. You can change it any time.
          </p>
          <select
            defaultValue={city?.label}
            onChange={(e) => chooseCity(e.target.value)}
            className="mt-5 w-full rounded border border-[#A62A34]/35 bg-[#160A0C] px-4 py-3.5 text-sm text-[#F7F5F0] outline-none focus:border-[#A62A34]"
          >
            {CITIES.map((c) => (
              <option key={c.label} value={c.label}>{c.label}</option>
            ))}
          </select>
          <button
            onClick={() => chooseCity(city?.label ?? CITIES[0].label)}
            className="mt-4 w-full rounded bg-[#7B1D26] px-4 py-3.5 text-sm font-semibold text-[#F7F5F0] transition-colors hover:bg-[#A62A34]"
          >
            Continue
          </button>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[#090909] text-[#EEE9DF] architectural-grid">
      <Header onStartReading={() => { window.location.href = '/'; }} />
      <div className="mx-auto flex min-h-screen w-full max-w-2xl flex-col px-5 pb-8">
        <div className="flex items-start justify-between gap-4 border-b border-[#A62A34]/25 pb-4">
          <div>
            <div className="text-lg font-bold tracking-[0.28em] text-[#F7F5F0]">KAVACH</div>
            <div className="mt-1 text-xs uppercase tracking-[0.24em] text-[#B39250]">Ask KAVACH</div>
          </div>
          <div className="mt-1 flex items-center gap-3">
            <button
              onClick={() => {
                setTurns([]);
                setConversationId(newConversationId());
                assistantCount.current = 0;
                setInspecting(null);
                setTrace(null);
              }}
              className="text-xs text-[#EEE9DF]/55 hover:text-[#D6BE85]"
            >
              New chat
            </button>
            <button
              onClick={() => setChangingLocation(true)}
              className="text-xs text-[#EEE9DF]/55 hover:text-[#D6BE85]"
            >
              {city.label} · Change
            </button>
          </div>
        </div>

        <div className="flex-1 space-y-4 py-6">
          {turns.length === 0 && (
            <div className="flex justify-start">
              <div className="max-w-[90%] rounded-2xl rounded-bl-sm border border-[#A62A34]/25 bg-[#160A0C]/80 px-4 py-3 text-[15px] leading-relaxed text-[#EEE9DF]/85">
                <RichAnswer text={WELCOME_MESSAGE} />
              </div>
            </div>
          )}

          {turns.length === 0 && (
            <div className="pt-6">
              <p className="text-sm text-[#EEE9DF]/60">Ask anything.</p>
              <div className="mt-4 space-y-2">
                {STARTERS.map((starter) => (
                  <button
                    key={starter}
                    onClick={() => send(starter)}
                    className="block w-full rounded-lg border border-[#A62A34]/25 bg-[#160A0C]/60 px-4 py-3 text-left text-sm text-[#EEE9DF]/80 transition-colors hover:border-[#A62A34]/50 hover:text-[#F7F5F0]"
                  >
                    {starter}
                  </button>
                ))}
              </div>
            </div>
          )}

          {turns.map((turn) => (
            <div key={turn.id} className="space-y-3">
              <div className="flex justify-end">
                <div className="max-w-[85%] rounded-2xl rounded-br-sm border border-[#A62A34]/30 bg-[#2B0C11]/70 px-4 py-2.5 text-[15px] text-[#F7F5F0]">
                  {turn.question}
                </div>
              </div>
              <div className="flex justify-start">
                <div className="max-w-[90%]">
                  <div className="rounded-2xl rounded-bl-sm border border-[#A62A34]/25 bg-[#160A0C]/80 px-4 py-3 text-[15px] leading-relaxed text-[#EEE9DF]/85">
                    <RichAnswer text={turn.answer} />
                  </div>
                  {turn.toolAction && (
                    <a
                      href={turn.toolAction.href}
                      className="mt-2 inline-flex rounded border border-[#D6BE85]/55 bg-[#B39250]/10 px-3 py-2 font-mono text-[10px] uppercase tracking-[0.14em] text-[#D6BE85] hover:border-[#D6BE85]"
                    >
                      {turn.toolAction.label} →
                    </a>
                  )}
                  {DEV_TOOLS_ENABLED && devEnabled && (
                    <button
                      onClick={() => openInspector(turn)}
                      className="mt-1 text-[11px] text-[#B39250]/80 hover:text-[#D6BE85]"
                    >
                      🔧 Inspect Reading
                    </button>
                  )}
                  {DEV_TOOLS_ENABLED && devEnabled && inspecting === turn.id && (
                    trace
                      ? <DevInspector event={trace} onClose={() => setInspecting(null)} />
                      : <div className="mt-2 text-[11px] text-[#E5B567]">{traceError || 'Loading trace…'}</div>
                  )}
                </div>
              </div>
            </div>
          ))}

          {busy && <div className="text-xs uppercase tracking-[0.18em] text-[#B39250]">KAVACH is considering…</div>}
        </div>

        <div className="sticky bottom-0 flex gap-2 bg-[#090909]/95 pb-2 pt-3 backdrop-blur">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && send()}
            placeholder="Ask anything…"
            className="flex-1 rounded border border-[#A62A34]/35 bg-[#160A0C] px-4 py-3 text-sm text-[#F7F5F0] outline-none focus:border-[#A62A34]"
          />
          <button
            onClick={() => send()}
            disabled={busy}
            className="rounded bg-[#7B1D26] px-5 py-3 text-sm font-semibold text-[#F7F5F0] transition-colors hover:bg-[#A62A34] disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </div>
    </main>
  );
}
