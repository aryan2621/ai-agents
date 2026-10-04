'use client'

import { useState, type ReactNode } from 'react'
import { Calendar, FileSpreadsheet, FileText, Globe, HardDrive, Mail } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { PRODUCT_TAGLINE } from '@/lib/onboarding'
import { startersForAgent } from '@/lib/workflows'
import { ROOM_AGENTS, getAgentLabel, type RoomAgentName } from '@/lib/agents'
import { iconStroke } from '@/lib/icon'
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

function greeting() {
  const hour = new Date().getHours()
  if (hour < 5) return 'Up late'
  if (hour < 12) return 'Good morning'
  if (hour < 18) return 'Good afternoon'
  return 'Good evening'
}

/** The clay burst that sits beside the greeting, after Claude's mark. */
function Spark() {
  return (
    <svg viewBox="0 0 32 32" className="h-9 w-9 shrink-0 text-brand" aria-hidden>
      {Array.from({ length: 12 }, (_, i) => (
        <line
          key={i}
          x1="16"
          y1="16"
          x2="16"
          y2={i % 2 ? 5 : 2.5}
          stroke="currentColor"
          strokeWidth="2.6"
          strokeLinecap="round"
          transform={`rotate(${i * 30} 16 16)`}
        />
      ))}
    </svg>
  )
}

function Chip({
  icon,
  label,
  onClick,
  title,
  onHover,
}: {
  icon?: ReactNode
  label: string
  onClick: () => void
  title?: string
  onHover?: (active: boolean) => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      title={title}
      onMouseEnter={() => onHover?.(true)}
      onMouseLeave={() => onHover?.(false)}
      onFocus={() => onHover?.(true)}
      onBlur={() => onHover?.(false)}
      className="inline-flex items-center gap-2 h-9 px-3.5 rounded-xl border border-border bg-background text-sm text-foreground/85 hover:bg-accent hover:text-foreground transition-colors duration-fast"
    >
      {icon}
      {label}
    </button>
  )
}

interface Props {
  mode: 'picker' | 'room'
  agent?: AgentName | string | null
  agentEnabled?: Partial<Record<AgentName, boolean>>
  /** The composer, placed under the greeting the way Claude centers it on a new chat. */
  composer?: ReactNode
  onSelectAgent: (agent: RoomAgentName) => void
  onSelectPrompt: (prompt: string) => void
}

export function WelcomeScreen({
  mode,
  agent,
  agentEnabled,
  composer,
  onSelectAgent,
  onSelectPrompt,
}: Props) {
  const user = useAuthStore((s) => s.user)
  const name = firstName(user?.name)
  const [hovered, setHovered] = useState<string | null>(null)

  if (mode === 'room' && agent) {
    const starters = startersForAgent(agent)
    const label = getAgentLabel(agent)
    const Icon = AGENT_ICONS[agent as RoomAgentName]
    return (
      <div className="flex-1 flex flex-col items-center justify-center py-10">
        <div className="w-full max-w-2xl">
          <div className="flex items-center justify-center gap-3 mb-2">
            <Spark />
            <h1 className="text-[2.5rem] leading-tight font-serif font-normal text-foreground">
              {label}
            </h1>
          </div>
          <p className="text-center text-app-body text-muted-foreground mb-7">
            {agent === 'web'
              ? 'This chat is web research only.'
              : `This chat stays in ${label}. Web search is available for public research.`}
          </p>
          {composer}
          {starters.length > 0 && (
            <div className="mt-4 flex flex-wrap justify-center gap-2">
              {starters.map((item) => (
                <Chip
                  key={item.id}
                  icon={Icon ? <Icon size={14} strokeWidth={iconStroke} className="text-muted-foreground" /> : null}
                  label={item.title}
                  onClick={() => onSelectPrompt(item.prompt)}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    )
  }

  const visibleAgents = ROOM_AGENTS.filter((item) => agentEnabled?.[item.id] !== false)

  return (
    <div className="flex-1 flex flex-col items-center justify-center py-10">
      <div className="w-full max-w-2xl">
        <div className="flex items-center justify-center gap-3 mb-3">
          <Spark />
          <h1 className="text-[2.5rem] leading-tight font-serif font-normal text-foreground">
            {greeting()}, {name}
          </h1>
        </div>
        <p className="text-center text-app-body text-muted-foreground mb-8">{PRODUCT_TAGLINE}</p>
        {visibleAgents.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center">
            All agents are disabled. Enable one in Settings → Agents.
          </p>
        ) : (
          <div className="flex flex-wrap justify-center gap-2">
            {visibleAgents.map((item) => {
              const Icon = AGENT_ICONS[item.id]
              return (
                <Chip
                  key={item.id}
                  icon={<Icon size={15} strokeWidth={iconStroke} className="text-brand" />}
                  label={item.label}
                  title={item.description}
                  onHover={(active) => setHovered(active ? item.description : null)}
                  onClick={() => onSelectAgent(item.id)}
                />
              )
            })}
          </div>
        )}
        <p className="mt-4 min-h-5 text-center text-sm text-muted-foreground">
          {hovered ?? (visibleAgents.length ? 'Pick an agent to start a chat.' : '')}
        </p>
      </div>
    </div>
  )
}
