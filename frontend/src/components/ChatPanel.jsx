import React, { useState, useRef, useEffect } from 'react'
import useVoice from '../hooks/useVoice'
import ArcReactor from './ArcReactor'

const API_URL = `/api/chat`

export default function ChatPanel({ wsSend }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [thinking, setThinking] = useState(false)
  const [voiceMode, setVoiceMode] = useState(false)
  const chatEnd = useRef(null)
  const { isListening, isAlwaysOn, isSpeaking, startAlwaysOn, stopListening, speak } = useVoice()

  const addMsg = (text, role, type = 'ai') => {
    setMessages((prev) => [...prev, { text, role, type, id: Date.now() + Math.random() }])
  }

  const updateLastMsg = (text) => {
    setMessages((prev) => {
      const copy = [...prev]
      if (copy.length > 0 && copy[copy.length - 1].role === 'assistant') {
        copy[copy.length - 1] = { ...copy[copy.length - 1], text }
      }
      return copy
    })
  }

  useEffect(() => {
    chatEnd.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async (text, fromVoice = false) => {
    if (!text.trim() || streaming) return
    if (fromVoice) setVoiceMode(true)
    setInput('')
    addMsg(text, 'user')
    setStreaming(true)
    setThinking(true)
    addMsg('', 'assistant')
    let full = ''

    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, session_id: 'default' }),
      })
      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buf = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buf += decoder.decode(value, { stream: true })
        const lines = buf.split('\n')
        buf = lines.pop() || ''

        for (const line of lines) {
          if (!line.trim()) continue
          try {
            const data = JSON.parse(line)
            if (data.thinking) {
              setThinking(true)
            } else if (data.token) {
              setThinking(false)
              full += data.token
              updateLastMsg(full)
            } else if (data.done) {
              if (full && (fromVoice || voiceMode)) speak(full)
            }
          } catch (e) { /* skip */ }
        }
      }
    } catch (e) {
      updateLastMsg('Connection error, Sir.')
    }
    setThinking(false)
    setStreaming(false)
  }

  const handleVoiceResult = (text) => {
    if (text) sendMessage(text, true)
  }

  const toggleVoiceMode = () => {
    if (isAlwaysOn) {
      stopListening()
      setVoiceMode(false)
    } else {
      setVoiceMode(true)
      startAlwaysOn(handleVoiceResult)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(input)
    }
  }

  return (
    <div className="chat-panel-center">
      <ArcReactor thinking={thinking} speaking={isSpeaking} />

      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-welcome">
            <div className="chat-welcome-line">J.A.R.V.I.S</div>
            <div className="chat-welcome-sub">at your service, Sir.</div>
          </div>
        )}
        {messages.map((m) => (
          <div key={m.id} className={`chat-msg chat-msg-${m.role}`}>
            {m.role === 'assistant' && <span className="msg-label">J.A.R.V.I.S \u25B8</span>}
            <div className={`msg-bubble msg-bubble-${m.type}`}>
              {m.text || (m.role === 'assistant' && streaming ? '\u00A0' : '')}
              {m.role === 'assistant' && streaming && !m.text && (
                <span className="thinking-dots"><span>.</span><span>.</span><span>.</span></span>
              )}
              {m.role === 'assistant' && m.text === '' && thinking && (
                <span className="thinking-dots"><span>.</span><span>.</span><span>.</span></span>
              )}
            </div>
          </div>
        ))}
        <div ref={chatEnd} />
      </div>

      {voiceMode && <div className="voice-status-hud">{isAlwaysOn ? 'ALWAYS-ON LISTENING' : 'LISTENING'}</div>}
      <div className="chat-input-bar">
        <button
          className={`voice-btn ${isAlwaysOn ? 'always-on' : ''} ${isListening && !isAlwaysOn ? 'listening' : ''}`}
          onClick={() => {
            if (isAlwaysOn) {
              toggleVoiceMode()
            } else if (isListening) {
              stopListening()
            } else {
              toggleVoiceMode()
            }
          }}
          title={isAlwaysOn ? 'Always-on listening (click to disable)' : isListening ? 'Listening (click to stop)' : 'Always-on voice (click to enable)'}
        >
          {isAlwaysOn ? '\uD83C\uDF99\uFE0F' : isListening ? '\uD83D\uDD34' : '\uD83C\uDFA4'}
        </button>
        <input
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type a message, Sir..."
          disabled={streaming}
        />
        <button
          className="send-btn"
          onClick={() => sendMessage(input)}
          disabled={!input.trim() || streaming}
        >
          \u2192
        </button>
      </div>
    </div>
  )
}
