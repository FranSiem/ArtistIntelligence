import { useRef, useEffect, type KeyboardEvent } from 'react'
import { marked } from 'marked'
import type { Artist, ArtistContext } from '../types'
import { useAnalysisStream } from '../hooks/useAnalysisStream'
import { useChatStream } from '../hooks/useChatStream'
import { MessageBubble } from './MessageBubble'

interface Props {
  artist: Artist | null
  onArtistContext: (ctx: ArtistContext) => void
}

export function ConversationPanel({ artist, onArtistContext }: Props) {
  const { analysisText, status, isAnalyzing, analyze } = useAnalysisStream(onArtistContext)
  const { messages, isStreaming, sendMessage } = useChatStream(
    // Pass artist context to chat only once analysis is done
    analysisText && !isAnalyzing && artist
      ? { name: artist.name, analysis: analysisText, session_id: '' }
      : null
  )

  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const analysisRef = useRef<HTMLDivElement>(null)

  // Kick off analysis as soon as an artist is selected
  useEffect(() => {
    if (artist) analyze(artist.cm_id)
  }, [artist?.cm_id])

  // Render markdown for completed analysis directly into DOM (avoids flicker)
  useEffect(() => {
    if (analysisRef.current && analysisText && !isAnalyzing) {
      analysisRef.current.innerHTML = marked.parse(analysisText) as string
    }
  }, [analysisText, isAnalyzing])

  // Auto-scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, analysisText])

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
    if (!text || isStreaming) return
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

  // ── Active source count for header pill ──────────────────────────────────
  const sourceCount = 2 // Chartmetric + YouTube active by default; will be dynamic later

  // ── Empty state — no artist selected ────────────────────────────────────
  if (!artist) {
    return (
      <main id="conversation-panel">
        <div className="conv-empty-state">
          <div className="conv-empty-icon">🎼</div>
          <div className="conv-empty-title">No artist loaded</div>
          <p className="conv-empty-sub">
            Search for an artist on the landing page to generate a strategic analysis.
          </p>
        </div>
        <div className="conv-input-area">
          <div className="conv-input-row">
            <textarea
              ref={textareaRef}
              id="chat-input"
              rows={1}
              placeholder="Load an artist first to start the conversation…"
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
        <div className="conv-sources-pill">
          {sourceCount} sources
        </div>
      </div>

      {/* ── Messages ────────────────────────────────────────────────────── */}
      <div className="conv-messages">

        {/* Analysis phase — skeleton while loading */}
        {isAnalyzing && !analysisText && (
          <div id="analysis-skeleton">
            <div className="skeleton skeleton-line wide"   style={{ marginBottom: '10px' }} />
            <div className="skeleton skeleton-line medium" style={{ marginBottom: '10px' }} />
            <div className="skeleton skeleton-line wide"   style={{ marginBottom: '10px' }} />
            <div className="skeleton skeleton-line narrow" style={{ marginBottom: '10px' }} />
            <div className="skeleton skeleton-line wide"   style={{ marginBottom: '10px' }} />
            <div className="skeleton skeleton-line medium" />
          </div>
        )}

        {/* Streaming analysis tokens rendered as a live assistant bubble */}
        {isAnalyzing && analysisText && (
          <div className="msg-row">
            <div className="msg-avatar">AI</div>
            <div
              className="msg assistant streaming"
              dangerouslySetInnerHTML={{ __html: marked.parse(analysisText) as string }}
            />
          </div>
        )}

        {/* Completed analysis — rendered via ref for performance */}
        {!isAnalyzing && analysisText && (
          <div className="msg-row">
            <div className="msg-avatar">AI</div>
            <div
              className="msg assistant"
              ref={analysisRef}
            />
          </div>
        )}

        {/* Follow-up conversation messages */}
        {messages.map((msg, i) => (
          <MessageBubble
            key={i}
            message={msg}
            streaming={isStreaming && i === messages.length - 1 && msg.role === 'assistant'}
          />
        ))}

        <div ref={bottomRef} />
      </div>

      {/* ── Status bar ──────────────────────────────────────────────────── */}
      {(isAnalyzing || isStreaming) && (
        <div className="conv-status-bar">
          <div className="spinner" />
          <span>{isAnalyzing ? (status || 'Analysing…') : 'Thinking…'}</span>
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
              isAnalyzing
                ? 'Analysis in progress…'
                : 'Ask anything about this artist…'
            }
            onInput={autoResize}
            onKeyDown={handleKeyDown}
            disabled={isAnalyzing}
          />
          <button
            className="btn-icon"
            onClick={handleSend}
            disabled={isStreaming || isAnalyzing}
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
