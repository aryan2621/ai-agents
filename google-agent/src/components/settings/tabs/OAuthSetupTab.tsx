'use client'

import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { fetchOAuthSetupStatus, saveOAuthCredentials } from '@/lib/api'
import { openExternalUrl as openExternal } from '@/lib/open-external'
import { toast } from 'sonner'
import { Check, ExternalLink } from 'lucide-react'
import { SettingsCard, SettingsSection, SettingsStatusBadge } from '../SettingsLayout'

/** The steps to make a client (Google Cloud project, APIs, sign-in screen, Desktop client) live here. */
const GUIDE_URL = 'https://github.com/aryan2621/ai-agents/blob/main/google-agent/docs/google-setup.md'

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
    const id = clientId.trim()
    if (!id || !clientSecret.trim()) {
      toast.error('Enter both Client ID and Client Secret')
      return
    }
    if (!id.endsWith('.apps.googleusercontent.com')) {
      toast.error("That isn't a Client ID. It ends in .apps.googleusercontent.com.")
      return
    }
    setSaving(true)
    try {
      await saveOAuthCredentials(id, clientSecret.trim())
      toast.success('Saved. You can sign in with Google now.')
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
    <div className="space-y-6">
      <p className="text-app-caption text-muted-foreground leading-relaxed">
        Google Agent signs in with your own free Google Cloud project, so only your account and keys
        are used. They're saved only on this Mac.{' '}
        <button
          type="button"
          className="inline-flex items-center gap-0.5 text-foreground underline"
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
              placeholder="ends in .apps.googleusercontent.com"
              spellCheck={false}
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
              placeholder="starts with GOCSPX-"
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
