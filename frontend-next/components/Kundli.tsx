import React, { useMemo, useState } from 'react';
import { Info } from 'lucide-react';
import { KundliData, BirthDetails, NorthHouseData, NorthPlanetPosition } from '../lib/types';
import { NorthIndianChart } from './NorthIndianChart';

interface KundliProps {
  kundli: KundliData;
  birthDetails: BirthDetails;
  ascendant: string;
  className?: string;
}

const abbreviations: Record<string, string> = {
  Sun: 'Su', Moon: 'Mo', Mars: 'Ma', Mercury: 'Me', Jupiter: 'Ju', Venus: 'Ve',
  Saturn: 'Sa', Rahu: 'Ra', Ketu: 'Ke', Uranus: 'Ur', Neptune: 'Ne', Pluto: 'Pl',
};

function toNorthPlanet(
  name: string,
  house: number,
  position?: { degree?: string; isRetrograde?: boolean },
): NorthPlanetPosition {
  return {
    key: name,
    name: abbreviations[name] || name.slice(0, 2),
    englishName: name,
    symbol: abbreviations[name] || name.slice(0, 2),
    degreeInSign: Number.parseFloat(position?.degree || '0') || 0,
    isRetrograde: Boolean(position?.isRetrograde),
    isCombust: false,
    dignity: 'Neutral',
    house,
  };
}

export function Kundli({ kundli, birthDetails, ascendant, className = '' }: KundliProps) {
  const [selectedHouse, setSelectedHouse] = useState<number | null>(null);

  const { houses, ascendantPosition } = useMemo(() => {
    const byName = new Map(kundli.planetaryPositions.map((planet) => [planet.planet, planet]));
    const mappedHouses: NorthHouseData[] = kundli.houses.map((house) => ({
      houseNumber: house.houseNumber,
      signNumber: house.signNumber,
      signEnglish: house.sign,
      planets: house.planets.map((name) => {
        const position = byName.get(name as any);
        return toNorthPlanet(name, house.houseNumber, position);
      }),
    }));
    return {
      houses: mappedHouses,
      ascendantPosition: toNorthPlanet('Ascendant', 1, { degree: kundli.ascendantDegree }),
    };
  }, [kundli]);

  return (
    <div className={`relative w-full ${className}`}>
      <div className="relative rounded-xl border border-[#B4232F]/35 bg-white p-3 sm:p-6">

        <div className="mb-5 grid grid-cols-2 gap-3 border-b border-[#B4232F]/20 pb-4 text-xs sm:grid-cols-4">
          <div><span className="font-mono text-[9px] uppercase tracking-widest text-[#B4232F]">DATE OF BIRTH</span><div className="mt-1 font-mono text-xs font-medium text-[#151719] sm:text-[13px]">{birthDetails.date}</div></div>
          <div><span className="font-mono text-[9px] uppercase tracking-widest text-[#B4232F]">TIME (LOCAL)</span><div className="mt-1 font-mono text-xs font-medium text-[#151719] sm:text-[13px]">{birthDetails.time}</div></div>
          <div><span className="font-mono text-[9px] uppercase tracking-widest text-[#B4232F]">COORDINATE FIX</span><div className="mt-1 truncate font-mono text-xs font-medium text-[#151719] sm:text-[13px]">{birthDetails.place}</div></div>
          <div><span className="font-mono text-[9px] uppercase tracking-widest text-[#B4232F]">ASCENDANT / LAGNA</span><div className="mt-1 truncate font-mono text-xs font-semibold text-[#B4232F] sm:text-[13px]">{kundli.ascendantSign} {kundli.ascendantDegree}</div></div>
        </div>

        <NorthIndianChart houses={houses} ascendant={ascendantPosition} selectedHouse={selectedHouse} onSelectHouse={setSelectedHouse} />

        <div className="mt-5 flex flex-col items-center justify-between gap-3 border-t border-[#B4232F]/20 pt-4 text-xs font-mono text-[#151719]/65 sm:flex-row">
          <div className="flex items-center gap-2"><Info className="h-4 w-4 text-[#B4232F]" />{selectedHouse ? `HOUSE ${selectedHouse} selected` : 'Click or tap any house to inspect it.'}</div>
          <span className="text-[10px] font-semibold uppercase tracking-wider text-[#B4232F]">TRADITIONAL NORTH INDIAN CARTOGRAPHY</span>
        </div>
      </div>
    </div>
  );
}
