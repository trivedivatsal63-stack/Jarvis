import React from 'react'

export default function HudOverlay({ visible = true }) {
  if (!visible) return null
  return (
    <>
      {/* Corner brackets */}
      <div className="hud-corner hud-corner-tl" />
      <div className="hud-corner hud-corner-tr" />
      <div className="hud-corner hud-corner-bl" />
      <div className="hud-corner hud-corner-br" />

      {/* Scanning line */}
      <div className="hud-scanline" />

      {/* Hexagonal grid background */}
      <svg className="hud-grid-bg" xmlns="http://www.w3.org/2000/svg" width="100%" height="100%">
        <defs>
          <pattern id="hexgrid" width="40" height="69.28" patternUnits="userSpaceOnUse"
            patternTransform="scale(1.5)">
            <path d="M40 17.32L20 5.77 0 17.32v23.04l20 11.55 20-11.55z" fill="none"
              stroke="rgba(0,212,255,0.04)" strokeWidth="0.5" />
            <path d="M20 40.41L0 28.86v11.55l20 11.55 20-11.55V28.86z" fill="none"
              stroke="rgba(0,212,255,0.03)" strokeWidth="0.5" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#hexgrid)" />
      </svg>
    </>
  )
}
