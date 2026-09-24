interface SpeechRecognitionResultList {
  readonly length: number
  [index: number]: {
    readonly isFinal: boolean
    readonly [index: number]: { readonly transcript: string }
  }
}

interface SpeechRecognitionEvent extends Event {
  readonly resultIndex: number
  readonly results: SpeechRecognitionResultList
}

interface SpeechRecognitionErrorEvent extends Event {
  readonly error: string
}

export interface BrowserSpeechRecognition extends EventTarget {
  continuous: boolean
  interimResults: boolean
  lang: string
  onresult: ((event: SpeechRecognitionEvent) => void) | null
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null
  onend: (() => void) | null
  start(): void
  stop(): void
  abort(): void
}

type SpeechRecognitionCtor = new () => BrowserSpeechRecognition

function getSpeechRecognitionCtor(): SpeechRecognitionCtor | null {
  if (typeof window === 'undefined') return null
  const w = window as Window & {
    SpeechRecognition?: SpeechRecognitionCtor
    webkitSpeechRecognition?: SpeechRecognitionCtor
  }
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null
}

export function isListeningSupported(): boolean {
  return getSpeechRecognitionCtor() !== null
}

export function mapSpeechRecognitionError(code: string): string {
  switch (code) {
    case 'not-allowed':
      return 'Microphone permission denied'
    case 'service-not-allowed':
      return 'Speech recognition is blocked in the desktop app — using recorded transcription instead'
    case 'network':
      return 'Speech recognition needs an internet connection'
    case 'no-speech':
      return 'No speech detected'
    default:
      return code
  }
}

export interface SpeechListenHandlers {
  onInterim?: (text: string) => void
  onFinal?: (text: string) => void
  onError?: (message: string) => void
  onEnd?: () => void
}

export function startListening(handlers: SpeechListenHandlers): BrowserSpeechRecognition | null {
  const Ctor = getSpeechRecognitionCtor()
  if (!Ctor) return null

  const recognition = new Ctor()
  recognition.continuous = true
  recognition.interimResults = true
  recognition.lang = navigator.language || 'en-US'

  recognition.onresult = (event: SpeechRecognitionEvent) => {
    let interim = ''
    let final = ''
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const part = event.results[i][0]?.transcript ?? ''
      if (event.results[i].isFinal) final += part
      else interim += part
    }
    if (interim.trim()) handlers.onInterim?.(interim.trim())
    if (final.trim()) handlers.onFinal?.(final.trim())
  }

  recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
    const err = event
    if (err.error === 'aborted') return
    const message = mapSpeechRecognitionError(err.error)
    handlers.onError?.(message)
  }

  recognition.onend = () => {
    handlers.onEnd?.()
  }

  recognition.start()
  return recognition
}

export function stopListening(recognition: BrowserSpeechRecognition | null) {
  if (!recognition) return
  try {
    recognition.abort()
  } catch {
    try {
      recognition.stop()
    } catch {
      // ignore
    }
  }
}
