let activeMessageId: string | null = null
const listeners = new Set<(id: string | null) => void>()

function notify(messageId: string | null) {
  activeMessageId = messageId
  listeners.forEach((listener) => listener(messageId))
}

export function subscribeSpeaking(listener: (messageId: string | null) => void) {
  listeners.add(listener)
  listener(activeMessageId)
  return () => {
    listeners.delete(listener)
  }
}

export function stripMarkdownForSpeech(text: string): string {
  return text
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/!\[([^\]]*)\]\([^)]+\)/g, '$1')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/^[#>*\-\d.]+\s+/gm, '')
    .replace(/[*_~]/g, '')
    .replace(/\s+/g, ' ')
    .trim()
}

export function isSpeechSupported(): boolean {
  return typeof window !== 'undefined' && 'speechSynthesis' in window
}

export function stopSpeaking() {
  if (!isSpeechSupported()) return
  window.speechSynthesis.cancel()
  notify(null)
}

export function speakMessage(messageId: string, text: string): boolean {
  if (!isSpeechSupported()) return false
  const plain = stripMarkdownForSpeech(text)
  if (!plain) return false

  stopSpeaking()

  const utterance = new SpeechSynthesisUtterance(plain)
  utterance.rate = 1
  utterance.pitch = 1
  utterance.onend = () => notify(null)
  utterance.onerror = () => notify(null)

  notify(messageId)
  window.speechSynthesis.speak(utterance)
  return true
}

export function toggleSpeakMessage(messageId: string, text: string): boolean {
  if (activeMessageId === messageId) {
    stopSpeaking()
    return false
  }
  return speakMessage(messageId, text)
}
