'use client'

import Image from 'next/image'
import { Calendar, FileSpreadsheet, FileText, Globe, HardDrive, Mail, Sparkles } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { PRODUCT_NAME, PRODUCT_TAGLINE } from '@/lib/onboarding'
import { startersForAgent } from '@/lib/workflows'
import { ROOM_AGENTS, getAgentLabel, type RoomAgentName } from '@/lib/agents'
import type { AgentName } from '@/types'

const AGENT_ICONS: Record<RoomAgentName, typeof Mail> = {
  gmail: Mail,
  calendar: Calendar,
  drive: HardDrive,
  docs: FileText,
  sheets: FileSpreadsheet,
  web: Globe,
}

function firstName(fullName?: string) {
  return fullName?.trim().split(/\s+/)[0] || 'there'
}

interface Props {
  mode: 'picker' | 'room'
  agent?: AgentName | string | null
  agentEnabled?: Partial<Record<AgentName, boolean>>
  onSelectAgent: (agent: RoomAgentName) => void
  onSelectPrompt: (prompt: string) => void
}

export function WelcomeScreen({
  mode,
  agent,
  agentEnabled,
  onSelectAgent,
  onSelectPrompt,
}: Props) {
  const user = useAuthStore((s) => s.user)
  const name = firstName(user?.name)

  if (mode === 'room' && agent) {
    const starters = startersForAgent(agent)
    const label = getAgentLabel(agent)
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-6 py-8 overflow-y-auto">
        <Image
          src="/app-icon.png"
          alt={PRODUCT_NAME}
          width={56}
          height={56}
          className="rounded-2xl shadow-sm"
          priority
        />
        <div className="text-center space-y-1 max-w-md">
          <h2 className="text-app-display font-rounded text-foreground">{label}</h2>
          <p className="text-app-body text-muted-foreground">
            {agent === 'web'
              ? 'This chat is web research only.'
              : `This chat stays in ${label}. Web search is available for public research.`}
          </p>
        </div>
        {starters.length > 0 && (
          <div className="w-full max-w-lg">
            <p className="text-app-caption text-muted-foreground mb-2 flex items-center gap-1.5">
              <Sparkles size={13} /> Quick prompts
            </p>
            <div className="flex flex-wrap gap-2">
              {starters.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => onSelectPrompt(item.prompt)}
                  className="text-app-caption px-3 py-1.5 rounded-full border border-border hover:bg-muted/50 transition-colors text-foreground"
                >
                  {item.title}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    )
  }

  const visibleAgents = ROOM_AGENTS.filter((item) => agentEnabled?.[item.id] !== false)

  return (
    <div className="flex-1 flex flex-col items-center justify-center gap-6 py-8 overflow-y-auto">
      <Image
        src="/app-icon.png"
        alt={PRODUCT_NAME}
        width={56}
        height={56}
        className="rounded-2xl shadow-sm"
        priority
      />
      <div className="text-center space-y-1 max-w-md">
        <h2 className="text-app-display font-rounded text-foreground">Hi {name}, pick an agent</h2>
        <p className="text-app-body text-muted-foreground">{PRODUCT_TAGLINE}</p>
      </div>

      <div className="w-full max-w-lg grid grid-cols-1 sm:grid-cols-2 gap-2">
        {visibleAgents.length === 0 ? (
          <p className="sm:col-span-2 text-app-caption text-muted-foreground text-center">
            All agents are disabled. Enable one in Settings → Agents.
          </p>
        ) : (
          visibleAgents.map((item) => {
          const Icon = AGENT_ICONS[item.id]
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onSelectAgent(item.id)}
              className="text-left p-3 rounded-xl border border-border hover:bg-muted/50 transition-colors"
            >
              <p className="text-app-body font-medium text-foreground flex items-center gap-2">
                <Icon size={16} className="shrink-0 text-muted-foreground" />
                {item.label}
                {item.includesWeb ? (
                  <span className="text-app-caption font-normal text-muted-foreground">+ Web</span>
                ) : null}
              </p>
              <p className="text-app-caption text-muted-foreground mt-1">{item.description}</p>
            </button>
          )
          })
        )}
      </div>
    </div>
  )
}
