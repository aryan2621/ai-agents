'use client'

import { useAuthStore } from '@/store/authStore'
import { useGitHubAuth } from '@/hooks/useGitHubAuth'
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import { toast } from 'sonner'
import { Check, X } from 'lucide-react'
import { SettingsCard, SettingsSection } from '../SettingsLayout'

const GITHUB_PERMISSION_IDS = new Set(['repo', 'notifications', 'read:user', 'user:email'])

export function AccountTab() {
  const { user, clearUser } = useAuthStore()
  const { signInWithGitHub } = useGitHubAuth()

  const permissions = user?.permissions ?? []
  const githubPermissions = permissions.filter((p) => GITHUB_PERMISSION_IDS.has(p.id))
  const missing = githubPermissions.filter((p) => !p.granted)

  const handleReauth = async () => {
    try {
      await signInWithGitHub({
        navigate: false,
        successMessage: 'Permissions updated',
      })
    } catch {
      toast.error('Failed to start re-authentication')
    }
  }

  return (
    <div className="space-y-8">
      <SettingsCard className="p-4 divide-y-0">
        <div className="flex items-center gap-4">
          <Avatar className="h-12 w-12">
            <AvatarImage src={user?.picture} />
            <AvatarFallback className="bg-muted">{user?.name?.[0]}</AvatarFallback>
          </Avatar>
          <div className="min-w-0">
            <p className="text-app-body font-medium text-foreground truncate">{user?.name}</p>
            <p className="text-app-caption text-muted-foreground truncate">{user?.email}</p>
          </div>
        </div>
      </SettingsCard>

      {githubPermissions.length > 0 && (
        <SettingsSection
          title="GitHub permissions"
          description={
            missing.length > 0
              ? 'Grant missing permissions to unlock related features.'
              : 'All GitHub permissions are granted.'
          }
        >
          <SettingsCard>
            {githubPermissions.map((permission) => (
              <div
                key={permission.id}
                className="flex items-center justify-between gap-3 px-4 py-3"
              >
                <span className="text-app-body text-foreground">{permission.label}</span>
                {permission.granted ? (
                  <span className="inline-flex items-center gap-1 text-app-caption text-green-600 dark:text-green-500">
                    <Check className="h-3.5 w-3.5" />
                    Granted
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-app-caption text-destructive">
                    <X className="h-3.5 w-3.5" />
                    Missing
                  </span>
                )}
              </div>
            ))}
          </SettingsCard>
        </SettingsSection>
      )}

      <SettingsSection title="Session">
        <div className="flex flex-col sm:flex-row gap-2">
          <Button onClick={handleReauth} variant="outline" className="sm:flex-1">
            {missing.length > 0 ? 'Grant missing permissions' : 'Re-authenticate'}
          </Button>
          <Button
            onClick={() => clearUser()}
            variant="outline"
            className="sm:flex-1 border-destructive/30 text-destructive hover:bg-destructive/10 hover:text-destructive"
          >
            Sign out
          </Button>
        </div>
      </SettingsSection>
    </div>
  )
}
