import React from 'react';
import { NorthHouseData as HouseData, NorthPlanetPosition as PlanetPosition } from '../lib/types';

interface NorthIndianChartProps {
  houses: HouseData[];
  ascendant: PlanetPosition;
  selectedHouse: number | null;
  onSelectHouse: (houseNumber: number) => void;
  highlightPlanet?: string | null;
}

interface HousePolygon {
  houseNum: number;
  points: string;
  rashiPos: { x: number; y: number };
  contentPos: { x: number; y: number };
  badgePos: { x: number; y: number };
  labelPos: { x: number; y: number };
}

// Planetary Vedic symbols and English abbreviations
const PLANET_SYMBOLS: Record<string, { abbr: string; symbol: string; color: string }> = {
  Sun: { abbr: 'Su', symbol: '☉', color: '#f59e0b' },
  Moon: { abbr: 'Mo', symbol: '☽', color: '#f8fafc' },
  Mars: { abbr: 'Ma', symbol: '♂', color: '#ef4444' },
  Mercury: { abbr: 'Me', symbol: '☿', color: '#10b981' },
  Jupiter: { abbr: 'Ju', symbol: '♃', color: '#fbbf24' },
  Venus: { abbr: 'Ve', symbol: '♀', color: '#38bdf8' },
  Saturn: { abbr: 'Sa', symbol: '♄', color: '#818cf8' },
  Rahu: { abbr: 'Ra', symbol: '☊', color: '#c084fc' },
  Ketu: { abbr: 'Ke', symbol: '☋', color: '#e879f9' },
  Uranus: { abbr: 'Ur', symbol: '♅', color: '#64748b' },
  Neptune: { abbr: 'Ne', symbol: '♆', color: '#64748b' },
  Pluto: { abbr: 'Pl', symbol: '♇', color: '#64748b' },
};

export const NorthIndianChart: React.FC<NorthIndianChartProps> = ({
  houses,
  ascendant,
  selectedHouse,
  onSelectHouse,
  highlightPlanet,
}) => {
  // Exact geometric coordinates for North Indian D1 Chart (500x500 SVG)
  const housePolygons: HousePolygon[] = [
    {
      houseNum: 1, // Top center diamond (Tanu Bhava / Lagna)
      points: '250,0 125,125 250,250 375,125',
      rashiPos: { x: 250, y: 62 },
      contentPos: { x: 250, y: 140 },
      badgePos: { x: 250, y: 16 },
      labelPos: { x: 250, y: 92 },
    },
    {
      houseNum: 2, // Top-left upper triangle (Dhana Bhava)
      points: '0,0 250,0 125,125',
      rashiPos: { x: 135, y: 40 },
      contentPos: { x: 105, y: 72 },
      badgePos: { x: 55, y: 25 },
      labelPos: { x: 165, y: 25 },
    },
    {
      houseNum: 3, // Left upper triangle (Bhratri Bhava)
      points: '0,0 125,125 0,250',
      rashiPos: { x: 40, y: 135 },
      contentPos: { x: 55, y: 105 },
      badgePos: { x: 25, y: 55 },
      labelPos: { x: 25, y: 165 },
    },
    {
      houseNum: 4, // Left center diamond (Sukha Bhava)
      points: '0,250 125,125 250,250 125,375',
      rashiPos: { x: 62, y: 250 },
      contentPos: { x: 140, y: 250 },
      badgePos: { x: 18, y: 250 },
      labelPos: { x: 92, y: 250 },
    },
    {
      houseNum: 5, // Left lower triangle (Putra Bhava)
      points: '0,250 125,375 0,500',
      rashiPos: { x: 40, y: 365 },
      contentPos: { x: 55, y: 395 },
      badgePos: { x: 25, y: 445 },
      labelPos: { x: 25, y: 335 },
    },
    {
      houseNum: 6, // Bottom-left triangle (Ari Bhava)
      points: '0,500 125,375 250,500',
      rashiPos: { x: 135, y: 460 },
      contentPos: { x: 105, y: 428 },
      badgePos: { x: 55, y: 475 },
      labelPos: { x: 165, y: 475 },
    },
    {
      houseNum: 7, // Bottom center diamond (Yuvati Bhava)
      points: '250,250 125,375 250,500 375,375',
      rashiPos: { x: 250, y: 438 },
      contentPos: { x: 250, y: 360 },
      badgePos: { x: 250, y: 482 },
      labelPos: { x: 250, y: 408 },
    },
    {
      houseNum: 8, // Bottom-right triangle (Randhra Bhava)
      points: '250,500 375,375 500,500',
      rashiPos: { x: 365, y: 460 },
      contentPos: { x: 395, y: 428 },
      badgePos: { x: 445, y: 475 },
      labelPos: { x: 335, y: 475 },
    },
    {
      houseNum: 9, // Right lower triangle (Dharma Bhava)
      points: '375,375 500,250 500,500',
      rashiPos: { x: 460, y: 365 },
      contentPos: { x: 445, y: 395 },
      badgePos: { x: 475, y: 445 },
      labelPos: { x: 475, y: 335 },
    },
    {
      houseNum: 10, // Right center diamond (Karma Bhava)
      points: '250,250 375,125 500,250 375,375',
      rashiPos: { x: 438, y: 250 },
      contentPos: { x: 360, y: 250 },
      badgePos: { x: 482, y: 250 },
      labelPos: { x: 408, y: 250 },
    },
    {
      houseNum: 11, // Right upper triangle (Labha Bhava)
      points: '375,125 500,0 500,250',
      rashiPos: { x: 460, y: 135 },
      contentPos: { x: 445, y: 105 },
      badgePos: { x: 475, y: 55 },
      labelPos: { x: 475, y: 165 },
    },
    {
      houseNum: 12, // Top-right upper triangle (Vyaya Bhava)
      points: '250,0 500,0 375,125',
      rashiPos: { x: 365, y: 40 },
      contentPos: { x: 395, y: 72 },
      badgePos: { x: 445, y: 25 },
      labelPos: { x: 335, y: 25 },
    },
  ];

  return (
    <div className="w-full flex flex-col items-center select-none">
      {/* Chart Interactive Controls */}
      <div className="w-full flex items-center justify-between mb-3 px-2 text-xs text-slate-400">
        <span className="flex items-center gap-1.5 font-mono text-[11px] text-amber-400">
          <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span>
          North Indian Vedic Diamond (Rashi Kundli)
        </span>
      </div>

      {/* SVG Canvas Container with distinct framing */}
      <div className="relative w-full max-w-[520px] aspect-square rounded-2xl p-2 bg-[#F7F5F0] border-2 border-[#B99145]/50 shadow-[0_20px_60px_rgba(0,0,0,0.38)]">
        <svg
          id="north-indian-kundli-svg"
          viewBox="0 0 500 500"
          className="kundli-archive-svg w-full h-full rounded-xl overflow-hidden block"
        >
          <defs>
            {/* Soft Glow for Vedic Geometric Borders */}
            <filter id="goldGlowFilter" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="0" stdDeviation="2" floodColor="#f59e0b" floodOpacity="0.5" />
            </filter>

            {/* Facet Fill Gradients - High Contrast so houses are visible */}
            <linearGradient id="kendraGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#1e1812" />
              <stop offset="100%" stopColor="#251f16" />
            </linearGradient>
            <linearGradient id="trikonaGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#161822" />
              <stop offset="100%" stopColor="#1c202e" />
            </linearGradient>
            <linearGradient id="dusthanaGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#171418" />
              <stop offset="100%" stopColor="#1f181f" />
            </linearGradient>
            <linearGradient id="normalHouseGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#121218" />
              <stop offset="100%" stopColor="#191922" />
            </linearGradient>
            <linearGradient id="selectedHouseGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#3d2108" />
              <stop offset="100%" stopColor="#572e0a" />
            </linearGradient>
          </defs>

          {/* Deep Base Canvas */}
          <rect width="500" height="500" fill="#F7F5F0" />

          {/* 12 House Polygons */}
          {housePolygons.map((poly) => {
            const house = houses[poly.houseNum - 1];
            const isSelected = selectedHouse === poly.houseNum;
            const isKendra = [1, 4, 7, 10].includes(poly.houseNum);
            const isTrikona = [5, 9].includes(poly.houseNum);
            const isDusthana = [6, 8, 12].includes(poly.houseNum);

            let fillUrl = 'url(#normalHouseGrad)';
            if (isKendra) fillUrl = 'url(#kendraGrad)';
            else if (isTrikona) fillUrl = 'url(#trikonaGrad)';
            else if (isDusthana) fillUrl = 'url(#dusthanaGrad)';

            if (isSelected) fillUrl = 'url(#selectedHouseGrad)';

            return (
              <g
                key={`house-${poly.houseNum}`}
                className="cursor-pointer transition-all duration-150"
                onClick={() => onSelectHouse(poly.houseNum)}
              >
                {/* House Compartment Polygon */}
                <polygon
                  points={poly.points}
                  fill={fillUrl}
                  stroke={isSelected ? '#fbbf24' : 'rgba(217,119,6,0.35)'}
                  strokeWidth={isSelected ? '2.5' : '1'}
                  className="hover:brightness-125 transition-all"
                />

                {/* House Identifier Tag (H1, H2.. or Roman) */}
                <text
                  x={poly.labelPos.x}
                  y={poly.labelPos.y}
                  textAnchor="middle"
                  dominantBaseline="central"
                  fill="rgba(148,163,184,0.4)"
                  fontSize="9"
                  fontWeight="600"
                  fontFamily="sans-serif"
                  className="kundli-house-label pointer-events-none"
                >
                  H{poly.houseNum}
                </text>

                {/* Rashi Sign Number Medallion */}
                <g transform={`translate(${poly.rashiPos.x}, ${poly.rashiPos.y})`} className="pointer-events-none">
                  <circle
                    r="11"
                    fill={isSelected ? '#B99145' : '#F7F5F0'}
                    stroke={isSelected ? '#6F1D1B' : '#6F1D1B'}
                    strokeWidth="1.2"
                  />
                  <text className="kundli-rashi-label"
                    textAnchor="middle"
                    dominantBaseline="central"
                    fill={isSelected ? '#151719' : '#6F1D1B'}
                    fontSize="11"
                    fontWeight="800"
                    fontFamily="sans-serif"
                  >
                    {house?.signNumber}
                  </text>
                </g>

                {/* Lagna / Ascendant Crown Badge on House 1 */}
                {poly.houseNum === 1 && (
                  <g transform={`translate(${poly.badgePos.x}, ${poly.badgePos.y + 12})`} className="pointer-events-none">
                    <rect
                      x="-36"
                      y="-9"
                      width="72"
                      height="18"
                      rx="9"
                      fill="#B99145"
                      stroke="#6F1D1B"
                      strokeWidth="1"
                    />
                      <text className="kundli-lagna-label"
                      textAnchor="middle"
                      dominantBaseline="central"
                      fill="#151719"
                      fontSize="9.5"
                      fontWeight="900"
                      letterSpacing="1px"
                      fontFamily="sans-serif"
                    >
                      LAGNA (1)
                    </text>
                  </g>
                )}

                {/* Planets occupying this house */}
                <g
                  transform={`translate(${poly.contentPos.x}, ${poly.contentPos.y})`}
                  className="kundli-planet-label pointer-events-none"
                >
                  {house?.planets.map((planet, pIdx) => {
                    const total = house.planets.length;
                    let dx = 0;
                    let dy = 0;

                    if (total === 1) {
                      dy = 0;
                    } else if (total === 2) {
                      dy = (pIdx - 0.5) * 22;
                    } else if (total === 3) {
                      dy = (pIdx - 1) * 19;
                    } else if (total === 4) {
                      dx = pIdx % 2 === 0 ? -30 : 30;
                      dy = (Math.floor(pIdx / 2) - 0.5) * 22;
                    } else {
                      dx = ((pIdx % 2) - 0.5) * 54;
                      dy = (Math.floor(pIdx / 2) - 1) * 18;
                    }

                    const meta = PLANET_SYMBOLS[planet.englishName] || {
                      abbr: planet.name.slice(0, 2),
                      symbol: '●',
                      color: '#f1f5f9',
                    };

                    const isRetro = planet.isRetrograde;
                    const isExalted = planet.dignity === 'Exalted';
                    const isDebilitated = planet.dignity === 'Debilitated';
                    const isCombust = planet.isCombust;

                    return (
                      <g key={planet.key} transform={`translate(${dx}, ${dy})`}>
                        {/* Planet name and symbol sit directly on the ivory chart surface. */}
                        <text className="kundli-planet-text"
                          x="0"
                          y="-1"
                          textAnchor="middle"
                          dominantBaseline="central"
                          fill="#6F1D1B"
                          fontSize="11"
                          fontWeight="700"
                          fontFamily="sans-serif"
                        >
                          {meta.abbr} {meta.symbol}
                          {isRetro && (
                            <tspan fill="#ef4444" fontSize="9" fontWeight="900">
                              {' '}R
                            </tspan>
                          )}
                          {isExalted && (
                            <tspan fill="#4ade80" fontSize="9" fontWeight="900">
                              {' '}↑
                            </tspan>
                          )}
                          {isDebilitated && (
                            <tspan fill="#f87171" fontSize="9" fontWeight="900">
                              {' '}↓
                            </tspan>
                          )}
                          {isCombust && (
                            <tspan fill="#f97316" fontSize="9" fontWeight="900">
                              {' '}c
                            </tspan>
                          )}
                        </text>

                      </g>
                    );
                  })}
                </g>
              </g>
            );
          })}

          {/* Golden Geometric Line Overlay - CRISP, LUMINOUS & ACCURATE */}
          <g stroke="rgba(120,25,35,0.45)" strokeWidth="2" fill="none" className="pointer-events-none">
            {/* Outer Border */}
            <rect x="2" y="2" width="496" height="496" rx="10" strokeWidth="3" stroke="rgba(120,25,35,0.5)" />
            <rect x="6" y="6" width="488" height="488" rx="8" strokeWidth="1" stroke="#B99145" strokeOpacity="0.55" />

            {/* Corner to Corner Diagonals */}
            <line x1="0" y1="0" x2="500" y2="500" strokeWidth="2.2" />
            <line x1="0" y1="500" x2="500" y2="0" strokeWidth="2.2" />

            {/* Diamond Connecting Midpoints */}
            <line x1="250" y1="0" x2="0" y2="250" strokeWidth="2.2" />
            <line x1="0" y1="250" x2="250" y2="500" strokeWidth="2.2" />
            <line x1="250" y1="500" x2="500" y2="250" strokeWidth="2.2" />
            <line x1="500" y1="250" x2="250" y2="0" strokeWidth="2.2" />
          </g>

          {/* Auspicious Center Bindu (Yantra Central Point) */}
          <g transform="translate(250, 250)" className="pointer-events-none">
            <circle r="18" fill="#F7F5F0" stroke="rgba(120,25,35,0.45)" strokeWidth="1.5" />
            <circle r="10" fill="#EDE2D1" stroke="#B99145" strokeWidth="1" />
            <circle r="4" fill="#6F1D1B" />
            <circle r="1.5" fill="#151719" />
          </g>
        </svg>
      </div>

      {/* Quick Footnote Legend */}
      <div className="mt-3 flex flex-wrap items-center justify-center gap-4 text-[11px] text-slate-400">
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-[#22190f] border border-amber-500 text-amber-300 flex items-center justify-center text-[9px] font-bold">1</span>
          <span>Rashi Sign No.</span>
        </span>
        <span className="flex items-center gap-1.5">
          <span className="text-emerald-400 font-bold">↑ Uchcha</span>
          <span className="text-slate-500">(Exalted)</span>
        </span>
        <span className="flex items-center gap-1.5">
          <span className="text-rose-400 font-bold">↓ Neecha</span>
          <span className="text-slate-500">(Debilitated)</span>
        </span>
        <span className="flex items-center gap-1.5">
          <span className="text-red-400 font-bold">R</span>
          <span className="text-slate-500">(Vakri / Retro)</span>
        </span>
        <span className="flex items-center gap-1.5">
          <span className="text-orange-400 font-bold">c</span>
          <span className="text-slate-500">(Combust)</span>
        </span>
      </div>
    </div>
  );
};
