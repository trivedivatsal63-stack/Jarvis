import React, { useEffect, useRef } from 'react'

export default function VoiceInput({ isListening, isSpeaking, onToggle }) {
  const canvasRef = useRef(null)
  const animRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas || !isSpeaking) return
    const ctx = canvas.getContext('2d')
    const bars = 32
    let frame = 0

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      const w = canvas.width / bars - 2
      for (let i = 0; i < bars; i++) {
        const h = Math.sin(frame * 0.1 + i * 0.3) * 10 + Math.random() * 8 + 4
        const x = i * (w + 2)
        const y = canvas.height - h
        ctx.fillStyle = `rgba(0, 212, 255, ${0.3 + (h / 30) * 0.7})`
        ctx.fillRect(x, y, w, h)
      }
      frame++
      animRef.current = requestAnimationFrame(draw)
    }
    draw()
    return () => cancelAnimationFrame(animRef.current)
  }, [isSpeaking])

  return (
    <div className="voice-indicator">
      <canvas ref={canvasRef} width="120" height="30" className="voice-waveform" />
      <button
        className={`voice-toggle-btn ${isListening ? 'active' : ''}`}
        onClick={onToggle}
      >
        {isListening ? '\uD83D\uDD34 Stop' : '\uD83C\uDF99\uFE0F Voice'}
      </button>
    </div>
  )
}
