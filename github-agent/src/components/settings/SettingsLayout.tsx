'use client'

import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

export function SettingsSection({
  title,
  description,
  children,
  className,
}: {
  title?: string
  description?: string
  children: ReactNode
  className?: string
}) {
  return (
    <section className={cn('space-y-4', className)}>
      {(title || description) && (
        <div className="space-y-1">
          {title && <h3 className="text-app-body font-medium text-foreground">{title}</h3>}
          {description && (
            <p className="text-app-caption text-muted-foreground leading-relaxed">{description}</p>
          )}
        </div>
      )}
      {children}
    </section>
  )
}

export function SettingsCard({
  children,
  className,
}: {
  children: ReactNode
  className?: string
}) {
  return (
    <div className={cn('rounded-xl border border-border bg-background divide-y divide-border', className)}>
      {children}
    </div>
  )
}

export function SettingsRow({
  label,
  description,
  children,
  className,
}: {
  label: string
  description?: string
  children: ReactNode
  className?: string
}) {
  return (
    <div
      className={cn(
        'flex items-center justify-between gap-4 px-4 py-3.5 first:rounded-t-xl last:rounded-b-xl',
        className
      )}
    >
      <div className="min-w-0 flex-1">
        <p className="text-app-body text-foreground">{label}</p>
        {description && (
          <p className="text-app-caption text-muted-foreground mt-0.5 leading-relaxed">{description}</p>
        )}
      </div>
      <div className="shrink-0">{children}</div>
    </div>
  )
}

export function SettingsDivider() {
  return <div className="border-t border-border" />
}

export function SegmentedControl<T extends string>({
  value,
  options,
  onChange,
  className,
}: {
  value: T
  options: { value: T; label: string }[]
  onChange: (value: T) => void
  className?: string
}) {
  return (
    <div
      className={cn(
        'inline-flex rounded-lg border border-border bg-muted/50 p-0.5',
        className
      )}
      role="group"
    >
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          onClick={() => onChange(option.value)}
          className={cn(
            'px-3 py-1.5 rounded-md text-app-caption font-medium transition-colors duration-fast',
            value === option.value
              ? 'bg-background text-foreground shadow-sm'
              : 'text-muted-foreground hover:text-foreground'
          )}
        >
          {option.label}
        </button>
      ))}
    </div>
  )
}

export function SettingsStatusBadge({
  variant,
  children,
}: {
  variant: 'success' | 'warning' | 'error' | 'neutral'
  children: ReactNode
}) {
  const styles = {
    success: 'text-green-600 dark:text-green-500 bg-green-500/10 border-green-500/20',
    warning: 'text-amber-600 dark:text-amber-500 bg-amber-500/10 border-amber-500/20',
    error: 'text-destructive bg-destructive/10 border-destructive/20',
    neutral: 'text-muted-foreground bg-muted border-border',
  }

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-md border px-2 py-1 text-app-caption font-medium',
        styles[variant]
      )}
    >
      {children}
    </span>
  )
}
