import { useState } from 'react'
import type { AnalysisEvent, ArtistContext } from '../types'

export function useAnalysisStream(onComplete: (ctx: ArtistContext) => void) {
  const [analysisText, setAnalysisText] = useState('')
  const [status, setStatus] = useState('')
  const [isAnalyzing, setIsAnalyzing] = useState(false)

  async function analyze(cmId: number) {
    setIsAnalyzing(true)
    setAnalysisText('')
    setStatus('')

    let buffer = ''

    try {
      const res = await fetch('/api/analyze/artist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cm_id: cmId }),
      })

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
              setAnalysisText(buffer)
            } else if (obj.type === 'done') {
              setStatus('')
              onComplete({ name: obj.artist_name, analysis: buffer })
            } else if (obj.type === 'error') {
              setStatus('')
              setAnalysisText(`**Error:** ${obj.text}`)
            }
          } catch {}
        }
      }
    } catch (e) {
      setAnalysisText(`**Error:** ${(e as Error).message}`)
      setStatus('')
    } finally {
      setIsAnalyzing(false)
    }
  }

  return { analysisText, status, isAnalyzing, analyze }
}
