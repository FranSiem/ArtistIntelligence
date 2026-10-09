import { useState } from 'react'
import type { SectionId, SectionEvent, Source } from '../types'

export function useSectionStream() {
  const [sections, setSections] = useState<Partial<Record<SectionId, string>>>({})
  const [sectionSources, setSectionSources] = useState<Partial<Record<SectionId, Source[]>>>({})
  const [activeSection, setActiveSection] = useState<SectionId | null>(null)
  const [activeBuffer, setActiveBuffer] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [isDone, setIsDone] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function generateSections(sessionId: string, selectedSections: SectionId[]) {
    setIsStreaming(true)
    setIsDone(false)
    setError(null)
    setSections({})
    setSectionSources({})
    setActiveSection(null)
    setActiveBuffer('')

    let currentBuffer = ''

    try {
      const res = await fetch('/api/analyze/sections', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, sections: selectedSections }),
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
            const obj = JSON.parse(line.slice(6)) as SectionEvent

            if (obj.type === 'section_start') {
              currentBuffer = ''
              setActiveSection(obj.section)
              setActiveBuffer('')

            } else if (obj.type === 'token') {
              currentBuffer += obj.text
              setActiveBuffer(currentBuffer)

            } else if (obj.type === 'section_done') {
              const completed = currentBuffer
              setSections(prev => ({ ...prev, [obj.section]: completed }))
              currentBuffer = ''
              setActiveSection(null)
              setActiveBuffer('')

            } else if (obj.type === 'section_sources') {
              // Sources arrive after section_done — store keyed by section ID
              setSectionSources(prev => ({ ...prev, [obj.section]: obj.sources }))

            } else if (obj.type === 'all_done') {
              setIsDone(true)

            } else if (obj.type === 'error') {
              setError(obj.text)
            }
          } catch {}
        }
      }
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setIsStreaming(false)
      setActiveSection(null)
      setActiveBuffer('')
    }
  }

  function reset() {
    setSections({})
    setSectionSources({})
    setActiveSection(null)
    setActiveBuffer('')
    setIsStreaming(false)
    setIsDone(false)
    setError(null)
  }

  return {
    sections,
    sectionSources,
    activeSection,
    activeBuffer,
    isStreaming,
    isDone,
    error,
    generateSections,
    reset,
  }
}
