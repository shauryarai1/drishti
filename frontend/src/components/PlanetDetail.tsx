type Planet = {
  name: string
  longitude: number
  sign: string
  house: number
  degree: number
  nakshatra?: string
  pada?: number
  source: string
  status: string
}

export default function PlanetDetail({ planet }: { planet: Planet | null }) {
  if (!planet) return null
  return (
    <div className="planet-detail">
      <div style={{ fontWeight: 600, marginBottom: 6 }}>{planet.name}</div>
      <div>House: {planet.house}</div>
      <div>Sign: {planet.sign}</div>
      <div>Longitude: {planet.longitude.toFixed(4)}°</div>
      <div>Degree in sign: {planet.degree.toFixed(4)}°</div>
      {planet.nakshatra && <div>Nakshatra: {planet.nakshatra} (Pada {planet.pada})</div>}
      <div>Source: {planet.source}</div>
      <div>Status: {planet.status}</div>
    </div>
  )
}