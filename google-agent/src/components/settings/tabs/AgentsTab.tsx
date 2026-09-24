'use client'

import { useSettingsStore } from '@/store/settingsStore'
import { Switch } from '@/components/ui/switch'
import { SettingsCard, SettingsRow } from '../SettingsLayout'
import { ROOM_AGENT_NAMES, getAgentLabel, type RoomAgentName } from '@/lib/agents'

const AGENT_INFO: Record<RoomAgentName, { description: string }> = {
  gmail: { description: 'Read, search, and manage emails. Web search is included in this room.' },
  calendar: { description: 'View and manage calendar events. Web search is included in this room.' },
  drive: { description: 'Search and manage Drive files. Web search is included in this room.' },
  docs: { description: 'Read and edit Google Docs. Web search is included in this room.' },
  sheets: { description: 'Read and analyze spreadsheets. Web search is included in this room.' },
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
