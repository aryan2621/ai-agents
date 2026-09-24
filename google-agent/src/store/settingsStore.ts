import { create } from 'zustand'
import { fetchSettings, updateSettingsApi } from '@/lib/api'
import { useReadinessStore } from '@/store/readinessStore'
import type { Settings } from '@/types'

const DEFAULT_LLM_MODEL = 'qwen2.5:7b'
const DEFAULT_OLLAMA_URL = 'http://127.0.0.1:11434'

const DEFAULTS: Settings = {
  defaultModel: DEFAULT_LLM_MODEL,
  temperature: 0.7,
  maxTokens: 2048,
  sendOnEnter: true,
  autoScroll: true,
  fontSize: 'md',
  theme: 'system',
  onboardingCompleted: false,
  tavilySearchApiKey: '',
  ollamaBaseUrl: DEFAULT_OLLAMA_URL,
  agentOverrides: {
    gmail: { enabled: true },
    calendar: { enabled: true },
    drive: { enabled: true },
    docs: { enabled: true },
    sheets: { enabled: true },
    web: { enabled: true },
  },
}

function normalizeAgentOverrides(
  overrides: Settings['agentOverrides'] | undefined
): Settings['agentOverrides'] {
  return {
    gmail: { enabled: overrides?.gmail?.enabled ?? true },
    calendar: { enabled: overrides?.calendar?.enabled ?? true },
    drive: { enabled: overrides?.drive?.enabled ?? true },
    docs: { enabled: overrides?.docs?.enabled ?? true },
    sheets: { enabled: overrides?.sheets?.enabled ?? true },
    web: { enabled: overrides?.web?.enabled ?? true },
  }
}

function normalizeSettings(settings: Settings): Settings {
  return {
    ...settings,
    defaultModel: settings.defaultModel?.trim() || DEFAULT_LLM_MODEL,
    ollamaBaseUrl: settings.ollamaBaseUrl || DEFAULT_OLLAMA_URL,
    agentOverrides: normalizeAgentOverrides(settings.agentOverrides),
  }
}

interface SettingsState {
  settings: Settings
  load: () => Promise<void>
  update: (patch: Partial<Settings>) => Promise<Settings>
}

export const useSettingsStore = create<SettingsState>((set) => ({
  settings: DEFAULTS,
  load: async () => {
    try {
      const saved = await fetchSettings()
      set({
        settings: normalizeSettings({
          ...DEFAULTS,
          ...saved,
          theme: saved.theme ?? DEFAULTS.theme,
        }),
      })
    } catch {
      set({ settings: DEFAULTS })
    }
  },
  update: async (patch) => {
    const next = await updateSettingsApi(patch)
    const normalized = normalizeSettings({ ...DEFAULTS, ...next })
    set({ settings: normalized })
    if (patch.ollamaBaseUrl !== undefined || patch.defaultModel !== undefined) {
      void useReadinessStore.getState().check({ silent: true })
    }
    return normalized
  },
}))
