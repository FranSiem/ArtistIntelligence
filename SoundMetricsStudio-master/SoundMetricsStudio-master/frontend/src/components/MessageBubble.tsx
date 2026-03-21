import type { Message } from '../types'

interface Props {
  message: Message
  streaming?: boolean
}

export function MessageBubble({ message, streaming }: Props) {
  return (
    <div className={`msg ${message.role}${streaming ? ' streaming' : ''}`}>
      {message.content}
    </div>
  )
}
