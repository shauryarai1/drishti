/**
 * KundliRenderer — North Indian (Diamond) Vedic birth chart.
 *
 * Geometry adapted from VicharaVandana/jyotichart (MIT License) and the
 * vedic-d1-kundli-calculator prototype.  All astrology calculations are
 * supplied by DRISHTI's own engine — this component only draws.
 *
 * Styling: DRISHTI "Indian heritage × luxury technology" aesthetic.
 */

import { useMemo } from 'react'
import type { ChartData, ChartPlanet } from '../types/interpretation'

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const RASHI_NAMES = [
  'Aries','Taurus','Gemini','Cancer','Leo','Virgo',
  'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces',
]

const PLANET_ABBR: Record<string, string> = {
  Sun: 'Su', Moon: 'Mo', Mars: 'Ma', Mercury: 'Me', Jupiter: 'Ju',
  Venus: 'Ve', Saturn: 'Sa', Rahu: 'Ra', Ketu: 'Ke',
  Uranus: 'Ur', Neptune: 'Ne', Pluto: 'Pl',
}

const SVG_SIZE = 500

// ---------------------------------------------------------------------------
// House geometry — North Indian diamond chart (500 × 500 SVG)
// Each house: polygon points + text placement coordinates.
// ---------------------------------------------------------------------------

interface HouseGeo {
  houseNum: number
  points: string
  /** Centre of the Rashi-medallion circle */
  rashiPos: { x: number; y: number }
  /** Centre where planet pills are anchored */
  contentPos: { x: number; y: number }
  /** Small label (house number watermark) */
  labelPos: { x: number; y: number }
}

const HOUSE_GEO: HouseGeo[] = [
  /* 1  Top center diamond (Lagna) */  { houseNum: 1,  points: '250,0 125,125 250,250 375,125',                       rashiPos: { x: 250, y: 62 },  contentPos: { x: 250, y: 140 }, labelPos: { x: 250, y: 92 } },
  /* 2  Top-left upper triangle */      { houseNum: 2,  points: '0,0 250,0 125,125',                                   rashiPos: { x: 135, y: 40 },  contentPos: { x: 105, y: 72 },  labelPos: { x: 165, y: 25 } },
  /* 3  Left upper triangle */          { houseNum: 3,  points: '0,0 125,125 0,250',                                   rashiPos: { x: 40,  y: 135 }, contentPos: { x: 55,  y: 105 }, labelPos: { x: 25,  y: 165 } },
  /* 4  Left center diamond */          { houseNum: 4,  points: '0,250 125,125 250,250 125,375',                       rashiPos: { x: 62,  y: 250 }, contentPos: { x: 140, y: 250 }, labelPos: { x: 92,  y: 250 } },
  /* 5  Left lower triangle */          { houseNum: 5,  points: '0,250 125,375 0,500',                                 rashiPos: { x: 40,  y: 365 }, contentPos: { x: 55,  y: 395 }, labelPos: { x: 25,  y: 335 } },
  /* 6  Bottom-left triangle */         { houseNum: 6,  points: '0,500 125,375 250,500',                               rashiPos: { x: 135, y: 460 }, contentPos: { x: 105, y: 428 }, labelPos: { x: 165, y: 475 } },
  /* 7  Bottom center diamond */        { houseNum: 7,  points: '250,250 125,375 250,500 375,375',                     rashiPos: { x: 250, y: 438 }, contentPos: { x: 250, y: 360 }, labelPos: { x: 250, y: 408 } },
  /* 8  Bottom-right triangle */        { houseNum: 8,  points: '250,500 375,375 500,500',                             rashiPos: { x: 365, y: 460 }, contentPos: { x: 395, y: 428 }, labelPos: { x: 335, y: 475 } },
  /* 9  Right lower triangle */         { houseNum: 9,  points: '375,375 500,250 500,500',                             rashiPos: { x: 460, y: 365 }, contentPos: { x: 445, y: 395 }, labelPos: { x: 475, y: 335 } },
  /* 10 Right center diamond */         { houseNum: 10, points: '250,250 375,125 500,250 375,375',                     rashiPos: { x: 438, y: 250 }, contentPos: { x: 360, y: 250 }, labelPos: { x: 408, y: 250 } },
  /* 11 Right upper triangle */         { houseNum: 11, points: '375,125 500,0 500,250',                               rashiPos: { x: 460, y: 135 }, contentPos: { x: 445, y: 105 }, labelPos: { x: 475, y: 165 } },
  /* 12 Top-right triangle */           { houseNum: 12, points: '250,0 500,0 375,125',                                 rashiPos: { x: 365, y: 40 },  contentPos: { x: 395, y: 72 },  labelPos: { x: 335, y: 25 } },
]

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

interface Props {
  chart: ChartData
}

export default function KundliRenderer({ chart }: Props) {
  const ascSign = chart.ascendant_sign || 'Aries'
  const ascIdx = RASHI_NAMES.indexOf(ascSign)

  // Group all planets (main + extra) by house
  const planetsByHouse = useMemo(() => {
    const map = new Map<number, ChartPlanet[]>()
    const allPlanets = [
      ...chart.planets,
      ...(chart.extra_planets || []),
    ]
    for (const p of allPlanets) {
      const list = map.get(p.house) || []
      list.push(p)
      map.set(p.house, list)
    }
    return map
  }, [chart.planets, chart.extra_planets])

  // Rashi number per house (1-based), derived from the ascendant
  const houseRashiNum = useMemo(() => {
    return Array.from({ length: 12 }, (_, i) => ((ascIdx + i) % 12) + 1)
  }, [ascIdx])

  return (
    <div className="kundli-renderer-wrap">
      <svg
        viewBox={`0 0 ${SVG_SIZE} ${SVG_SIZE}`}
        className="kundli-renderer-svg"
        xmlns="http://www.w3.org/2000/svg"
        role="img"
        aria-label="North Indian Vedic birth chart (Kundli)"
      >
        {/* ─── Background ─── */}
        <rect width={SVG_SIZE} height={SVG_SIZE} fill="var(--kundli-bg, #111115)" rx="8" />

        {/* ─── Subtle house fills ─── */}
        {HOUSE_GEO.map((geo) => {
          const isAsc = geo.houseNum === 1
          return (
            <polygon
              key={`fill-${geo.houseNum}`}
              points={geo.points}                fill={
                isAsc
                  ? 'rgba(230,183,46,0.06)'
                  : geo.houseNum % 2 === 0
                    ? 'rgba(230,183,46,0.02)'
                    : 'transparent'
              }
            />
          )
        })}

        {/* ─── Geometric line overlay (borders, diagonals, diamond) ─── */}
        <g stroke="var(--kundli-line, rgba(245,197,66,0.35))" strokeWidth="1.5" fill="none">
          {/* Outer border */}
          <rect x="3" y="3" width={SVG_SIZE - 6} height={SVG_SIZE - 6} rx="6" strokeWidth="2" stroke="var(--kundli-line-strong, rgba(23,19,15,0.40))" />
          <rect x="7" y="7" width={SVG_SIZE - 14} height={SVG_SIZE - 14} rx="4" strokeWidth="0.8" stroke="var(--kundli-line, rgba(23,19,15,0.15))" />

          {/* Corner-to-corner diagonals */}
          <line x1="0" y1="0" x2={SVG_SIZE} y2={SVG_SIZE} strokeWidth="1.5" />
          <line x1="0" y1={SVG_SIZE} x2={SVG_SIZE} y2="0" strokeWidth="1.5" />

          {/* Inner diamond connecting midpoints */}
          <line x1="250" y1="0" x2="0" y2="250" strokeWidth="1.5" />
          <line x1="0" y1="250" x2="250" y2={SVG_SIZE} strokeWidth="1.5" />
          <line x1="250" y1={SVG_SIZE} x2={SVG_SIZE} y2="250" strokeWidth="1.5" />
          <line x1={SVG_SIZE} y1="250" x2="250" y2="0" strokeWidth="1.5" />
        </g>

        {/* ─── House labels + Rashi medallions + Planets ─── */}
        {HOUSE_GEO.map((geo) => {
          const houseNum = geo.houseNum
          const rashiNum = houseRashiNum[houseNum - 1]
          const isAsc = houseNum === 1
          const planets = planetsByHouse.get(houseNum) || []

          return (
            <g key={`house-${houseNum}`}>
              {/* House watermark label */}
              <text
                x={geo.labelPos.x}
                y={geo.labelPos.y}
                textAnchor="middle"
                dominantBaseline="central"
                fill="var(--kundli-label, rgba(245,197,66,0.18))"
                fontSize="9"
                fontWeight="600"
                fontFamily="var(--font-body, sans-serif)"
                className="kundli-no-select"
              >
                H{houseNum}
              </text>

              {/* Rashi number medallion */}
              <g transform={`translate(${geo.rashiPos.x}, ${geo.rashiPos.y})`} className="kundli-no-select">
                <circle
                  r="11"
                  fill={isAsc ? 'var(--kundli-asc-bg, #2d1c08)' : 'var(--kundli-rashi-bg, #1a1714)'}
                  stroke={isAsc ? 'var(--kundli-asc-stroke, #F5C542)' : 'var(--kundli-rashi-stroke, rgba(245,197,66,0.5))'}
                  strokeWidth="1.2"
                />
                <text
                  textAnchor="middle"
                  dominantBaseline="central"
                  fill={isAsc ? 'var(--kundli-asc-text, #FFFDF7)' : 'var(--kundli-rashi-text, #F5C542)'}
                  fontSize="11"
                  fontWeight="800"
                  fontFamily="var(--font-body, sans-serif)"
                >
                  {rashiNum}
                </text>
              </g>

              {/* Lagna badge on House 1 */}
              {isAsc && (
                <g transform={`translate(${geo.rashiPos.x}, ${geo.rashiPos.y - 22})`} className="kundli-no-select">
                  <rect
                    x="-32"
                    y="-8"
                    width="64"
                    height="16"
                    rx="8"
                    fill="var(--kundli-asc-badge-bg, rgba(245,197,66,0.15))"
                    stroke="var(--kundli-asc-badge-stroke, rgba(245,197,66,0.4))"
                    strokeWidth="0.8"
                  />
                  <text
                    textAnchor="middle"
                    dominantBaseline="central"                     fill="var(--kundli-asc-badge-text, #F5C542)"
                    fontSize="8"
                    fontWeight="700"
                    letterSpacing="1px"
                    fontFamily="var(--font-body, sans-serif)"
                  >
                    LAGNA
                  </text>
                </g>
              )}

              {/* Planets in this house */}
              <g transform={`translate(${geo.contentPos.x}, ${geo.contentPos.y})`}>
                {planets.map((planet, idx) => {
                  const total = planets.length
                  let dx = 0
                  let dy = 0

                  // Dynamic layout: arrange planets without overlap
                  const cols = total <= 2 ? 1 : total <= 4 ? 2 : Math.min(3, total)
                  const rows = Math.ceil(total / cols)
                  const col = idx % cols
                  const row = Math.floor(idx / cols)

                  if (total === 1) {
                    dy = 0
                  } else if (total === 2) {
                    dy = (idx - 0.5) * 18
                  } else if (total === 3) {
                    dy = (idx - 1) * 16
                  } else if (total === 4) {
                    dx = (col - 0.5) * 48
                    dy = (row - 0.5) * 18
                  } else {
                    // 5–12 planets: compact multi-column grid
                    const xSpacing = cols === 2 ? 46 : 42
                    const ySpacing = rows <= 2 ? 16 : rows <= 3 ? 14 : 12
                    dx = (col - (cols - 1) / 2) * xSpacing
                    dy = (row - (rows - 1) / 2) * ySpacing
                  }

                  const abbr = PLANET_ABBR[planet.name] || planet.name.substring(0, 2)

                  return (
                    <g key={planet.name} transform={`translate(${dx}, ${dy})`}>
                      {/* Planet pill background */}
                      <rect
                        x={total > 6 ? '-20' : '-24'}
                        y={total > 6 ? '-7' : '-8'}
                        width={total > 6 ? '40' : '48'}
                        height={total > 6 ? '14' : '16'}
                        rx="4"
                        fill="var(--kundli-planet-bg, rgba(0,0,0,0.5))"
                        stroke="var(--kundli-planet-border, rgba(245,197,66,0.22))"
                        strokeWidth="0.8"
                      />
                      {/* Planet abbreviation */}
                      <text
                        textAnchor="middle"
                        dominantBaseline="central"
                        fill="var(--kundli-planet-text, #f0ebe3)"
                        fontSize={total > 6 ? '8.5' : '10'}
                        fontWeight="700"
                        fontFamily="var(--font-body, sans-serif)"
                      >
                        {abbr}
                      </text>
                    </g>
                  )
                })}
              </g>
            </g>
          )
        })}

        {/* ─── Auspicious centre bindu ─── */}
        <g transform="translate(250, 250)" className="kundli-no-select">
          <circle r="16" fill="var(--kundli-bindu-outer, #111010)" stroke="var(--kundli-bindu-ring, rgba(245,197,66,0.4))" strokeWidth="1" />
          <circle r="8" fill="var(--kundli-bindu-inner, #1a1610)" stroke="var(--kundli-bindu-ring2, rgba(245,197,66,0.3))" strokeWidth="0.8" />
          <circle r="3" fill="var(--kundli-bindu-dot, #F5C542)" />
        </g>
      </svg>
    </div>
  )
}
