'use client'

import { getCurrentWindow } from '@tauri-apps/api/window'
import { Minus, Square, X, Maximize2 } from 'lucide-react'
import { useState, useEffect } from 'react'

export function TitleBarInner() {
  const [isMaximized, setIsMaximized] = useState(false)

  useEffect(() => {
    let unlisten: (() => void) | undefined

    async function setup() {
      const win = getCurrentWindow()
      setIsMaximized(await win.isMaximized())
      unlisten = await win.onResized(async () => {
        setIsMaximized(await win.isMaximized())
      })
    }

    setup()
    return () => {
      unlisten?.()
    }
  }, [])

  const handleMinimize = () => getCurrentWindow().minimize()
  const handleToggleMaximize = () => getCurrentWindow().toggleMaximize()
  const handleClose = () => getCurrentWindow().close()

  return (
    <div
      className="h-8 flex items-center justify-between select-none shrink-0 bg-background border-b border-border"
      style={{ WebkitAppRegion: 'drag' } as React.CSSProperties}
    >
      <div className="flex-1 flex items-center px-3">
        <span className="text-app-caption text-muted-foreground font-medium">GitHub Agent</span>
      </div>

      <div
        className="flex items-center"
        style={{ WebkitAppRegion: 'no-drag' } as React.CSSProperties}
      >
        <button
          onClick={handleMinimize}
          className="h-8 w-10 flex items-center justify-center hover:bg-accent text-muted-foreground hover:text-foreground transition-colors duration-fast"
        >
          <Minus size={12} />
        </button>
        <button
          onClick={handleToggleMaximize}
          className="h-8 w-10 flex items-center justify-center hover:bg-accent text-muted-foreground hover:text-foreground transition-colors duration-fast"
        >
          {isMaximized ? <Square size={11} /> : <Maximize2 size={11} />}
        </button>
        <button
          onClick={handleClose}
          className="h-8 w-10 flex items-center justify-center hover:bg-destructive text-muted-foreground hover:text-destructive-foreground transition-colors duration-fast"
        >
          <X size={12} />
        </button>
      </div>
    </div>
  )
}
