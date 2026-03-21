import { useState } from 'react'
import type { Artist } from '../types'

export function useArtistSearch() {
  const [results, setResults] = useState<Artist[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function search(q: string) {
    if (!q.trim()) return
    setIsLoading(true)
    setError(null)
    try {
      const res = await fetch(`/api/search/artists?q=${encodeURIComponent(q)}`)
      if (!res.ok) throw new Error(`Server error ${res.status}`)
      const data: Artist[] = await res.json()
      setResults(data)
    } catch (e) {
      setError((e as Error).message)
      setResults([])
    } finally {
      setIsLoading(false)
    }
  }

  return { results, isLoading, error, search }
}
