'use client'

import { useEffect, useMemo, useState } from 'react'
import { ChevronLeft, ChevronRight, Search, Trash2, X } from 'lucide-react'
import { useChatStore } from '@/store/chatStore'
import { ConversationItem } from '@/components/sidebar/ConversationItem'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
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
import { iconStroke } from '@/lib/icon'
import { cn } from '@/lib/utils'

const PAGE_SIZE = 25

export function ChatsPanel() {
  const { conversations, activeId, deleteConversations, loadConversations } = useChatStore()

  const [search, setSearch] = useState('')
  const [page, setPage] = useState(0)
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [deleteOpen, setDeleteOpen] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)

  useEffect(() => {
    void loadConversations()
  }, [loadConversations])

  const filtered = useMemo(
    () =>
      [...conversations]
        .sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime())
        .filter((c) => c.title.toLowerCase().includes(search.toLowerCase())),
    [conversations, search]
  )

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const safePage = Math.min(page, totalPages - 1)
  const pageItems = filtered.slice(safePage * PAGE_SIZE, safePage * PAGE_SIZE + PAGE_SIZE)
  const pageIds = useMemo(() => pageItems.map((c) => c.id), [pageItems])

  const selectedCount = selectedIds.size
  const hasSelection = selectedCount > 0
  const allPageSelected = pageIds.length > 0 && pageIds.every((id) => selectedIds.has(id))

  useEffect(() => {
    setPage(0)
  }, [search])

  useEffect(() => {
    if (page > totalPages - 1) {
      setPage(Math.max(0, totalPages - 1))
    }
  }, [page, totalPages])

  const clearSelection = () => setSelectedIds(new Set())

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const toggleSelectPage = () => {
    if (allPageSelected) {
      setSelectedIds((prev) => {
        const next = new Set(prev)
        for (const id of pageIds) next.delete(id)
        return next
      })
      return
    }
    setSelectedIds((prev) => {
      const next = new Set(prev)
      for (const id of pageIds) next.add(id)
      return next
    })
  }

  const handleBulkDelete = async () => {
    const ids = Array.from(selectedIds)
    if (ids.length === 0) return
    setIsDeleting(true)
    try {
      await deleteConversations(ids)
      clearSelection()
      setDeleteOpen(false)
    } finally {
      setIsDeleting(false)
    }
  }

  const rangeStart = filtered.length === 0 ? 0 : safePage * PAGE_SIZE + 1
  const rangeEnd = Math.min((safePage + 1) * PAGE_SIZE, filtered.length)

  return (
    <div className="flex flex-col flex-1 min-h-0 bg-background">
      <header className="shrink-0 px-6 py-4 border-b border-border space-y-4">
        <div>
          <h1 className="text-app-body font-semibold text-foreground">Chats</h1>
          <p className="text-app-caption text-muted-foreground mt-0.5">
            {filtered.length} conversation{filtered.length === 1 ? '' : 's'}
          </p>
        </div>

        <div className="relative max-w-md">
          <Search
            size={14}
            strokeWidth={iconStroke}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground"
          />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search chats..."
            className="pl-9 h-9 text-app-caption bg-card border-border"
          />
        </div>
      </header>

      <div className="group/list flex flex-col flex-1 min-h-0">
        <div className="flex-1 overflow-y-auto px-6 py-3">
          {pageItems.length > 0 && (
            <label
              className={cn(
                'flex items-center gap-2.5 px-3 py-2 mb-2 rounded-lg cursor-pointer transition-opacity',
                hasSelection
                  ? 'opacity-100'
                  : 'opacity-0 group-hover/list:opacity-100 focus-within:opacity-100'
              )}
            >
              <input
                type="checkbox"
                checked={allPageSelected}
                onChange={toggleSelectPage}
                className="h-3.5 w-3.5 rounded border-border accent-primary cursor-pointer"
                aria-label={allPageSelected ? 'Deselect page' : 'Select all on page'}
              />
              <span className="text-app-caption text-muted-foreground">Select all on page</span>
            </label>
          )}

          <div className="space-y-0.5">
            {pageItems.map((conv) => (
              <ConversationItem
                key={conv.id}
                conversation={conv}
                isActive={conv.id === activeId}
                selectable
                disableRowClick
                isSelected={selectedIds.has(conv.id)}
                showCheckbox={hasSelection}
                showUpdatedAt
                onToggleSelect={() => toggleSelect(conv.id)}
              />
            ))}

            {filtered.length === 0 && (
              <p className="text-app-caption text-muted-foreground text-center py-12">
                No conversations found
              </p>
            )}
          </div>
        </div>

        {filtered.length > PAGE_SIZE && (
          <div className="shrink-0 border-t border-border px-6 py-3 flex items-center justify-between gap-3 bg-background">
            <p className="text-app-caption text-muted-foreground">
              {rangeStart}–{rangeEnd} of {filtered.length}
            </p>
            <div className="flex items-center gap-1">
              <Button
                variant="outline"
                size="sm"
                disabled={safePage === 0}
                onClick={() => setPage((p) => Math.max(0, p - 1))}
              >
                <ChevronLeft className="h-4 w-4" />
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={safePage >= totalPages - 1}
                onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
              >
                Next
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        )}

        {hasSelection && (
          <div className="shrink-0 border-t border-border bg-background px-6 py-3 flex items-center justify-between gap-2">
            <span className="text-app-caption text-foreground font-medium">
              {selectedCount} selected
            </span>
            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={() => setDeleteOpen(true)}
                className="p-2 rounded-lg text-destructive hover:bg-destructive/10 transition-colors"
                aria-label="Delete selected conversations"
              >
                <Trash2 size={16} strokeWidth={iconStroke} />
              </button>
              <button
                type="button"
                onClick={clearSelection}
                className="p-2 rounded-lg text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
                aria-label="Clear selection"
              >
                <X size={16} strokeWidth={iconStroke} />
              </button>
            </div>
          </div>
        )}
      </div>

      <AlertDialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {selectedCount === 1 ? 'Delete this chat?' : `Delete ${selectedCount} chats?`}
            </AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to permanently delete{' '}
              {selectedCount === 1 ? 'this chat' : 'these chats'}? This cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => void handleBulkDelete()}
              disabled={isDeleting}
              className="bg-destructive hover:bg-destructive/90"
            >
              {isDeleting ? 'Deleting…' : 'Delete'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
