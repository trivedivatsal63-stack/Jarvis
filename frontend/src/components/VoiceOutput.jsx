import React, { useMemo } from 'react'

const BAR_COUNT = 20

export default function VoiceOutput({ isSpeaking, volume, onVolumeChange, onMuteToggle, isMuted }) {
  const delays = useMemo(() =>
    Array.from({ length: BAR_COUNT }, () => `${(Math.random() * 0.4).toFixed(2)}s`),
  [])

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: '8px',
      padding: '12px 0',
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'flex-end',
        gap: '3px',
        height: '40px',
        width: '100%',
        maxWidth: '140px',
        justifyContent: 'center',
      }}>
        {delays.map((d, i) => (
          <div
            key={i}
            className={`voice-waveform-bar ${isSpeaking ? 'speaking' : 'idle'}`}
            style={{
              background: isSpeaking
                ? `rgba(0, 212, 255, ${0.3 + (i / BAR_COUNT) * 0.7})`
                : 'rgba(0, 212, 255, 0.06)',
              animationDelay: isSpeaking ? d : '0s',
              height: isSpeaking ? '100%' : '100%',
            }}
          />
        ))}
      </div>

      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        width: '100%',
        maxWidth: '140px',
      }}>
        <button
          className="voice-mute-btn"
          onClick={onMuteToggle}
          title={isMuted ? 'Unmute' : 'Mute'}
          style={{ color: isMuted ? '#555' : '#00d4ff' }}
        >
          {isMuted ? '\uD83D\uDD07' : '\uD83D\uDD0A'}
        </button>

        <input
          type="range"
          min="0"
          max="100"
          value={volume ?? 50}
          onChange={(e) => onVolumeChange?.(Number(e.target.value))}
          className="voice-range-input"
          style={{
            background: `linear-gradient(90deg, #00d4ff ${volume ?? 50}%, rgba(255,255,255,0.06) ${volume ?? 50}%)`,
          }}
        />
      </div>

      <span
        className="voice-status-text"
        style={{
          color: isSpeaking ? '#00d4ff' : '#444',
          textShadow: isSpeaking ? '0 0 8px rgba(0,212,255,0.4)' : 'none',
        }}
      >
        {isSpeaking ? 'SPEAKING' : 'IDLE'}
      </span>
    </div>
  )
}
