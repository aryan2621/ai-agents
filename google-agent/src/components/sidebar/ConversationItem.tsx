'use client'

import { useState } from 'react'
import { format } from 'date-fns'
import { MoreHorizontal, Pencil, Trash2 } from 'lucide-react'
import { useChatStore } from '@/store/chatStore'
import type { Conversation } from '@/types'
import { getAgentLabel, isRoomAgent } from '@/lib/agents'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'

interface Props {
  conversation: Conversation
  isActive: boolean
  isSelected?: boolean
  selectable?: boolean
  showCheckbox?: boolean
  showUpdatedAt?: boolean
  disableRowClick?: boolean
  onSelect?: () => void
  onToggleSelect?: () => void
}

export function ConversationItem({
  conversation,
  isActive,
  isSelected = false,
  selectable = false,
  showCheckbox = false,
  showUpdatedAt = false,
  disableRowClick = false,
  onSelect,
  onToggleSelect,
}: Props) {
  const renameConversation = useChatStore((s) => s.renameConversation)
  const deleteConversation = useChatStore((s) => s.deleteConversation)
  const [isRenaming, setIsRenaming] = useState(false)
  const [renameValue, setRenameValue] = useState(conversation.title)
  const [deleteOpen, setDeleteOpen] = useState(false)

  const handleRename = async () => {
    const title = renameValue.trim()
    if (title) {
      await renameConversation(conversation.id, title)
    }
    setIsRenaming(false)
  }

  if (isRenaming) {
    return (
      <Input
        autoFocus
        value={renameValue}
        onChange={(e) => setRenameValue(e.target.value)}
        onBlur={handleRename}
        onKeyDown={(e) => {
          if (e.key === 'Enter') handleRename()
          if (e.key === 'Escape') setIsRenaming(false)
        }}
        className="h-8 text-app-caption mx-1"
      />
    )
  }

  const checkboxVisible = selectable && (showCheckbox || isSelected)
  const agentLabel = isRoomAgent(conversation.agentFilter)
    ? getAgentLabel(conversation.agentFilter)
    : null

  return (
    <>
      <div
        className={cn(
          'group flex items-center gap-2 px-2 py-1.5 rounded-lg transition-colors duration-fast',
          !disableRowClick && 'cursor-pointer',
          isSelected
            ? 'bg-accent text-foreground'
            : isActive
              ? 'bg-accent text-foreground'
              : 'text-muted-foreground hover:bg-accent/60 hover:text-foreground'
        )}
        onClick={disableRowClick ? undefined : onSelect}
      >
        {selectable && (
          <label
            className={cn(
              'shrink-0 flex items-center transition-opacity cursor-pointer',
              checkboxVisible ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'
            )}
            onClick={(e) => e.stopPropagation()}
          >
            <input
              type="checkbox"
              checked={isSelected}
              onChange={onToggleSelect}
              className="h-3.5 w-3.5 rounded border-border accent-primary cursor-pointer"
              aria-label={`Select ${conversation.title}`}
            />
          </label>
        )}

        <span className="flex-1 min-w-0">
          <span className="block text-app-caption truncate">{conversation.title}</span>
          {agentLabel ? (
            <span className="block text-[10px] text-muted-foreground truncate">{agentLabel}</span>
          ) : null}
        </span>

        {showUpdatedAt && (
          <span className="shrink-0 text-app-caption text-muted-foreground hidden sm:block">
            {format(new Date(conversation.updatedAt), 'MMM d, yyyy')}
          </span>
        )}

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              onClick={(e) => e.stopPropagation()}
              className={cn(
                'p-1 rounded hover:bg-accent text-muted-foreground hover:text-foreground transition-opacity duration-fast',
                showCheckbox ? 'opacity-0 pointer-events-none' : 'opacity-0 group-hover:opacity-100'
              )}
            >
              <MoreHorizontal size={12} />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-40">
            <DropdownMenuItem
              onClick={(e) => {
                e.stopPropagation()
                setRenameValue(conversation.title)
                setIsRenaming(true)
              }}
              className="gap-2 cursor-pointer"
            >
              <Pencil size={12} /> Rename
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={(e) => {
                e.stopPropagation()
                setDeleteOpen(true)
              }}
              className="text-destructive gap-2 cursor-pointer"
            >
              <Trash2 size={12} /> Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <AlertDialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete this chat?</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to permanently delete this chat? This cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => deleteConversation(conversation.id)}
              className="bg-destructive hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
