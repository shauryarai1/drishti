import React from 'react';
import { NorthHouseData as HouseData, NorthPlanetPosition as PlanetPosition } from '../lib/types';

interface NorthIndianChartProps {
  houses: HouseData[];
  ascendant: PlanetPosition;
  selectedHouse?: number | null;
  onSelectHouse?: (houseNumber: number) => void;
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
      <div className="relative w-full max-w-[680px] aspect-square bg-white p-0">
        <svg
          id="north-indian-kundli-svg"
          viewBox="0 0 500 500"
          className="kundli-archive-svg block h-auto w-full"
        >
          {/* Flat printed chart surface. */}
          <rect width="500" height="500" fill="#ffffff" />

          {/* 12 House Polygons */}
          {housePolygons.map((poly) => {
            const house = houses[poly.houseNum - 1];
            const isSelected = selectedHouse === poly.houseNum;
            const isKendra = [1, 4, 7, 10].includes(poly.houseNum);
            const isTrikona = [5, 9].includes(poly.houseNum);
            const isDusthana = [6, 8, 12].includes(poly.houseNum);

            const fillUrl = isSelected ? '#fff1f1' : (isKendra || isTrikona || isDusthana ? '#fffafa' : '#ffffff');

            return (
              <g
                key={`house-${poly.houseNum}`}
                className={onSelectHouse ? 'cursor-pointer transition-all duration-150' : 'transition-all duration-150'}
                onClick={() => onSelectHouse?.(poly.houseNum)}
              >
                {/* House Compartment Polygon */}
                <polygon
                  points={poly.points}
                  fill={fillUrl}
                  stroke="none"
                  strokeWidth="0"
                  className="transition-all hover:fill-[#fff1f1]"
                />

                {/* Small printed Rashi number, without a medallion. */}
                <text className="kundli-rashi-label pointer-events-none"
                    x={poly.rashiPos.x}
                    y={poly.rashiPos.y}
                    textAnchor="middle"
                    dominantBaseline="central"
                    fill={isSelected ? '#ffffff' : '#B4232F'}
                    fontSize="12"
                    fontWeight="800"
                    fontFamily="sans-serif"
                >{house?.signNumber}</text>

                {/* Planets occupying this house */}
                <g
                  transform={`translate(${poly.contentPos.x}, ${poly.contentPos.y})`}
                  className="kundli-planet-label pointer-events-none"
                >
                  {house?.planets.map((planet, pIdx) => {
                    const total = house.planets.length;
                    const slots = total === 1
                      ? [[0, 0]]
                      : total === 2
                        ? [[-23, 0], [23, 0]]
                        : total === 3
                          ? [[-25, -12], [25, -12], [0, 16]]
                          : [[-25, -13], [25, -13], [-25, 14], [25, 14], [0, 38]];
                    const [dx, dy] = slots[pIdx] ?? [0, 38 + (pIdx - 4) * 18];

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
                          y="-5"
                          textAnchor="middle"
                          dominantBaseline="central"
                          fill="#151719"
                          fontSize="14"
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

                        <text className="kundli-degree-text"
                          x="0"
                          y="11"
                          textAnchor="middle"
                          dominantBaseline="central"
                          fill="#B4232F"
                          fontSize="10.5"
                          fontWeight="700"
                          fontFamily="ui-monospace, SFMono-Regular, Menlo, monospace"
                        >
                          {Math.floor(planet.degreeInSign).toString().padStart(2, '0')}°
                        </text>

                      </g>
                    );
                  })}
                </g>
              </g>
            );
          })}

          {/* Golden Geometric Line Overlay - CRISP, LUMINOUS & ACCURATE */}
          <g stroke="#C94B43" strokeWidth="1.8" fill="none" className="pointer-events-none">
            {/* Outer Border */}
            <rect x="2" y="2" width="496" height="496" strokeWidth="2.5" stroke="#B4232F" />

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
            <circle r="18" fill="#ffffff" stroke="#C94B43" strokeWidth="1.5" />
            <circle r="10" fill="#fff1f1" stroke="#B4232F" strokeWidth="1" />
            <circle r="4" fill="#B4232F" />
            <circle r="1.5" fill="#151719" />
          </g>
        </svg>
      </div>

    </div>
  );
};
