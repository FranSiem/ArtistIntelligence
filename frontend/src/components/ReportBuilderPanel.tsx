import { useState } from 'react'
import type { ArtistContext, ReportSection } from '../types'

interface Props {
  artistContext: ArtistContext | null
}

// ── Default sections (matches mockup exactly) ─────────────────────────────────
const DEFAULT_SECTIONS: ReportSection[] = [
  {
    id: 'baseline',
    icon: '📍',
    title: 'Baseline Reality',
    status: 'done',
    summary: 'Steady growth across 6 platforms. YouTube sentiment outperforms indie-pop average by 17 points.',
    selected: true,
  },
  {
    id: 'fanbase',
    icon: '👥',
    title: 'Fanbase Intelligence',
    status: 'done',
    summary: '12 community anchors identified. London and Lagos are top cities by engagement rate.',
    selected: true,
  },
  {
    id: 'blindspot',
    icon: '🔍',
    title: 'Critical Blindspot',
    status: 'building',
    summary: 'Organic Lagos audience identified — unaddressed diaspora signal not present in benchmarking artists.',
    selected: false,
  },
  {
    id: 'revenue',
    icon: '💷',
    title: 'Revenue & Royalties',
    status: 'locked',
    summary: 'Upload PRS statements to unlock',
    selected: false,
    lockReason: 'Upload PRS statements to unlock',
  },
  {
    id: 'pivot',
    icon: '🎯',
    title: 'Strategic Pivot',
    status: 'locked',
    summary: 'Continue the conversation to unlock',
    selected: false,
    lockReason: 'Continue the conversation to unlock',
  },
]

// ── Status badge ──────────────────────────────────────────────────────────────
function SectionBadge({ status }: { status: ReportSection['status'] }) {
  const map: Record<ReportSection['status'], { cls: string; label: string }> = {
    done:     { cls: 'badge-green', label: 'Done' },
    building: { cls: 'badge-pink',  label: 'Building' },
    pending:  { cls: 'badge-amber', label: 'Pending' },
    locked:   { cls: 'badge-muted', label: 'Pending' },
  }
  const { cls, label } = map[status]
  return <span className={`badge ${cls}`}>{label}</span>
}

// ── Main component ────────────────────────────────────────────────────────────
export function ReportBuilderPanel({ artistContext }: Props) {
  const [sections, setSections] = useState<ReportSection[]>(DEFAULT_SECTIONS)

  const selectedCount = sections.filter(s => s.selected).length
  const totalUnlocked = sections.filter(s => s.status !== 'locked').length

  function toggleSection(id: string) {
    setSections(prev =>
      prev.map(s =>
        s.id === id && s.status !== 'locked'
          ? { ...s, selected: !s.selected }
          : s
      )
    )
  }

  function handleDownload() {
    if (!artistContext) {
      alert('Load an artist and generate an analysis first.')
      return
    }
    const selected = sections.filter(s => s.selected)
    if (selected.length === 0) {
      alert('Select at least one section to include in your report.')
      return
    }
    // Pro feature placeholder — full download implemented when Pro tier launches
    alert('Report download is a Pro feature. Create a free account to get early access.')
  }

  function handleShare() {
    alert('Share feature coming soon.')
  }

  return (
    <aside id="report-builder-panel" aria-label="Report builder">

      {/* ── Header ──────────────────────────────────────────────────────── */}
      <div className="rb-header">
        <div className="rb-header-top">
          <div className="rb-title">Report builder</div>
          {selectedCount > 0 && (
            <span className="rb-count">{selectedCount} selected</span>
          )}
        </div>
        <div className="rb-sub">Select what to include</div>
        {totalUnlocked > 0 && (
          <div className="rb-sub" style={{ marginTop: '4px' }}>
            {selectedCount} of {totalUnlocked} sections selected
          </div>
        )}
      </div>

      {/* ── Section list ────────────────────────────────────────────────── */}
      <div className="rb-sections">
        {sections.map(section => {
          const isLocked = section.status === 'locked'
          return (
            <div
              key={section.id}
              className={`rb-section-item${isLocked ? ' locked' : ''}`}
              onClick={() => toggleSection(section.id)}
              role={isLocked ? undefined : 'checkbox'}
              aria-checked={isLocked ? undefined : section.selected}
              tabIndex={isLocked ? -1 : 0}
              onKeyDown={e => {
                if (!isLocked && (e.key === 'Enter' || e.key === ' ')) {
                  e.preventDefault()
                  toggleSection(section.id)
                }
              }}
            >
              <div className="rb-section-top">
                <div className="rb-section-left">
                  {/* Checkbox */}
                  <div className={`rb-checkbox${section.selected ? ' checked' : ''}`}>
                    {section.selected && '✓'}
                  </div>
                  <span className="rb-section-icon">{section.icon}</span>
                  <span className="rb-section-name">{section.title}</span>
                </div>
                <SectionBadge status={section.status} />
              </div>
              <div className="rb-section-body">
                {section.lockReason ?? section.summary}
              </div>
            </div>
          )
        })}
      </div>

      {/* ── Footer ──────────────────────────────────────────────────────── */}
      <div className="rb-footer">
        <div className="rb-footer-count">
          {selectedCount} section{selectedCount !== 1 ? 's' : ''} selected
        </div>
        <button
          className="btn btn-primary btn-full"
          onClick={handleDownload}
          disabled={selectedCount === 0}
        >
          Download report
        </button>
        <button
          className="btn btn-ghost btn-full btn-sm"
          onClick={handleShare}
          disabled={selectedCount === 0}
        >
          Share with artist
        </button>
      </div>

    </aside>
  )
}
