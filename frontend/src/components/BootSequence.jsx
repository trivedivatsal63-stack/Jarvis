import React, { useState, useEffect, useRef } from 'react'

const STEPS = [
  { label: 'Loading Neural Core...', duration: 800 },
  { label: 'Connecting Sensors...', duration: 600 },
  { label: 'Calibrating Voice Module...', duration: 700 },
  { label: 'Establishing Connections...', duration: 500 },
  { label: 'All systems nominal.', duration: 400 },
]

export default function BootSequence({ onComplete }) {
  const [currentStep, setCurrentStep] = useState(0)
  const [progress, setProgress] = useState(0)
  const [fadeOut, setFadeOut] = useState(false)
  const onCompleteRef = useRef(onComplete)
  onCompleteRef.current = onComplete

  useEffect(() => {
    if (currentStep >= STEPS.length) {
      setFadeOut(true)
      setTimeout(() => onCompleteRef.current(), 800)
      return
    }

    const step = STEPS[currentStep]
    setProgress(0)
    const interval = 30
    const increment = 100 / (step.duration / interval)

    const timer = setInterval(() => {
      setProgress((prev) => {
        const next = prev + increment
        if (next >= 100) {
          clearInterval(timer)
          setTimeout(() => setCurrentStep((c) => c + 1), 200)
          return 100
        }
        return next
      })
    }, interval)

    return () => clearInterval(timer)
  }, [currentStep])

  return (
    <div className={`boot-sequence ${fadeOut ? 'boot-fade-out' : ''}`}>
      <div className="boot-content">
        <div className="boot-title">
          <span className="boot-letter" style={{ animationDelay: '0s' }}>I</span>
          <span className="boot-letter" style={{ animationDelay: '0.1s' }}>N</span>
          <span className="boot-letter" style={{ animationDelay: '0.2s' }}>I</span>
          <span className="boot-letter" style={{ animationDelay: '0.3s' }}>T</span>
          <span className="boot-letter" style={{ animationDelay: '0.4s' }}>I</span>
          <span className="boot-letter" style={{ animationDelay: '0.5s' }}>A</span>
          <span className="boot-letter" style={{ animationDelay: '0.6s' }}>L</span>
          <span className="boot-letter" style={{ animationDelay: '0.7s' }}>I</span>
          <span className="boot-letter" style={{ animationDelay: '0.8s' }}>Z</span>
          <span className="boot-letter" style={{ animationDelay: '0.9s' }}>I</span>
          <span className="boot-letter" style={{ animationDelay: '1.0s' }}>N</span>
          <span className="boot-letter" style={{ animationDelay: '1.1s' }}>G</span>
          <span className="boot-letter" style={{ animationDelay: '1.2s' }}> </span>
          <span className="boot-letter" style={{ animationDelay: '1.3s' }}>J</span>
          <span className="boot-letter" style={{ animationDelay: '1.4s' }}>.</span>
          <span className="boot-letter" style={{ animationDelay: '1.5s' }}>A</span>
          <span className="boot-letter" style={{ animationDelay: '1.6s' }}>.</span>
          <span className="boot-letter" style={{ animationDelay: '1.7s' }}>R</span>
          <span className="boot-letter" style={{ animationDelay: '1.8s' }}>.</span>
          <span className="boot-letter" style={{ animationDelay: '1.9s' }}>V</span>
          <span className="boot-letter" style={{ animationDelay: '2.0s' }}>.</span>
          <span className="boot-letter" style={{ animationDelay: '2.1s' }}>I</span>
          <span className="boot-letter" style={{ animationDelay: '2.2s' }}>.</span>
          <span className="boot-letter" style={{ animationDelay: '2.3s' }}>S</span>
          <span className="boot-letter" style={{ animationDelay: '2.4s' }}>.</span>
        </div>

        <div className="boot-status">
          {currentStep < STEPS.length ? (
            <span className="boot-step-text">{STEPS[currentStep].label}</span>
          ) : (
            <span className="boot-step-text boot-done">Ready.</span>
          )}
        </div>

        <div className="boot-progress-bar">
          <div className="boot-progress-fill" style={{ width: `${progress}%` }} />
        </div>

        <div className="boot-percentage">{Math.round(progress)}%</div>

        {/* Arc Reactor mini */}
        <svg className="boot-reactor" viewBox="0 0 80 80" width="60" height="60">
          <circle cx="40" cy="40" r="36" fill="none" stroke="rgba(0,212,255,0.2)" strokeWidth="1" />
          <circle cx="40" cy="40" r="30" fill="none" stroke="rgba(0,212,255,0.3)" strokeWidth="0.8"
            strokeDasharray="4 6" className="boot-ring-spin" />
          <circle cx="40" cy="40" r="8" fill="#00d4ff" opacity="0.6" className="boot-pulse" />
        </svg>
      </div>
    </div>
  )
}
