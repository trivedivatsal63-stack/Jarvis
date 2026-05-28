import { useState, useRef, useCallback, useEffect } from 'react'

export default function useVoice() {
  const [isListening, setIsListening] = useState(false)
  const [isAlwaysOn, setIsAlwaysOn] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const onResultRef = useRef(null)
  const shouldRestart = useRef(false)
  const recRef = useRef(null)
  const restartTimer = useRef(null)

  const SR = (typeof window !== 'undefined') && (window.SpeechRecognition || window.webkitSpeechRecognition)

  const _createRec = useCallback(() => {
    if (!SR) return null
    const rec = new SR()
    rec.continuous = false
    rec.interimResults = false
    rec.lang = 'en-US'
    return rec
  }, [SR])

  const _startRec = useCallback(() => {
    const rec = _createRec()
    if (!rec) return

    rec.onresult = (event) => {
      const text = event.results[0][0].transcript
      if (text && onResultRef.current) {
        onResultRef.current(text)
      }
    }

    rec.onend = () => {
      recRef.current = null
      if (shouldRestart.current) {
        clearTimeout(restartTimer.current)
        restartTimer.current = setTimeout(() => _startRec(), 300)
      } else {
        setIsListening(false)
      }
    }

    rec.onerror = () => {
      recRef.current = null
      if (shouldRestart.current) {
        clearTimeout(restartTimer.current)
        restartTimer.current = setTimeout(() => _startRec(), 500)
      } else {
        setIsListening(false)
      }
    }

    recRef.current = rec
    try { rec.start() } catch { setIsListening(false); setIsAlwaysOn(false); shouldRestart.current = false }
  }, [_createRec])

  const startAlwaysOn = useCallback((onResult) => {
    clearTimeout(restartTimer.current)
    shouldRestart.current = false
    if (recRef.current) { try { recRef.current.stop() } catch {} }
    recRef.current = null
    shouldRestart.current = true
    onResultRef.current = onResult
    setIsAlwaysOn(true)
    setIsListening(true)
    _startRec()
  }, [_startRec])

  const stopListening = useCallback(() => {
    clearTimeout(restartTimer.current)
    shouldRestart.current = false
    setIsAlwaysOn(false)
    setIsListening(false)
    if (recRef.current) { try { recRef.current.stop() } catch {} }
    recRef.current = null
  }, [])

  const speak = useCallback((text) => {
    if (!window.speechSynthesis) return
    window.speechSynthesis.cancel()
    const utter = new SpeechSynthesisUtterance(text)
    utter.rate = 0.92
    utter.pitch = 0.85
    utter.volume = 1.0
    const voices = window.speechSynthesis.getVoices()
    const british = voices.find(v => v.lang.startsWith('en-GB') && v.name.includes('British'))
    if (british) utter.voice = british
    utter.onstart = () => setIsSpeaking(true)
    utter.onend = () => setIsSpeaking(false)
    window.speechSynthesis.speak(utter)
  }, [])

  useEffect(() => {
    return () => {
      clearTimeout(restartTimer.current)
      shouldRestart.current = false
      if (recRef.current) { try { recRef.current.stop() } catch {} }
    }
  }, [])

  return { isListening, isAlwaysOn, isSpeaking, startAlwaysOn, stopListening, speak }
}
