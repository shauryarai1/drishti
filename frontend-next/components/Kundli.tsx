import React, { useMemo, useState } from 'react';
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
      <div className="w-full bg-transparent p-0">
        <NorthIndianChart houses={houses} ascendant={ascendantPosition} />
      </div>
    </div>
  );
}
