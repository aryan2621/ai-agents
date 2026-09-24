import { toast } from 'sonner'

export function isTauriRuntime(): boolean {
  return typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window
}

export function sanitizeExternalUrl(url: string): string | null {
  const trimmed = url.trim().replace(/[)\]"'`,.;:]+$/g, '')
  if (trimmed.startsWith('https://') || trimmed.startsWith('http://')) {
    return trimmed
  }
  return null
}

export function isInternalAppUrl(url: string): boolean {
  try {
    const parsed = new URL(url, window.location.href)
    if (parsed.protocol === 'tauri:') return true

    const host = parsed.hostname
    const path = parsed.pathname

    const isLocalHost =
      host === window.location.hostname ||
      host === 'localhost' ||
      host === '127.0.0.1'

    if (!isLocalHost) return false

    return (
      path === '/' ||
      path.startsWith('/chat') ||
      path.startsWith('/auth') ||
      path.startsWith('/onboarding') ||
      path.startsWith('/_next') ||
      path.startsWith('/out')
    )
  } catch {
    return false
  }
}

export async function openExternalUrl(url: string): Promise<void> {
  const cleaned = sanitizeExternalUrl(url)
  if (!cleaned) {
    toast.error('Invalid link')
    return
  }

  if (isTauriRuntime()) {
    try {
      const { openUrl } = await import('@tauri-apps/plugin-opener')
      await openUrl(cleaned)
    } catch (error) {
      console.error('[openExternalUrl]', error)
      toast.error('Could not open link in browser')
    }
    return
  }

  const popup = window.open(cleaned, '_blank', 'noopener,noreferrer')
  if (!popup) {
    window.location.assign(cleaned)
  }
}

export function interceptExternalLinkClick(event: MouseEvent): boolean {
  if (event.defaultPrevented || event.button !== 0) return false

  const target = event.target
  if (!(target instanceof Element)) return false

  const anchor = target.closest('a')
  if (!anchor) return false

  const rawHref = anchor.getAttribute('href')
  if (!rawHref || rawHref.startsWith('#') || rawHref.startsWith('mailto:') || rawHref.startsWith('tel:')) {
    return false
  }

  const cleaned = sanitizeExternalUrl(anchor.href)
  if (!cleaned || isInternalAppUrl(cleaned)) return false

  event.preventDefault()
  event.stopPropagation()
  void openExternalUrl(cleaned)
  return true
}
