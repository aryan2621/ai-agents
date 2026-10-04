'use client'

import { useEffect, useState } from 'react'
import Image from 'next/image'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { OAuthSetupTab } from '@/components/settings/tabs/OAuthSetupTab'
import { ModelManager } from '@/components/settings/ModelManager'
import { useGoogleAuth } from '@/hooks/useGoogleAuth'
import { useAuthStore } from '@/store/authStore'
import { useSettingsStore } from '@/store/settingsStore'
import { useChatStore } from '@/store/chatStore'
import { fetchHealth, fetchLlmSetupStatus } from '@/lib/api'
import { markOnboardingComplete, PRODUCT_NAME, PRODUCT_TAGLINE } from '@/lib/onboarding'
import { STARTER_PROMPTS } from '@/lib/workflows'
import { toast } from 'sonner'
import { Check, ChevronRight, Shield } from 'lucide-react'
import type { AgentName } from '@/types'

const STEPS = ['welcome', 'llm', 'google', 'privacy', 'starters'] as const
type Step = (typeof STEPS)[number]

export function OnboardingWizard() {
  const router = useRouter()
  const { signInWithGoogle } = useGoogleAuth()
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const { update } = useSettingsStore()
  const [step, setStep] = useState<Step>('welcome')
  const [oauthConfigured, setOauthConfigured] = useState(false)
  const [llmConfigured, setLlmConfigured] = useState(false)
  const [signingIn, setSigningIn] = useState(false)

  useEffect(() => {
    void fetchHealth().then((h) => {
      setOauthConfigured(Boolean(h.oauthConfigured))
      setLlmConfigured(Boolean(h.llmConfigured))
    })
    void fetchLlmSetupStatus()
      .then((s) => setLlmConfigured(s.configured))
      .catch(() => {})
  }, [])

  useEffect(() => {
    if (step === 'google' && isAuthenticated) {
      setStep('privacy')
    }
  }, [step, isAuthenticated])

  const stepIndex = STEPS.indexOf(step)

  const handleGoogleSignIn = async () => {
    setSigningIn(true)
    try {
      await signInWithGoogle()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Sign-in failed')
    } finally {
      setSigningIn(false)
    }
  }

  const finish = async (starter?: { prompt: string; agent: AgentName }) => {
    await markOnboardingComplete()
    if (isAuthenticated) {
      await update({ onboardingCompleted: true })
    }
    if (starter) {
      useChatStore.getState().setPendingStarterPrompt({
        text: starter.prompt,
        agent: starter.agent,
      })
    }
    router.push(isAuthenticated ? '/chat' : '/auth')
  }

  return (
    <div className="flex-1 min-h-0 flex items-center justify-center bg-background px-4 py-8 overflow-y-auto">
      <div className="w-full max-w-lg bg-popover border border-border rounded-2xl shadow-[0_24px_64px_-24px_hsl(var(--foreground)/0.2)] p-8 space-y-6">
        <div className="flex items-center gap-3">
          <Image src="/app-icon.png" alt={PRODUCT_NAME} width={40} height={40} className="rounded-xl" />
          <div>
            <h1 className="font-serif text-2xl font-normal text-foreground">{PRODUCT_NAME}</h1>
            <p className="text-app-caption text-muted-foreground">Setup · Step {stepIndex + 1} of {STEPS.length}</p>
          </div>
        </div>

        <div className="flex gap-1">
          {STEPS.map((s, i) => (
            <div
              key={s}
              className={`h-1 flex-1 rounded-full ${i <= stepIndex ? 'bg-brand' : 'bg-muted'}`}
            />
          ))}
        </div>

        {step === 'welcome' && (
          <div className="space-y-4">
            <p className="text-app-body text-muted-foreground leading-relaxed">{PRODUCT_TAGLINE}</p>
            <ul className="space-y-2 text-app-caption text-muted-foreground">
              <li className="flex gap-2"><Check size={14} className="mt-0.5 shrink-0 text-success" /> A built-in AI runs the agents on this Mac — nothing to install</li>
              <li className="flex gap-2"><Check size={14} className="mt-0.5 shrink-0 text-success" /> Separate agent rooms for Gmail, Calendar, Drive, Docs, Sheets, and Web</li>
              <li className="flex gap-2"><Check size={14} className="mt-0.5 shrink-0 text-success" /> Chats and settings are saved on this Mac</li>
            </ul>
            <Button className="w-full" onClick={() => setStep('llm')}>
              Get started <ChevronRight size={16} className="ml-1" />
            </Button>
          </div>
        )}

        {step === 'llm' && (
          <div className="space-y-4">
            <p className="text-app-body text-muted-foreground">
              The agents run on an open AI model on this Mac. Download the one that fits it best;
              you can switch models later in Settings → Models.
            </p>
            <ModelManager only="recommended" onInstalled={() => setLlmConfigured(true)} />
            <Button className="w-full" disabled={!llmConfigured} onClick={() => setStep('google')}>
              Continue <ChevronRight size={16} className="ml-1" />
            </Button>
          </div>
        )}

        {step === 'google' && (
          <div className="space-y-4">
            <p className="text-app-body text-muted-foreground">
              Sign in with Google to connect Gmail, Calendar, Drive, Docs, and Sheets.
            </p>
            {!oauthConfigured && (
              <div className="max-h-[50vh] overflow-y-auto -mx-1 px-1">
                <p className="text-app-caption text-muted-foreground mb-4">
                  First, connect your own Google OAuth client. It's a one-time step.
                </p>
                <OAuthSetupTab onSaved={() => setOauthConfigured(true)} />
              </div>
            )}
            {isAuthenticated ? (
              <p className="text-app-caption text-success flex items-center gap-2">
                <Check size={14} /> Signed in successfully
              </p>
            ) : (
              <Button className="w-full" disabled={signingIn || !oauthConfigured} onClick={handleGoogleSignIn}>
                {signingIn ? 'Waiting for Google…' : 'Continue with Google'}
              </Button>
            )}
            <Button variant="outline" className="w-full" onClick={() => setStep('privacy')}>
              {isAuthenticated ? 'Continue' : 'Skip for now'}
            </Button>
          </div>
        )}

        {step === 'privacy' && (
          <div className="space-y-4">
            <div className="flex gap-3 p-4 rounded-xl bg-card">
              <Shield size={20} className="shrink-0 text-brand mt-0.5" />
              <div className="space-y-2 text-app-caption text-muted-foreground">
                <p><strong className="text-foreground">What stays local:</strong> chat history, settings, and Google tokens are stored on your device.</p>
                <p><strong className="text-foreground">What uses the AI:</strong> the built-in model runs on this Mac. Nothing you ask is sent to an AI service.</p>
                <p><strong className="text-foreground">What uses Google APIs:</strong> Gmail, Calendar, Drive, Docs, and Sheets actions you request.</p>
              </div>
            </div>
            <Button className="w-full" onClick={() => setStep('starters')}>
              Continue <ChevronRight size={16} className="ml-1" />
            </Button>
          </div>
        )}

        {step === 'starters' && (
          <div className="space-y-4">
            <p className="text-app-body text-muted-foreground">Try one of these to see Google Agent in action:</p>
            <div className="grid gap-2">
              {STARTER_PROMPTS.slice(0, 3).map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => finish({ prompt: item.prompt, agent: item.agent })}
                  className="text-left px-4 py-3 rounded-xl border border-border hover:bg-accent transition-colors duration-fast"
                >
                  <p className="text-app-body font-medium text-foreground">{item.title}</p>
                  <p className="text-app-caption text-muted-foreground line-clamp-2 mt-0.5">{item.prompt}</p>
                </button>
              ))}
            </div>
            <Button variant="outline" className="w-full" onClick={() => finish()}>
              Skip — go to chat
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}
