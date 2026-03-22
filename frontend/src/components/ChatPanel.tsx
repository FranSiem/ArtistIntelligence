import { useRef, useEffect, type KeyboardEvent } from 'react'
import type { ArtistContext } from '../types'
import { useChatStream } from '../hooks/useChatStream'
import { MessageBubble } from './MessageBubble'

interface Props {
  artistContext: ArtistContext | null
  onClearContext: () => void
}

export function ChatPanel({ artistContext, onClearContext }: Props) {
  const { messages, isStreaming, sendMessage } = useChatStream(artistContext)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

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

  const hasMessages = messages.length > 0

  return (
    <div className="panel" id="chat-panel">
      <div className="panel-header">
        <div className="panel-title">
          <span className="panel-title-icon">💬</span>
          Chat
        </div>
        <p className="panel-subtitle">Ask anything — load an artist first for deeper analysis</p>
      </div>

      <div id="chat-messages">
        {!hasMessages && (
          <div className="chat-empty-state">
            <div className="chat-empty-icon">✨</div>
            <div className="chat-empty-title">Start a conversation</div>
            <div className="chat-empty-sub">
              Search for an artist in the right panel, then ask anything about them.
            </div>
          </div>
        )}
        {messages.map((msg, i) => (
          <MessageBubble
            key={i}
            message={msg}
            streaming={isStreaming && i === messages.length - 1 && msg.role === 'assistant'}
          />
        ))}
        <div ref={bottomRef} />
      </div>

      {artistContext && (
        <div id="context-banner" className="active">
          <span id="context-banner-icon">🎵</span>
          <span className="label">Context: <strong>{artistContext.name}</strong></span>
          <span id="context-clear" onClick={onClearContext}>clear</span>
        </div>
      )}

      <div id="chat-input-row">
        <textarea
          ref={textareaRef}
          id="chat-input"
          rows={1}
          placeholder="Ask about an artist or anything else…"
          onInput={autoResize}
          onKeyDown={handleKeyDown}
        />
        <button
          className="btn-icon"
          id="send-btn"
          onClick={handleSend}
          disabled={isStreaming}
          title="Send (Enter)"
        >
          ➤
        </button>
      </div>
    </div>
  )
}
