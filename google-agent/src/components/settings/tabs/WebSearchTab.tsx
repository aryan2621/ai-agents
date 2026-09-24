'use client'

import { useSettingsStore } from '@/store/settingsStore'
import { Input } from '@/components/ui/input'
import { SettingsCard, SettingsSection } from '../SettingsLayout'

export function WebSearchTab() {
  const { settings, update } = useSettingsStore()

  return (
    <SettingsSection
      title="Tavily API"
      description="Powers the Web Search agent for public web research."
    >
      <SettingsCard className="p-4 space-y-3 divide-y-0">
        <div className="space-y-2">
          <label htmlFor="tavily-api-key" className="text-app-body text-foreground">
            API key
          </label>
          <Input
            id="tavily-api-key"
            type="password"
            autoComplete="off"
            placeholder="tvly-..."
            value={settings.tavilySearchApiKey}
            onChange={(e) => update({ tavilySearchApiKey: e.target.value })}
          />
        </div>
        <p className="text-app-caption text-muted-foreground leading-relaxed">
          Get a free key at{' '}
          <a
            href="https://tavily.com"
            target="_blank"
            rel="noreferrer"
            className="underline underline-offset-2 hover:text-foreground"
          >
            tavily.com
          </a>
          . You can also set <code className="text-[11px]">TAVILY_API_KEY</code> in{' '}
          <code className="text-[11px]">backend/.env</code> as a server default.
        </p>
      </SettingsCard>
    </SettingsSection>
  )
}
