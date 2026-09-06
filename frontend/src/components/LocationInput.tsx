import { useState, useRef, useEffect, useCallback } from 'react'

interface PlaceResult {
  display: string
  lat: number
  lon: number
}

interface LocationInputProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  autoFocus?: boolean
}

export default function LocationInput({
  value,
  onChange,
  placeholder = 'Start typing a city…',
  autoFocus,
}: LocationInputProps) {
  const [query, setQuery] = useState(value)
  const [results, setResults] = useState<PlaceResult[]>([])
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [highlightedIndex, setHighlightedIndex] = useState(-1)

  const inputRef = useRef<HTMLInputElement>(null)
  const listRef = useRef<HTMLDivElement>(null)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  // Sync external value changes
  useEffect(() => {
    setQuery(value)
  }, [value])

  const search = useCallback(async (q: string) => {
    if (abortRef.current) abortRef.current.abort()
    if (q.trim().length < 2) {
      setResults([])
      setOpen(false)
      return
    }

    const controller = new AbortController()
    abortRef.current = controller
    setLoading(true)

    try {
      const res = await fetch(
        `/api/places/search?q=${encodeURIComponent(q.trim())}`,
        { signal: controller.signal }
      )
      if (!res.ok) return
      const data = await res.json()
      if (data.status === 'ok' && data.results?.length > 0) {
        setResults(data.results)
        setOpen(true)
        setHighlightedIndex(-1)
      } else {
        setResults([])
        setOpen(false)
      }
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        setResults([])
        setOpen(false)
      }
    } finally {
      setLoading(false)
    }
  }, [])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value
    setQuery(val)
    onChange(val) // keep parent in sync for validation

    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => search(val), 300)
  }

  const selectResult = (place: PlaceResult) => {
    setQuery(place.display)
    onChange(place.display)
    setResults([])
    setOpen(false)
    setHighlightedIndex(-1)
    inputRef.current?.blur()
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!open || results.length === 0) return

    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setHighlightedIndex((i) => (i + 1) % results.length)
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setHighlightedIndex((i) => (i - 1 + results.length) % results.length)
    } else if (e.key === 'Enter' && highlightedIndex >= 0) {
      e.preventDefault()
      selectResult(results[highlightedIndex])
    } else if (e.key === 'Escape') {
      setOpen(false)
      setHighlightedIndex(-1)
    }
  }

  // Close on outside click
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (
        listRef.current &&
        !listRef.current.contains(e.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(e.target as Node)
      ) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  // Cleanup debounce and abort on unmount
  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
      if (abortRef.current) abortRef.current.abort()
    }
  }, [])

  return (
    <div className="location-input-wrap">
      <div className="location-input-field">
        <input
          ref={inputRef}
          type="text"
          className="form-input location-input"
          value={query}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={() => results.length > 0 && setOpen(true)}
          placeholder={placeholder}
          autoFocus={autoFocus}
          autoComplete="off"
          aria-label="Place of birth"
          aria-autocomplete="list"
          aria-expanded={open}
          role="combobox"
        />
        {loading && (
          <div className="location-input-spinner" aria-hidden="true">
            <span className="spinner spinner--dark" />
          </div>
        )}
      </div>

      {open && results.length > 0 && (
        <div className="location-dropdown" ref={listRef} role="listbox">
          {results.map((place, i) => (
            <div
              key={`${place.lat}-${place.lon}-${i}`}
              className={`location-dropdown__item ${
                i === highlightedIndex ? 'location-dropdown__item--active' : ''
              }`}
              role="option"
              aria-selected={i === highlightedIndex}
              onMouseDown={(e) => {
                e.preventDefault() // prevent blur
                selectResult(place)
              }}
              onMouseEnter={() => setHighlightedIndex(i)}
            >
              <svg
                className="location-dropdown__icon"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                aria-hidden="true"
              >
                <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z" />
                <circle cx="12" cy="9" r="2.5" />
              </svg>
              <span className="location-dropdown__text">{place.display}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
