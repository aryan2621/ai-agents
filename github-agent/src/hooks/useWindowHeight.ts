'use client'

import { useEffect } from 'react'

function syncAppHeight() {
  document.documentElement.style.setProperty('--app-height', `${window.innerHeight}px`)
}

export function useWindowHeight() {
  useEffect(() => {
    syncAppHeight()

    window.addEventListener('resize', syncAppHeight)

    let unlisten: (() => void) | undefined

    import('@tauri-apps/api/window')
      .then(({ getCurrentWindow }) => getCurrentWindow())
      .then(async (win) => {
        unlisten = await win.onResized(() => {
          syncAppHeight()
        })
      })
      .catch(() => {
        // Web-only dev outside Tauri
      })

    return () => {
      window.removeEventListener('resize', syncAppHeight)
      unlisten?.()
    }
  }, [])
}
