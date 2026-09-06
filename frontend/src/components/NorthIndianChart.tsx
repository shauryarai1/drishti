/**
 * NorthIndianChart — SVG rendering of a North Indian (diamond) Vedic Kundli.
 *
 * Chart geometry adapted from VicharaVandana/jyotichart (MIT License).
 * Original: https://github.com/VicharaVandana/jyotichart
 *
 * Styling customized for DRISHTI premium aesthetic.
 */

import { useMemo } from 'react'
import type { ChartData, ChartPlanet } from '../types/interpretation'

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const PLANET_SYMBOLS: Record<string, string> = {
  Sun: 'Su', Moon: 'Mo', Mars: 'Ma', Mercury: 'Me', Jupiter: 'Ju',
  Venus: 'Ve', Saturn: 'Sa', Rahu: 'Ra', Ketu: 'Ke',
}

// ---------------------------------------------------------------------------
// House geometry — North Indian diamond chart
//
// 8 visual sections in a 400×400 SVG.
// House 1 (Ascendant) = top diamond, counter-clockwise through 12.
// ---------------------------------------------------------------------------

const SIZE = 400
const C = SIZE / 2 // 200

interface HouseGeo {
  points: string
  signX: number
  signY: number
  zone: { x: number; y: number; w: number; h: number }
}

const GEO: HouseGeo[] = [
  /* 1 */ { points: `${C},10 ${SIZE-10},${C} ${C},${C} 10,${C}`, signX: C, signY: C - 28, zone: { x: C-60, y: C-85, w: 120, h: 60 } },
  /* 2 */ { points: `10,10 ${C},10 10,${C}`, signX: 52, signY: 58, zone: { x: 20, y: 18, w: 100, h: 55 } },
  /* 3 */ { points: `10,${C} ${C},${C} 10,${SIZE-10}`, signX: 58, signY: C, zone: { x: 18, y: C-30, w: 100, h: 55 } },
  /* 4 */ { points: `10,${SIZE-10} ${C},${SIZE-10} ${C},${C}`, signX: C-55, signY: SIZE-50, zone: { x: 20, y: SIZE-85, w: 100, h: 55 } },
  /* 5 */ { points: `${C},${SIZE-10} ${SIZE-10},${C} ${C},${C} 10,${C}`, signX: C, signY: C+55, zone: { x: C-60, y: C+35, w: 120, h: 60 } },
  /* 6 */ { points: `${SIZE-10},${SIZE-10} ${C},${SIZE-10} ${SIZE-10},${C}`, signX: SIZE-55, signY: SIZE-55, zone: { x: SIZE-125, y: SIZE-85, w: 100, h: 55 } },
  /* 7 */ { points: `${SIZE-10},${C} ${C},${C} ${SIZE-10},${SIZE-10}`, signX: SIZE-58, signY: C, zone: { x: SIZE-125, y: C-30, w: 100, h: 55 } },
  /* 8 */ { points: `${SIZE-10},10 ${C},10 ${SIZE-10},${C}`, signX: SIZE-55, signY: 58, zone: { x: SIZE-125, y: 18, w: 100, h: 55 } },
]

// ---------------------------------------------------------------------------
// Mapping: house number → geometry index
// ---------------------------------------------------------------------------

function houseToGeo(houseNum: number): number {
  const h = (houseNum - 1) % 12
  if (h < 8) return h
  // 9→1, 10→2, 11→3, 12→7
  return [1, 2, 3, 7][h - 8]
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

interface Props { chart: ChartData }

export default function NorthIndianChart({ chart }: Props) {
  const ascSign = chart.ascendant_sign || 'Aries'
  const RASHI_NAMES = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
  const ascIdx = RASHI_NAMES.indexOf(ascSign)

  // Group planets by house
  const planetsByHouse = useMemo(() => {
    const map = new Map<number, ChartPlanet[]>()
    for (const p of chart.planets) {
      const list = map.get(p.house) || []
      list.push(p)
      map.set(p.house, list)
    }
    return map
  }, [chart.planets])

  // Sign numbers per house (1-based)
  const houseSigns = useMemo(() => {
    return Array.from({ length: 12 }, (_, i) => ((ascIdx + i) % 12) + 1)
  }, [ascIdx])

  // Planet positions
  const planetPos = useMemo(() => {
    const out: Array<{ p: ChartPlanet; x: number; y: number; sym: string }> = []
    for (const [house, planets] of planetsByHouse) {
      const geo = GEO[houseToGeo(house)]
      if (!geo) continue
      const z = geo.zone
      const cols = Math.min(planets.length, 3)
      const rows = Math.ceil(planets.length / cols)
      const cw = z.w / cols
      const ch = rows > 1 ? Math.min(z.h / rows, 22) : 20
      planets.forEach((p, i) => {
        const col = i % cols
        const row = Math.floor(i / cols)
        out.push({
          p,
          x: z.x + col * cw + cw / 2,
          y: z.y + row * ch + ch / 2,
          sym: PLANET_SYMBOLS[p.name] || p.name.substring(0, 2),
        })
      })
    }
    return out
  }, [planetsByHouse])

  const allHouses = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

  return (
    <div className="kundli-chart-wrap">
      <svg
        viewBox={`0 0 ${SIZE} ${SIZE}`}
        className="kundli-svg"
        xmlns="http://www.w3.org/2000/svg"
        role="img"
        aria-label="North Indian Vedic birth chart"
      >
        {/* Background */}
        <rect x="0" y="0" width={SIZE} height={SIZE} fill="var(--color-bg-card)" rx="4" />

        {/* Outer border */}
        <rect x="2" y="2" width={SIZE - 4} height={SIZE - 4} fill="none" stroke="var(--color-accent-dim)" strokeWidth="1.5" rx="3" />

        {/* House sections */}
        {allHouses.map((hn) => {
          const geo = GEO[houseToGeo(hn)]
          if (!geo) return null
          const signNum = houseSigns[hn - 1]
          const isAsc = hn === 1
          return (
            <g key={hn}>
              <polygon
                points={geo.points}
                fill={isAsc ? 'rgba(230,183,46,0.06)' : 'transparent'}
                stroke="var(--color-accent-dim)"
                strokeWidth="1"
                opacity={0.5}
              />
              <text
                x={geo.signX}
                y={geo.signY}
                textAnchor="middle"
                className="kundli-sign-num"
                fill={isAsc ? 'var(--color-accent)' : 'var(--color-text-muted)'}
                fontSize="14"
                fontWeight={isAsc ? '600' : '400'}
              >
                {String(signNum).padStart(2, '0')}
              </text>
            </g>
          )
        })}

        {/* Planets */}
        {planetPos.map(({ p, x, y, sym }) => (
          <text
            key={p.name}
            x={x}
            y={y}
            textAnchor="middle"
            dominantBaseline="central"
            className="kundli-planet"
            fill="var(--color-text)"
            fontSize="13"
            fontWeight="600"
          >
            {sym}
          </text>
        ))}

        {/* Footer label */}
        <text x={C} y={SIZE - 14} textAnchor="middle" fill="var(--color-text-muted)" fontSize="9" letterSpacing="0.15em">
          NORTH INDIAN
        </text>
      </svg>
    </div>
  )
}
