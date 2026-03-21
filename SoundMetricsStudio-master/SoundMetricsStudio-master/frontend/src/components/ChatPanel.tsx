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

  return (
    <div className="panel" id="chat-panel">
      <div className="panel-header">
        <h2>Chat</h2>
        <p>Ask anything — use the right panel to load an artist first</p>
      </div>

      <div id="chat-messages">
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
          <span>Artist context: {artistContext.name}</span>
          <span id="context-clear" onClick={onClearContext}>clear context</span>
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
        <button className="btn" id="send-btn" onClick={handleSend} disabled={isStreaming}>
          Send
        </button>
      </div>
    </div>
  )
}
