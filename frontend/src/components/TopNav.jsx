import React, { useState, useEffect } from 'react'

const TABS = ['CHAT', 'VISION', 'HOME', 'LEGION', 'FILES', 'NOTES']

function pad(n) {
  return String(n).padStart(2, '0')
}

function getClock() {
  const d = new Date()
  return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

export default function TopNav({ activeTab, onTabChange, connected, cameraOn, audioOn, onCameraToggle, onAudioToggle, onSettingsClick }) {
  const [clock, setClock] = useState(getClock)

  useEffect(() => {
    const id = setInterval(() => setClock(getClock), 1000)
    return () => clearInterval(id)
  }, [])

  return (
    <nav className="top-nav">
      <div className="top-nav-left">
        <span className="top-nav-title">J.A.R.V.I.S.</span>
        <span className="top-nav-version">v4.1</span>
      </div>

      <div className="top-nav-center">
        {TABS.map((tab) => (
          <button
            key={tab}
            className={`top-nav-tab${(activeTab || '').toUpperCase() === tab ? ' active' : ''}`}
            onClick={() => onTabChange?.(tab)}
          >
            {tab}
          </button>
        ))}
      </div>

      <div className="top-nav-right">
        <span className={`top-nav-status-dot ${connected ? 'online' : 'offline'}`} />

        <button
          className={`top-nav-icon-btn${cameraOn ? ' active' : ''}`}
          onClick={onCameraToggle}
          title="Camera"
        >
          {'\uD83D\uDCF7'}
        </button>

        <button
          className={`top-nav-icon-btn${audioOn ? ' active' : ''}`}
          onClick={onAudioToggle}
          title="Audio"
        >
          {'\uD83D\uDD0A'}
        </button>

        <button
          className="top-nav-icon-btn"
          onClick={onSettingsClick}
          title="Settings"
        >
          {'\u2699\uFE0F'}
        </button>

        <span className="top-nav-clock">{clock}</span>
      </div>
    </nav>
  )
}
