'use client'

import { useEffect, useState, type ReactNode } from 'react'
import Image from 'next/image'
import {
  ChevronsUpDown,
  LogOut,
  MessagesSquare,
  Monitor,
  Moon,
  PanelLeft,
  Plus,
  Search,
  Settings,
  Sun,
} from 'lucide-react'
import { useChatStore } from '@/store/chatStore'
import { useAuthStore } from '@/store/authStore'
import { hydrateSidebarCollapsed, useAppViewStore } from '@/store/appViewStore'
import { ConversationList } from './ConversationList'
import { SettingsModal } from '@/components/settings/SettingsModal'
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { registerSettingsOpenHandler } from '@/hooks/useKeyboardShortcuts'
import { useTheme } from '@/hooks/useTheme'
import { iconStroke } from '@/lib/icon'
import { PRODUCT_NAME } from '@/lib/onboarding'
import { cn } from '@/lib/utils'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'

const THEME_ICONS = { light: Sun, dark: Moon, system: Monitor } as const
const THEME_LABELS = { light: 'Light', dark: 'Dark', system: 'Match system' } as const

function IconTip({ label, children }: { label: string; children: ReactNode }) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>{children}</TooltipTrigger>
      <TooltipContent side="right">
        <p>{label}</p>
      </TooltipContent>
    </Tooltip>
  )
}

/** A sidebar row in Claude's style: icon + label, quiet until hovered or active. */
function NavRow({
  icon,
  label,
  active = false,
  collapsed,
  onClick,
}: {
  icon: ReactNode
  label: string
  active?: boolean
  collapsed: boolean
  onClick: () => void
}) {
  const row = (
    <button
      type="button"
      onClick={onClick}
      aria-label={label}
      aria-pressed={active}
      className={cn(
        'flex items-center gap-2.5 rounded-lg text-sm transition-colors duration-fast',
        collapsed ? 'h-9 w-9 justify-center' : 'h-9 w-full px-2',
        active
          ? 'bg-accent text-foreground'
          : 'text-foreground/80 hover:bg-accent hover:text-foreground'
      )}
    >
      {icon}
      {!collapsed && <span className="truncate">{label}</span>}
    </button>
  )
  return collapsed ? <IconTip label={label}>{row}</IconTip> : row
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

  useEffect(() => {
    hydrateSidebarCollapsed()
  }, [])

  useEffect(() => {
    registerSettingsOpenHandler(handleOpenSettings)
    return () => registerSettingsOpenHandler(() => {})
  }, [])

  const initials = (user?.name || user?.email || '?').trim()[0]?.toUpperCase()

  return (
    <aside
      className={cn(
        'shrink-0 flex flex-col min-h-0 bg-sidebar border-r border-border transition-[width] duration-fast',
        collapsed ? 'w-[52px] items-center' : 'w-[272px]'
      )}
    >
      <TooltipProvider delayDuration={300}>
        <div className="mac-window-space shrink-0 w-full" data-tauri-drag-region />
        <div className={cn('flex items-center h-12 shrink-0', collapsed ? 'justify-center' : 'pl-4 pr-3 gap-2.5')}>
          {!collapsed && (
            <>
              <Image src="/app-icon.png" alt="" width={26} height={26} className="shrink-0 rounded-[7px]" />
              <span className="flex-1 truncate font-serif text-xl font-medium text-foreground">
                {PRODUCT_NAME}
              </span>
            </>
          )}
          <IconTip label={collapsed ? 'Open sidebar' : 'Close sidebar'}>
            <button
              type="button"
              onClick={toggleSidebar}
              className="h-8 w-8 flex items-center justify-center rounded-lg text-muted-foreground hover:bg-accent hover:text-foreground transition-colors duration-fast"
              aria-label={collapsed ? 'Open sidebar' : 'Close sidebar'}
            >
              <PanelLeft size={18} strokeWidth={iconStroke} />
            </button>
          </IconTip>
        </div>

        <nav className={cn('shrink-0 flex flex-col gap-0.5 pb-3', collapsed ? 'items-center' : 'px-2')}>
          <NavRow
            collapsed={collapsed}
            onClick={handleNewChat}
            label="New chat"
            icon={
              <span className="h-6 w-6 shrink-0 rounded-full bg-brand text-brand-foreground flex items-center justify-center">
                <Plus size={15} strokeWidth={2.25} />
              </span>
            }
          />
          <NavRow
            collapsed={collapsed}
            onClick={() => (chatsSubview === 'list' ? openChat() : openChatsList())}
            label="Chats"
            active={chatsSubview === 'list'}
            icon={
              <span className="h-6 w-6 shrink-0 flex items-center justify-center">
                <MessagesSquare size={17} strokeWidth={iconStroke} />
              </span>
            }
          />
        </nav>

        {collapsed ? (
          <div className="flex-1" />
        ) : (
          <div className="flex-1 min-h-0 flex flex-col">
            <div className="px-2 pb-2">
              <label className="flex items-center gap-2 h-8 px-2.5 rounded-lg border border-border bg-popover text-muted-foreground focus-within:border-input transition-colors duration-fast">
                <Search size={14} strokeWidth={iconStroke} className="shrink-0" />
                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search chats..."
                  className="flex-1 min-w-0 bg-transparent text-sm text-foreground placeholder:text-muted-foreground outline-none"
                />
              </label>
            </div>
            <div className="flex-1 min-h-0 overflow-y-auto scrollbar-none px-2 pb-2">
              <ConversationList searchQuery={search} />
            </div>
          </div>
        )}

        <div className={cn('shrink-0 border-t border-border', collapsed ? 'py-2' : 'p-2')}>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                type="button"
                className={cn(
                  'flex items-center gap-2.5 rounded-lg text-left hover:bg-accent transition-colors duration-fast',
                  collapsed ? 'h-9 w-9 justify-center' : 'w-full px-2 py-1.5'
                )}
                aria-label="Account menu"
              >
                <Avatar className="h-7 w-7 shrink-0">
                  <AvatarImage src={user?.picture} />
                  <AvatarFallback className="bg-foreground text-background text-xs font-medium">
                    {initials}
                  </AvatarFallback>
                </Avatar>
                {!collapsed && (
                  <>
                    <span className="flex-1 min-w-0">
                      <span className="block text-sm font-medium text-foreground truncate">
                        {user?.name || 'Account'}
                      </span>
                      {user?.email ? (
                        <span className="block text-xs text-muted-foreground truncate">{user.email}</span>
                      ) : null}
                    </span>
                    <ChevronsUpDown size={14} strokeWidth={iconStroke} className="text-muted-foreground" />
                  </>
                )}
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent side="top" align="start" className="w-60">
              {user?.email ? (
                <>
                  <DropdownMenuLabel className="font-normal text-xs text-muted-foreground truncate">
                    {user.email}
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />
                </>
              ) : null}
              <DropdownMenuItem onClick={handleOpenSettings} className="gap-2 cursor-pointer">
                <Settings size={14} strokeWidth={iconStroke} /> Settings
              </DropdownMenuItem>
              <DropdownMenuItem
                onSelect={(e) => {
                  e.preventDefault()
                  cycleTheme()
                }}
                className="gap-2 cursor-pointer"
              >
                <ThemeIcon size={14} strokeWidth={iconStroke} /> Theme: {THEME_LABELS[theme]}
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => clearUser()} className="gap-2 cursor-pointer text-destructive">
                <LogOut size={14} strokeWidth={iconStroke} /> Sign out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </TooltipProvider>

      <SettingsModal open={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </aside>
  )
}
