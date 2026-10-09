import { useRef, useEffect, useState, type KeyboardEvent } from 'react'
import { marked } from 'marked'
import type { Artist, ArtistContext, SectionId } from '../types'
import { useSnapshotStream } from '../hooks/useSnapshotStream'
import { useSectionStream } from '../hooks/useSectionStream'
import { useChatStream } from '../hooks/useChatStream'
import { SnapshotCard } from './SnapshotCard'
import { SectionSelector } from './SectionSelector'
import { MessageBubble } from './MessageBubble'
import { SourcesPanel } from './SourcesPanel'

// Section metadata for result card labels/icons
const SECTION_META: Record<SectionId, { icon: string; title: string }> = {
  audience_geography:    { icon: '🌍', title: 'Audience & Geography' },
  streaming_performance: { icon: '📊', title: 'Streaming Performance' },
  radio_press:           { icon: '📻', title: 'Radio & Press Reach' },
  collaborators:         { icon: '🤝', title: 'Collaborator Opportunities' },
  next_steps:            { icon: '🎯', title: 'Next Steps' },
  revenue_royalties:     { icon: '💷', title: 'Revenue & Royalties' },
}

// Ordered list matches SectionSelector display order
const SECTION_ORDER: SectionId[] = [
  'audience_geography',
  'streaming_performance',
  'radio_press',
  'collaborators',
  'next_steps',
  'revenue_royalties',
]

interface Props {
  artist: Artist | null
  onArtistContext: (ctx: ArtistContext) => void
}

export function ConversationPanel({ artist, onArtistContext }: Props) {
  // Plain useState — setter is stable across renders and safe in async callbacks
  const [artistCtx, setArtistCtx] = useState<ArtistContext | null>(null)

  // Phase 1 — snapshot
  const {
    snapshotText,
    status: snapshotStatus,
    isLoading: isSnapshotLoading,
    fetchSnapshot,
    reset: resetSnapshot,
  } = useSnapshotStream((ctx) => {
    onArtistContext(ctx)
    setArtistCtx(ctx)
  })

  // Phase 2/3 — sections
  const {
    sections: completedSections,
    sectionSources,
    activeSection,
    activeBuffer,
    isStreaming: isSectionStreaming,
    isDone: sectionsAllDone,
    generateSections,
    reset: resetSections,
  } = useSectionStream()

  // Chat — available once snapshot completes
  const { messages, isStreaming: isChatStreaming, sendMessage } = useChatStream(
    snapshotText && !isSnapshotLoading ? artistCtx : null
  )

  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  // Kick off snapshot as soon as an artist is selected
  useEffect(() => {
    if (!artist) return
    resetSnapshot()
    resetSections()
    setArtistCtx(null)
    fetchSnapshot(artist.cm_id)
  }, [artist?.cm_id])

  // Auto-scroll to bottom on any new content
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [snapshotText, completedSections, activeBuffer, messages])

  function autoResize() {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 120) + 'px'
  }

  function handleSend() {
    const el = textareaRef.current
    if (!el) return
    const text = el.value.trim()
    if (!text || isChatStreaming || isSnapshotLoading) return
    sendMessage(text)
    el.value = ''
    autoResize()
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  // Derived state
  const snapshotDone = snapshotText.length > 0 && !isSnapshotLoading
  const hasSectionContent =
    Object.keys(completedSections).length > 0 || activeSection !== null
  const sourceCount = 2

  // ── Empty state ────────────────────────────────────────────────────────────
  if (!artist) {
    return (
      <main id="conversation-panel">
        <div className="conv-empty-state">
          <div className="conv-empty-icon">🎼</div>
          <div className="conv-empty-title">No artist loaded</div>
          <p className="conv-empty-sub">
            Search for an artist to get an instant snapshot and choose your analysis sections.
          </p>
        </div>
        <div className="conv-input-area">
          <div className="conv-input-row">
            <textarea
              ref={textareaRef}
              id="chat-input"
              rows={1}
              placeholder="Load an artist first…"
              disabled
            />
            <button className="btn-icon" disabled aria-label="Send">➤</button>
          </div>
          <p className="conv-footer-text">
            <strong>Artist Intelligence</strong> · Sound Metrics Studio
          </p>
        </div>
      </main>
    )
  }

  return (
    <main id="conversation-panel">

      {/* ── Header ──────────────────────────────────────────────────────── */}
      <div className="conv-header">
        <div className="conv-artist-info">
          <div className="conv-artist-name">{artist.name}</div>
          <div className="conv-window-label">
            Analysis window: last 90 days · {sourceCount} sources active
          </div>
        </div>
        <div className="conv-sources-pill">{sourceCount} sources</div>
      </div>

      {/* ── Content area ────────────────────────────────────────────────── */}
      <div className="conv-messages">

        {/* Phase 1: skeleton before first token */}
        {isSnapshotLoading && !snapshotText && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div className="skeleton skeleton-line wide" />
            <div className="skeleton skeleton-line medium" />
            <div className="skeleton skeleton-line narrow" />
          </div>
        )}

        {/* Phase 1: snapshot card (streaming or complete) */}
        {snapshotText && (
          <SnapshotCard
            text={snapshotText}
            isStreaming={isSnapshotLoading}
            artistName={artist.name}
          />
        )}

        {/* Phase 2: section selector — appears once snapshot completes,
            and again after a batch finishes so user can generate more */}
        {snapshotDone && (!hasSectionContent || sectionsAllDone) && (
          <SectionSelector
            onGenerate={(ids) => generateSections(artistCtx!.session_id, ids)}
            isGenerating={isSectionStreaming}
          />
        )}

        {/* Phase 3: section result cards stream in order */}
        {SECTION_ORDER.filter(id =>
          completedSections[id] !== undefined || activeSection === id
        ).map(id => {
          const meta = SECTION_META[id]
          const isActive = activeSection === id
          const content = isActive ? activeBuffer : (completedSections[id] ?? '')
          return (
            <div
              key={id}
              className={`section-result-card${isActive ? ' streaming' : ''}`}
            >
              <div className="section-result-title">
                <span className="section-result-icon">{meta.icon}</span>
                {meta.title}
                {isActive && (
                  <span className="spinner" style={{ marginLeft: 'auto', flexShrink: 0 }} />
                )}
              </div>
              <div
                className="section-result-body"
                dangerouslySetInnerHTML={{
                  __html:
                    (marked.parse(content) as string) +
                    (isActive ? '<span class="streaming-cursor"></span>' : ''),
                }}
              />
              {/* Sources panel — appears after section completes */}
              {!isActive && sectionSources[id] && (
                <SourcesPanel sources={sectionSources[id]!} />
              )}
            </div>
          )
        })}

        {/* Chat follow-up messages */}
        {messages.map((msg, i) => (
          <MessageBubble
            key={i}
            message={msg}
            streaming={isChatStreaming && i === messages.length - 1 && msg.role === 'assistant'}
          />
        ))}

        <div ref={bottomRef} />
      </div>

      {/* ── Status bar ──────────────────────────────────────────────────── */}
      {(isSnapshotLoading || isSectionStreaming || isChatStreaming) && (
        <div className="conv-status-bar">
          <div className="spinner" />
          <span>
            {isSnapshotLoading
              ? (snapshotStatus || 'Building snapshot…')
              : isSectionStreaming
                ? `Generating ${activeSection ? SECTION_META[activeSection].title : ''}…`
                : 'Thinking…'}
          </span>
        </div>
      )}

      {/* ── Input ───────────────────────────────────────────────────────── */}
      <div className="conv-input-area">
        <div className="conv-input-row">
          <textarea
            ref={textareaRef}
            id="chat-input"
            rows={1}
            placeholder={
              isSnapshotLoading
                ? 'Building snapshot…'
                : 'Ask anything about this artist…'
            }
            onInput={autoResize}
            onKeyDown={handleKeyDown}
            disabled={isSnapshotLoading}
          />
          <button
            className="btn-icon"
            onClick={handleSend}
            disabled={isChatStreaming || isSnapshotLoading}
            aria-label="Send message"
          >
            ➤
          </button>
        </div>
        <p className="conv-footer-text">
          <strong>Artist Intelligence</strong> · Sound Metrics Studio
        </p>
      </div>

    </main>
  )
}
