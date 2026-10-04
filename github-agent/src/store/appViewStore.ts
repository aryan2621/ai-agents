import { create } from 'zustand'

export type MainView = 'chats'
export type ChatsSubview = 'list' | 'chat'

interface AppViewState {
  mainView: MainView
  chatsSubview: ChatsSubview
  setMainView: (view: MainView) => void
  setChatsSubview: (subview: ChatsSubview) => void
  openChatsList: () => void
  openChat: () => void
}

export const useAppViewStore = create<AppViewState>((set) => ({
  mainView: 'chats',
  chatsSubview: 'chat',

  setMainView: (mainView) => set({ mainView }),

  setChatsSubview: (chatsSubview) => set({ chatsSubview }),

  openChatsList: () => set({ mainView: 'chats', chatsSubview: 'list' }),

  openChat: () => set({ mainView: 'chats', chatsSubview: 'chat' }),
}))

