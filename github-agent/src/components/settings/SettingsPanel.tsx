'use client'

import { useState } from 'react'
import { cn } from '@/lib/utils'
import { SETTINGS_NAV_GROUPS, SETTINGS_NAV_ITEMS } from './settingsNav'
import type { SettingsSectionId } from './settingsNav'

export function SettingsPanel({ onNavigateAway }: { onNavigateAway?: () => void }) {
  const [activeId, setActiveId] = useState<SettingsSectionId>('general')
  const active = SETTINGS_NAV_ITEMS.find((item) => item.id === activeId) ?? SETTINGS_NAV_ITEMS[0]
  const ActiveComponent = active.component

  const handleNavigateAway = () => {
    onNavigateAway?.()
  }

  return (
    <div className="flex flex-1 min-h-0 bg-background">
      <aside className="w-[13.5rem] shrink-0 border-r border-border bg-muted/30 flex flex-col">
        <div className="px-4 py-4 border-b border-border">
          <h1 className="text-app-body font-semibold text-foreground">Settings</h1>
        </div>

        <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-4" aria-label="Settings sections">
          {SETTINGS_NAV_GROUPS.map((group) => (
            <div key={group.label}>
              <p className="px-2 mb-1.5 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                {group.label}
              </p>
              <ul className="space-y-0.5">
                {group.items.map((item) => {
                  const Icon = item.icon
                  const isActive = item.id === activeId
                  return (
                    <li key={item.id}>
                      <button
                        type="button"
                        onClick={() => setActiveId(item.id)}
                        className={cn(
                          'w-full flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-left text-app-caption transition-colors duration-fast',
                          isActive
                            ? 'bg-accent text-foreground font-medium'
                            : 'text-muted-foreground hover:text-foreground hover:bg-accent/60'
                        )}
                      >
                        <Icon className="h-4 w-4 shrink-0 opacity-80" />
                        {item.label}
                      </button>
                    </li>
                  )
                })}
              </ul>
            </div>
          ))}
        </nav>
      </aside>

      <div className="flex-1 flex flex-col min-w-0 min-h-0">
        <header className="shrink-0 px-6 py-4 border-b border-border">
          <h2 className="text-app-body font-semibold text-foreground">{active.label}</h2>
          <p className="text-app-caption text-muted-foreground mt-0.5">{active.description}</p>
        </header>

        <div className="flex-1 overflow-y-auto px-6 py-5">
          <ActiveComponent onNavigateAway={handleNavigateAway} />
        </div>
      </div>
    </div>
  )
}
