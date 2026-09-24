import { create } from 'zustand'

export type MainView = 'chats'
export type ChatsSubview = 'list' | 'chat'

const SIDEBAR_COLLAPSED_KEY = 'google-agent.sidebar-collapsed'

function readSidebarCollapsed(): boolean {
  if (typeof window === 'undefined') return false
  try {
    return window.localStorage.getItem(SIDEBAR_COLLAPSED_KEY) === '1'
  } catch {
    return false
  }
}

function persistSidebarCollapsed(collapsed: boolean) {
  try {
    window.localStorage.setItem(SIDEBAR_COLLAPSED_KEY, collapsed ? '1' : '0')
  } catch {
    // ignore quota / private mode
  }
}

interface AppViewState {
  mainView: MainView
  chatsSubview: ChatsSubview
  sidebarCollapsed: boolean
  setMainView: (view: MainView) => void
  setChatsSubview: (subview: ChatsSubview) => void
  openChatsList: () => void
  openChat: () => void
  setSidebarCollapsed: (collapsed: boolean) => void
  toggleSidebar: () => void
}

export const useAppViewStore = create<AppViewState>((set) => ({
  mainView: 'chats',
  chatsSubview: 'chat',
  sidebarCollapsed: false,

  setMainView: (mainView) => set({ mainView }),

  setChatsSubview: (chatsSubview) => set({ chatsSubview }),

  openChatsList: () => set({ mainView: 'chats', chatsSubview: 'list' }),

  openChat: () => set({ mainView: 'chats', chatsSubview: 'chat' }),

  setSidebarCollapsed: (collapsed) => {
    persistSidebarCollapsed(collapsed)
    set({ sidebarCollapsed: collapsed })
  },

  toggleSidebar: () =>
    set((state) => {
      const sidebarCollapsed = !state.sidebarCollapsed
      persistSidebarCollapsed(sidebarCollapsed)
      return { sidebarCollapsed }
    }),
}))

export function hydrateSidebarCollapsed() {
  useAppViewStore.getState().setSidebarCollapsed(readSidebarCollapsed())
}
