'use client'

import { useEffect, useState } from 'react'
import Image from 'next/image'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useGoogleAuth } from '@/hooks/useGoogleAuth'
import { useAuthStore } from '@/store/authStore'
import { useSettingsStore } from '@/store/settingsStore'
import { useChatStore } from '@/store/chatStore'
import { fetchHealth, fetchLlmSetupStatus, saveLlmCredentials } from '@/lib/api'
import { markOnboardingComplete, PRODUCT_NAME, PRODUCT_TAGLINE } from '@/lib/onboarding'
import { STARTER_PROMPTS } from '@/lib/workflows'
import { toast } from 'sonner'
import { Check, ChevronRight, Loader2, Shield } from 'lucide-react'
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
  const [savingLlm, setSavingLlm] = useState(false)
  const [ollamaUrl, setOllamaUrl] = useState('http://127.0.0.1:11434')
  const [ollamaModel, setOllamaModel] = useState('qwen2.5:7b')

  useEffect(() => {
    void fetchHealth().then((h) => {
      setOauthConfigured(Boolean(h.oauthConfigured))
      setLlmConfigured(Boolean(h.llmConfigured || h.ollamaConfigured))
      if (h.ollamaBaseUrl) setOllamaUrl(h.ollamaBaseUrl)
    })
    void fetchLlmSetupStatus()
      .then((s) => {
        setLlmConfigured(s.configured)
        if (s.ollamaBaseUrl) setOllamaUrl(s.ollamaBaseUrl)
      })
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

  const saveKeys = async () => {
    setSavingLlm(true)
    try {
      await saveLlmCredentials(ollamaUrl.trim(), ollamaModel.trim())
      if (isAuthenticated) {
        await update({
          ollamaBaseUrl: ollamaUrl.trim() || undefined,
          defaultModel: ollamaModel.trim() || undefined,
        })
      }
      setLlmConfigured(true)
      toast.success('LLM settings saved')
      setStep('google')
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Could not reach Ollama. Start it and pull a model.')
    } finally {
      setSavingLlm(false)
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
      <div className="w-full max-w-lg bg-card border border-border rounded-xl shadow-sm p-8 space-y-6">
        <div className="flex items-center gap-3">
          <Image src="/app-icon.png" alt={PRODUCT_NAME} width={40} height={40} className="rounded-xl" />
          <div>
            <h1 className="text-app-heading font-rounded text-foreground">{PRODUCT_NAME}</h1>
            <p className="text-app-caption text-muted-foreground">Setup · Step {stepIndex + 1} of {STEPS.length}</p>
          </div>
        </div>

        <div className="flex gap-1">
          {STEPS.map((s, i) => (
            <div
              key={s}
              className={`h-1 flex-1 rounded-full ${i <= stepIndex ? 'bg-primary' : 'bg-muted'}`}
            />
          ))}
        </div>

        {step === 'welcome' && (
          <div className="space-y-4">
            <p className="text-app-body text-muted-foreground leading-relaxed">{PRODUCT_TAGLINE}</p>
            <ul className="space-y-2 text-app-caption text-muted-foreground">
              <li className="flex gap-2"><Check size={14} className="mt-0.5 shrink-0 text-green-600" /> Local Ollama models run the agents on this machine</li>
              <li className="flex gap-2"><Check size={14} className="mt-0.5 shrink-0 text-green-600" /> Separate agent rooms for Gmail, Calendar, Drive, Docs, Sheets, and Web</li>
              <li className="flex gap-2"><Check size={14} className="mt-0.5 shrink-0 text-green-600" /> Embedded database — no PostgreSQL setup required</li>
            </ul>
            <Button className="w-full" onClick={() => setStep('llm')}>
              Get started <ChevronRight size={16} className="ml-1" />
            </Button>
          </div>
        )}

        {step === 'llm' && (
          <div className="space-y-4">
            <p className="text-app-body text-muted-foreground">
              Agents run on{' '}
              <a href="https://ollama.com" className="text-primary underline" target="_blank" rel="noreferrer">
                Ollama
              </a>{' '}
              on this machine. Start Ollama, then pull a model such as{' '}
              <code className="text-[11px]">qwen2.5:7b</code>.
            </p>
            {llmConfigured && (
              <p className="text-app-caption text-green-600 dark:text-green-500 flex items-center gap-2">
                <Check size={14} /> An LLM is already available
              </p>
            )}
            <div className="space-y-2">
              <label className="text-app-caption text-foreground" htmlFor="onboard-ollama-url">Ollama URL</label>
              <Input
                id="onboard-ollama-url"
                autoComplete="off"
                placeholder="http://127.0.0.1:11434"
                value={ollamaUrl}
                onChange={(e) => setOllamaUrl(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <label className="text-app-caption text-foreground" htmlFor="onboard-ollama-model">Model</label>
              <Input
                id="onboard-ollama-model"
                autoComplete="off"
                placeholder="qwen2.5:7b"
                value={ollamaModel}
                onChange={(e) => setOllamaModel(e.target.value)}
              />
            </div>
            <Button className="w-full" disabled={savingLlm} onClick={() => void saveKeys()}>
              {savingLlm ? <Loader2 size={16} className="animate-spin" /> : <>Save and continue <ChevronRight size={16} className="ml-1" /></>}
            </Button>
            {llmConfigured && (
              <Button variant="outline" className="w-full" onClick={() => setStep('google')}>
                Skip — already configured
              </Button>
            )}
          </div>
        )}

        {step === 'google' && (
          <div className="space-y-4">
            <p className="text-app-body text-muted-foreground">
              Sign in with Google to connect Gmail, Calendar, Drive, Docs, and Sheets.
            </p>
            {!oauthConfigured && (
              <p className="text-app-caption text-amber-600 dark:text-amber-500">
                Google OAuth is not configured yet. Complete setup in Settings → Google OAuth, or add credentials to backend/.env.
              </p>
            )}
            {isAuthenticated ? (
              <p className="text-app-caption text-green-600 flex items-center gap-2">
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
            <div className="flex gap-3 p-4 rounded-lg bg-muted/50">
              <Shield size={20} className="shrink-0 text-primary mt-0.5" />
              <div className="space-y-2 text-app-caption text-muted-foreground">
                <p><strong className="text-foreground">What stays local:</strong> chat history, settings, and Google tokens are stored on your device.</p>
                <p><strong className="text-foreground">What uses the LLM:</strong> Ollama runs locally on your machine. No cloud LLM keys are used.</p>
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
                  className="text-left p-3 rounded-lg border border-border hover:bg-muted/50 transition-colors"
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
