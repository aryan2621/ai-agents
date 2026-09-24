'use client'

import { Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { iconStroke } from '@/lib/icon'

export function NewChatButton({ onClick }: { onClick: () => void }) {
  return (
    <Button
      onClick={onClick}
      variant="outline"
      className="w-full justify-center gap-2 h-9 rounded-lg border-border bg-transparent hover:bg-accent text-foreground transition-colors duration-fast"
    >
      <Plus size={14} strokeWidth={iconStroke} />
      New Chat
    </Button>
  )
}
