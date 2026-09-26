// Backward-compatibility helpers for Kundli panels and saved snapshots.
//
// Older saved Kundli snapshots predate recently added additive fields
// (Navtara, Ascendant Nakshatra, newer Dasha levels). These pure helpers make
// the UI tolerant of missing fields and fill additive fields from an
// authoritative fresh calculation without ever touching the historical natal
// placements. No astrology is calculated here.

export interface NavtaraRow {
  position: number;
  nakshatra: string;
  tara: string;
  specialRoles: string[];
  meaning: string;
}

export function hasNavtara(data: unknown): boolean {
  const value = data as { positions?: unknown } | null | undefined;
  return value != null && Array.isArray(value.positions) && value.positions.length > 0;
}

/** Normalise a Navtara payload into safe rows; never throws on legacy data. */
export function navtaraRows(data: unknown): NavtaraRow[] {
  const value = data as { positions?: unknown } | null | undefined;
  const positions = value && Array.isArray(value.positions) ? value.positions : [];
  return positions
    .filter((item) => item && typeof item === 'object')
    .map((item, index) => {
      const row = item as Record<string, unknown>;
      const roles = Array.isArray(row.specialRoles) ? row.specialRoles.filter((r) => typeof r === 'string') : [];
      return {
        position: typeof row.position === 'number' ? row.position : index + 1,
        nakshatra: typeof row.nakshatra === 'string' ? row.nakshatra : '—',
        tara: typeof row.tara === 'string' ? row.tara : '—',
        specialRoles: roles as string[],
        meaning: typeof row.meaning === 'string' ? row.meaning : '',
      };
    });
}

export function navtaraJanma(data: unknown): string {
  const value = data as { janmaNakshatra?: unknown } | null | undefined;
  return value && typeof value.janmaNakshatra === 'string' ? value.janmaNakshatra : '';
}

export interface AscendantNakshatraView {
  rashi: string;
  nakshatra: string;
  pada: string;
  lord: string;
  available: boolean;
}

/** Ascendant Nakshatra from authoritative fields only; blank when absent. */
export function ascendantNakshatraView(kundli: unknown): AscendantNakshatraView {
  const page = (kundli ?? {}) as {
    summary?: Record<string, unknown>;
    chart?: { ascendant?: Record<string, unknown> };
  };
  const summary = page.summary ?? {};
  const ascendant = page.chart?.ascendant ?? {};
  const pick = (...values: unknown[]): string => {
    for (const value of values) {
      if (typeof value === 'string' && value.trim()) return value;
      if (typeof value === 'number') return String(value);
    }
    return '';
  };
  const nakshatra = pick(ascendant.nakshatra, summary.ascendantNakshatra);
  const pada = pick(ascendant.pada, summary.ascendantPada);
  const lord = pick(ascendant.nakshatraLord, summary.ascendantNakshatraLord);
  return {
    rashi: pick(ascendant.rashi, (summary as { lagnaRashi?: unknown }).lagnaRashi),
    nakshatra,
    pada,
    lord,
    available: Boolean(nakshatra),
  };
}

/**
 * Merge additive fields from a fresh authoritative calculation into a legacy
 * snapshot. The historical snapshot's natal placements (planets, houses,
 * ascendant sign/degree/longitude, dasha balance) are preserved; only missing
 * additive fields are filled.
 */
export function mergeAdditiveFields<T extends Record<string, unknown>>(snapshot: T, fresh: unknown): T {
  const source = (fresh ?? {}) as Record<string, unknown>;
  if (!snapshot || !source) return snapshot;

  const snapshotSummary = (snapshot.summary ?? {}) as Record<string, unknown>;
  const freshSummary = (source.summary ?? {}) as Record<string, unknown>;
  const summary: Record<string, unknown> = { ...snapshotSummary };
  for (const key of ['ascendantNakshatra', 'ascendantPada', 'ascendantNakshatraLord']) {
    if (summary[key] === undefined || summary[key] === null || summary[key] === '') {
      summary[key] = freshSummary[key];
    }
  }

  const snapshotChart = (snapshot.chart ?? {}) as Record<string, unknown>;
  const freshChart = (source.chart ?? {}) as Record<string, unknown>;
  const snapshotAsc = (snapshotChart.ascendant ?? {}) as Record<string, unknown>;
  const freshAsc = (freshChart.ascendant ?? {}) as Record<string, unknown>;
  const ascendant: Record<string, unknown> = { ...snapshotAsc };
  for (const key of ['nakshatra', 'pada', 'nakshatraLord']) {
    if (ascendant[key] === undefined || ascendant[key] === null || ascendant[key] === '') {
      ascendant[key] = freshAsc[key];
    }
  }
  const chart = { ...snapshotChart, ascendant };

  const snapshotDasha = (snapshot.dasha ?? {}) as Record<string, unknown>;
  const freshDasha = (source.dasha ?? {}) as Record<string, unknown>;
  const dasha: Record<string, unknown> = { ...snapshotDasha };
  for (const key of ['currentPratyantardasha', 'currentSookshma', 'currentPrana', 'currentDashaFlow']) {
    if (dasha[key] === undefined || dasha[key] === null) {
      dasha[key] = freshDasha[key];
    }
  }

  const navtara = hasNavtara(snapshot.navtara) ? snapshot.navtara : source.navtara;

  return { ...snapshot, summary, chart, dasha, navtara };
}
