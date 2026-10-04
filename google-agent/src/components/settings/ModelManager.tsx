'use client'

import { useCallback, useEffect, useState } from 'react'
import { ArrowDownToLine, Check, Cpu, Loader2, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { cancelModelDownload, deleteModel, downloadModel, fetchModels } from '@/lib/api'
import { iconStroke } from '@/lib/icon'
import { useAuthStore } from '@/store/authStore'
import { useReadinessStore } from '@/store/readinessStore'
import { useSettingsStore } from '@/store/settingsStore'
import { Button } from '@/components/ui/button'
import type { LocalModel, ModelCatalog } from '@/types'

const gb = (mb: number) => `${(mb / 1000).toFixed(1)} GB`

/** The model chats use: the chosen one if downloaded, else the backend's automatic pick. */
function activeModel(catalog: ModelCatalog, chosen: string): string | null {
  const installed = catalog.models.filter((m) => m.installed)
  if (chosen && installed.some((m) => m.id === chosen)) return chosen
  if (installed.some((m) => m.id === catalog.recommended)) return catalog.recommended
  const fits = installed.filter((m) => m.minRamGb <= catalog.ramGb)
  return (fits.length ? fits : installed).at(-1)?.id ?? null
}

/**
 * Lists the built-in models with download, use and delete. `only` limits the list
 * (onboarding shows just the recommended model).
 */
export function ModelManager({
  only,
  onInstalled,
}: {
  only?: 'recommended'
  onInstalled?: () => void
}) {
  const [catalog, setCatalog] = useState<ModelCatalog | null>(null)
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const { settings, update } = useSettingsStore()

  const refresh = useCallback(async () => {
    try {
      setCatalog(await fetchModels())
    } catch {
      /* backend still starting; the poll below retries */
    }
  }, [])

  useEffect(() => {
    void refresh()
  }, [refresh])

  const downloading = catalog?.download && !catalog.download.finished && !catalog.download.error
  useEffect(() => {
    if (!downloading) return
    const timer = setInterval(() => void refresh(), 700)
    return () => clearInterval(timer)
  }, [downloading, refresh])

  // Report the end of a download once.
  const finishedId = catalog?.download?.finished ? catalog.download.id : null
  const failed = catalog?.download?.error || null
  useEffect(() => {
    if (finishedId) {
      toast.success('Model downloaded and verified')
      // The first model downloaded becomes the one chats use (selecting it also loads it).
      if (isAuthenticated && !useSettingsStore.getState().settings.defaultModel) {
        void update({ defaultModel: finishedId })
      }
      void useReadinessStore.getState().check({ silent: true })
      onInstalled?.()
    }
  }, [finishedId]) // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (failed) toast.error(failed)
  }, [failed])

  if (!catalog) {
    return (
      <div className="flex justify-center py-10" role="status" aria-label="Loading models">
        <Loader2 size={20} strokeWidth={iconStroke} className="animate-spin text-muted-foreground" />
      </div>
    )
  }

  const active = activeModel(catalog, settings.defaultModel)
  const models =
    only === 'recommended'
      ? catalog.models.filter((m) => m.id === catalog.recommended)
      : catalog.models
  const recommended = catalog.models.find((m) => m.id === catalog.recommended)

  const run = async (action: () => Promise<ModelCatalog>) => {
    try {
      setCatalog(await action())
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Something went wrong'
      toast.error(message)
    }
  }

  const use = async (m: LocalModel) => {
    if (!isAuthenticated) return
    await update({ defaultModel: m.id })
    toast.success(`${m.name} is now used for chats`)
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2.5 rounded-xl bg-card px-4 py-3 text-sm text-foreground">
        <Cpu size={16} strokeWidth={iconStroke} className="shrink-0 text-brand" />
        <span>
          This Mac has <strong className="font-medium">{catalog.ramGb} GB</strong> of memory.
          {recommended ? (
            <>
              {' '}
              <strong className="font-medium">{recommended.name}</strong> is the best fit for it.
            </>
          ) : null}
        </span>
      </div>

      <div className="rounded-xl border border-border bg-popover divide-y divide-border">
        {models.map((m) => {
          const isDownloading = downloading && catalog.download?.id === m.id
          const progress = catalog.download && catalog.download.total
            ? Math.round((catalog.download.done / catalog.download.total) * 100)
            : 0
          const tooBig = m.minRamGb > catalog.ramGb
          return (
            <div key={m.id} className="flex items-center gap-4 px-4 py-3.5">
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-sm font-medium text-foreground">{m.name}</span>
                  {m.id === catalog.recommended && (
                    <span className="rounded-md bg-brand/10 px-1.5 py-0.5 text-xs font-medium text-brand">
                      Recommended
                    </span>
                  )}
                  {m.installed && m.id === active && (
                    <span className="rounded-md bg-success/10 px-1.5 py-0.5 text-xs font-medium text-success">
                      In use
                    </span>
                  )}
                </div>
                <p className="mt-0.5 text-xs text-muted-foreground leading-relaxed">{m.note}</p>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  {gb(m.sizeMb)} · needs {m.minRamGb} GB of memory
                  {tooBig ? ' · more than this Mac has' : ''}
                </p>
              </div>
              <div className="flex shrink-0 items-center gap-1.5">
                {isDownloading ? (
                  <>
                    <div className="h-1.5 w-28 overflow-hidden rounded-full bg-muted">
                      <div className="h-full bg-brand transition-[width]" style={{ width: `${progress}%` }} />
                    </div>
                    <span className="w-9 text-right text-xs tabular-nums text-muted-foreground">
                      {catalog.download?.total ? `${progress}%` : '…'}
                    </span>
                    <Button variant="ghost" size="sm" onClick={() => void run(cancelModelDownload)}>
                      Cancel
                    </Button>
                  </>
                ) : m.installed ? (
                  <>
                    {isAuthenticated && m.id !== active && (
                      <Button variant="outline" size="sm" onClick={() => void use(m)}>
                        <Check size={14} strokeWidth={iconStroke} /> Use
                      </Button>
                    )}
                    <button
                      type="button"
                      onClick={() => void run(() => deleteModel(m.id))}
                      className="h-8 w-8 inline-flex items-center justify-center rounded-lg text-muted-foreground hover:bg-accent hover:text-foreground transition-colors duration-fast"
                      aria-label={`Delete ${m.name}`}
                    >
                      <Trash2 size={15} strokeWidth={iconStroke} />
                    </button>
                  </>
                ) : (
                  <Button
                    variant={m.id === catalog.recommended ? 'default' : 'outline'}
                    size="sm"
                    disabled={Boolean(downloading)}
                    onClick={() => void run(() => downloadModel(m.id))}
                  >
                    <ArrowDownToLine size={14} strokeWidth={iconStroke} /> Download
                  </Button>
                )}
              </div>
            </div>
          )
        })}
      </div>
      <p className="text-xs text-muted-foreground leading-relaxed">
        Models run on this Mac with llama.cpp; nothing you ask leaves it. 4-bit versions from Hugging
        Face, checked against their published checksum after download.
      </p>
    </div>
  )
}
