import { create } from 'zustand'
import { fetchSettings, updateSettingsApi } from '@/lib/api'
import { useReadinessStore } from '@/store/readinessStore'
import type { Settings } from '@/types'

/** '' = automatic: the recommended built-in model that's downloaded. */
const DEFAULT_LLM_MODEL = ''

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
  agentOverrides: {
    repos: { enabled: true },
    issues: { enabled: true },
    pulls: { enabled: true },
    code: { enabled: true },
    notifications: { enabled: true },
    web: { enabled: true },
  },
}

function normalizeAgentOverrides(
  overrides: Settings['agentOverrides'] | undefined
): Settings['agentOverrides'] {
  return {
    repos: { enabled: overrides?.repos?.enabled ?? true },
    issues: { enabled: overrides?.issues?.enabled ?? true },
    pulls: { enabled: overrides?.pulls?.enabled ?? true },
    code: { enabled: overrides?.code?.enabled ?? true },
    notifications: { enabled: overrides?.notifications?.enabled ?? true },
    web: { enabled: overrides?.web?.enabled ?? true },
  }
}

function normalizeSettings(settings: Settings): Settings {
  return {
    ...settings,
    defaultModel: settings.defaultModel?.trim() || DEFAULT_LLM_MODEL,
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
    if (patch.defaultModel !== undefined) {
      void useReadinessStore.getState().check({ silent: true })
    }
    return normalized
  },
}))
