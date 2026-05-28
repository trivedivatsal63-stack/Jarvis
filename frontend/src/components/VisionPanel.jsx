import React, { useState } from 'react'

const API_URL = '/api/vision/analyze'

export default function VisionPanel({ onScan, onRegister, threats = false, faces = [], objects = [] }) {
  const [showFaces, setShowFaces] = useState(true)
  const [showObjects, setShowObjects] = useState(true)
  const [name, setName] = useState('')
  const [scanning, setScanning] = useState(false)

  const handleScan = async () => {
    setScanning(true)
    if (onScan) {
      await onScan()
    } else {
      try {
        await fetch(API_URL, { method: 'POST' })
      } catch (e) { /* ignore */ }
    }
    setScanning(false)
  }

  const handleRegister = () => {
    if (!name.trim()) return
    if (onRegister) onRegister(name.trim())
    setName('')
  }

  return (
    <div className="vision-panel">
      <div className="panel-header">
        <span className="panel-dot" />
        VISION SYSTEMS
        {threats && <span className="threat-alert">THREAT</span>}
      </div>

      <div className="webcam-preview">
        <svg viewBox="0 0 80 60" className="camera-icon">
          <rect x="2" y="10" width="76" height="44" rx="4" fill="none" stroke="rgba(0,212,255,0.3)" strokeWidth="1.5" />
          <circle cx="40" cy="32" r="12" fill="none" stroke="rgba(0,212,255,0.2)" strokeWidth="1.5" />
          <circle cx="40" cy="32" r="3" fill="rgba(0,212,255,0.15)" />
          <rect x="28" y="6" width="24" height="6" rx="2" fill="none" stroke="rgba(0,212,255,0.3)" strokeWidth="1.5" />
          <rect x="18" y="54" width="44" height="3" rx="1.5" fill="rgba(0,212,255,0.15)" />
          <circle cx="14" cy="20" r="2" fill="rgba(0,212,255,0.08)" />
          <circle cx="66" cy="20" r="2" fill="rgba(0,212,255,0.08)" />
        </svg>
        <div className="webcam-label">CAMERA FEED</div>
      </div>

      {faces.length > 0 && (
        <div className="vision-section">
          <div className="vision-section-header" onClick={() => setShowFaces(!showFaces)}>
            <span className="section-toggle">{showFaces ? '\u25BC' : '\u25B6'}</span>
            <span className="section-title">FACES ({faces.length})</span>
          </div>
          {showFaces && (
            <div className="vision-list">
              {faces.map((f, i) => (
                <div key={i} className="vision-item">
                  <span className="vision-item-icon">{'\uD83D\uDC64'}</span>
                  <span className="vision-item-label">{f.name || f.label || `Face ${i + 1}`}</span>
                  {f.confidence != null && (
                    <span className="vision-item-conf">{Math.round(f.confidence * 100)}%</span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {objects.length > 0 && (
        <div className="vision-section">
          <div className="vision-section-header" onClick={() => setShowObjects(!showObjects)}>
            <span className="section-toggle">{showObjects ? '\u25BC' : '\u25B6'}</span>
            <span className="section-title">OBJECTS ({objects.length})</span>
          </div>
          {showObjects && (
            <div className="vision-list">
              {objects.map((o, i) => (
                <div key={i} className="vision-item">
                  <span className="vision-item-icon">{'\uD83D\uDCA0'}</span>
                  <span className="vision-item-label">{o.name || o.label || `Object ${i + 1}`}</span>
                  {o.confidence != null && (
                    <span className="vision-item-conf">{Math.round(o.confidence * 100)}%</span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="vision-actions">
        <button className="vision-btn" onClick={handleScan} disabled={scanning}>
          {scanning ? 'SCANNING...' : 'SCAN ENVIRONMENT'}
        </button>
      </div>

      <div className="vision-register">
        <input
          className="vision-name-input"
          value={name}
          onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') handleRegister() }}
          placeholder="Face name..."
        />
        <button className="vision-btn vision-btn-sm" onClick={handleRegister} disabled={!name.trim()}>
          REGISTER FACE
        </button>
      </div>
    </div>
  )
}
