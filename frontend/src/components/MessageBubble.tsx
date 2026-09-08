import { marked } from 'marked'
import type { Message } from '../types'

interface Props {
  message: Message
  streaming?: boolean
}

export function MessageBubble({ message, streaming = false }: Props) {
  if (!message.content) return null

  if (message.role === 'user') {
    return (
      <div className="msg user">
        {message.content}
      </div>
    )
  }

  // Assistant message — render markdown, show streaming cursor if active
  return (
    <div className="msg-row">
      <div className="msg-avatar">AI</div>
      <div
        className={`msg assistant${streaming ? ' streaming' : ''}`}
        dangerouslySetInnerHTML={{
          __html: (marked.parse(message.content) as string) +
            (streaming ? '<span class="streaming-cursor"></span>' : ''),
        }}
      />
    </div>
  )
}
