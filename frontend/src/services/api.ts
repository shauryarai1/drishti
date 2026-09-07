import type { ChartResponse } from '../types/chart'
import type { InterpretationResponse, BirthPayload } from '../types/interpretation'

const API_HOST = import.meta.env.VITE_API_URL?.replace(/\/$/, '')
export const API_BASE = API_HOST ? `${API_HOST}/api` : '/api'

export async function fetchChart(payload: {
  date: string
  time: string
  place: string
  ayanamsa?: string
}): Promise<ChartResponse> {
  const res = await fetch(`${API_BASE}/chart`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || `Server error: ${res.status}`)
  }

  const data = (await res.json()) as ChartResponse
  if (data.status === 'ERROR') {
    throw new Error(data.reason || 'Chart calculation failed')
  }
  return data
}

export async function fetchInterpretation(
  payload: BirthPayload
): Promise<InterpretationResponse> {
  const res = await fetch(`${API_BASE}/interpretation`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  if (!res.ok) {
    let body = ''
    try { body = await res.text() } catch { /* ignore */ }
    console.error(`[DRISHTI] POST /api/interpretation → ${res.status}`, body)
    throw new Error('Something went wrong while preparing your reading.')
  }

  const data = (await res.json()) as InterpretationResponse
  if (data.status === 'error') {
    console.error('[DRISHTI] Interpretation returned error:', data.message)
    throw new Error(data.message || 'Unable to complete your reading.')
  }
  return data
}
