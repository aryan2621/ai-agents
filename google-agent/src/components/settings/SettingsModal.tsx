'use client'

import { useState } from 'react'
import { Dialog, DialogContent, DialogTitle } from '@/components/ui/dialog'
import { SettingsPanel } from './SettingsPanel'

interface Props {
  open: boolean
  onClose: () => void
}

export function SettingsModal({ open, onClose }: Props) {
  const [key, setKey] = useState(0)

  return (
    <Dialog
      open={open}
      onOpenChange={(v) => {
        if (!v) onClose()
        else setKey((k) => k + 1)
      }}
    >
      <DialogContent className="max-w-4xl w-[min(56rem,calc(100vw-2rem))] h-[min(640px,85vh)] p-0 gap-0 overflow-hidden flex flex-col bg-card border-border">
        <DialogTitle className="sr-only">Settings</DialogTitle>
        <div key={key} className="flex flex-1 min-h-0">
          <SettingsPanel />
        </div>
      </DialogContent>
    </Dialog>
  )
}
