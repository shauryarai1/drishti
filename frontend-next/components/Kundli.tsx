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

function toNorthPlanet(name: string, house: number, degree?: string): NorthPlanetPosition {
  return {
    key: name,
    name: abbreviations[name] || name.slice(0, 2),
    englishName: name,
    symbol: abbreviations[name] || name.slice(0, 2),
    degreeInSign: Number.parseFloat(degree || '0') || 0,
    isRetrograde: false,
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
        return toNorthPlanet(name, house.houseNumber, position?.degree);
      }),
    }));
    return {
      houses: mappedHouses,
      ascendantPosition: toNorthPlanet('Ascendant', 1, kundli.ascendantDegree),
    };
  }, [kundli]);

  return (
    <div className={`relative w-full ${className}`}>
      <div className="relative rounded-2xl border border-[#A62A34]/40 bg-gradient-to-b from-[#160A0C]/95 via-[#2B0C11]/70 to-[#090909] p-6 shadow-[0_32px_120px_rgba(0,0,0,0.95)] sm:p-10">
        <div className="absolute left-4 top-4 h-3.5 w-3.5 rounded-full border border-[#7B1D26] bg-[#B39250]" />
        <div className="absolute right-4 top-4 h-3.5 w-3.5 rounded-full border border-[#7B1D26] bg-[#B39250]" />
        <div className="absolute bottom-4 left-4 h-3.5 w-3.5 rounded-full border border-[#7B1D26] bg-[#B39250]" />
        <div className="absolute bottom-4 right-4 h-3.5 w-3.5 rounded-full border border-[#7B1D26] bg-[#B39250]" />

        <div className="mb-6 grid grid-cols-2 gap-3 border-b border-[#A62A34]/20 pb-5 text-xs sm:grid-cols-4">
          <div><span className="font-mono text-[9px] uppercase tracking-widest text-[#B39250]">DATE OF BIRTH</span><div className="mt-1 font-mono text-xs font-medium text-[#F7F5F0] sm:text-[13px]">{birthDetails.date}</div></div>
          <div><span className="font-mono text-[9px] uppercase tracking-widest text-[#B39250]">TIME (LOCAL)</span><div className="mt-1 font-mono text-xs font-medium text-[#F7F5F0] sm:text-[13px]">{birthDetails.time}</div></div>
          <div><span className="font-mono text-[9px] uppercase tracking-widest text-[#B39250]">COORDINATE FIX</span><div className="mt-1 truncate font-mono text-xs font-medium text-[#F7F5F0] sm:text-[13px]">{birthDetails.place}</div></div>
          <div><span className="font-mono text-[9px] uppercase tracking-widest text-[#B39250]">ASCENDANT / LAGNA</span><div className="mt-1 truncate font-mono text-xs font-semibold text-[#A62A34] sm:text-[13px]">{kundli.ascendantSign} {kundli.ascendantDegree}</div></div>
        </div>

        <NorthIndianChart houses={houses} ascendant={ascendantPosition} selectedHouse={selectedHouse} onSelectHouse={setSelectedHouse} />

        <div className="mt-6 flex flex-col items-center justify-between gap-3 border-t border-[#A62A34]/20 pt-4 text-xs font-mono text-[#EEE9DF]/70 sm:flex-row">
          <div className="flex items-center gap-2"><Info className="h-4 w-4 text-[#B39250]" />{selectedHouse ? `HOUSE ${selectedHouse} selected` : 'Click or tap any house to inspect it.'}</div>
          <span className="text-[10px] font-semibold uppercase tracking-wider text-[#A62A34]">TRADITIONAL NORTH INDIAN CARTOGRAPHY</span>
        </div>
      </div>
    </div>
  );
}
