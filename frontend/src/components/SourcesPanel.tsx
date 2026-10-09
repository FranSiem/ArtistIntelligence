import { useState } from 'react'
import type { Source } from '../types'

interface Props {
  sources: Source[]
}

export function SourcesPanel({ sources }: Props) {
  const [expanded, setExpanded] = useState(false)

  if (!sources || sources.length === 0) return null

  return (
    <div className="sources-panel">
      <button
        className="sources-toggle"
        onClick={() => setExpanded(e => !e)}
        aria-expanded={expanded}
      >
        <span className="sources-toggle-icon">{expanded ? '▾' : '▸'}</span>
        📚 Sources ({sources.length})
      </button>

      {expanded && (
        <div className="sources-list">
          {sources.map((src, i) => (
            <div key={i} className="source-item">
              <a
                href={src.url}
                target="_blank"
                rel="noopener noreferrer"
                className="source-item-title"
              >
                {src.title || src.url}
              </a>
              {src.snippet && (
                <p className="source-item-snippet">{src.snippet}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
