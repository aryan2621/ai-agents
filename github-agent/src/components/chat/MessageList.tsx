'use client'

import { MessageBubble } from './MessageBubble'
import type { Message } from '@/types'

interface Props {
  messages: Message[]
  isGenerating?: boolean
  onEditResend?: (messageId: string, content: string) => void
}

export function MessageList({ messages, isGenerating, onEditResend }: Props) {
  return (
    <div>
      {messages.map((message) => (
        <MessageBubble
          key={message.id}
          message={message}
          disabled={isGenerating}
          onEditResend={onEditResend}
        />
      ))}
    </div>
  )
}
