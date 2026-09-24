'use client'

import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { fetchOAuthSetupStatus, saveOAuthCredentials } from '@/lib/api'
import { openExternalUrl as openExternal } from '@/lib/open-external'
import { toast } from 'sonner'
import { Check, ExternalLink } from 'lucide-react'
import { SettingsCard, SettingsSection, SettingsStatusBadge } from '../SettingsLayout'

const CONSOLE_URL = 'https://github.com/settings/developers'

export function OAuthSetupTab() {
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
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to save credentials')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-8">
      {configured && (
        <SettingsStatusBadge variant="success">
          <Check size={12} />
          OAuth configured{preview ? ` (${preview})` : ''}
        </SettingsStatusBadge>
      )}

      <SettingsSection title="Setup steps">
        <SettingsCard className="p-4 divide-y-0">
          <ol className="space-y-3 text-app-caption text-muted-foreground list-decimal list-inside leading-relaxed">
            <li>
              Open{' '}
              <button
                type="button"
                className="text-foreground underline inline-flex items-center gap-0.5"
                onClick={() => openExternal(CONSOLE_URL)}
              >
                GitHub Developer settings <ExternalLink size={12} />
              </button>
            </li>
            <li>
              Create an <strong className="text-foreground">OAuth App</strong>
            </li>
            <li>
              Set the authorization callback URL to{' '}
              <code className="text-foreground bg-muted px-1 rounded">
                http://127.0.0.1:8000/auth/github/callback
              </code>
            </li>
            <li>Copy the Client ID and Client Secret below</li>
          </ol>
        </SettingsCard>
      </SettingsSection>

      <SettingsSection title="Credentials">
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

          <p className="text-app-caption text-muted-foreground leading-relaxed">
            Stored locally in <code className="text-[11px]">app_config.json</code> next to the backend.
            You can also set <code className="text-[11px]">GITHUB_CLIENT_ID</code> and{' '}
            <code className="text-[11px]">GITHUB_CLIENT_SECRET</code> in{' '}
            <code className="text-[11px]">backend/.env</code>.
          </p>
        </SettingsCard>
      </SettingsSection>
    </div>
  )
}
