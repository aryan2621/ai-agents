import type { Settings } from '@/types'

export type FontSize = Settings['fontSize']

export function applyFontSize(size: FontSize) {
  if (typeof document === 'undefined') return
  document.documentElement.dataset.fontSize = size
}

export function chatProseSizeClass(fontSize: FontSize): string {
  switch (fontSize) {
    case 'sm':
      return 'prose-sm'
    case 'lg':
      return 'prose-lg'
    default:
      return 'prose-base'
  }
}

export const fontSizeInitScript = `
(function() {
  try {
    document.documentElement.dataset.fontSize = 'md';
  } catch (e) {}
})();
`
