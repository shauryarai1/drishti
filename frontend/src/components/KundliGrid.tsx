import type { ChartResponse } from '../types/chart'

const RASHI_NAMES = [
  'Aries','Taurus','Gemini','Cancer','Leo','Virgo',
  'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces'
]

const ABBREVIATIONS: Record<string, string> = {
  Sun: 'Su', Moon: 'Mo', Mercury: 'Me', Venus: 'Ve', Mars: 'Ma',
  Jupiter: 'Ju', Saturn: 'Sa', Rahu: 'Ra', Ketu: 'Ke',
  Uranus: 'Ur', Neptune: 'Ne', Pluto: 'Pl'
}

export default function KundliGrid({ chart }: { chart: ChartResponse }) {
  const houseMap = new Map((chart.houses || []).map(h => [h.number, h.sign]))
  const mainPlanetsByHouse = new Map<number, typeof chart.planets>()
  const extraPlanetsByHouse = new Map<number, typeof chart.extra_planets>()

  for (const p of chart.planets || []) {
    const list = mainPlanetsByHouse.get(p.house) || []
    list.push(p)
    mainPlanetsByHouse.set(p.house, list)
  }

  for (const p of chart.extra_planets || []) {
    const list = extraPlanetsByHouse.get(p.house) || []
    list.push(p)
    extraPlanetsByHouse.set(p.house, list)
  }

  const boxes = Array.from({ length: 12 }, (_, i) => {
    const number = i + 1
    const signName = houseMap.get(number) || RASHI_NAMES[i]
    const signIndex = RASHI_NAMES.indexOf(signName)
    const mainPlanets = mainPlanetsByHouse.get(number) || []
    const extraPlanets = extraPlanetsByHouse.get(number) || []
    return { number, signName, signIndex: signIndex >= 0 ? signIndex + 1 : number, mainPlanets, extraPlanets }
  })

  return (
    <div className="grid">
      {boxes.map(box => (
        <div key={box.number} className={"box" + (box.number === 1 ? " lagna" : "")}>
          <div className="box-header">
            <span className="house-number">House {box.number}</span>
            <span className="sign-number">{box.signIndex}</span>
          </div>
          <div className="sign-name">{box.signName}</div>
          <div className="planets">
            {box.mainPlanets.map(p => (
              <span key={p.name} className="planet">{ABBREVIATIONS[p.name] || p.name}</span>
            ))}
          </div>
          {box.extraPlanets.length > 0 && (
            <div className="planets extra">
              {box.extraPlanets.map(p => (
                <span key={p.name} className="planet extra-planet">{ABBREVIATIONS[p.name] || p.name}</span>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
