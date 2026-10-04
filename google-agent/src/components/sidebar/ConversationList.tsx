'use client'

import { useMemo } from 'react'
import { useChatStore } from '@/store/chatStore'
import { useAppViewStore } from '@/store/appViewStore'
import { ConversationItem } from './ConversationItem'
import { isToday, isYesterday, isThisWeek } from 'date-fns'

const GROUP_LABELS = ['Today', 'Yesterday', 'Last 7 days', 'Older'] as const

export function ConversationList({ searchQuery }: { searchQuery: string }) {
  const { conversations, activeId, selectConversation } = useChatStore()
  const openChat = useAppViewStore((s) => s.openChat)

  const filtered = useMemo(
    () =>
      conversations.filter((c) => !c.draft).filter((c) =>
        c.title.toLowerCase().includes(searchQuery.toLowerCase())
      ),
    [conversations, searchQuery]
  )

  const grouped = useMemo(() => {
    const groups: Record<string, typeof filtered> = {
      Today: [],
      Yesterday: [],
      'Last 7 days': [],
      Older: [],
    }
    for (const c of filtered) {
      const d = new Date(c.updatedAt)
      if (isToday(d)) groups.Today.push(c)
      else if (isYesterday(d)) groups.Yesterday.push(c)
      else if (isThisWeek(d)) groups['Last 7 days'].push(c)
      else groups.Older.push(c)
    }
    return groups
  }, [filtered])

  return (
    <div className="flex flex-col min-h-full py-1 space-y-4">
      {GROUP_LABELS.map((label) => {
        const items = grouped[label]
        if (!items.length) return null
        return (
          <div key={label}>
            <p className="px-2 pb-1 text-xs font-medium text-muted-foreground">
              {label}
            </p>
            <div className="space-y-px">
              {items.map((conv) => (
                <ConversationItem
                  key={conv.id}
                  conversation={conv}
                  isActive={conv.id === activeId}
                  onSelect={() => {
                    void selectConversation(conv.id)
                    openChat()
                  }}
                />
              ))}
            </div>
          </div>
        )
      })}

      {filtered.length === 0 && (
        <p className="px-2 py-2 text-xs text-muted-foreground">
          No conversations found
        </p>
      )}
    </div>
  )
}
