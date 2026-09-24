'use client'

import dynamic from 'next/dynamic'
import { isMacOS } from '@/hooks/usePlatform'

const TitleBarInner = dynamic(
  () => import('./TitleBarInner').then((m) => m.TitleBarInner),
  { ssr: false }
)

/** Native macOS traffic lights are used when decorations are enabled. */
export function TitleBar() {
  if (isMacOS()) return null
  return <TitleBarInner />
}
