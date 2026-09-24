'use client'

interface Props {
  label?: string
}

export function MessageLoader({ label = 'Thinking' }: Props) {
  return (
    <div className="flex items-center gap-3 py-1" aria-live="polite" aria-busy="true">
      <div className="flex items-center gap-1">
        <span className="message-loader-dot" />
        <span className="message-loader-dot animation-delay-150" />
        <span className="message-loader-dot animation-delay-300" />
      </div>
      <span className="text-app-caption text-muted-foreground">{label}</span>
    </div>
  )
}
