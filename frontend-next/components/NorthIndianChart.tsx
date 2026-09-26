import React from 'react';
import { NorthHouseData as HouseData, NorthPlanetPosition as PlanetPosition } from '../lib/types';
import { HOUSE_GEOMETRY, planetSlots, polygonPoints } from './kundli/chartGeometry';

interface NorthIndianChartProps {
  houses: HouseData[];
  ascendant: PlanetPosition;
  selectedHouse?: number | null;
  onSelectHouse?: (houseNumber: number) => void;
  highlightPlanet?: string | null;
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
  return (
    <div className="flex w-full flex-col items-center select-none">
      <div className="relative w-full max-w-[680px] aspect-[0.862] bg-white p-0 sm:aspect-square">
        <svg
          id="north-indian-kundli-svg"
          viewBox="0 0 500 500"
          className="kundli-archive-svg block h-full w-full"
          preserveAspectRatio="none"
        >
          {/* Flat printed chart surface. */}
          <rect width="500" height="500" fill="#ffffff" />

          {/* 12 House Polygons */}
          {Object.keys(HOUSE_GEOMETRY).map((key) => {
            const houseNum = Number(key);
            const geometry = HOUSE_GEOMETRY[houseNum];
            const house = houses[houseNum - 1];
            const isSelected = selectedHouse === houseNum;
            const isKendra = [1, 4, 7, 10].includes(houseNum);
            const isTrikona = [5, 9].includes(houseNum);
            const isDusthana = [6, 8, 12].includes(houseNum);

            const fillUrl = isSelected ? '#fff1f1' : (isKendra || isTrikona || isDusthana ? '#fffafa' : '#ffffff');

            return (
              <g
                key={`house-${houseNum}`}
                className={onSelectHouse ? 'cursor-pointer transition-all duration-150' : 'transition-all duration-150'}
                onClick={() => onSelectHouse?.(houseNum)}
              >
                <polygon
                  points={polygonPoints(houseNum)}
                  fill={fillUrl}
                  stroke="none"
                  strokeWidth="0"
                  className="transition-all hover:fill-[#fff1f1]"
                />

                {/* Small printed Rashi number, without a medallion. */}
                <text className="kundli-rashi-label pointer-events-none"
                  x={geometry.rashi[0]}
                  y={geometry.rashi[1]}
                  textAnchor="middle"
                  dominantBaseline="central"
                  fill={isSelected ? '#ffffff' : '#B4232F'}
                  fontSize="12"
                  fontWeight="800"
                  fontFamily="sans-serif"
                >{house?.signNumber}</text>

                {/* Planets occupying this house. Each label is a single compact
                    line (abbreviation + tiny degree + status marker) and sits on
                    a verified slot so conjunctions never overlap. */}
                <g className="kundli-planet-label pointer-events-none">
                  {(house?.planets ?? []).map((planet, pIdx) => {
                    const [x, y] = planetSlots(houseNum, house.planets.length)[pIdx] ?? geometry.slots[0];

                    const meta = PLANET_SYMBOLS[planet.englishName] || {
                      abbr: planet.name.slice(0, 2),
                      symbol: '●',
                      color: '#f1f5f9',
                    };

                    const isRetro = planet.isRetrograde;
                    const isExalted = planet.dignity === 'Exalted';
                    const isDebilitated = planet.dignity === 'Debilitated';
                    const isCombust = planet.isCombust;
                    const highlighted = highlightPlanet === planet.englishName;

                    return (
                      <g key={planet.key} transform={`translate(${x}, ${y})`}>
                        <text className="kundli-planet-text"
                          x="0"
                          y="0"
                          textAnchor="middle"
                          dominantBaseline="central"
                          fill={highlighted ? '#7B1D26' : '#151719'}
                          fontSize="14"
                          fontWeight="700"
                          fontFamily="sans-serif"
                        >
                          {meta.abbr}
                          <tspan className="kundli-degree-text" fill="#B4232F" fontSize="9.5" fontWeight="700" fontFamily="ui-monospace, SFMono-Regular, Menlo, monospace">
                            {' '}{Math.floor(planet.degreeInSign).toString().padStart(2, '0')}°
                          </tspan>
                          {isRetro && (
                            <tspan fill="#ef4444" fontSize="9" fontWeight="900">{' R'}</tspan>
                          )}
                          {isExalted && (
                            <tspan fill="#16a34a" fontSize="9" fontWeight="900">{' ↑'}</tspan>
                          )}
                          {isDebilitated && (
                            <tspan fill="#dc2626" fontSize="9" fontWeight="900">{' ↓'}</tspan>
                          )}
                          {isCombust && (
                            <tspan fill="#ea580c" fontSize="9" fontWeight="900">{' c'}</tspan>
                          )}
                        </text>
                      </g>
                    );
                  })}
                </g>
              </g>
            );
          })}

          {/* Thin red geometric overlay. */}
          <g stroke="#C94B43" strokeWidth="1.8" fill="none" className="pointer-events-none">
            <rect x="2" y="2" width="496" height="496" strokeWidth="2.5" stroke="#B4232F" />
            <line x1="0" y1="0" x2="500" y2="500" strokeWidth="2.2" />
            <line x1="0" y1="500" x2="500" y2="0" strokeWidth="2.2" />
            <line x1="250" y1="0" x2="0" y2="250" strokeWidth="2.2" />
            <line x1="0" y1="250" x2="250" y2="500" strokeWidth="2.2" />
            <line x1="250" y1="500" x2="500" y2="250" strokeWidth="2.2" />
            <line x1="500" y1="250" x2="250" y2="0" strokeWidth="2.2" />
          </g>

          {/* Center bindu. */}
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
