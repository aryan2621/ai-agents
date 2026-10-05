'use client'

import { API_BASE_URL } from '@/lib/config'
import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { fetchOAuthSetupStatus, saveOAuthCredentials } from '@/lib/api'
import { openExternalUrl as openExternal } from '@/lib/open-external'
import { toast } from 'sonner'
import { Check, ExternalLink } from 'lucide-react'
import { SettingsCard, SettingsSection, SettingsStatusBadge } from '../SettingsLayout'

const CONSOLE_URL = 'https://github.com/settings/developers'
/** The full steps (homepage URL, secret, troubleshooting) live in the user guide. */
const GUIDE_URL = 'https://github.com/aryan2621/ai-agents/blob/main/github-agent/docs/user.md#first-run'

/** The OAuth client setup. Also shown before sign-in (onboarding, sign-in screen), since
 * builds ship without a client: each person uses their own. */
export function OAuthSetupTab({ onSaved }: { onSaved?: () => void; onNavigateAway?: () => void } = {}) {
  const [clientId, setClientId] = useState('')
  const [clientSecret, setClientSecret] = useState('')
  const [configured, setConfigured] = useState(false)
  const [preview, setPreview] = useState('')
  const [saving, setSaving] = useState(false)

  const refresh = async () => {
    try {
      const status = await fetchOAuthSetupStatus()
      setConfigured(status.configured)
      setPreview(status.clientIdPreview)
    } catch {
      // backend may be starting
    }
  }

  useEffect(() => {
    void refresh()
  }, [])

  const handleSave = async () => {
    if (!clientId.trim() || !clientSecret.trim()) {
      toast.error('Enter both Client ID and Client Secret')
      return
    }
    setSaving(true)
    try {
      await saveOAuthCredentials(clientId.trim(), clientSecret.trim())
      toast.success('OAuth credentials saved')
      setClientSecret('')
      await refresh()
      onSaved?.()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to save credentials')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-8">
      <p className="text-app-caption text-muted-foreground leading-relaxed">
        Create an OAuth App in{' '}
        <button
          type="button"
          className="text-foreground underline inline-flex items-center gap-0.5"
          onClick={() => openExternal(CONSOLE_URL)}
        >
          GitHub Developer settings <ExternalLink size={12} />
        </button>{' '}
        with callback URL{' '}
        <code className="text-foreground bg-muted px-1 rounded">{API_BASE_URL}/auth/github/callback</code>,
        then paste its Client ID and Secret. They're saved only on this Mac.{' '}
        <button
          type="button"
          className="text-foreground underline inline-flex items-center gap-0.5"
          onClick={() => openExternal(GUIDE_URL)}
        >
          Setup guide <ExternalLink size={12} />
        </button>
      </p>

      {configured && (
        <SettingsStatusBadge variant="success">
          <Check size={12} />
          OAuth configured{preview ? ` (${preview})` : ''}
        </SettingsStatusBadge>
      )}

      <SettingsSection title={configured ? 'Use a different client' : 'Client ID and Secret'}>
        <SettingsCard className="p-4 space-y-4 divide-y-0">
          <div className="space-y-2">
            <label htmlFor="oauth-client-id" className="text-app-body text-foreground">
              Client ID
            </label>
            <Input
              id="oauth-client-id"
              value={clientId}
              onChange={(e) => setClientId(e.target.value)}
              placeholder="Ov23li…"
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="oauth-client-secret" className="text-app-body text-foreground">
              Client Secret
            </label>
            <Input
              id="oauth-client-secret"
              type="password"
              value={clientSecret}
              onChange={(e) => setClientSecret(e.target.value)}
              placeholder="GitHub client secret"
            />
          </div>

          <Button onClick={handleSave} disabled={saving} className="w-full sm:w-auto">
            {saving ? 'Saving…' : 'Save OAuth credentials'}
          </Button>

        </SettingsCard>
      </SettingsSection>
    </div>
  )
}
