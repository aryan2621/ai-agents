'use client'

import type { ReactNode } from 'react'
import { sanitizeExternalUrl } from '@/lib/open-external'

export function renderMarkdownLink(href: string | undefined, children: ReactNode) {
  const cleaned = href ? sanitizeExternalUrl(href) : null
  if (!cleaned) return <span>{children}</span>

  return (
    <a
      href={cleaned}
      target="_blank"
      rel="noopener noreferrer"
      className="underline underline-offset-2"
    >
      {children}
    </a>
  )
}
