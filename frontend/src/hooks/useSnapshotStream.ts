import { useState } from 'react'
import type { ArtistContext, AnalysisEvent } from '../types'

export function useSnapshotStream(onComplete: (ctx: ArtistContext) => void) {
  const [snapshotText, setSnapshotText] = useState('')
  const [status, setStatus] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  async function fetchSnapshot(cmId: number) {
    setIsLoading(true)
    setSnapshotText('')
    setStatus('')

    let buffer = ''

    try {
      const res = await fetch('/api/analyze/snapshot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cm_id: cmId }),
      })

      if (!res.ok) throw new Error(`Server error ${res.status}`)

      const reader = res.body!.getReader()
      const decoder = new TextDecoder()
      let partial = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        partial += decoder.decode(value, { stream: true })
        const lines = partial.split('\n')
        partial = lines.pop()!

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            const obj = JSON.parse(line.slice(6)) as AnalysisEvent
            if (obj.type === 'status') {
              setStatus(obj.text)
            } else if (obj.type === 'token') {
              buffer += obj.text
              setSnapshotText(buffer)
            } else if (obj.type === 'done') {
              setStatus('')
              onComplete({
                name: obj.artist_name,
                analysis: buffer,
                session_id: obj.session_id,
              })
            } else if (obj.type === 'error') {
              setStatus('')
              setSnapshotText(`Error: ${obj.text}`)
            }
          } catch {}
        }
      }
    } catch (e) {
      setSnapshotText(`Error: ${(e as Error).message}`)
      setStatus('')
    } finally {
      setIsLoading(false)
    }
  }

  function reset() {
    setSnapshotText('')
    setStatus('')
    setIsLoading(false)
  }

  return { snapshotText, status, isLoading, fetchSnapshot, reset }
}
