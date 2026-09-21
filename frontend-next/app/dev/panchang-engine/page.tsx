'use client';

import React, { useState } from 'react';
import { API_BASE } from '../../../lib/api';

interface Placement {
  planet: string;
  rashi?: string;
  house?: number;
  longitude?: number;
  missing_in_chart?: boolean;
}
interface Channel {
  limb: string;
  value: string;
  context: Record<string, string | number>;
  selected_lord: string;
  interpretation_domain: string[];
  natal_placement: Placement | null;
}
interface ChannelInterpretation {
  dignity: string;
  base_interpretation: string[] | null;
  channel_interpretation: string | null;
  public_text: string | null;
  assessment: string;
  strengths: string[];
  watch_for: string[];
  guidance: string[];
}
interface EngineResult {
  engine: string;
  status: string;
  provenance: Record<string, string>;
  birth_panchang: Record<string, never>;
  channels: Record<string, Channel>;
  interpretation?: { channels: Record<string, ChannelInterpretation> };
  notes: string[];
}

const LABELS: Record<string, { title: string; use: string }> = {
  vaar: { title: 'VAAR', use: 'Personality Â· Vitality' },
  tithi: { title: 'TITHI', use: 'Marriage Â· Relationships Â· Prosperity' },
  karana: { title: 'KARANA', use: 'Career Â· Decision Making' },
  nakshatra: { title: 'NAKSHATRA', use: 'Subconscious Â· Instinctive Patterns' },
  yoga: { title: 'YOGA', use: 'Protection Â· Overcoming Obstacles' },
};

interface DailyMoon {
  date: string;
  moon: { rashi: string; nakshatra: string; pada: number; nakshatra_lord: string };
  daily_chart: { reference: string; reference_status: string; reference_time: string; lord_house: number | null; lord_rashi: string | null };
  classification: string;
  notes: string[];
}

export default function PanchangEngineTest() {
  const [date, setDate] = useState('2008-05-14');
  const [time, setTime] = useState('14:35');
  const [place, setPlace] = useState('Delhi, India');
  const [lat, setLat] = useState(28.632803);
  const [lon, setLon] = useState(77.219771);
  const [tz, setTz] = useState('Asia/Kolkata');
  const [query, setQuery] = useState('');
  const [hits, setHits] = useState<Array<{ display: string; lat: number; lon: number }>>([]);
  const [data, setData] = useState<EngineResult | null>(null);
  const [raw, setRaw] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [dailyDate, setDailyDate] = useState(new Date().toISOString().slice(0, 10));
  const [daily, setDaily] = useState<DailyMoon | null>(null);
  const [dailyBusy, setDailyBusy] = useState(false);

  const runDaily = async () => {
    setDailyBusy(true);
    try {
      const res = await fetch(`${API_BASE}/dev/daily-moon`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ date: dailyDate, place, latitude: lat, longitude: lon, timezone: tz }),
      });
      const body = await res.json();
      setDaily(body.status === 'error' ? null : body);
    } catch {
      setDaily(null);
    } finally {
      setDailyBusy(false);
    }
  };

  const search = async () => {
    if (query.trim().length < 3) return;
    try {
      const res = await fetch(`${API_BASE}/places/search?q=${encodeURIComponent(query.trim())}`);
      const body = await res.json();
      setHits(body.results || []);
    } catch {
      setHits([]);
    }
  };

  const run = async () => {
    setBusy(true); setError(''); setData(null);
    try {
      const res = await fetch(`${API_BASE}/dev/panchang-engine`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ date, time, place, latitude: lat, longitude: lon, timezone: tz }),
      });
      const body = await res.json();
      if (body.status === 'error') throw new Error(body.message);
      setData(body);
      setRaw(JSON.stringify(body, null, 2));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Calculation failed');
    } finally {
      setBusy(false);
    }
  };

  const input = {
    background: '#160A0C', color: '#F7F5F0', border: '1px solid rgba(166,42,52,.35)',
    borderRadius: 4, padding: '7px 9px', font: 'inherit', fontSize: 13, width: '100%',
  } as const;

  return (
    <main style={{ minHeight: '100vh', background: '#090909', color: '#EEE9DF', paddingBottom: 80 }}>
      <div style={{ maxWidth: 1100, margin: '0 auto', padding: '20px 16px' }}>
        <div style={{ borderBottom: '1px solid rgba(166,42,52,.25)', paddingBottom: 12 }}>
          <div style={{ fontWeight: 800, letterSpacing: '.28em', color: '#F7F5F0' }}>KAVACH</div>
          <div style={{ fontSize: 12, letterSpacing: '.18em', textTransform: 'uppercase', color: '#D6BE85' }}>Panchang Significator Engine</div>
          <div style={{ marginTop: 6, fontFamily: 'ui-monospace,monospace', fontSize: 10, color: '#E53E3E' }}>
            LOCAL TESTING ONLY Â· NOT IN NAVIGATION Â· SIGNIFICATORS ONLY, NO PREDICTIONS
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(170px,1fr))', gap: 12, marginTop: 16 }}>
          <label><div style={{ fontSize: 9.5, color: 'rgba(238,233,223,.5)', marginBottom: 4 }}>Birth date</div><input type="date" value={date} onChange={(e) => setDate(e.target.value)} style={input} /></label>
          <label><div style={{ fontSize: 9.5, color: 'rgba(238,233,223,.5)', marginBottom: 4 }}>Birth time</div><input type="time" value={time} onChange={(e) => setTime(e.target.value)} style={input} /></label>
          <label><div style={{ fontSize: 9.5, color: 'rgba(238,233,223,.5)', marginBottom: 4 }}>Timezone</div><input value={tz} onChange={(e) => setTz(e.target.value)} style={input} /></label>
          <label><div style={{ fontSize: 9.5, color: 'rgba(238,233,223,.5)', marginBottom: 4 }}>Latitude</div><input value={lat} onChange={(e) => setLat(Number(e.target.value))} style={input} /></label>
          <label><div style={{ fontSize: 9.5, color: 'rgba(238,233,223,.5)', marginBottom: 4 }}>Longitude</div><input value={lon} onChange={(e) => setLon(Number(e.target.value))} style={input} /></label>
        </div>

        <div style={{ marginTop: 12 }}>
          <div style={{ fontSize: 9.5, color: 'rgba(238,233,223,.5)', marginBottom: 4 }}>Birth place</div>
          <div style={{ display: 'flex', gap: 6 }}>
            <input value={query} placeholder="Search a cityâ€¦" onChange={(e) => setQuery(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && search()} style={input} />
            <button onClick={search} style={{ ...input, width: 'auto', cursor: 'pointer' }}>Search</button>
          </div>
          {hits.length > 0 && (
            <div style={{ marginTop: 6, border: '1px solid rgba(166,42,52,.25)', borderRadius: 4, maxHeight: 140, overflowY: 'auto' }}>
              {hits.map((h, i) => (
                <div key={i} onClick={() => { setPlace(h.display); setLat(h.lat); setLon(h.lon); setHits([]); }}
                  style={{ padding: '6px 9px', cursor: 'pointer', borderBottom: '1px solid rgba(166,42,52,.15)', fontSize: 12 }}>{h.display}</div>
              ))}
            </div>
          )}
          <div style={{ marginTop: 6, fontSize: 12, color: 'rgba(238,233,223,.6)' }}>Selected: {place}</div>
        </div>

        <button onClick={run} disabled={busy} style={{ ...input, width: 'auto', marginTop: 14, cursor: 'pointer', background: '#7B1D26', borderColor: '#A62A34', fontWeight: 700 }}>
          {busy ? 'Calculatingâ€¦' : 'Calculate significators'}
        </button>

        {error && <div style={{ marginTop: 12, border: '1px solid rgba(229,62,62,.5)', background: 'rgba(84,18,25,.35)', padding: 10, borderRadius: 6, fontSize: 13 }}>{error}</div>}

        {/* DAILY MOON SIGNAL — transit-based, no birth details */}
        <section style={{ marginTop: 28, borderTop: '1px solid rgba(166,42,52,.25)', paddingTop: 18 }}>
          <div style={{ fontSize: 12, letterSpacing: '.18em', textTransform: 'uppercase', color: '#B39250' }}>Daily Moon Signal</div>
          <div style={{ marginTop: 4, fontSize: 11, color: 'rgba(238,233,223,.5)' }}>
            Uses today&apos;s transits only · no birth details · separate from the birth-panchang channels above
          </div>
          <div style={{ display: 'flex', gap: 8, marginTop: 10, flexWrap: 'wrap', alignItems: 'flex-end' }}>
            <label style={{ minWidth: 170 }}><div style={{ fontSize: 9.5, color: 'rgba(238,233,223,.5)', marginBottom: 4 }}>Date</div>
              <input type="date" value={dailyDate} onChange={(e) => setDailyDate(e.target.value)} style={input} /></label>
            <div style={{ fontSize: 11, color: 'rgba(238,233,223,.55)', paddingBottom: 9 }}>Location: {place} ({lat}, {lon}) · {tz}</div>
            <button onClick={runDaily} disabled={dailyBusy} style={{ ...input, width: 'auto', cursor: 'pointer', background: '#7B1D26', borderColor: '#A62A34', fontWeight: 700 }}>
              {dailyBusy ? 'Calculating…' : 'Daily signal'}
            </button>
          </div>

          {daily && (
            <div style={{ marginTop: 14, display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(220px,1fr))', gap: 12 }}>
              <div style={{ background: 'rgba(22,10,12,.72)', border: '1px solid rgba(166,42,52,.25)', borderRadius: 8, padding: '14px 16px' }}>
                <div style={{ fontSize: 10, letterSpacing: '.2em', color: '#B39250' }}>MOON RASHI</div>
                <div style={{ marginTop: 6, fontSize: 20, fontWeight: 700, color: '#F7F5F0' }}>{daily.moon.rashi}</div>
                <div style={{ marginTop: 4, fontSize: 11, color: 'rgba(238,233,223,.55)' }}>Comfort zone</div>
              </div>
              <div style={{ background: 'rgba(22,10,12,.72)', border: '1px solid rgba(166,42,52,.25)', borderRadius: 8, padding: '14px 16px' }}>
                <div style={{ fontSize: 10, letterSpacing: '.2em', color: '#B39250' }}>MOON NAKSHATRA</div>
                <div style={{ marginTop: 6, fontSize: 20, fontWeight: 700, color: '#F7F5F0' }}>{daily.moon.nakshatra}</div>
                <div style={{ marginTop: 4, fontSize: 11, color: 'rgba(238,233,223,.55)' }}>Day pattern · pada {daily.moon.pada}</div>
              </div>
              <div style={{ background: 'rgba(22,10,12,.72)', border: '1px solid rgba(166,42,52,.25)', borderRadius: 8, padding: '14px 16px' }}>
                <div style={{ fontSize: 10, letterSpacing: '.2em', color: '#B39250' }}>NAKSHATRA LORD</div>
                <div style={{ marginTop: 6, fontSize: 20, fontWeight: 700, color: '#F7F5F0' }}>{daily.moon.nakshatra_lord}</div>
                <div style={{ marginTop: 4, fontSize: 11, color: 'rgba(238,233,223,.55)' }}>
                  House {daily.daily_chart.lord_house ?? '—'} in today&apos;s chart{daily.daily_chart.lord_rashi ? ` · ${daily.daily_chart.lord_rashi}` : ''}
                </div>
              </div>
              <div style={{
                background: daily.classification === 'extra_care' ? 'rgba(84,18,25,.5)' : 'rgba(22,10,12,.72)',
                border: `1px solid ${daily.classification === 'extra_care' ? 'rgba(229,62,62,.55)' : 'rgba(179,146,80,.4)'}`,
                borderRadius: 8, padding: '14px 16px',
              }}>
                <div style={{ fontSize: 10, letterSpacing: '.2em', color: '#B39250' }}>DAY SIGNAL</div>
                <div style={{ marginTop: 6, fontSize: 20, fontWeight: 700, color: daily.classification === 'extra_care' ? '#E53E3E' : '#D6BE85' }}>
                  {daily.classification === 'extra_care' ? 'EXTRA CARE' : 'SUPPORTIVE'}
                </div>
                <div style={{ marginTop: 4, fontSize: 11, color: 'rgba(238,233,223,.55)' }}>
                  Houses 6 / 8 / 12 → extra care · all others → supportive
                </div>
              </div>
            </div>
          )}

          {daily && (
            <div style={{ marginTop: 10, fontSize: 11, color: 'rgba(238,233,223,.6)', fontFamily: 'ui-monospace,monospace' }}>
              Chart reference: {daily.daily_chart.reference} [{daily.daily_chart.reference_status}] · {daily.daily_chart.reference_time}
            </div>
          )}
        </section>

        {data && (          <>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(260px,1fr))', gap: 12, marginTop: 18 }}>
              {Object.entries(data.channels).map(([key, channel]) => (
                <section key={key} style={{ background: 'rgba(22,10,12,.72)', border: '1px solid rgba(166,42,52,.25)', borderRadius: 8, padding: '14px 16px' }}>
                  <div style={{ fontSize: 10, letterSpacing: '.2em', color: '#B39250', fontFamily: 'ui-monospace,monospace' }}>{LABELS[key]?.title ?? key.toUpperCase()}</div>
                  <div style={{ marginTop: 8, fontSize: 20, fontWeight: 700, color: '#F7F5F0' }}>
                    {channel.value}
                    {channel.context?.paksha ? <span style={{ fontSize: 12, fontWeight: 400, color: 'rgba(238,233,223,.6)' }}> Â· {channel.context.paksha}</span> : null}
                    {channel.context?.pada ? <span style={{ fontSize: 12, fontWeight: 400, color: 'rgba(238,233,223,.6)' }}> Â· pada {channel.context.pada}</span> : null}
                  </div>
                  <div style={{ marginTop: 10, display: 'flex', justifyContent: 'space-between', gap: 10, borderTop: '1px solid rgba(166,42,52,.2)', paddingTop: 8 }}>
                    <span style={{ color: 'rgba(238,233,223,.6)', fontSize: 12 }}>Lord</span>
                    <span style={{ color: '#F7F5F0', fontWeight: 700 }}>{channel.selected_lord || 'â€”'}</span>
                  </div>
                  <div style={{ marginTop: 6, display: 'flex', justifyContent: 'space-between', gap: 10 }}>
                    <span style={{ color: 'rgba(238,233,223,.6)', fontSize: 12 }}>Used for</span>
                    <span style={{ color: '#D6BE85', fontSize: 12, textAlign: 'right' }}>{LABELS[key]?.use ?? channel.interpretation_domain.join(' Â· ')}</span>
                  </div>
                  <div style={{ marginTop: 6, display: 'flex', justifyContent: 'space-between', gap: 10 }}>
                    <span style={{ color: 'rgba(238,233,223,.6)', fontSize: 12 }}>Natal placement</span>
                    <span style={{ color: '#F7F5F0', fontFamily: 'ui-monospace,monospace', fontSize: 12 }}>
                      {channel.natal_placement?.missing_in_chart
                        ? 'not found'
                        : `${channel.natal_placement?.rashi ?? 'â€”'} Â· House ${channel.natal_placement?.house ?? 'â€”'}`}
                    </span>
                  </div>
                  {data.interpretation?.channels?.[key] && (
                    <div style={{ marginTop: 10, borderTop: '1px solid rgba(166,42,52,.2)', paddingTop: 8 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10 }}>
                        <span style={{ color: 'rgba(238,233,223,.6)', fontSize: 12 }}>Dignity</span>
                        <span style={{ color: '#D6BE85', fontSize: 12 }}>{data.interpretation.channels[key].dignity} ?? {data.interpretation.channels[key].assessment}</span>
                      </div>
                      <div style={{ marginTop: 8, fontSize: 11, color: 'rgba(238,233,223,.55)' }}>
                        <strong style={{ color: '#B39250' }}>Base Graha-in-Bhava:</strong> {(data.interpretation.channels[key].base_interpretation ?? []).join(' / ')}
                      </div>
                      <div style={{ marginTop: 6, fontSize: 11, color: 'rgba(238,233,223,.55)' }}>
                        <strong style={{ color: '#B39250' }}>Channel-filtered:</strong> {data.interpretation.channels[key].channel_interpretation}
                      </div>
                      <div style={{ marginTop: 8, fontSize: 12, color: '#EEE9DF', lineHeight: 1.5 }}>
                        <strong style={{ color: '#B39250' }}>Public text:</strong> {data.interpretation.channels[key].public_text}
                      </div>
                    </div>
                  )}
                </section>
              ))}
            </div>

            <details style={{ marginTop: 18 }}>
              <summary style={{ cursor: 'pointer', color: '#D6BE85', fontSize: 12, letterSpacing: '.1em', textTransform: 'uppercase' }}>Raw JSON</summary>              <textarea readOnly value={raw} style={{ width: '100%', height: 300, marginTop: 8, background: '#090909', color: '#EEE9DF', border: '1px solid rgba(166,42,52,.25)', borderRadius: 4, fontFamily: 'ui-monospace,monospace', fontSize: 11, padding: 10 }} />
              <button onClick={() => navigator.clipboard?.writeText(raw)} style={{ ...input, width: 'auto', marginTop: 8, cursor: 'pointer' }}>Copy JSON</button>
            </details>

            <ul style={{ marginTop: 14, paddingLeft: 18, fontSize: 12, color: 'rgba(238,233,223,.55)' }}>
              {data.notes.map((note) => <li key={note}>{note}</li>)}
            </ul>
          </>
        )}
      </div>
    </main>
  );
}
