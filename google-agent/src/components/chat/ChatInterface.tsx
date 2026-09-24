'use client'

import { useRef, useEffect } from 'react'
import { useChatStore } from '@/store/chatStore'
import { useSettingsStore } from '@/store/settingsStore'
import { MessageList } from './MessageList'
import { ChatInput } from './ChatInput'
import { WelcomeScreen } from './WelcomeScreen'
import { SystemBlockedScreen } from '@/components/layout/SystemBlockedScreen'
import { useAppReadiness } from '@/hooks/useAppReadiness'
import { useChatSend } from '@/hooks/useChatSend'
import { cancelActiveStream } from '@/lib/streaming'
import { getAgentLabel, isRoomAgent, type RoomAgentName } from '@/lib/agents'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { toast } from 'sonner'
import type { AgentName, Conversation } from '@/types'

export function ChatInterface() {
  const {
    activeId,
    conversations,
    setGenerating,
    isGenerating,
    createConversation,
    setActiveId,
    isLoadingChats,
    isSwitchingChat,
  } = useChatStore()
  const pendingStarterPrompt = useChatStore((s) => s.pendingStarterPrompt)
  const { settings } = useSettingsStore()
  const { loading: readinessLoading, ready, issues, retry } = useAppReadiness()
  const chatBlocked = !readinessLoading && !ready
  const chatDisabled = readinessLoading || !ready
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const lastConvRef = useRef<Conversation | undefined>(undefined)

  const activeConv = conversations.find((c) => c.id === activeId)
  if (activeConv?.messages.length) {
    lastConvRef.current = activeConv
  }
  const displayConv =
    activeConv ?? (isSwitchingChat ? lastConvRef.current : undefined)
  const isEmptyChat = !displayConv || displayConv.messages.length === 0
  const roomAgent = isRoomAgent(displayConv?.agentFilter) ? displayConv.agentFilter : null
  const showPicker = !roomAgent && isEmptyChat
  const showLegacyBanner = Boolean(displayConv && !roomAgent && !isEmptyChat)
  const inputLockedToRoom = !roomAgent || showLegacyBanner

  const {
    handleSend,
    handleEditResend,
    handleGrantOAuthPermission,
    cancelPendingOAuth,
    oauthPermissionError,
    isReauthing,
  } = useChatSend({
    activeId,
    roomAgent,
    chatDisabled,
    isGenerating,
    settings,
  })

  useEffect(() => {
    if (chatDisabled || !isEmptyChat || showPicker) return
    requestAnimationFrame(() => inputRef.current?.focus())
  }, [activeId, chatDisabled, isEmptyChat, showPicker])

  useEffect(() => {
    const pending = useChatStore.getState().consumePendingAutoSend()
    if (!pending || chatDisabled || isGenerating) return
    if (pending.convId !== activeId) return
    void handleSend(pending.text)
  }, [activeId, chatDisabled, isGenerating, conversations])

  useEffect(() => {
    const starter = useChatStore.getState().consumePendingStarterPrompt()
    if (!starter || chatDisabled || isGenerating) return
    void (async () => {
      const convId = await createConversation(starter.agent as RoomAgentName)
      setActiveId(convId)
      void handleSend(starter.text, convId)
    })()
  }, [chatDisabled, isGenerating, pendingStarterPrompt, createConversation, setActiveId])

  const streamingContentLength = displayConv?.messages
    .filter((m) => m.isStreaming)
    .reduce((sum, m) => sum + m.content.length, 0)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [displayConv?.messages.length, streamingContentLength])

  const handleSelectAgent = async (agent: RoomAgentName) => {
    try {
      const id = await createConversation(agent)
      setActiveId(id)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to start chat')
    }
  }

  const isEmpty = isEmptyChat
  const showChatLoader = isLoadingChats || isSwitchingChat
  const agentEnabled = Object.fromEntries(
    Object.entries(settings.agentOverrides).map(([key, value]) => [key, value.enabled])
  ) as Partial<Record<AgentName, boolean>>

  return (
    <>
      <div className="flex-1 min-h-0 flex flex-col w-full">
        <div className="flex-1 flex flex-col min-h-0 w-full max-w-[48rem] mx-auto px-4">
          <div className="relative flex-1 min-h-0 overflow-y-auto scrollbar-none flex flex-col">
            {showChatLoader && (
              <div className="absolute inset-0 z-10 flex items-center justify-center bg-background/90">
                <div className="w-5 h-5 border-2 border-muted border-t-muted-foreground rounded-full animate-spin" />
              </div>
            )}
            {readinessLoading && isEmpty ? (
              <div className="flex-1 flex items-center justify-center">
                <div className="w-5 h-5 border-2 border-muted border-t-muted-foreground rounded-full animate-spin" />
              </div>
            ) : chatBlocked && isEmpty ? (
              <SystemBlockedScreen loading={readinessLoading} issues={issues} onRetry={retry} />
            ) : showPicker ? (
              <WelcomeScreen
                mode="picker"
                agentEnabled={agentEnabled}
                onSelectAgent={(agent) => void handleSelectAgent(agent)}
                onSelectPrompt={() => {}}
              />
            ) : isEmpty ? (
              <WelcomeScreen
                mode="room"
                agent={roomAgent}
                agentEnabled={agentEnabled}
                onSelectAgent={(agent) => void handleSelectAgent(agent)}
                onSelectPrompt={handleSend}
              />
            ) : (
              <div className="py-6 pb-8">
                <MessageList
                  messages={displayConv!.messages}
                  isGenerating={isGenerating}
                  onEditResend={handleEditResend}
                />
                <div ref={bottomRef} />
              </div>
            )}
          </div>

          <div className="shrink-0 pb-4">
            {chatBlocked && !isEmpty ? (
              <div className="mb-3 rounded-xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-app-caption text-destructive">
                {issues[0]?.message ?? 'App is not ready. Fix system issues before sending messages.'}
              </div>
            ) : null}
            {showLegacyBanner ? (
              <div className="mb-3 rounded-xl border border-border bg-muted/40 px-4 py-3 text-app-caption text-muted-foreground">
                This chat is not tied to an agent. Start a new chat from the home screen.
              </div>
            ) : null}
            {!showPicker && !showLegacyBanner ? (
              <ChatInput
                ref={inputRef}
                onSend={handleSend}
                onStop={() => {
                  cancelActiveStream()
                  setGenerating(false)
                }}
                isGenerating={isGenerating}
                isAwaitingApproval={oauthPermissionError !== null}
                disabled={chatDisabled || inputLockedToRoom}
                checking={readinessLoading}
                placeholder={
                  roomAgent
                    ? `Message ${getAgentLabel(roomAgent) ?? roomAgent}…`
                    : 'Ask anything'
                }
              />
            ) : null}
          </div>
        </div>
      </div>

      <AlertDialog
        open={oauthPermissionError !== null}
        onOpenChange={() => {
          /* no dismiss without explicit cancel */
        }}
      >
        <AlertDialogContent onEscapeKeyDown={(e) => e.preventDefault()}>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {oauthPermissionError?.label ?? 'Google'} permission required
            </AlertDialogTitle>
            <AlertDialogDescription>
              {oauthPermissionError?.message ??
                'This action needs a Google permission you did not grant. Re-authenticate to grant access.'}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isReauthing} onClick={cancelPendingOAuth}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction onClick={handleGrantOAuthPermission} disabled={isReauthing}>
              {isReauthing ? 'Waiting for Google…' : 'Grant permission in Google'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
