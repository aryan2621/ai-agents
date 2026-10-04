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
      <aside className="w-[14rem] shrink-0 border-r border-border bg-sidebar flex flex-col">
        <div className="px-4 pt-5 pb-3">
          <h1 className="font-serif text-xl font-normal text-foreground">Settings</h1>
        </div>

        <nav className="flex-1 overflow-y-auto pb-3 px-2 space-y-4" aria-label="Settings sections">
          {SETTINGS_NAV_GROUPS.map((group) => (
            <div key={group.label}>
              <p className="px-2.5 mb-1 text-xs font-medium text-muted-foreground">
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
                          'w-full flex items-center gap-2.5 rounded-lg px-2.5 h-8 text-left text-sm transition-colors duration-fast',
                          isActive
                            ? 'bg-accent text-foreground font-medium'
                            : 'text-foreground/80 hover:text-foreground hover:bg-accent'
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
        <header className="shrink-0 px-8 pt-7 pb-4">
          <h2 className="font-serif text-2xl font-normal text-foreground">{active.label}</h2>
          <p className="text-sm text-muted-foreground mt-1">{active.description}</p>
        </header>

        <div className="flex-1 overflow-y-auto px-8 pt-2 pb-8">
          <ActiveComponent onNavigateAway={handleNavigateAway} />
        </div>
      </div>
    </div>
  )
}
