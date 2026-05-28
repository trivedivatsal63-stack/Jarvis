import React from 'react'

export default function ArcReactor({ thinking = false, speaking = false }) {
  const speed = thinking || speaking ? '0.6s' : '3s'
  const glowIntensity = thinking || speaking ? '0.8' : '0.3'

  return (
    <div className="arc-reactor" style={{ '--speed': speed, '--glow': glowIntensity }}>
      <svg viewBox="0 0 200 200" className="w-full h-full">
        <defs>
          <radialGradient id="coreGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#00d4ff" stopOpacity={0.9} />
            <stop offset="50%" stopColor="#00d4ff" stopOpacity={0.4} />
            <stop offset="100%" stopColor="#00d4ff" stopOpacity="0" />
          </radialGradient>
          <filter id="glowFilter">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Outer glow */}
        <circle cx="100" cy="100" r="90" fill="url(#coreGlow)" opacity={glowIntensity} />

        {/* Outer ring */}
        <circle
          cx="100" cy="100" r="85" fill="none"
          stroke="#00d4ff" strokeWidth="2" opacity="0.3"
        />

        {/* Rotating outer ring */}
        <g className="reactor-ring-outer" style={{ animationDuration: speed }}>
          <circle
            cx="100" cy="100" r="82" fill="none"
            stroke="#00d4ff" strokeWidth="1.5" opacity="0.6"
            strokeDasharray="8 12"
          />
          {[0, 60, 120, 180, 240, 300].map((angle, i) => (
            <circle
              key={i}
              cx={100 + 82 * Math.cos((angle * Math.PI) / 180)}
              cy={100 + 82 * Math.sin((angle * Math.PI) / 180)}
              r="3" fill="#00d4ff" opacity="0.8"
            />
          ))}
        </g>

        {/* Counter-rotating inner ring */}
        <g className="reactor-ring-inner" style={{ animationDuration: speed }}>
          <circle
            cx="100" cy="100" r="60" fill="none"
            stroke="#00d4ff" strokeWidth="1" opacity="0.4"
            strokeDasharray="5 15"
          />
          {[30, 90, 150, 210, 270, 330].map((angle, i) => (
            <circle
              key={i}
              cx={100 + 60 * Math.cos((angle * Math.PI) / 180)}
              cy={100 + 60 * Math.sin((angle * Math.PI) / 180)}
              r="2" fill="#00ff9d" opacity="0.6"
            />
          ))}
        </g>

        {/* Central hexagon */}
        <g filter="url(#glowFilter)">
          <polygon
            points="100,40 144,65 144,115 100,140 56,115 56,65"
            fill="none" stroke="#00d4ff" strokeWidth="1.5" opacity="0.8"
            className="reactor-hex"
          />
          <polygon
            points="100,50 134,68 134,108 100,126 66,108 66,68"
            fill="none" stroke="#00ff9d" strokeWidth="0.8" opacity="0.4"
          />
          {/* Center dot */}
          <circle cx="100" cy="88" r="6" fill="#00d4ff" opacity="0.9" className="reactor-core" />
          <circle cx="100" cy="88" r="12" fill="none" stroke="#00d4ff" strokeWidth="0.5" opacity="0.5" />
          {/* Cross lines */}
          <line x1="70" y1="88" x2="130" y2="88" stroke="#00d4ff" strokeWidth="0.5" opacity="0.3" />
          <line x1="100" y1="58" x2="100" y2="118" stroke="#00d4ff" strokeWidth="0.5" opacity="0.3" />
        </g>

        {/* Corner arc markers */}
        {[45, 135, 225, 315].map((angle, i) => {
          const r = 78
          const x = 100 + r * Math.cos((angle * Math.PI) / 180)
          const y = 100 + r * Math.sin((angle * Math.PI) / 180)
          return (
            <circle key={i} cx={x} cy={y} r="2" fill="#ff6b00" opacity="0.9" />
          )
        })}
      </svg>
    </div>
  )
}
