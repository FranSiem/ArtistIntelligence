import type { Message } from '../types'
import { marked } from 'marked'

interface Props {
  message: Message
  streaming?: boolean
}

export function MessageBubble({ message, streaming }: Props) {
  if (message.role === 'user') {
    return (
      <div className="msg user">
        {message.content}
      </div>
    )
  }

  // Render assistant messages with markdown
  const html = marked.parse(message.content || '') as string

  return (
    <div className="msg-row">
      <div className="msg-avatar">🤖</div>
      <div className={`msg assistant${streaming ? ' streaming' : ''}`}>
        {message.content
          ? <div dangerouslySetInnerHTML={{ __html: html }} />
          : null
        }
        {streaming && <span className="streaming-cursor" />}
      </div>
    </div>
  )
}
