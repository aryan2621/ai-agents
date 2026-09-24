import type { ComponentType } from 'react'
import {
  Bot,
  Cpu,
  Globe,
  KeyRound,
  Palette,
  User,
  type LucideIcon,
} from 'lucide-react'
import { GeneralTab } from './tabs/GeneralTab'
import { ModelsTab } from './tabs/ModelsTab'
import { AgentsTab } from './tabs/AgentsTab'
import { WebSearchTab } from './tabs/WebSearchTab'
import { AccountTab } from './tabs/AccountTab'
import { OAuthSetupTab } from './tabs/OAuthSetupTab'

export type SettingsSectionId =
  | 'general'
  | 'models'
  | 'agents'
  | 'web'
  | 'oauth'
  | 'account'

export interface SettingsNavItem {
  id: SettingsSectionId
  label: string
  description: string
  icon: LucideIcon
  component: ComponentType<{ onNavigateAway?: () => void }>
}

export interface SettingsNavGroup {
  label: string
  items: SettingsNavItem[]
}

export const SETTINGS_NAV_GROUPS: SettingsNavGroup[] = [
  {
    label: 'Appearance',
    items: [
      {
        id: 'general',
        label: 'General',
        description: 'Theme, typography, and chat behavior',
        icon: Palette,
        component: GeneralTab,
      },
    ],
  },
  {
    label: 'AI',
    items: [
      {
        id: 'models',
        label: 'Models',
        description: 'Ollama local models for agent rooms',
        icon: Cpu,
        component: ModelsTab,
      },
      {
        id: 'agents',
        label: 'Agents',
        description: 'Enable or disable agent rooms',
        icon: Bot,
        component: AgentsTab,
      },
    ],
  },
  {
    label: 'Integrations',
    items: [
      {
        id: 'web',
        label: 'Web search',
        description: 'Tavily API for public web research',
        icon: Globe,
        component: WebSearchTab,
      },
      {
        id: 'oauth',
        label: 'Google OAuth',
        description: 'Desktop OAuth client credentials',
        icon: KeyRound,
        component: OAuthSetupTab,
      },
    ],
  },
  {
    label: 'Account',
    items: [
      {
        id: 'account',
        label: 'Profile',
        description: 'Google account and permissions',
        icon: User,
        component: AccountTab,
      },
    ],
  },
]

export const SETTINGS_NAV_ITEMS = SETTINGS_NAV_GROUPS.flatMap((group) => group.items)
