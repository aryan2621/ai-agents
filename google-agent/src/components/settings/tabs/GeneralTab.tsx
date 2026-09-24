'use client'

import { useSettingsStore } from '@/store/settingsStore'
import { useChatStore } from '@/store/chatStore'
import { Button } from '@/components/ui/button'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import { Switch } from '@/components/ui/switch'
import type { ThemeMode } from '@/types'
import {
  SegmentedControl,
  SettingsCard,
  SettingsRow,
  SettingsSection,
} from '../SettingsLayout'

export function GeneralTab() {
  const { settings, update } = useSettingsStore()
  const clearAllConversations = useChatStore((s) => s.clearAllConversations)

  const themes: { value: ThemeMode; label: string }[] = [
    { value: 'light', label: 'Light' },
    { value: 'dark', label: 'Dark' },
    { value: 'system', label: 'System' },
  ]

  return (
    <div className="space-y-8">
      <SettingsSection title="Appearance">
        <SettingsCard>
          <SettingsRow label="Theme" description="Choose how the app looks">
            <SegmentedControl
              value={settings.theme}
              options={themes}
              onChange={(theme) => update({ theme })}
            />
          </SettingsRow>
          <SettingsRow label="Font size" description="Adjust text size across the app">
            <SegmentedControl
              value={settings.fontSize}
              options={[
                { value: 'sm' as const, label: 'S' },
                { value: 'md' as const, label: 'M' },
                { value: 'lg' as const, label: 'L' },
              ]}
              onChange={(fontSize) => update({ fontSize })}
            />
          </SettingsRow>
        </SettingsCard>
      </SettingsSection>

      <SettingsSection title="Chat">
        <SettingsCard>
          <SettingsRow
            label="Send on Enter"
            description="Press Enter to send; Shift+Enter for a new line"
          >
            <Switch
              checked={settings.sendOnEnter}
              onCheckedChange={(v) => update({ sendOnEnter: v })}
            />
          </SettingsRow>
          <SettingsRow label="Auto-scroll chat" description="Scroll to the latest message automatically">
            <Switch
              checked={settings.autoScroll}
              onCheckedChange={(v) => update({ autoScroll: v })}
            />
          </SettingsRow>
        </SettingsCard>
      </SettingsSection>

      <SettingsSection
        title="Data"
        description="Permanently remove all conversation history from this device."
      >
        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button
              variant="outline"
              className="border-destructive/30 text-destructive hover:bg-destructive/10 hover:text-destructive"
            >
              Clear all conversations
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Clear all conversations?</AlertDialogTitle>
              <AlertDialogDescription>
                This will permanently delete all chat history. This action cannot be undone.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction
                onClick={() => clearAllConversations()}
                className="bg-destructive hover:bg-destructive/90"
              >
                Clear all
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </SettingsSection>
    </div>
  )
}
