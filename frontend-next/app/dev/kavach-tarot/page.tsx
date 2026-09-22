'use client';

import React, { useState } from 'react';
import { API_BASE } from '../../../lib/api';

const DECK = [
  'the_fool','the_magician','the_high_priestess','the_empress','the_emperor','the_hierophant','the_lovers',
  'the_chariot','strength','the_hermit','wheel_of_fortune','justice','the_hanged_man','death','temperance',
  'the_devil','the_tower','the_star','the_moon','the_sun','judgement','the_world',
  'ace_of_wands','two_of_wands','three_of_wands','four_of_wands','five_of_wands','six_of_wands','seven_of_wands',
  'eight_of_wands','nine_of_wands','ten_of_wands','page_of_wands','knight_of_wands','queen_of_wands','king_of_wands',
  'ace_of_cups','two_of_cups','three_of_cups','four_of_cups','five_of_cups','six_of_cups','seven_of_cups',
  'eight_of_cups','nine_of_cups','ten_of_cups','page_of_cups','knight_of_cups','queen_of_cups','king_of_cups',
  'ace_of_swords','two_of_swords','three_of_swords','four_of_swords','five_of_swords','six_of_swords','seven_of_swords',
  'eight_of_swords','nine_of_swords','ten_of_swords','page_of_swords','knight_of_swords','queen_of_swords','king_of_swords',
  'ace_of_pentacles','two_of_pentacles','three_of_pentacles','four_of_pentacles','five_of_pentacles','six_of_pentacles',
  'seven_of_pentacles','eight_of_pentacles','nine_of_pentacles','ten_of_pentacles','page_of_pentacles',
  'knight_of_pentacles','queen_of_pentacles','king_of_pentacles',
];

interface Card { position: string; position_label: string; card_id: string; name: string; orientation: string;
  valence: string | null; core_meaning: string | null; contextual_meaning: string | null; source: string | null;
  themes: string[]; available: boolean }
interface Event {
  n: number; question: string; request: { type: string; reason: string };
  draw: { before: string | null; after: string; reused: boolean };
  context: Record<string, string | null>; cards: Card[]; private_context: string;
  history: Array<{ role: string; content: string }>;
  model: { called: boolean; status: string; preferred: string; actual: string | null;
    attempts: Array<{ model: string; reason: string }> };
  response: { raw: string | null; public: string | null; sanitised: boolean; unavailable_message?: string | null };
  localMode: boolean;
}

const TITLE: React.CSSProperties = { fontSize: 10, letterSpacing: '.2em', color: '#B39250', fontFamily: 'ui-monospace,monospace' };
const PANEL: React.CSSProperties = { background: 'rgba(22,10,12,.72)', border: '1px solid rgba(166,42,52,.25)', borderRadius: 8, padding: '12px 14px', marginTop: 10 };
const input: React.CSSProperties = { width: '100%', background: '#0b0b0b', color: '#EEE9DF', border: '1px solid rgba(166,42,52,.3)', borderRadius: 4, padding: '9px 10px', fontFamily: 'inherit', fontSize: 13 };
const btn: React.CSSProperties = { ...input, width: 'auto', cursor: 'pointer', padding: '8px 12px' };
const mono: React.CSSProperties = { fontFamily: 'ui-monospace,monospace', fontSize: 11 };

function label(value: string) { return value.replace(/_/g, ' ').replace(/\b\w/g, (m) => m.toUpperCase()); }

export default function AskKavachDevInspector() {
  // Development-only tool. `process.env.NODE_ENV` is inlined at build time, so a
  // production build always takes this branch and never renders the inspector.
  // The backend independently refuses every /api/dev/* request in production.
  if (process.env.NODE_ENV === 'production') {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[#090909] p-8 text-[#EEE9DF]">
        <div className="max-w-xl rounded-lg border border-[#A62A34]/25 bg-[#160A0C]/70 p-6 text-center">
          <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-[#B39250]">KAVACH</div>
          <h1 className="mt-2 text-lg font-semibold text-[#F7F5F0]">Not available</h1>
          <p className="mt-2 text-[13px] text-[#EEE9DF]/60">
            This is a development-only tool and is disabled in production.
          </p>
          <a href="/ask" className="mt-4 inline-block font-mono text-[11px] uppercase tracking-[0.16em] text-[#D6BE85] hover:text-[#F7F5F0]">
            Return to Ask KAVACH
          </a>
        </div>
      </main>
    );
  }

  const [conversationId, setConversationId] = useState(() => (typeof crypto !== 'undefined' && 'randomUUID' in crypto ? crypto.randomUUID() : String(Date.now())));
  const [messages, setMessages] = useState<Array<{ role: string; text: string }>>([]);
  const [events, setEvents] = useState<Event[]>([]);
  const [selected, setSelected] = useState<number>(0);
  const [question, setQuestion] = useState('Should I become an engineer?');
  const [forceCard, setForceCard] = useState('auto');
  const [orientation, setOrientation] = useState('auto');
  const [busy, setBusy] = useState(false);
  const [sim, setSim] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState('');

  const active = events.find((event) => event.n === selected) || events[events.length - 1] || null;

  async function run(opts: { mode?: 'local' | 'chat' | 'redraw'; generate?: boolean; text?: string }) {
    const text = (opts.text ?? question).trim();
    if (!text || busy) return;
    setBusy(true); setError('');
    try {
      const response = await fetch(`${API_BASE}/dev/kavach-tarot`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: text, conversation_id: conversationId,
          mode: opts.mode ?? 'local', generate: Boolean(opts.generate),
          force: forceCard === 'auto' ? [] : [forceCard], orientation,
        }),
      });
      const body = await response.json();
      if (body.status === 'error') throw new Error(body.message || 'request failed');
      const event = { ...body, n: events.length + 1, localMode: !(opts.generate || opts.mode === 'chat') } as Event;
      setEvents((prev) => [...prev, event]);
      setSelected(event.n);
      const shown = event.response.public || (event.localMode
        ? '[LOCAL ONLY - MODEL CALL: NOT MADE] ' + (event.cards[0]?.contextual_meaning ?? '')
        : (event.response.unavailable_message ?? ''));
      setMessages((prev) => [...prev, { role: 'user', text }, { role: 'assistant', text: shown }]);
      setQuestion('');
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : 'request failed');
    } finally { setBusy(false); }
  }

  async function simulate() {
    setBusy(true); setError('');
    try {
      const response = await fetch(`${API_BASE}/dev/kavach-tarot`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ simulate: 10000 }),
      });
      const body = await response.json();
      setSim(body.simulation ?? body);
    } catch { setError('simulation failed'); } finally { setBusy(false); }
  }

  function newChat() {
    setConversationId(typeof crypto !== 'undefined' && 'randomUUID' in crypto ? crypto.randomUUID() : String(Date.now()));
    setMessages([]); setEvents([]); setSelected(0); setSim(null); setError('');
  }

  return (
    <main style={{ minHeight: '100vh', background: '#090909', color: '#EEE9DF', padding: '22px 18px', fontFamily: 'system-ui,sans-serif' }}>
      <div style={{ maxWidth: 1400, margin: '0 auto' }}>
        <div style={TITLE}>ASK KAVACH — DEV INSPECTOR</div>
        <h1 style={{ fontSize: 20, margin: '6px 0 4px' }}>Hidden reading, context and model response</h1>
        <div style={{ fontSize: 12, color: 'rgba(238,233,223,.55)' }}>
          Inspect hidden reading, contextual interpretation, conversation state, and final model response.
          · conversation: <span style={mono}>{conversationId.slice(0, 8)}</span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(320px,1fr) minmax(420px,1.25fr)', gap: 14, marginTop: 14 }}>
          {/* ---------------- CHAT ---------------- */}
          <section>
            <div style={PANEL}>
              <div style={TITLE}>ASK KAVACH CHAT (same engine as public /ask)</div>
              <div style={{ marginTop: 8, maxHeight: 300, overflowY: 'auto' }}>
                {messages.length === 0 && <div style={{ fontSize: 12, color: 'rgba(238,233,223,.5)' }}>No messages yet.</div>}
                {messages.map((message, index) => (
                  <div key={index} style={{ marginTop: 8, fontSize: 13, textAlign: message.role === 'user' ? 'right' : 'left' }}>
                    <div style={{ display: 'inline-block', maxWidth: '92%', padding: '7px 10px', borderRadius: 8,
                      border: '1px solid rgba(166,42,52,.3)',
                      background: message.role === 'user' ? '#2B0C11' : 'rgba(22,10,12,.8)' }}>
                      {message.text}
                    </div>
                  </div>
                ))}
              </div>
              <input style={{ ...input, marginTop: 10 }} value={question} onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && run({ generate: true })}
                placeholder="Ask a test question..." />
              <div style={{ display: 'flex', gap: 8, marginTop: 8, flexWrap: 'wrap' }}>
                <button style={{ ...btn, background: '#541219', borderColor: '#A62A34' }} disabled={busy} onClick={() => run({ generate: true })}>SEND (1 model call)</button>
                <button style={btn} disabled={busy} onClick={() => run({ mode: 'local' })}>DRAW + INTERPRET LOCALLY</button>
                <button style={btn} disabled={busy} onClick={() => run({ mode: 'redraw' })}>DRAW AGAIN (dev)</button>
                {active && active.response.raw === null && (
                  <button style={btn} disabled={busy} onClick={() => run({ generate: true, text: active.question })}>GENERATE RESPONSE</button>
                )}
                <button style={btn} onClick={newChat}>NEW CHAT</button>
                <button style={btn} disabled={busy} onClick={simulate}>RUN 10,000 DRAWS</button>
              </div>
              <div style={{ display: 'flex', gap: 12, marginTop: 8, flexWrap: 'wrap', fontSize: 12 }}>
                <label style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                  <span style={{ color: 'rgba(238,233,223,.6)' }}>Force card</span>
                  <select style={{ ...input, width: 'auto', padding: '6px 8px' }} value={forceCard} onChange={(e) => setForceCard(e.target.value)}>
                    <option value="auto">AUTO / RANDOM</option>
                    {DECK.map((id) => <option key={id} value={id}>{label(id)}</option>)}
                  </select>
                </label>
                <label style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                  <span style={{ color: 'rgba(238,233,223,.6)' }}>Orientation</span>
                  <select style={{ ...input, width: 'auto', padding: '6px 8px' }} value={orientation} onChange={(e) => setOrientation(e.target.value)}>
                    <option value="auto">AUTO</option><option value="upright">Upright</option><option value="reversed">Reversed</option>
                  </select>
                </label>
              </div>
              <div style={{ fontSize: 11, color: 'rgba(238,233,223,.5)', marginTop: 6 }}>
                Forced card + local mode make zero model calls. SEND makes exactly one.
              </div>
            </div>

            <div style={PANEL}>
              <div style={TITLE}>READING HISTORY</div>
              <div style={{ marginTop: 6, fontSize: 12, maxHeight: 220, overflowY: 'auto' }}>
                {events.length === 0 && <div style={{ color: 'rgba(238,233,223,.5)' }}>No events yet.</div>}
                {events.map((event) => (
                  <button key={event.n} onClick={() => setSelected(event.n)}
                    style={{ display: 'block', width: '100%', textAlign: 'left', background: event.n === selected ? '#2B0C11' : 'transparent',
                      color: '#EEE9DF', border: '1px solid rgba(166,42,52,.25)', borderRadius: 6, padding: '7px 9px', marginTop: 6, cursor: 'pointer' }}>
                    <span style={mono}>#{event.n}</span> {event.question}
                    <div style={{ fontSize: 11, color: event.draw.reused ? '#D6BE85' : '#7BD88F' }}>
                      {event.draw.reused ? 'REUSED' : 'NEW READING'} · {event.draw.after}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {sim && (
              <div style={PANEL}>
                <div style={TITLE}>SHUFFLE SIMULATION</div>
                <div style={{ fontSize: 12, marginTop: 6 }}>
                  cards: {String(sim.total_cards)} · upright: {String(sim.upright_pct)}% · reversed: {String(sim.reversed_pct)}% ·
                  duplicates: {String(sim.duplicate_spreads)}
                </div>
              </div>
            )}
          </section>

          {/* ---------------- INSPECTOR ---------------- */}
          <section style={PANEL}>
            <div style={TITLE}>INTERNAL INSPECTOR</div>
            {error && <div style={{ marginTop: 8, color: '#E5B567', fontSize: 12 }}>{error}</div>}
            {!active && <div style={{ fontSize: 12, color: 'rgba(238,233,223,.5)', marginTop: 8 }}>Send a message or run a local draw to inspect.</div>}
            {active && (
              <>
                <div style={{ marginTop: 8, fontSize: 13 }}>
                  <div><span style={TITLE}>MESSAGE</span><div>{active.question}</div></div>
                  <div style={{ marginTop: 6 }}><span style={TITLE}>REQUEST TYPE</span>
                    <div style={{ display: 'inline-block', marginLeft: 8, padding: '2px 8px', borderRadius: 10,
                      background: active.draw.reused ? 'rgba(214,190,133,.15)' : 'rgba(123,216,143,.15)',
                      color: active.draw.reused ? '#D6BE85' : '#7BD88F', fontSize: 11 }}>
                      {active.request.type}
                    </div>
                    <div style={{ fontSize: 11, color: 'rgba(238,233,223,.6)', marginTop: 4 }}>reason: {active.request.reason}</div>
                  </div>
                  <div style={{ marginTop: 6, ...mono }}>
                    draw before: {active.draw.before ?? 'none'} → after: {active.draw.after}
                  </div>
                </div>

                <details style={PANEL} open>
                  <summary style={{ cursor: 'pointer', ...TITLE }}>CONTEXT DETECTION</summary>
                  <div style={{ fontSize: 12, marginTop: 6 }}>
                    {['domain','subcontext','intent','subject','concern','timeframe','follow_up'].map((key) => (
                      <div key={key}><span style={{ color: 'rgba(238,233,223,.6)' }}>{label(key)}:</span> {String((active.context as Record<string, unknown>)[key] ?? '—')}</div>
                    ))}
                  </div>
                </details>

                <details style={PANEL} open>
                  <summary style={{ cursor: 'pointer', ...TITLE }}>DRAW ({active.cards.length} CARDS)</summary>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(200px,1fr))', gap: 10, marginTop: 8 }}>
                    {active.cards.map((card, index) => (
                      <div key={index} style={{ border: '1px solid rgba(166,42,52,.3)', borderRadius: 8, padding: '10px 11px', background: 'rgba(11,11,11,.6)' }}>
                        <div style={TITLE}>{card.position_label || card.position}</div>
                        <div style={{ fontSize: 15, fontWeight: 700, marginTop: 6 }}>{card.name}</div>
                        <div style={{ fontSize: 11, color: '#D6BE85', letterSpacing: '.1em', marginTop: 2 }}>
                          {card.orientation.toUpperCase()}{card.valence ? ` · ${card.valence}` : ''}
                        </div>
                        <div style={{ ...mono, marginTop: 4, color: 'rgba(238,233,223,.5)' }}>{card.card_id}</div>
                        <details style={{ marginTop: 6 }}>
                          <summary style={{ cursor: 'pointer', fontSize: 11, color: '#B39250' }}>core meaning</summary>
                          <div style={{ fontSize: 12, marginTop: 4 }}>{card.core_meaning ?? '—'}</div>
                          <div style={{ fontSize: 11, color: 'rgba(238,233,223,.5)', marginTop: 4 }}>{card.themes.join(', ')}</div>
                        </details>
                        <details style={{ marginTop: 4 }} open>
                          <summary style={{ cursor: 'pointer', fontSize: 11, color: '#B39250' }}>contextual meaning</summary>
                          <div style={{ fontSize: 12, marginTop: 4 }}>{card.contextual_meaning ?? '—'}</div>
                        </details>
                        <div style={{ fontSize: 11, marginTop: 6, color: card.source === 'fallback' ? '#E5B567' : '#7BD88F' }}>
                          source: {card.source ?? '—'}
                        </div>
                        <div style={{ ...mono, marginTop: 6, color: 'rgba(238,233,223,.45)', fontSize: 10 }}>
                          {card.name} → {card.orientation} → {String(active.context.domain)}/{String(active.context.subcontext)} → {card.source ?? '—'}
                        </div>
                      </div>
                    ))}
                  </div>
                </details>

                <details style={PANEL}>
                  <summary style={{ cursor: 'pointer', ...TITLE }}>PRIVATE CONTEXT SENT TO MODEL</summary>
                  <button style={{ ...btn, marginTop: 6, fontSize: 11 }} onClick={() => navigator.clipboard?.writeText(active.private_context)}>COPY PRIVATE CONTEXT</button>
                  <pre style={{ ...mono, whiteSpace: 'pre-wrap', marginTop: 6, color: '#EEE9DF' }}>{active.private_context}</pre>
                </details>

                <details style={PANEL}>
                  <summary style={{ cursor: 'pointer', ...TITLE }}>MODEL CONVERSATION HISTORY</summary>
                  <div style={{ marginTop: 6, fontSize: 12 }}>
                    {active.history.length === 0 && <div style={{ color: 'rgba(238,233,223,.5)' }}>empty</div>}
                    {active.history.map((item, index) => (
                      <div key={index} style={{ marginTop: 4 }}>
                        <span style={{ color: '#B39250', ...mono }}>{item.role.toUpperCase()}</span> {item.content}
                      </div>
                    ))}
                  </div>
                </details>

                <details style={PANEL} open>
                  <summary style={{ cursor: 'pointer', ...TITLE }}>MODEL</summary>
                  <div style={{ fontSize: 12, marginTop: 6 }}>
                    <div>status: <strong>{active.model.status}</strong>{active.localMode && ' · MODEL CALL: NOT MADE'}</div>
                    <div>preferred: <span style={mono}>{active.model.preferred}</span></div>
                    <div>actual: <span style={mono}>{active.model.actual ?? '—'}</span></div>
                    {active.model.attempts.length > 0 && (
                      <div style={{ marginTop: 4 }}>
                        attempts:
                        {active.model.attempts.map((item, index) => (
                          <div key={index} style={mono}>&nbsp;&nbsp;{item.model} → {item.reason}</div>
                        ))}
                      </div>
                    )}
                  </div>
                </details>

                <details style={PANEL} open>
                  <summary style={{ cursor: 'pointer', ...TITLE }}>FINAL RESPONSE</summary>
                  <div style={{ fontSize: 12, marginTop: 6 }}>
                    <div style={{ color: 'rgba(238,233,223,.6)' }}>RAW MODEL RESPONSE</div>
                    <div style={{ marginTop: 2 }}>{active.response.raw ?? '—'}</div>
                    <div style={{ color: 'rgba(238,233,223,.6)', marginTop: 8 }}>PUBLIC RESPONSE AFTER SANITISATION</div>
                    <div style={{ marginTop: 2 }}>{active.response.public ?? active.response.unavailable_message ?? '—'}</div>
                    <div style={{ marginTop: 8, color: active.response.sanitised ? '#E5B567' : '#7BD88F' }}>
                      SANITISER MODIFIED RESPONSE: {active.response.sanitised ? 'YES' : 'NO'}
                    </div>
                  </div>
                </details>

                <details style={PANEL}>
                  <summary style={{ cursor: 'pointer', ...TITLE }}>RAW DEBUG JSON</summary>
                  <pre style={{ ...mono, whiteSpace: 'pre-wrap', maxHeight: 260, overflow: 'auto' }}>{JSON.stringify(active, null, 2)}</pre>
                </details>
              </>
            )}
          </section>
        </div>
      </div>
    </main>
  );
}
