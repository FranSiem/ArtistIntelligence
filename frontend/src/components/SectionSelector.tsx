import { useState } from 'react'
import type { SectionId, SectionCard } from '../types'

const SECTIONS: SectionCard[] = [
  {
    id: 'audience_geography',
    icon: '🌍',
    title: 'Audience & Geography',
    description: 'Where your listeners are and who they are',
    proOnly: false,
  },
  {
    id: 'streaming_performance',
    icon: '📊',
    title: 'Streaming Performance',
    description: 'Track and playlist data across platforms',
    proOnly: false,
  },
  {
    id: 'radio_press',
    icon: '📻',
    title: 'Radio & Press Reach',
    description: 'Airplay, sync, and media coverage signals',
    proOnly: false,
  },
  {
    id: 'collaborators',
    icon: '🤝',
    title: 'Collaborator Opportunities',
    description: 'Named artists and channels to connect with',
    proOnly: false,
  },
  {
    id: 'next_steps',
    icon: '🎯',
    title: 'Next Steps',
    description: 'Specific 30-day recommendations',
    proOnly: false,
  },
  {
    id: 'revenue_royalties',
    icon: '💷',
    title: 'Revenue & Royalties',
    description: 'Earnings signals and monetisation gaps',
    proOnly: true,
  },
]

interface Props {
  onGenerate: (sections: SectionId[]) => void
  isGenerating: boolean
}

export function SectionSelector({ onGenerate, isGenerating }: Props) {
  const [selected, setSelected] = useState<Set<SectionId>>(new Set())

  function toggle(id: SectionId, proOnly: boolean) {
    if (proOnly || isGenerating) return
    setSelected(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  function handleGenerate() {
    if (selected.size === 0 || isGenerating) return
    // Preserve display order
    const ordered = SECTIONS
      .filter(s => selected.has(s.id))
      .map(s => s.id)
    onGenerate(ordered)
  }

  return (
    <div className="section-selector">
      <div className="section-selector-heading">Choose your sections</div>
      <p className="section-selector-sub">
        Select the areas you want to explore. Each generates as a separate insight card.
      </p>

      <div className="section-selector-grid">
        {SECTIONS.map(section => {
          const isSelected = selected.has(section.id)
          const isLocked = section.proOnly
          return (
            <div
              key={section.id}
              className={[
                'section-card',
                isSelected ? 'selected' : '',
                isLocked ? 'locked' : '',
              ].filter(Boolean).join(' ')}
              onClick={() => toggle(section.id, section.proOnly)}
              role={isLocked ? undefined : 'checkbox'}
              aria-checked={isLocked ? undefined : isSelected}
              tabIndex={isLocked ? -1 : 0}
              onKeyDown={e => {
                if (!isLocked && (e.key === 'Enter' || e.key === ' ')) {
                  e.preventDefault()
                  toggle(section.id, section.proOnly)
                }
              }}
              aria-label={isLocked ? `${section.title} — Pro only` : section.title}
            >
              <div className="section-card-top">
                <div className="section-card-left">
                  <span className="section-card-icon">{section.icon}</span>
                  <span className="section-card-title">{section.title}</span>
                </div>
                {isLocked
                  ? <span className="section-pro-badge">Pro</span>
                  : <div className={`section-card-tick${isSelected ? ' checked' : ''}`}>
                      {isSelected && '✓'}
                    </div>
                }
              </div>
              <div className="section-card-desc">{section.description}</div>
            </div>
          )
        })}
      </div>

      <div className="section-generate-row">
        <button
          className="btn btn-primary"
          onClick={handleGenerate}
          disabled={selected.size === 0 || isGenerating}
          style={{ minWidth: '180px' }}
        >
          {isGenerating
            ? 'Generating…'
            : selected.size > 0
              ? `Generate ${selected.size} section${selected.size !== 1 ? 's' : ''}`
              : 'Select sections above'
          }
        </button>
        {selected.size > 0 && !isGenerating && (
          <span className="section-generate-count">
            {selected.size} of {SECTIONS.filter(s => !s.proOnly).length} selected
          </span>
        )}
      </div>
    </div>
  )
}
