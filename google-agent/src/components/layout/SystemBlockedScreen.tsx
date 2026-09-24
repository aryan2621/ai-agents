'use client'

import { AlertCircle, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { iconStroke } from '@/lib/icon'
import type { ReadinessIssue } from '@/types'

interface Props {
  loading: boolean
  issues: ReadinessIssue[]
  onRetry: () => void
}

export function SystemBlockedScreen({ loading, issues, onRetry }: Props) {
  const list =
    loading && (issues?.length ?? 0) === 0
      ? [{ code: 'checking', message: 'Checking system status…', remediation: '' }]
      : (issues ?? [])

  return (
    <div className="flex-1 flex flex-col items-center justify-center gap-5 px-6 py-10">
      <div className="w-12 h-12 rounded-full bg-destructive/10 border border-destructive/20 flex items-center justify-center">
        <AlertCircle size={22} className="text-destructive" strokeWidth={iconStroke} />
      </div>
      <div className="text-center space-y-1 max-w-md">
        <h2 className="text-app-display font-rounded text-foreground">App not ready</h2>
        <p className="text-app-body text-muted-foreground">
          Fix the issues below before starting a conversation.
        </p>
      </div>
      <ul className="w-full max-w-md space-y-3">
        {list.map((issue) => (
          <li
            key={issue.code}
            className="rounded-xl border border-border bg-card px-4 py-3 text-left"
          >
            <p className="text-app-body text-foreground">{issue.message}</p>
            {issue.remediation ? (
              <p className="text-app-caption text-muted-foreground mt-1">{issue.remediation}</p>
            ) : null}
          </li>
        ))}
      </ul>
      <Button variant="outline" onClick={onRetry} disabled={loading} className="gap-2">
        <RefreshCw size={14} strokeWidth={iconStroke} className={loading ? 'animate-spin' : ''} />
        Check again
      </Button>
    </div>
  )
}
