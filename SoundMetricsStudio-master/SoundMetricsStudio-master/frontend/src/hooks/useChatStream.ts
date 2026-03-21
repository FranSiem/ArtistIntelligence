import { useState, useEffect, useRef } from 'react'
import type { Message, ArtistContext } from '../types'

export function useChatStream(artistContext: ArtistContext | null) {
  const [messages, setMessages] = useState<Message[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => {
    return () => { abortRef.current?.abort() }
  }, [])

  async function sendMessage(text: string) {
    if (!text.trim() || isStreaming) return

    const userMsg: Message = { role: 'user', content: text }
    const history = [...messages, userMsg]
    setMessages([...history, { role: 'assistant', content: '' }])
    setIsStreaming(true)

    abortRef.current = new AbortController()
    let buffer = ''

    try {
      const body: { messages: Message[]; artist_context?: ArtistContext } = { messages: history }
      if (artistContext) body.artist_context = artistContext

      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        signal: abortRef.current.signal,
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
          const raw = line.slice(6)
          if (raw === '[DONE]') break
          try {
            const obj = JSON.parse(raw)
            if (obj.text) {
              buffer += obj.text
              setMessages(prev => {
                const next = [...prev]
                next[next.length - 1] = { role: 'assistant', content: buffer }
                return next
              })
            }
          } catch {}
        }
      }
    } catch (e) {
      if ((e as Error).name !== 'AbortError') {
        setMessages(prev => {
          const next = [...prev]
          next[next.length - 1] = { role: 'assistant', content: `Error: ${(e as Error).message}` }
          return next
        })
      }
    } finally {
      setIsStreaming(false)
    }
  }

  return { messages, isStreaming, sendMessage }
}
