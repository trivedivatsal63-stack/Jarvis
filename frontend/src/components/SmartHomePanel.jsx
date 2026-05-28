import React, { useState } from 'react'

const DEFAULT_DEVICES = [
  { id: 'light.1', name: 'Main Light', state: 'on', type: 'light' },
  { id: 'light.2', name: 'Desk Lamp', state: 'off', type: 'light' },
  { id: 'switch.1', name: 'Fan', state: 'on', type: 'switch' },
]

const TYPE_ICONS = {
  light: '\uD83D\uDCA1',
  switch: '\u26A1',
  plug: '\uD83D\uDD0C',
  sensor: '\uD83C\uDFE0',
}

export default function SmartHomePanel({ devices: externalDevices, onControl, brightness: externalBrightness, onBrightnessChange }) {
  const [localDevices, setLocalDevices] = useState(DEFAULT_DEVICES)
  const [localBrightness, setLocalBrightness] = useState(80)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const devices = externalDevices || localDevices
  const brightness = externalBrightness != null ? externalBrightness : localBrightness

  const handleToggle = (id) => {
    if (onControl) {
      onControl(id)
    } else {
      setLocalDevices((prev) =>
        prev.map((d) => (d.id === id ? { ...d, state: d.state === 'on' ? 'off' : 'on' } : d))
      )
    }
  }

  const handleAllOff = () => {
    if (onControl) {
      devices.forEach((d) => { if (d.state === 'on') onControl(d.id) })
    } else {
      setLocalDevices((prev) => prev.map((d) => ({ ...d, state: 'off' })))
    }
  }

  const handleAllOn = () => {
    if (onControl) {
      devices.forEach((d) => { if (d.state === 'off') onControl(d.id) })
    } else {
      setLocalDevices((prev) => prev.map((d) => ({ ...d, state: 'on' })))
    }
  }

  const handleBrightness = (e) => {
    const val = parseInt(e.target.value, 10)
    if (onBrightnessChange) {
      onBrightnessChange(val)
    } else {
      setLocalBrightness(val)
    }
  }

  if (error) {
    return (
      <div className="smarthome-panel">
        <div className="panel-header"><span className="panel-dot" />SMART HOME</div>
        <div className="smarthome-error">{error}</div>
      </div>
    )
  }

  return (
    <div className="smarthome-panel">
      <div className="panel-header"><span className="panel-dot" />SMART HOME</div>

      {loading && <div className="smarthome-loading">Loading...</div>}

      <div className="smarthome-list">
        {devices.map((d) => (
          <div key={d.id} className="smarthome-item">
            <span className="smarthome-icon">{TYPE_ICONS[d.type] || '\u2753'}</span>
            <span className="smarthome-name">{d.name}</span>
            <span className={`smarthome-state smarthome-state-${d.state}`}>{d.state.toUpperCase()}</span>
            <button
              className={`smarthome-toggle ${d.state === 'on' ? 'smarthome-toggle-on' : ''}`}
              onClick={() => handleToggle(d.id)}
            />
          </div>
        ))}
      </div>

      <div className="smarthome-brightness">
        <span className="smarthome-brightness-label">BRIGHTNESS</span>
        <input
          type="range"
          min="0"
          max="100"
          value={brightness}
          onChange={handleBrightness}
          className="smarthome-slider"
        />
        <span className="smarthome-brightness-value">{brightness}%</span>
      </div>

      <div className="smarthome-master">
        <button className="smarthome-master-btn smarthome-master-on" onClick={handleAllOn}>
          ALL ON
        </button>
        <button className="smarthome-master-btn smarthome-master-off" onClick={handleAllOff}>
          ALL OFF
        </button>
      </div>
    </div>
  )
}
