'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { toast } from 'sonner'
import { transcribeAudioApi } from '@/lib/api'
import { isTauriRuntime } from '@/lib/open-external'
import { isMicrophoneSupported, WavRecorder } from '@/lib/recordWav'
import {
  type BrowserSpeechRecognition,
  isListeningSupported,
  startListening,
  stopListening,
} from '@/lib/speechToText'

export function useSpeechToText(onFinal: (text: string) => void) {
  const [listening, setListening] = useState(false)
  const [transcribing, setTranscribing] = useState(false)
  const recognitionRef = useRef<BrowserSpeechRecognition | null>(null)
  const recorderRef = useRef<WavRecorder | null>(null)
  const useRecorderRef = useRef(isTauriRuntime() || !isListeningSupported())
  const onFinalRef = useRef(onFinal)
  onFinalRef.current = onFinal

  const stopWebSpeech = useCallback(() => {
    stopListening(recognitionRef.current)
    recognitionRef.current = null
    setListening(false)
  }, [])

  const stopRecorder = useCallback(async () => {
    const recorder = recorderRef.current
    recorderRef.current = null
    setListening(false)
    if (!recorder) return

    setTranscribing(true)
    try {
      const blob = await recorder.stop()
      if (blob.size <= 44) {
        toast.error('No speech detected')
        return
      }
      const { text } = await transcribeAudioApi(blob)
      const trimmed = text.trim()
      if (!trimmed) {
        toast.error('No speech detected')
        return
      }
      onFinalRef.current(trimmed)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Transcription failed')
    } finally {
      setTranscribing(false)
    }
  }, [])

  const stop = useCallback(() => {
    if (recorderRef.current) {
      void stopRecorder()
      return
    }
    stopWebSpeech()
  }, [stopRecorder, stopWebSpeech])

  const startRecorder = useCallback(async () => {
    if (!isMicrophoneSupported()) {
      toast.error('Microphone is not available on this device')
      return
    }
    try {
      const recorder = new WavRecorder()
      await recorder.start()
      recorderRef.current = recorder
      setListening(true)
    } catch {
      toast.error('Microphone permission denied')
    }
  }, [])

  const startWebSpeech = useCallback(() => {
    const recognition = startListening({
      onFinal: (text) => onFinalRef.current(text),
      onError: (message) => {
        if (message.includes('service-not-allowed') || message.includes('desktop app')) {
          useRecorderRef.current = true
          stopWebSpeech()
          void startRecorder()
          return
        }
        toast.error(message)
        stopWebSpeech()
      },
      onEnd: () => {
        recognitionRef.current = null
        setListening(false)
      },
    })

    if (!recognition) {
      useRecorderRef.current = true
      void startRecorder()
      return
    }

    recognitionRef.current = recognition
    setListening(true)
  }, [startRecorder, stopWebSpeech])

  const start = useCallback(() => {
    if (useRecorderRef.current) {
      void startRecorder()
      return
    }
    startWebSpeech()
  }, [startRecorder, startWebSpeech])

  const toggle = useCallback(() => {
    if (transcribing) return
    if (listening) stop()
    else start()
  }, [listening, start, stop, transcribing])

  useEffect(() => () => {
    stopWebSpeech()
    if (recorderRef.current) {
      void recorderRef.current.stop().catch(() => {})
      recorderRef.current = null
    }
  }, [stopWebSpeech])

  return {
    supported: isMicrophoneSupported() || isListeningSupported(),
    listening,
    transcribing,
    start,
    stop,
    toggle,
  }
}
