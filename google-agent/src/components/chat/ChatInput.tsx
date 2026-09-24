'use client'

import { forwardRef, useCallback, useEffect, useState } from 'react'
import { ArrowUp, AudioLines, Loader2, Mic, Square } from 'lucide-react'
import { iconStroke } from '@/lib/icon'
import { useSpeechToText } from '@/hooks/useSpeechToText'
import { cn } from '@/lib/utils'
import { Textarea } from '@/components/ui/textarea'

const MAX_COMPOSER_HEIGHT = 128

interface Props {
  onSend: (text: string) => void
  onStop?: () => void
  isGenerating: boolean
  isAwaitingApproval?: boolean
  disabled?: boolean
  checking?: boolean
  placeholder?: string
}

function resizeComposer(el: HTMLTextAreaElement | null) {
  if (!el) return
  el.style.height = 'auto'
  el.style.height = `${Math.min(el.scrollHeight, MAX_COMPOSER_HEIGHT)}px`
}

export const ChatInput = forwardRef<HTMLTextAreaElement, Props>(function ChatInput(
  {
    onSend,
    onStop,
    isGenerating,
    isAwaitingApproval = false,
    disabled = false,
    checking = false,
    placeholder,
  },
  ref
) {
  const [value, setValue] = useState('')
  const appendTranscript = useCallback((text: string) => {
    setValue((prev) => (prev ? `${prev.trimEnd()} ${text}` : text))
  }, [])
  const { supported: micSupported, listening, transcribing, toggle: toggleMic } =
    useSpeechToText(appendTranscript)

  useEffect(() => {
    if (!value && typeof ref !== 'function') resizeComposer(ref?.current ?? null)
  }, [value, ref])

  const inputLocked = disabled || isGenerating || isAwaitingApproval

  const setRefs = (node: HTMLTextAreaElement | null) => {
    if (typeof ref === 'function') ref(node)
    else if (ref) ref.current = node
    resizeComposer(node)
  }

  const handleSend = () => {
    const text = value.trim()
    if (!text || inputLocked) return
    if (listening) toggleMic()
    onSend(text)
    setValue('')
    if (typeof ref !== 'function') resizeComposer(ref?.current ?? null)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex items-end gap-1 rounded-2xl border border-border bg-card px-2 py-1.5 focus-within:border-muted-foreground transition-colors duration-fast">
      <Textarea
        ref={setRefs}
        value={value}
        onChange={(e) => {
          setValue(e.target.value)
          resizeComposer(e.target)
        }}
        onKeyDown={handleKeyDown}
        placeholder={
          checking
            ? 'Checking system status…'
            : disabled
              ? 'App not ready — fix issues above to chat'
              : placeholder ?? 'Ask anything'
        }
        rows={1}
        disabled={inputLocked}
        className="min-h-[2.25rem] max-h-32 resize-none border-0 bg-transparent rounded-none px-2 py-1.5 text-app-body leading-snug focus-visible:ring-0 shadow-none scrollbar-none font-sans"
      />
      {micSupported && (
        <button
          type="button"
          onClick={toggleMic}
          disabled={inputLocked || transcribing}
          className={cn(
            'relative shrink-0 w-8 h-8 mb-0.5 rounded-full flex items-center justify-center transition-all duration-fast disabled:opacity-50 disabled:pointer-events-none',
            transcribing
              ? 'text-muted-foreground'
              : listening
                ? 'bg-destructive/15 text-destructive animate-recording-pulse'
                : 'text-muted-foreground hover:bg-accent hover:text-foreground'
          )}
          aria-label={
            transcribing
              ? 'Transcribing speech'
              : listening
                ? 'Stop recording'
                : 'Start voice input'
          }
          aria-pressed={listening}
        >
          {listening && (
            <span
              className="pointer-events-none absolute inset-0 rounded-full bg-destructive/20 animate-ping"
              aria-hidden
            />
          )}
          <span className="relative z-10 flex items-center justify-center">
            {transcribing ? (
              <Loader2 size={16} strokeWidth={iconStroke} className="animate-spin" />
            ) : listening ? (
              <AudioLines size={16} strokeWidth={iconStroke} className="animate-pulse" />
            ) : (
              <Mic size={16} strokeWidth={iconStroke} />
            )}
          </span>
        </button>
      )}

      <button
        type="button"
        onClick={isGenerating ? onStop : handleSend}
        disabled={(!value.trim() && !isGenerating) || isAwaitingApproval}
        className={`shrink-0 w-8 h-8 mb-0.5 rounded-full flex items-center justify-center transition-all duration-fast ${
          value.trim() || isGenerating
            ? 'bg-foreground text-background hover:opacity-90 cursor-pointer'
            : 'bg-muted text-muted-foreground cursor-not-allowed'
        }`}
      >
        {isGenerating ? (
          <Square size={14} className="fill-current" strokeWidth={iconStroke} />
        ) : (
          <ArrowUp size={16} strokeWidth={iconStroke} />
        )}
      </button>
    </div>
  )
})
