import { useState, FormEvent } from 'react'
import { fetchChart } from '../services/api'

export default function BirthForm({ onChart }: { onChart: (chart: any) => void }) {
  const [date, setDate] = useState('')
  const [time, setTime] = useState('')
  const [place, setPlace] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const chart = await fetchChart({ date, time, place })
      onChart(chart)
    } catch (err: any) {
      setError(err.message || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form className="card" onSubmit={submit}>
      <div className="form">
        <div className="field">
          <label>Date of birth</label>
          <input type="date" value={date} onChange={(e) => setDate(e.target.value)} required />
        </div>
        <div className="field">
          <label>Birth time</label>
          <input type="time" value={time} onChange={(e) => setTime(e.target.value)} required />
        </div>
        <div className="field" style={{ gridColumn: '1 / -1' }}>
          <label>Birthplace</label>
          <input type="text" value={place} onChange={(e) => setPlace(e.target.value)} placeholder="Delhi, India" required />
        </div>
      </div>
      <div className="actions">
        <button type="submit" disabled={loading}>{loading ? 'Calculating...' : 'Generate Kundli'}</button>
      </div>
      {error && <div className="error">{error}</div>}
    </form>
  )
}