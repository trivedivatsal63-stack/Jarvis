import React from 'react'

function CircularProgress({ value, label, color = '#00d4ff', size = 80 }) {
  const r = (size - 10) / 2
  const circ = 2 * Math.PI * r
  const offset = circ - (value / 100) * circ
  return (
    <div className="sys-stat" style={{ width: size, height: size }}>
      <svg viewBox={`0 0 ${size} ${size}`} className="circular-progress">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none"
          stroke="rgba(255,255,255,0.05)" strokeWidth="4" />
        <circle cx={size / 2} cy={size / 2} r={r} fill="none"
          stroke={color} strokeWidth="4" strokeDasharray={circ}
          strokeDashoffset={offset} strokeLinecap="round"
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
          className="progress-ring" />
        <text x={size / 2} y={size / 2 - 4} textAnchor="middle" fill="white"
          fontSize="16" fontFamily="'Orbitron', monospace" fontWeight="700">
          {value}%
        </text>
        <text x={size / 2} y={size / 2 + 14} textAnchor="middle" fill="#888"
          fontSize="8" fontFamily="'Share Tech Mono', monospace">{label}</text>
      </svg>
    </div>
  )
}

export default function SystemStats({ stats }) {
  if (!stats) return null
  return (
    <div className="system-stats">
      <div className="panel-header">
        <span className="panel-dot" />
        SYSTEM STATUS
      </div>
      <div className="stats-grid">
        <CircularProgress value={stats.cpu} label="CPU" color="#00d4ff" />
        <CircularProgress value={stats.ram} label="RAM" color="#00ff9d" />
        {stats.battery != null && (
          <CircularProgress value={stats.battery} label="BAT" color="#ff6b00" />
        )}
        <CircularProgress value={stats.disk} label="DISK" color="#7b2ff7" />
      </div>
      <div className="stats-footer">
        <div className="stat-row">
          <span className="stat-label">TIME</span>
          <span className="stat-value">{stats.time}</span>
        </div>
        <div className="stat-row">
          <span className="stat-label">DATE</span>
          <span className="stat-value">{stats.date}</span>
        </div>
        <div className="stat-row">
          <span className="stat-label">IP</span>
          <span className="stat-value">{stats.ip}</span>
        </div>
      </div>
    </div>
  )
}
