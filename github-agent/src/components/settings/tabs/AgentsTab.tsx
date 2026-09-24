'use client'

import { useSettingsStore } from '@/store/settingsStore'
import { Switch } from '@/components/ui/switch'
import { SettingsCard, SettingsRow } from '../SettingsLayout'
import { ROOM_AGENT_NAMES, getAgentLabel, type RoomAgentName } from '@/lib/agents'

const AGENT_INFO: Record<RoomAgentName, { description: string }> = {
  repos: { description: 'List, search, and inspect repositories. Web search is included in this room.' },
  issues: { description: 'Assigned issues, comments, and tracking. Web search is included in this room.' },
  pulls: { description: 'Open PRs, reviews, and merges. Web search is included in this room.' },
  code: { description: 'Files, search, and commits. Web search is included in this room.' },
  notifications: { description: 'Unread GitHub notifications. Web search is included in this room.' },
  web: { description: 'Research the public web via Tavily. Standalone research room.' },
}

export function AgentsTab() {
  const { settings, update } = useSettingsStore()

  return (
    <SettingsCard>
      {ROOM_AGENT_NAMES.map((agent) => {
        const info = AGENT_INFO[agent]
        const enabled = settings.agentOverrides[agent]?.enabled ?? true
        return (
          <SettingsRow
            key={agent}
            label={getAgentLabel(agent) ?? agent}
            description={info.description}
          >
            <Switch
              checked={enabled}
              onCheckedChange={(v) =>
                update({
                  agentOverrides: {
                    ...settings.agentOverrides,
                    [agent]: { ...settings.agentOverrides[agent], enabled: v },
                  },
                })
              }
            />
          </SettingsRow>
        )
      })}
    </SettingsCard>
  )
}
