'use client'

import { useEffect, useState, type ReactNode } from 'react'
import { LogOut, MessageSquare, Monitor, Moon, PanelLeftClose, PanelLeftOpen, Plus, Search, Settings, Sun } from 'lucide-react'
import { useChatStore } from '@/store/chatStore'
import { useAuthStore } from '@/store/authStore'
import { hydrateSidebarCollapsed, useAppViewStore } from '@/store/appViewStore'
import { ConversationList } from './ConversationList'
import { NewChatButton } from './NewChatButton'
import { SettingsModal } from '@/components/settings/SettingsModal'
import { Input } from '@/components/ui/input'
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar'
import { registerSettingsOpenHandler } from '@/hooks/useKeyboardShortcuts'
import { useTheme } from '@/hooks/useTheme'
import { iconStroke } from '@/lib/icon'
import { cn } from '@/lib/utils'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'

const THEME_ICONS = {
  light: Sun,
  dark: Moon,
  system: Monitor,
} as const

const THEME_LABELS = {
  light: 'Light mode',
  dark: 'Dark mode',
  system: 'System theme',
} as const

function IconTip({
  label,
  side = 'right',
  children,
}: {
  label: string
  side?: 'right' | 'top'
  children: ReactNode
}) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>{children}</TooltipTrigger>
      <TooltipContent side={side}>
        <p>{label}</p>
      </TooltipContent>
    </Tooltip>
  )
}

export function Sidebar() {
  const [search, setSearch] = useState('')
  const [settingsOpen, setSettingsOpen] = useState(false)
  const { user, clearUser } = useAuthStore()
  const startNewChat = useChatStore((s) => s.startNewChat)
  const { theme, cycleTheme } = useTheme()
  const openChat = useAppViewStore((s) => s.openChat)
  const openChatsList = useAppViewStore((s) => s.openChatsList)
  const chatsSubview = useAppViewStore((s) => s.chatsSubview)
  const collapsed = useAppViewStore((s) => s.sidebarCollapsed)
  const toggleSidebar = useAppViewStore((s) => s.toggleSidebar)

  const ThemeIcon = THEME_ICONS[theme]

  const handleOpenSettings = () => setSettingsOpen(true)

  const handleNewChat = () => {
    startNewChat()
    openChat()
  }

  const handleChatsList = () => {
    if (chatsSubview === 'list') openChat()
    else openChatsList()
  }

  useEffect(() => {
    hydrateSidebarCollapsed()
  }, [])

  useEffect(() => {
    registerSettingsOpenHandler(handleOpenSettings)
    return () => registerSettingsOpenHandler(() => {})
  }, [])

  const footerControls = (
    <>
      <IconTip label={THEME_LABELS[theme]} side={collapsed ? 'right' : 'top'}>
        <button
          type="button"
          onClick={cycleTheme}
          className="shrink-0 p-2 rounded-lg hover:bg-accent text-muted-foreground hover:text-foreground transition-colors duration-fast"
          aria-label={THEME_LABELS[theme]}
        >
          <ThemeIcon size={16} strokeWidth={iconStroke} />
        </button>
      </IconTip>
      <IconTip label="Settings" side={collapsed ? 'right' : 'top'}>
        <button
          type="button"
          onClick={handleOpenSettings}
          className="shrink-0 p-2 rounded-lg hover:bg-accent text-muted-foreground hover:text-foreground transition-colors duration-fast"
          aria-label="Settings"
        >
          <Settings size={16} strokeWidth={iconStroke} />
        </button>
      </IconTip>
      <IconTip label="Sign out" side={collapsed ? 'right' : 'top'}>
        <button
          type="button"
          onClick={() => clearUser()}
          className="shrink-0 p-2 rounded-lg text-destructive hover:bg-destructive/10 transition-colors duration-fast"
          aria-label="Sign out"
        >
          <LogOut size={16} strokeWidth={iconStroke} />
        </button>
      </IconTip>
    </>
  )

  return (
    <div
      className={cn(
        'shrink-0 flex flex-col min-h-0 bg-background border-r border-border transition-[width] duration-fast',
        collapsed ? 'w-14' : 'w-[300px]'
      )}
    >
      <TooltipProvider>
        {collapsed ? (
          <div className="flex flex-1 min-h-0 flex-col items-center py-2 gap-1">
            <IconTip label="Expand sidebar">
              <button
                type="button"
                onClick={toggleSidebar}
                className="p-2 rounded-lg hover:bg-accent text-muted-foreground hover:text-foreground transition-colors duration-fast"
                aria-label="Expand sidebar"
              >
                <PanelLeftOpen size={16} strokeWidth={iconStroke} />
              </button>
            </IconTip>
            <IconTip label="New chat">
              <button
                type="button"
                onClick={handleNewChat}
                className="p-2 rounded-lg hover:bg-accent text-muted-foreground hover:text-foreground transition-colors duration-fast"
                aria-label="New chat"
              >
                <Plus size={16} strokeWidth={iconStroke} />
              </button>
            </IconTip>
            <IconTip label="Chats">
              <button
                type="button"
                onClick={handleChatsList}
                className={cn(
                  'p-2 rounded-lg hover:bg-accent transition-colors duration-fast',
                  chatsSubview === 'list'
                    ? 'bg-accent text-foreground'
                    : 'text-muted-foreground hover:text-foreground'
                )}
                aria-label="Chats"
                aria-pressed={chatsSubview === 'list'}
              >
                <MessageSquare size={16} strokeWidth={iconStroke} />
              </button>
            </IconTip>
            <div className="flex-1" />
            {footerControls}
            <IconTip label={user?.name || 'Account'}>
              <Avatar className="h-7 w-7 mt-1">
                <AvatarImage src={user?.picture} />
                <AvatarFallback className="bg-muted text-app-caption">
                  {user?.name?.[0]}
                </AvatarFallback>
              </Avatar>
            </IconTip>
          </div>
        ) : (
          <>
            <div className="flex-1 min-h-0 m-2 flex flex-col rounded-xl border border-border bg-card/40 overflow-hidden">
              <div className="shrink-0 p-2 border-b border-border grid grid-cols-2 gap-1.5">
                <NewChatButton onClick={handleNewChat} />
                <button
                  type="button"
                  onClick={handleChatsList}
                  aria-pressed={chatsSubview === 'list'}
                  className={cn(
                    'inline-flex items-center justify-center gap-2 h-9 rounded-lg border border-border text-sm font-medium transition-colors duration-fast',
                    chatsSubview === 'list'
                      ? 'bg-accent text-foreground'
                      : 'bg-transparent text-foreground hover:bg-accent'
                  )}
                >
                  <MessageSquare size={14} strokeWidth={iconStroke} />
                  Chats
                </button>
              </div>

              <div className="shrink-0 p-2 border-b border-border flex items-center gap-1">
                <div className="relative flex-1 min-w-0">
                  <Search
                    size={13}
                    strokeWidth={iconStroke}
                    className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground"
                  />
                  <Input
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Search chats..."
                    className="pl-8 h-8 text-app-caption bg-background border-border text-foreground placeholder:text-muted-foreground focus-visible:ring-1 focus-visible:ring-ring"
                  />
                </div>
                <IconTip label="Collapse sidebar" side="top">
                  <button
                    type="button"
                    onClick={toggleSidebar}
                    className="shrink-0 p-2 rounded-lg hover:bg-accent text-muted-foreground hover:text-foreground transition-colors duration-fast"
                    aria-label="Collapse sidebar"
                  >
                    <PanelLeftClose size={16} strokeWidth={iconStroke} />
                  </button>
                </IconTip>
              </div>

              <div className="flex-1 min-h-0 overflow-y-auto scrollbar-none">
                <ConversationList searchQuery={search} />
              </div>
            </div>

            <div className="p-2 border-t border-border shrink-0">
              <div className="flex items-center gap-0.5">
                <div className="flex-1 flex items-center gap-2.5 px-2 py-2 min-w-0">
                  <Avatar className="h-7 w-7 shrink-0">
                    <AvatarImage src={user?.picture} />
                    <AvatarFallback className="bg-muted text-app-caption">
                      {user?.name?.[0]}
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex-1 min-w-0 text-left">
                    <p className="text-app-caption font-medium text-foreground truncate">{user?.name}</p>
                    <p className="text-app-caption text-muted-foreground truncate">{user?.email}</p>
                  </div>
                </div>
                {footerControls}
              </div>
            </div>
          </>
        )}
      </TooltipProvider>

      <SettingsModal open={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </div>
  )
}
