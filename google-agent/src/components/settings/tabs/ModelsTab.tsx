'use client'

import { useSettingsStore } from '@/store/settingsStore'
import { Input } from '@/components/ui/input'
import { SettingsCard, SettingsSection } from '../SettingsLayout'

export function ModelsTab() {
  const { settings, update } = useSettingsStore()

  return (
    <div className="space-y-8">
      <SettingsSection
        title="Ollama"
        description="Local models run the agent rooms. Install Ollama, then pull a tool-capable model."
      >
        <SettingsCard className="p-4 space-y-3 divide-y-0">
          <Input
            autoComplete="off"
            placeholder="http://127.0.0.1:11434"
            value={settings.ollamaBaseUrl}
            onChange={(e) => update({ ollamaBaseUrl: e.target.value })}
            aria-label="Ollama base URL"
          />
          <Input
            autoComplete="off"
            placeholder="qwen2.5:7b"
            value={settings.defaultModel}
            onChange={(e) => update({ defaultModel: e.target.value })}
            aria-label="Ollama model"
          />
          <p className="text-app-caption text-muted-foreground leading-relaxed">
            Example: <code className="text-[11px]">ollama pull qwen2.5:7b</code>. You can also set{' '}
            <code className="text-[11px]">OLLAMA_BASE_URL</code> in <code className="text-[11px]">backend/.env</code>.
          </p>
        </SettingsCard>
      </SettingsSection>
    </div>
  )
}
